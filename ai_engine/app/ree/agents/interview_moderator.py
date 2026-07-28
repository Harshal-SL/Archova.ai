"""
Interview Moderator

Responsible for conducting adaptive stakeholder interviews.

Design principles:
  - Questions are reasoning-based, not field-fill-in-the-blank.
    The moderator reads the ReviewResult (ambiguities, contradictions,
    missing items, confidence scores) and generates questions that
    address the *root cause* of the review failure — not simply
    "field X is empty, please fill it."
  - Context is rich: questions use BusinessContext, DomainContext,
    DiscussionNotes, and the full ReviewResult to craft targeted questions.
  - Answers are applied back to the SRC parameters so the next review
    pass has richer input.
  - The interview loop repeats until the ReviewResult verdict is READY
    or the maximum rounds limit is reached.
  - Full interview history is stored in SRC.interview_session.

Does NOT:
  - Finalize ARSRS.
  - Modify the design generator.
  - Modify BusinessContext or DomainContext directly.
    (Only requirements.parameters are updated from answers.)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.ree.models import (
    CompletenessLevel,
    InterviewAnswer,
    InterviewQuestion,
    InterviewRound,
    InterviewSession,
    REEStatus,
    ReviewResult,
    ReviewVerdict,
    SharedRequirementContext,
)
from app.ree.llm import llm_gateway, LLMGateway
from app.ree.llm.model_registry import Capability
from app.services.elicitation.answer_merger import merge_answers

logger = logging.getLogger(__name__)

_AGENT_NAME = "InterviewModerator"
_STAGE = "interviewing"

# ── Prompt ────────────────────────────────────────────────────────────────────

_QUESTION_PROMPT = """\
AGENCY CONTRACT: Interview Moderator

RESPONSIBILITY:
You are the Interview Moderator. Your sole responsibility is to generate targeted clarification questions to reduce ambiguity in the requirements.
CRITICAL: Never invent requirements, never answer your own questions, and never modify requirement specifications directly.

WHAT TO GENERATE:
Up to {num_questions} targeted clarification questions that address ambiguities, missing critical parameters, or architectural tradeoffs identified in the review findings.

REVIEW FINDINGS:
{review_findings}

REQUIREMENTS CONTEXT:
{requirements_summary}

BUSINESS CONTEXT:
{business_context}

DOMAIN CONTEXT:
{domain_context}

DISCUSSION NOTES (recent):
{discussion_notes}

