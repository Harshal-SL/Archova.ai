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
from app.ree.agents.answer_merger import merge_answers

logger = logging.getLogger(__name__)

_AGENT_NAME = "InterviewModerator"
_STAGE = "interviewing"

# ── Prompt ────────────────────────────────────────────────────────────────────

_QUESTION_PROMPT = """\
Generate {num_questions} plain-language, non-technical clarification questions for business stakeholders to finalize requirements for this project:

PROJECT DESCRIPTION:
{project_description}

AMBIGUITIES & FINDINGS:
{review_findings}

RULES:
1. NON-TECHNICAL: Ask about business rules, operational policies, user roles, limits, or notifications in simple English (no developer jargon).
2. PROBLEM-SPECIFIC: Tightly tailored to the project above.
3. FOR EVERY QUESTION, provide 5 options:
   - 3 Best Suitable domain options
   - 1 Recommended Default option (labeled with '(Recommended Default)')
   - 1 Custom option: 'Other / Custom (Please specify)'
4. Output MUST be ONLY valid, raw JSON (no ```json code fences, no intro, no thinking text).

REQUIRED JSON FORMAT:
{{
  "questions": [
    {{
      "question": "What is the standard policy for borrowing duration and item renewals?",
      "rationale": "Clarifies loan periods and member circulation limits.",
      "target_section": "requirements",
      "target_field": "loan_period_policy",
      "options": [
        "14-day loan period with up to 1 renewal allowed",
        "21-day loan period with no renewals permitted",
        "30-day flexible loan period for students and faculty",
        "14-day loan period with up to 2 renewals if no reservations exist (Recommended Default)",
        "Other / Custom (Please specify)"
      ],
      "default_option": "14-day loan period with up to 2 renewals if no reservations exist (Recommended Default)",
      "priority": "high"
    }}
  ]
}}
"""

# Pair-wise question generation — exactly 2 focused questions per round
_MAX_QUESTIONS_PER_ROUND = 2
_MIN_QUESTIONS_PER_ROUND = 2