RULES:
- CRITICAL: Return ONLY a raw, valid JSON object starting with '{{' and ending with '}}'.
- Do NOT wrap the JSON in Markdown code fences (NO ```json).
- Do NOT include any preamble, intro, explanation, or postscript.
- Questions must address ROOT CAUSES found in the review findings above.
- Each question must have a clear rationale explaining why it is being asked.
- target_section must be one of: requirements, business_context, domain_context.
- priority must be: high, medium, or low.

OUTPUT SCHEMA:
{{
  "questions": [
    {{
      "question": "...",
      "rationale": "...",
      "target_section": "requirements",
      "target_field": "functional_requirements",
      "options": ["option A", "option B"],
      "priority": "high"
    }}
  ]
}}
"""

# Maximum questions per round — keeps the interview focused
_MAX_QUESTIONS_PER_ROUND = 5
_MIN_QUESTIONS_PER_ROUND = 2


class InterviewModerator:
    """
    Adaptive stakeholder interview conductor.

    Workflow per call to run():
      1. Read the current ReviewResult from the SRC.
      2. Build a rich context from ReviewResult + BusinessContext +
         DomainContext + DiscussionNotes.
      3. Call the LLM to generate targeted questions.
      4. Create a new InterviewRound with those questions.
      5. Store the round in SRC.interview_session.
      6. Return the SRC with INTERVIEWING status — the caller is
         expected to collect answers and call apply_answers().

    Workflow per call to apply_answers():
      1. Map answers back to questions by question_id.
      2. Apply answers to SRC.parameters via the existing answer_merger.
      3. Record which sections were updated.
      4. Close the round in SRC.interview_session.
      5. Return the updated SRC — the Orchestrator then runs Review again.
    """

    def __init__(self, gateway: Optional[LLMGateway] = None) -> None:
        self._gateway = gateway or llm_gateway

    # ── Public: generate questions ─────────────────────────────────────────

    def run(self, src: SharedRequirementContext) -> SharedRequirementContext:
        """
        Generate the next interview round's questions from the current SRC state.

        Reads SRC.review_result for the issues to address.
        Creates a new InterviewRound and stores it in SRC.interview_session.
        Sets SRC.status = INTERVIEWING.

        Args:
            src: SRC after a failed Review pass (verdict == NEED_CLARIFICATION).

        Returns:
            Updated SRC with clarification_questions populated and an open
            InterviewRound in SRC.interview_session.
        """
        src.status = REEStatus.INTERVIEWING
        session = src.get_or_create_interview_session()
        round_number = len(session.rounds) + 1

        logger.info(
            "%s: generating questions for round %d", _AGENT_NAME, round_number
        )

        # Determine how many questions to ask
        num_questions = self._determine_question_count(src)

        # Build the prompt context
        review_findings = _format_review_findings(src.review_result)
        requirements_summary = _format_requirements(src.parameters)
        business_ctx = _format_business_context(src.business_context)
        domain_ctx = _format_domain_context(src.domain_context)
        discussion_notes = _format_recent_notes(src.discussion_notes.notes, limit=5)

        # Decide whether to use LLM or fallback to rule-based generation
        questions: List[InterviewQuestion]
        if self._gateway.is_ready() and src.review_result is not None:
            questions = self._llm_generate_questions(
                review_findings=review_findings,
                requirements_summary=requirements_summary,
                business_context=business_ctx,
                domain_context=domain_ctx,
                discussion_notes=discussion_notes,
                num_questions=num_questions,
            )
        else:
            logger.info(
                "%s: LLM not available or no review result — using rule-based fallback",
                _AGENT_NAME,
            )
            questions = self._rule_based_questions(src)

        # Guarantee at least one question
        if not questions:
            questions = self._rule_based_questions(src)

        # ── Issue 9: Interview Memory Filtering ────────────────────────────────
        # Filter out questions addressing target fields that were already answered
        answered_fields: set = set()
        for r in session.rounds:
            for ans in r.answers:
                if ans.answer and str(ans.answer).strip():
                    answered_fields.add(str(ans.question_id).lower())

        for entry in src.interview_history:
            for ans in entry.get("answers", []):
                p = ans.get("parameter") or ans.get("target_field") or ans.get("question_id")
                if p and ans.get("answer_text"):
                    answered_fields.add(str(p).lower())

        if answered_fields:
            filtered_questions = [
                q for q in questions
                if (q.target_field or "").lower() not in answered_fields
                and q.question_id.lower() not in answered_fields
            ]
            if filtered_questions:
                questions = filtered_questions

        # ── Issue 6: Question Ranking & Hard Limit (Max 5) ────────────────────
        def _rank_key(q: InterviewQuestion) -> int:
            txt = (q.question + " " + (q.target_field or "") + " " + (q.target_section or "") + " " + (q.rationale or "")).lower()
            if any(k in txt for k in ["business decision", "business model", "goal", "business objective", "strategy", "critical"]):
                return 1
            if any(k in txt for k in ["functional requirement", "feature", "user capability", "workflow", "use case", "functional"]):
                return 2
            if any(k in txt for k in ["non-functional", "non functional", "performance", "sla", "latency", "uptime", "concurrency", "scalability", "security"]):
                return 3
            if any(k in txt for k in ["technical constraint", "database", "infrastructure", "cloud", "integration", "legacy", "compliance"]):
                return 4
            return 5

        questions.sort(key=_rank_key)
        questions = questions[:5]

        # Create the interview round
        interview_round = InterviewRound(
            round_number=round_number,
            questions=questions,
        )
        session.add_round(interview_round)

        # Sync to the flat clarification_questions field (backward compat)
        src.clarification_questions = [
            {
                "parameter": q.target_field or q.target_section,
                "question": q.question,
                "options": q.options,
                "rationale": q.rationale,
                "priority": q.priority,
                "question_id": q.question_id,
            }
            for q in questions
        ]
        src.interview_round = round_number

        src.add_note(
            _STAGE, _AGENT_NAME,
            f"Round {round_number}: Generated {len(questions)} question(s). "
            + (
                f"Addressing: {', '.join(q.target_field or q.target_section for q in questions[:3])}."
                if questions else "No questions generated."
            ),
        )

        logger.info(
            "%s: round %d ready — %d question(s)", _AGENT_NAME, round_number, len(questions)
        )
        return src

    # ── Public: apply answers ──────────────────────────────────────────────

    def apply_answers(
        self,
        src: SharedRequirementContext,
        raw_answers: List[Dict[str, Any]],
    ) -> SharedRequirementContext:
        """
        Apply stakeholder answers to the SRC and close the current round.

        Answers are in the format:
            [{"question_id": "...", "answer": "..."}, ...]

        For backward compatibility also accepts:
            [{"parameter": "...", "answer": "..."}, ...]

        Args:
            src: SRC with an open InterviewRound.
            raw_answers: Stakeholder answers to the current round's questions.

        Returns:
            Updated SRC with parameters enriched and round closed.
        """
        if not raw_answers:
            logger.warning("%s: apply_answers called with empty answers list", _AGENT_NAME)
            return src

        session = src.get_or_create_interview_session()
        current = session.current_round()

        if current is None:
            logger.warning(
                "%s: apply_answers called but no open round found", _AGENT_NAME
            )
            return src

        logger.info(
            "%s: applying %d answer(s) to round %d",
            _AGENT_NAME, len(raw_answers), current.round_number,
        )

        # Build question_id → question map for this round
        qid_map: Dict[str, InterviewQuestion] = {
            q.question_id: q for q in current.questions
        }

        # Normalise answers → InterviewAnswer objects
        # Also build the legacy {parameter: ..., answer: ...} format for merge_answers
        interview_answers: List[InterviewAnswer] = []
        param_answers: List[Dict[str, str]] = []
        updated_sections: List[str] = []

        for raw in raw_answers:
            answer_text = str(raw.get("answer", "")).strip()
            if not answer_text:
                continue

            question_id = str(raw.get("question_id", "")).strip()
            param_key = str(raw.get("parameter", "")).strip()

            # Try to look up the question for richer context
            question: Optional[InterviewQuestion] = qid_map.get(question_id)
            if question is None:
                match_key = param_key or question_id
                if match_key:
                    question = next(
                        (q for q in current.questions if q.target_field == match_key or q.question_id == match_key),
                        None,
                    )

            resolved_field = (
                (question.target_field if question and question.target_field else None)
                or param_key
                or question_id
            )
            resolved_section = (
                (question.target_section if question and question.target_section else None)
                or "requirements"
            )

            interview_answers.append(InterviewAnswer(
                question_id=question_id or resolved_field,
                answer=answer_text,
            ))

            if resolved_field:
                param_answers.append({"parameter": resolved_field, "answer": answer_text})
                if resolved_section not in updated_sections:
                    updated_sections.append(resolved_section)

        # Apply to SRC parameters using the existing merge_answers utility
        if param_answers:
            src.parameters = merge_answers(src.parameters, param_answers)
            for item in param_answers:
                pk = item.get("parameter")
                pv = src.get_parameter_value(pk)
                if pk and pv is not None:
                    src.set_parameter_value(pk, pv)
            src.sync_parameters()

        # Record answers in the interview round
        current.answers = interview_answers
        current.updated_sections = updated_sections
        current.completed_at = datetime.now(timezone.utc).isoformat()

        # Also update the legacy interview_history flat field
        src.interview_history.append({
            "round": current.round_number,
            "questions": [q.to_dict() for q in current.questions],
            "answers": [
                {"parameter": a.question_id, "answer": a.answer}
                for a in interview_answers
            ],
            "updated_sections": updated_sections,
            "completed_at": current.completed_at,
        })

        src.add_note(
            _STAGE, _AGENT_NAME,
            f"Round {current.round_number} complete. "
            f"Applied {len(interview_answers)} answer(s). "
            f"Updated sections: {', '.join(updated_sections) or 'none'}.",
        )

        logger.info(
            "%s: round %d complete — %d param(s) updated, sections: %s",
            _AGENT_NAME,
            current.round_number,
            len(param_answers),
            updated_sections,
        )
        return src

    # ── LLM question generation ────────────────────────────────────────────

    def _llm_generate_questions(
        self,
        review_findings: str,
        requirements_summary: str,
        business_context: str,
        domain_context: str,
        discussion_notes: str,
        num_questions: int,
    ) -> List[InterviewQuestion]:
        """Call the LLM to generate adaptive questions. Returns [] on failure."""
        prompt = _QUESTION_PROMPT.format(
            review_findings=review_findings,
            requirements_summary=requirements_summary,
            business_context=business_context,
            domain_context=domain_context,
            discussion_notes=discussion_notes,
            num_questions=num_questions,
        )

        result = self._gateway.complete(
            capability=Capability.INTERVIEW,
            prompt=prompt,
            max_tokens=1500,
            temperature=0.3,
            agent_name=_AGENT_NAME,
        )

        if result is None:
            logger.warning("%s: LLM returned None — falling back to rule-based", _AGENT_NAME)
            return []

        raw_questions = result.get("questions", [])
        if not isinstance(raw_questions, list):
            logger.warning("%s: LLM response missing questions array", _AGENT_NAME)
            return []

        questions: List[InterviewQuestion] = []
        for item in raw_questions:
            if not isinstance(item, dict):
                continue
            question_text = str(item.get("question", "")).strip()
            if not question_text:
                continue
            questions.append(InterviewQuestion(
                question_id=str(uuid.uuid4())[:8],
                question=question_text,
                rationale=str(item.get("rationale", "")).strip(),
                target_section=str(item.get("target_section", "requirements")).strip(),
                target_field=item.get("target_field") or None,
                options=[str(o) for o in item.get("options", []) if o],
                priority=str(item.get("priority", "medium")).lower(),
            ))

        return questions[:_MAX_QUESTIONS_PER_ROUND]

    # ── Rule-based fallback question generation ────────────────────────────

    def _rule_based_questions(
        self, src: SharedRequirementContext
    ) -> List[InterviewQuestion]:
        """
        Generate targeted questions from ReviewResult findings without the LLM.

        Order of priority:
          1. Missing critical fields (goal, functional_requirements, system_type)
          2. Ambiguities flagged by the review agent (highest severity first)
          3. Contradictions found by the review agent
          4. Missing important fields
        """
        questions: List[InterviewQuestion] = []
        review = src.review_result

        # 1. Address ambiguities first — most actionable
        if review and review.ambiguities:
            sorted_amb = sorted(
                review.ambiguities,
                key=lambda a: {"high": 0, "medium": 1, "low": 2}.get(a.severity, 1),
            )
            for amb in sorted_amb[:2]:
                questions.append(InterviewQuestion(
                    question_id=str(uuid.uuid4())[:8],
                    question=f"Regarding '{amb.field}': {amb.description} "
                             f"Can you clarify what you mean?",
                    rationale=f"The review identified an ambiguity in '{amb.field}' "
                               f"(severity: {amb.severity}) that would affect architecture decisions.",
                    target_section="requirements",
                    target_field=amb.field,
                    options=[],
                    priority=amb.severity,
                ))

        # 2. Address contradictions
        if review and review.contradictions and len(questions) < _MAX_QUESTIONS_PER_ROUND:
            for contradiction in review.contradictions[:1]:
                questions.append(InterviewQuestion(
                    question_id=str(uuid.uuid4())[:8],
                    question=(
                        f"There appears to be a conflict between '{contradiction.field_a}' "
                        f"and '{contradiction.field_b}': {contradiction.description} "
                        f"Which should take priority?"
                    ),
                    rationale="Contradicting requirements prevent a consistent architecture design.",
                    target_section="requirements",
                    target_field=contradiction.field_a,
                    options=[
                        f"Prioritise {contradiction.field_a}",
                        f"Prioritise {contradiction.field_b}",
                        "Both are required — redesign needed",
                        "Neither is a hard requirement",
                    ],
                    priority="high",
                ))

        # 3. Missing critical and important fields
        missing_all = (
            (review.missing_items if review else [])
            or src.missing_parameters
        )
        _field_questions = {
            "goal": (
                "What is the primary business goal this system needs to achieve? "
                "Please describe it in terms of business outcome, not technical implementation.",
                ["Increase revenue / user acquisition",
                 "Reduce operational cost or manual effort",
                 "Improve customer experience or satisfaction",
                 "Achieve regulatory compliance",
                 "Replace or modernise a legacy system"],
                "business_context",
                "high",
            ),
            "functional_requirements": (
                "What are the 3–5 most critical features the system must deliver "
                "on day one (MVP)? Please list them in order of business priority.",
                [],
                "requirements",
                "high",
            ),
            "system_type": (
                "How would you classify this system architecturally? "
                "This helps select the right architecture patterns.",
                ["Consumer-facing web / mobile application",
                 "Internal tooling / back-office system",
                 "B2B API / integration platform",
                 "Data pipeline / analytics platform",
                 "Real-time event-driven system",
                 "IoT or embedded system"],
                "domain_context",
                "high",
            ),
            "non_functional_requirements": (
                "What are the most critical quality attributes? "
                "For example: expected user load, response time targets, uptime SLA, "
                "compliance requirements (GDPR, HIPAA, PCI-DSS).",
                ["< 200ms response time for core user actions",
                 "99.9%+ availability (three-nines)",
                 "Support 100k+ concurrent users",
                 "GDPR / data privacy compliance",
                 "Zero-downtime deployments"],
                "requirements",
                "medium",
            ),
            "actors": (
                "Who will use this system? Please list the distinct user roles "
                "and briefly describe what each role does.",
                ["End user / customer",
                 "Admin / operator",
                 "Third-party / API consumer",
                 "Internal staff",
                 "Automated system / service"],
                "requirements",
                "medium",
            ),
            "system_behaviour": (
                "How should the system behave when it is under heavy load or "
                "when a critical component fails?",
                ["Serve cached data — graceful degradation",
                 "Reject new requests — circuit breaker",
                 "Queue requests and retry — async resilience",
                 "Auto-scale to absorb the load",
                 "Fail fast with a clear error message"],
                "requirements",
                "medium",
            ),
            "core_objectives": (
                "What are the 2–3 measurable success criteria for this project? "
                "How will you know it has been delivered successfully?",
                ["Specific user adoption target (e.g. 10k MAU in 3 months)",
                 "Performance benchmark met (e.g. < 100ms p99 latency)",
                 "Revenue or cost target achieved",
                 "Feature parity with existing system",
                 "Successful launch on schedule"],
                "business_context",
                "medium",
            ),
        }

        for field in missing_all:
            if len(questions) >= _MAX_QUESTIONS_PER_ROUND:
                break
            if field in _field_questions:
                q_text, opts, section, priority = _field_questions[field]
                questions.append(InterviewQuestion(
                    question_id=str(uuid.uuid4())[:8],
                    question=q_text,
                    rationale=(
                        f"The review found '{field}' is missing or incomplete. "
                        "This field is needed to determine a suitable architecture."
                    ),
                    target_section=section,
                    target_field=field,
                    options=opts,
                    priority=priority,
                ))

        # Final fallback — generic catch-all
        if not questions:
            questions.append(InterviewQuestion(
                question_id=str(uuid.uuid4())[:8],
                question=(
                    "The requirements review could not reach a confident verdict. "
                    "Could you provide more detail about the most important aspect "
                    "of the system that is still unclear?"
                ),
                rationale="Insufficient information to proceed with architecture generation.",
                target_section="requirements",
                target_field=None,
                options=[],
                priority="high",
            ))

        return questions[:_MAX_QUESTIONS_PER_ROUND]

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _determine_question_count(src: SharedRequirementContext) -> int:
        """
        Decide how many questions to generate this round.

        More questions when there are many issues; fewer in later rounds
        to avoid interview fatigue.
        """
        review = src.review_result
        if review is None:
            return _MIN_QUESTIONS_PER_ROUND

        issue_count = (
            len(review.missing_items)
            + len(review.ambiguities)
            + len(review.contradictions)
        )
        round_num = src.interview_round + 1

        # Reduce questions in later rounds
        base = min(issue_count, _MAX_QUESTIONS_PER_ROUND)
        adjusted = max(_MIN_QUESTIONS_PER_ROUND, base - (round_num - 1))
        return adjusted


# ── Context formatting helpers ─────────────────────────────────────────────────


def _format_review_findings(review: Optional[ReviewResult]) -> str:
    """Build a compact summary of the ReviewResult for the LLM prompt."""
    if review is None:
        return "No review result available."

    lines = [
        f"Verdict: {review.verdict.value}",
        f"Confidence: {review.confidence.overall:.0%}",
    ]

    if review.missing_items:
        lines.append(f"Missing items: {', '.join(review.missing_items)}")

    if review.ambiguities:
        lines.append("Ambiguities:")
        for a in review.ambiguities[:4]:
            lines.append(f"  [{a.severity.upper()}] {a.field}: {a.description}")

    if review.contradictions:
        lines.append("Contradictions:")
        for c in review.contradictions[:2]:
            lines.append(f"  {c.field_a} vs {c.field_b}: {c.description}")

    if review.review_summary:
        lines.append(f"Summary: {review.review_summary}")

    return "\n".join(lines)


def _format_requirements(parameters: dict) -> str:
    """Build a compact summary of current requirements."""
    lines: List[str] = []
    _CORE_KEYS = [
        "goal", "system_type", "functional_requirements",
        "non_functional_requirements", "actors", "system_behaviour",
        "core_objectives", "external_services",
    ]
    for key in _CORE_KEYS:
        node = parameters.get(key)
        if node is None:
            lines.append(f"{key}: [MISSING]")
            continue
        value = node.get("value") if isinstance(node, dict) else node
        if value is None or value == [] or value == "":
            lines.append(f"{key}: [EMPTY]")
        elif isinstance(value, list):
            lines.append(f"{key}: {'; '.join(str(v) for v in value[:3])}"
                         + (" ..." if len(value) > 3 else ""))
        else:
            lines.append(f"{key}: {str(value)[:120]}")
    return "\n".join(lines)


def _format_business_context(bc) -> str:
    parts: List[str] = []
    if bc.domain:
        parts.append(f"Domain: {bc.domain}")
    if bc.business_objectives:
        parts.append(f"Goals: {'; '.join(bc.business_objectives[:3])}")
    if bc.stakeholders:
        parts.append(f"Stakeholders: {'; '.join(bc.stakeholders[:3])}")
    if bc.constraints:
        parts.append(f"Constraints: {'; '.join(bc.constraints[:2])}")
    return "\n".join(parts) if parts else "No business context available."


def _format_domain_context(dc) -> str:
    parts: List[str] = []
    if dc.system_type:
        parts.append(f"System type: {dc.system_type}")
    if dc.architecture_patterns:
        parts.append(f"Patterns: {'; '.join(dc.architecture_patterns[:3])}")
    compliance = getattr(dc, "compliance", [])
    if compliance:
        parts.append(f"Compliance: {'; '.join(compliance[:2])}")
    risks = getattr(dc, "risks", [])
    if risks:
        parts.append(f"Risks: {'; '.join(risks[:2])}")
    return "\n".join(parts) if parts else "No domain context available."


def _format_recent_notes(notes: List[Dict[str, Any]], limit: int = 5) -> str:
    if not notes:
        return "No discussion notes yet."
    recent = notes[-limit:]
    lines = [
        f"[{n.get('agent', '?')}] {n.get('note', '')[:150]}"
        for n in recent
    ]
    return "\n".join(lines)