def _normalize_options_set(
    raw_opts: List[str],
    default_opt: Optional[str] = None,
    question_text: str = "",
) -> Tuple[List[str], str]:
    """
    Ensure every question has:
      - 3 suitable options
      - 1 default option (marked Recommended Default)
      - 1 Custom option ('Other / Custom (Please specify)')
    Returns (normalized_options_list, default_option_str)
    """
    clean_opts: List[str] = []
    for o in raw_opts:
        s = str(o).strip()
        if s and s.lower() not in (
            "option a", "option b", "option c", "option d",
            "option 1", "option 2", "option 3", "choice a", "choice b",
            "placeholder", "none", "n/a"
        ):
            if s not in clean_opts:
                clean_opts.append(s)

    # Filter out custom placeholder if already present
    non_custom_opts = [
        o for o in clean_opts
        if not any(k in o.lower() for k in ["other / custom", "custom (please specify)", "other (please specify)"])
    ]

    # Identify or synthesize recommended default option
    resolved_default = default_opt
    if not resolved_default or resolved_default not in non_custom_opts:
        def_match = next((o for o in non_custom_opts if "recommended" in o.lower() or "default" in o.lower()), None)
        if def_match:
            resolved_default = def_match
        elif non_custom_opts:
            resolved_default = non_custom_opts[0]
            if not ("(recommended default)" in resolved_default.lower() or "(default)" in resolved_default.lower()):
                tagged = f"{resolved_default} (Recommended Default)"
                idx = non_custom_opts.index(resolved_default)
                non_custom_opts[idx] = tagged
                resolved_default = tagged
        else:
            resolved_default = "Standard system default (Recommended Default)"
            non_custom_opts.append(resolved_default)

    # Ensure we have at least 3 suitable options + 1 default
    if len(non_custom_opts) < 4:
        sample_fallbacks = [
            "Self-service option for registered users with email confirmation",
            "Staff / Admin review required before confirming request",
            "Automated instant processing with real-time status updates",
            "Standard workflow with automated notification alerts (Recommended Default)"
        ]
        for fb in sample_fallbacks:
            if fb not in non_custom_opts and len(non_custom_opts) < 4:
                non_custom_opts.append(fb)

    # Keep 4 non-custom options (3 choices + 1 Default)
    final_opts = list(non_custom_opts[:4])
    if resolved_default not in final_opts and final_opts:
        final_opts[-1] = resolved_default

    # Append custom option at the end
    custom_label = "Other / Custom (Please specify)"
    if custom_label not in final_opts:
        final_opts.append(custom_label)

    return final_opts, resolved_default


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
        project_desc = src.project_context.normalized_text or src.raw_input
        review_findings = _format_review_findings(src.review_result)
        requirements_summary = _format_requirements(src.parameters)
        business_ctx = _format_business_context(src.business_context)
        domain_ctx = _format_domain_context(src.domain_context)
        discussion_notes = _format_recent_notes(src.discussion_notes.notes, limit=5)

        # Decide whether to use LLM or fallback to rule-based generation
        questions: List[InterviewQuestion]
        if self._gateway.is_ready() and src.review_result is not None:
            questions = self._llm_generate_questions(
                project_description=project_desc,
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
        questions = questions[:_MAX_QUESTIONS_PER_ROUND]

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
                "default_option": q.default_option,
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
            src.flags.interview_answers_changed = True

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
        project_description: str,
        review_findings: str,
        requirements_summary: str,
        business_context: str,
        domain_context: str,
        discussion_notes: str,
        num_questions: int,
    ) -> List[InterviewQuestion]:
        """Call the LLM to generate adaptive questions. Returns [] on failure."""
        prompt = _QUESTION_PROMPT.format(
            project_description=project_description[:2000],
            review_findings=review_findings,
            num_questions=num_questions,
        )

        result = self._gateway.complete(
            capability=Capability.INTERVIEW,
            prompt=prompt,
            max_tokens=600,
            temperature=0.1,
            system_prompt="You are a strict JSON generator. Output ONLY a valid JSON object starting with { and ending with }. Do NOT write any markdown fences, preamble, or commentary.",
            agent_name=_AGENT_NAME,
        )

        if result is None:
            logger.warning("%s: LLM returned None — falling back to rule-based", _AGENT_NAME)
            return []

        if isinstance(result, list):
            raw_questions = result
        elif isinstance(result, dict):
            raw_questions = result.get("questions", [])
            if not raw_questions and "items" in result:
                raw_questions = result.get("items", [])
        else:
            raw_questions = []

        if not isinstance(raw_questions, list):
            logger.warning("%s: LLM response missing questions array", _AGENT_NAME)
            return []

        questions: List[InterviewQuestion] = []
        for item in raw_questions:
            if not isinstance(item, dict):
                continue
            question_text = str(
                item.get("question")
                or item.get("question_text")
                or item.get("text")
                or item.get("prompt")
                or item.get("clarification")
                or item.get("title")
                or item.get("q")
                or ""
            ).strip()
            if not question_text:
                continue

            raw_opts = item.get("options") or item.get("suggested_options") or item.get("choices") or []
            if isinstance(raw_opts, str):
                raw_opts = [o.strip() for o in raw_opts.split(",") if o.strip()]
            elif not isinstance(raw_opts, list):
                raw_opts = []

            clean_opts, default_opt = _normalize_options_set(
                raw_opts=raw_opts,
                default_opt=item.get("default_option"),
                question_text=question_text,
            )

            questions.append(InterviewQuestion(
                question_id=str(item.get("question_id") or uuid.uuid4())[:8],
                question=question_text,
                rationale=str(item.get("rationale") or item.get("reason") or item.get("description") or "").strip(),
                target_section=str(item.get("target_section", "requirements")).strip(),
                target_field=item.get("target_field") or item.get("parameter") or None,
                options=clean_opts,
                default_option=default_opt,
                priority=str(item.get("priority", "medium")).lower(),
            ))

        return questions[:_MAX_QUESTIONS_PER_ROUND]

    # ── Rule-based fallback question generation ────────────────────────────

    def _rule_based_questions(
        self, src: SharedRequirementContext
    ) -> List[InterviewQuestion]:
        """
        Generate domain-specific, non-technical questions from the project description
        and review findings without requiring an LLM.
        """
        questions: List[InterviewQuestion] = []
        project_raw = (src.project_context.normalized_text or src.raw_input).lower()

        # ── Comprehensive Domain-Adaptive Fast-Path Question Packs ─────────
        if any(k in project_raw for k in ["librar", "book", "borrow", "loan", "catalog", "circulation"]):
            domain_q_defs = [
                (
                    "What is the standard borrowing duration and renewal policy for members?",
                    "Defines loan period limits, renewal conditions, and member circulation rules.",
                    "loan_policy",
                    [
                        "14-day loan period with up to 1 renewal allowed",
                        "21-day loan period with no renewals permitted",
                        "30-day flexible loan period for students and faculty",
                        "14-day loan period with up to 2 renewals if no reservations exist (Recommended Default)",
                    ],
                ),
                (
                    "How should book reservations and waitlists be handled when a copy is returned?",
                    "Clarifies hold duration and notification policies for reserved items.",
                    "reservation_policy",
                    [
                        "First-come, first-served hold for 48 hours with email alert",
                        "Notify all waitlisted members simultaneously (first to claim receives it)",
                        "Allow reservations only if fewer than 3 members are currently waiting",
                        "Hold book for top waitlisted member for 48 hours before notifying the next person (Recommended Default)",
                    ],
                ),
            ]
        elif any(k in project_raw for k in ["shop", "store", "e-commerce", "ecommerce", "cart", "product", "checkout", "order", "retail"]):
            domain_q_defs = [
                (
                    "What payment and checkout methods should be supported for customers?",
                    "Determines customer checkout workflows and payment processing integration.",
                    "payment_methods",
                    [
                        "Credit/Debit cards only",
                        "Cards, Digital Wallets (Apple Pay/Google Pay), and Cash on Delivery",
                        "Direct Bank Transfer and Buy Now Pay Later (BNPL)",
                        "Cards, Digital Wallets, and Net Banking (Recommended Default)",
                    ],
                ),
                (
                    "What is the return and refund policy timeframe for delivered orders?",
                    "Clarifies customer satisfaction workflows and inventory restocking logic.",
                    "return_policy",
                    [
                        "7-day return window with instant store credit",
                        "14-day return window with original payment refund",
                        "30-day exchange only for unopened items",
                        "14-day return window with customer-selected refund or store credit (Recommended Default)",
                    ],
                ),
            ]
        elif any(k in project_raw for k in ["hospital", "clinic", "patient", "doctor", "health", "medical", "appointment", "pharmacy"]):
            domain_q_defs = [
                (
                    "How should patients be able to book and reschedule appointments?",
                    "Clarifies patient scheduling channels and operational calendar management.",
                    "booking_policy",
                    [
                        "Online self-service portal with instant appointment confirmation",
                        "Online request followed by staff phone confirmation",
                        "Walk-in registration and front-desk phone booking only",
                        "Online portal with instant confirmation and automated calendar invite (Recommended Default)",
                    ],
                ),
                (
                    "What is the cancellation and reminder policy for scheduled appointments?",
                    "Minimizes clinic no-shows and defines appointment slot reallocation.",
                    "cancellation_policy",
                    [
                        "Free cancellation up to 2 hours before the appointment",
                        "Strict 24-hour advance cancellation required",
                        "Automated SMS reminder 24 hours prior with one-click confirmation",
                        "24-hour advance cancellation with SMS reminder 48 hours prior (Recommended Default)",
                    ],
                ),
            ]
        elif any(k in project_raw for k in ["college", "university", "student", "course", "lms", "school", "exam", "grade", "faculty", "academic"]):
            domain_q_defs = [
                (
                    "How should course enrollment and student class capacity limits be managed?",
                    "Defines course registration eligibility and waitlist policies.",
                    "enrollment_policy",
                    [
                        "First-come, first-served enrollment with hard seat caps",
                        "Advisor approval required before enrolling in any course",
                        "Priority enrollment for graduating seniors, then open registration",
                        "Automated online registration with waitlist auto-promotion (Recommended Default)",
                    ],
                ),
                (
                    "How should grades and academic feedback be published to students?",
                    "Establishes grading privacy standards and instructor approval workflows.",
                    "grading_policy",
                    [
                        "Instant publication as soon as instructor submits each assignment grade",
                        "Grades held until end of term and released simultaneously",
                        "Department head approval required before releasing final semester grades",
                        "Continuous gradebook visibility with automated notifications on grade post (Recommended Default)",
                    ],
                ),
            ]
        elif any(k in project_raw for k in ["event", "ticket", "conference", "booking", "venue", "seminar", "workshop", "festival"]):
            domain_q_defs = [
                (
                    "How should attendee ticketing and seat reservations be organized?",
                    "Defines registration tiers, attendee capacity, and ticket dispatch.",
                    "ticketing_policy",
                    [
                        "Single general admission tier with digital QR code ticket",
                        "Multi-tiered tickets (VIP, Standard, Early Bird) with reserved seating",
                        "Free RSVP with confirmation email and entry pass",
                        "Tiered ticketing with QR code mobile entry passes and refund options (Recommended Default)",
                    ],
                ),
                (
                    "What is the policy for event cancellation or attendee refund requests?",
                    "Sets attendee financial expectations and organizer liability terms.",
                    "event_refund_policy",
                    [
                        "No refunds permitted under any circumstances",
                        "Full refund allowed up to 7 days before event start",
                        "Ticket transfer to another attendee permitted at zero fee",
                        "Full refund up to 7 days prior or ticket transfer to another attendee (Recommended Default)",
                    ],
                ),
            ]
        elif any(k in project_raw for k in ["bank", "finance", "fintech", "wallet", "payment", "loan", "invest", "crypto", "trading"]):
            domain_q_defs = [
                (
                    "What identity verification (KYC) requirements should apply for user transactions?",
                    "Ensures compliance with financial regulations and user verification standards.",
                    "kyc_policy",
                    [
                        "Basic email and phone verification for low-limit transfers",
                        "Government ID upload and facial verification required for all accounts",
                        "Tiered verification: basic for transactions under $500, full KYC for higher amounts",
                        "Tiered verification with automated ID verification and instant approval (Recommended Default)",
                    ],
                ),
                (
                    "What transaction approval workflow should be required for large fund transfers?",
                    "Prevents unauthorized transactions and protects user funds.",
                    "transfer_security_policy",
                    [
                        "Standard password confirmation on submit",
                        "Mandatory Two-Factor Authentication (SMS/Authenticator OTP) for all transfers",
                        "Dual-authorization (Two signatories required) for corporate accounts",
                        "Biometric/OTP confirmation with temporary hold on unusually large transfers (Recommended Default)",
                    ],
                ),
            ]
        elif any(k in project_raw for k in ["food", "restaurant", "dining", "menu", "kitchen", "recipe", "delivery"]):
            domain_q_defs = [
                (
                    "How should customer orders be transmitted to the kitchen and tracked?",
                    "Streamlines kitchen workflow and order fulfillment status.",
                    "kitchen_order_flow",
                    [
                        "Printed physical tickets at the kitchen station",
                        "Live Kitchen Display System (KDS) tablet with status taps",
                        "Automated queue assignment based on item preparation time",
                        "Digital Kitchen Display System with real-time customer status tracking (Recommended Default)",
                    ],
                ),
                (
                    "What order modification and cancellation window should customers have?",
                    "Balances customer flexibility with kitchen food preparation timing.",
                    "order_change_policy",
                    [
                        "No order changes allowed once payment is submitted",
                        "Modifications allowed within 2 minutes of placing the order",
                        "Full cancellation allowed until the kitchen accepts the order",
                        "Modifications or cancellation allowed until food preparation begins (Recommended Default)",
                    ],
                ),
            ]
        elif any(k in project_raw for k in ["delivery", "courier", "logistics", "fleet", "tracking", "shipment", "warehouse"]):
            domain_q_defs = [
                (
                    "How should delivery drivers or couriers be assigned to incoming shipments?",
                    "Optimizes dispatch efficiency and route allocation.",
                    "driver_dispatch_policy",
                    [
                        "Manual dispatch by logistics coordinator",
                        "Broadcast to all nearby drivers (first to accept gets shipment)",
                        "Automated assignment based on driver proximity and current load",
                        "Automated proximity-based assignment with driver acceptance timeout (Recommended Default)",
                    ],
                ),
                (
                    "How should delivery confirmation and proof of delivery be captured?",
                    "Ensures reliable shipment handoff and customer verification.",
                    "proof_of_delivery",
                    [
                        "Customer physical signature only",
                        "Driver photo of package at doorstep with GPS timestamp",
                        "One-Time Password (OTP) provided by customer to driver at delivery",
                        "Customer OTP confirmation or photo proof with GPS timestamp (Recommended Default)",
                    ],
                ),
            ]
        else:
            domain_q_defs = [
                (
                    "Who should have administrative authority to manage user accounts and system configuration?",
                    "Establishes role-based permission boundaries and administrative control.",
                    "user_roles_policy",
                    [
                        "Single central administrator with complete access",
                        "Department managers and delegated team leads",
                        "Multi-tiered roles: Super Admin, Staff Manager, and Regular User",
                        "Standard role-based access: Administrator, Staff, and Standard User (Recommended Default)",
                    ],
                ),
                (
                    "How should users and staff receive important updates and system alerts?",
                    "Defines primary notification channels and messaging preferences.",
                    "notification_preferences",
                    [
                        "Email notifications for all major events",
                        "In-app notification center on user dashboard only",
                        "SMS alerts for critical time-sensitive actions",
                        "Email notifications with in-app dashboard alert badge (Recommended Default)",
                    ],
                ),
            ]

        for q_text, rationale, field_name, opt_list in domain_q_defs:
            if len(questions) >= _MAX_QUESTIONS_PER_ROUND:
                break
            clean_opts, def_opt = _normalize_options_set(opt_list, question_text=q_text)
            questions.append(InterviewQuestion(
                question_id=str(uuid.uuid4())[:8],
                question=q_text,
                rationale=rationale,
                target_section="requirements",
                target_field=field_name,
                options=clean_opts,
                default_option=def_opt,
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
        # Always generate focused pairs (2 questions per round)
        return _MAX_QUESTIONS_PER_ROUND


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
