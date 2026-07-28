"""
REE Orchestrator

The single deterministic workflow controller for the Requirements Engineering Engine.
No AI reasoning happens here — the Orchestrator only decides what runs next.

Workflow:
  1. Input Understanding   — parse + normalise stakeholder input
  2. Engineering Team      — parallel AI specialists enrich the SRC
  3. Requirement Review    — Technical Lead assesses readiness
  4. Interview Loop        — if NEED_CLARIFICATION:
       a. Interview Moderator generates questions → return to caller
       b. Caller submits answers → Moderator applies them to SRC
       c. Requirement Review runs again
       d. Repeat until READY or max rounds reached
  5. Finalization          — assemble the ARSRS

Two execution modes:
  Fresh start  — REERequest with only combined_prompt
  Resume       — REERequest with prior_src (full SRC dict) + interview_answers
                 The Orchestrator restores state and continues from where it left off.

The Orchestrator NEVER modifies the SRC directly.
All SRC mutations go through the appropriate agent.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.ree.models import (
    CompletenessLevel,
    REERequest,
    REEResponse,
    REEStatus,
    ReviewVerdict,
    SharedRequirementContext,
)
from app.ree.agents import (
    InputUnderstandingAgent,
    EngineeringTeamAgent,
    RequirementReviewAgent,
    InterviewModerator,
    FinalizationAgent,
)
from app.ree.logger import ree_logger

logger = logging.getLogger(__name__)

_DEFAULT_MAX_INTERVIEW_ROUNDS = 3


class REEOrchestrator:
    """
    Deterministic workflow controller for the REE pipeline.

    Invariants:
      - The Orchestrator never mutates the SRC directly.
      - All interview-related SRC updates go through InterviewModerator.
      - The review → interview → review loop repeats until READY or
        max rounds is exhausted.
    """

    def __init__(self, max_interview_rounds: int = _DEFAULT_MAX_INTERVIEW_ROUNDS) -> None:
        self.max_interview_rounds = max_interview_rounds

        # Agents are stateless — safe to reuse across requests
        self._input_agent = InputUnderstandingAgent()
        self._engineering_agent = EngineeringTeamAgent()
        self._review_agent = RequirementReviewAgent()
        self._interview_moderator = InterviewModerator()
        self._finalizer = FinalizationAgent()

    # ── Public API ─────────────────────────────────────────────────────────────

    def run(self, request: REERequest) -> REEResponse:
        """
        Execute or resume a REE workflow run.

        Fresh start:   Pass only combined_prompt.
        Resume with answers: Pass prior_src (the SRC dict from the previous
                             response) and interview_answers.

        Returns:
            REEResponse with status INTERVIEWING, COMPLETE, or FAILED.
        """
        logger.info("REEOrchestrator: starting run (resume=%s)", request.prior_src is not None)

        src = self._build_src(request)
        max_rounds = max(
            0,
            request.max_interview_rounds
            if request.max_interview_rounds is not None
            else self.max_interview_rounds,
        )

        try:
            if not request.prior_src:
                ree_logger.print_pipeline_header()

            # ── Stage 1: Input Understanding ──────────────────────────────────
            # Skipped on resume — project_context is already populated in the SRC
            src = self._input_agent.run(src)
            if not request.prior_src:
                ree_logger.print_stage_success("Input Understanding")

            # ── Stage 2: Apply interview answers (if this is a resume) ─────────
            # The Moderator applies them and updates the InterviewSession history.
            if request.interview_answers:
                logger.info(
                    "REEOrchestrator: applying %d answer(s) via InterviewModerator",
                    len(request.interview_answers),
                )
                src = self._interview_moderator.apply_answers(
                    src, request.interview_answers
                )
                ree_logger.print_after_interview_header()
                ree_logger.print_stage_success("Interview Completed")

            # ── Stage 3: Engineering Team ─────────────────────────────────────
            src = self._engineering_agent.run(src)
            if not request.prior_src:
                ree_logger.print_stage_success("Requirement Engineer")
                ree_logger.print_stage_success("Business Analyst")
                ree_logger.print_stage_success("Domain Expert")

            # ── Stage 4: Review → Interview loop ─────────────────────────────
            # Run the Review Agent, then enter the interview loop if needed.
            # The loop exits when the verdict is READY or max rounds is reached.
            src = self._review_agent.run(src)
            if not request.prior_src:
                ree_logger.print_stage_success("Requirement Review")

            while self._needs_interview(src, max_rounds):
                response = self._conduct_interview(src)
                if response is not None:
                    # No answers available — return the interview to the caller.
                    # The caller will submit answers in the next request.
                    if response.interview_result and response.interview_result.get("questions"):
                        q_cnt = len(response.interview_result["questions"])
                        ree_logger.print_interview_required(q_cnt)
                    return response

                # Answers were already applied in _conduct_interview (single-turn path).
                # Re-run the Review Agent.
                src = self._review_agent.run(src)

            # ── Stage 5: Finalization ─────────────────────────────────────────
            arsrs = self._finalizer.run(src)
            src.status = REEStatus.COMPLETE
            ree_logger.print_stage_success("Finalizer")
            ree_logger.print_stage_success("ARSRS Generated")
            ree_logger.print_pipeline_footer()

            logger.info(
                "REEOrchestrator: complete — session_id=%s, verdict=%s",
                arsrs.session_id,
                src.review_result.verdict.value if src.review_result else "n/a",
            )

            return REEResponse(
                status=REEStatus.COMPLETE,
                message="Requirements engineering complete. ARSRS is ready for architecture generation.",
                src=self._serialise_src(src),
                arsrs=arsrs.to_dict(),
            )

        except Exception as exc:  # noqa: BLE001
            logger.error("REEOrchestrator: workflow failed: %s", exc, exc_info=True)
            src.status = REEStatus.FAILED
            src.errors.append(str(exc))
            return REEResponse(
                status=REEStatus.FAILED,
                message=f"REE workflow failed: {exc}",
                src=self._serialise_src(src),
            )

    def run_from_src(
        self,
        src_dict: Dict[str, Any],
        answers: Optional[List[Dict[str, Any]]] = None,
    ) -> REEResponse:
        """
        Resume a workflow from a serialised SRC dict (from a previous response).

        Convenience wrapper around run() — builds a REERequest with prior_src.

        Args:
            src_dict:  The 'src' dict from the previous REEResponse.
            answers:   Stakeholder answers for the current interview round.

        Returns:
            Updated REEResponse.
        """
        return self.run(REERequest(
            combined_prompt=src_dict.get("raw_input", ""),
            prior_src=src_dict,
            interview_answers=answers,
            max_interview_rounds=self.max_interview_rounds,
        ))

    # ── Internal: SRC construction ─────────────────────────────────────────

    def _build_src(self, request: REERequest) -> SharedRequirementContext:
        """
        Construct (or restore) a SharedRequirementContext from the request.

        Priority order:
          1. prior_src   — full SRC dict (restores complete pipeline state)
          2. prior_parameters — thin parameter dict only
          3. fresh SRC   — brand-new session
        """
        if request.prior_src:
            # Full resume: restore the entire SRC including interview session
            src = self._deserialise_src(request.prior_src)
            # Update raw_input if a newer prompt was provided
            if request.combined_prompt and request.combined_prompt != src.raw_input:
                # Don't overwrite project_context — only update the flat field
                # so the input agent's skip-guard fires correctly
                pass  # raw_input comes from the SRC; keep original
            logger.debug(
                "REEOrchestrator: restored SRC session_id=%s, interview_round=%d",
                src.session_id, src.interview_round,
            )
            return src

        # Fresh start (possibly with pre-extracted parameters)
        src = SharedRequirementContext(
            raw_input=request.combined_prompt,
            input_sources=list(request.input_sources),
        )
        if request.prior_parameters:
            src.parameters = dict(request.prior_parameters)
            src.requirements.parameters = src.parameters

        return src

    # ── Internal: interview loop logic ────────────────────────────────────

    def _needs_interview(
        self,
        src: SharedRequirementContext,
        max_rounds: int,
    ) -> bool:
        """
        Return True if the Review verdict requires another interview round.

        Gates:
          - Verdict must be NEED_CLARIFICATION (not READY).
          - interview_round must be below max_rounds.
        """
        # Check ReviewResult verdict (primary signal from Task 5)
        if src.review_result is not None:
            if src.review_result.verdict == ReviewVerdict.READY:
                return False
        else:
            # Fall back to completeness level when no review_result yet
            if src.completeness in (
                CompletenessLevel.SUFFICIENT,
                CompletenessLevel.COMPLETE,
            ):
                return False

        # Hard cap on rounds
        if src.interview_round >= max_rounds:
            logger.info(
                "REEOrchestrator: max interview rounds (%d) reached — forcing finalization",
                max_rounds,
            )
            return False

        return True

    def _conduct_interview(
        self,
        src: SharedRequirementContext,
    ) -> Optional[REEResponse]:
        """
        Ask the InterviewModerator to generate questions for the current round.

        Returns:
            REEResponse with INTERVIEWING status if questions were generated
            and no answers are available yet (multi-turn path).

            None if question generation produced nothing (loop should stop).
        """
        logger.info(
            "REEOrchestrator: invoking InterviewModerator (round %d)",
            src.interview_round + 1,
        )

        # InterviewModerator.run() generates questions, creates an InterviewRound,
        # and sets SRC.status = INTERVIEWING.
        src = self._interview_moderator.run(src)

        session = src.interview_session
        current_round = session.current_round() if session else None

        # If no questions were produced, there is nothing to ask — stop the loop.
        if current_round is None or not current_round.questions:
            logger.warning(
                "REEOrchestrator: InterviewModerator generated no questions — "
                "skipping interview round"
            )
            return None

        questions_out = [q.to_dict() for q in current_round.questions]
        round_number = current_round.round_number

        logger.info(
            "REEOrchestrator: interview round %d — %d question(s) generated",
            round_number, len(questions_out),
        )

        return REEResponse(
            status=REEStatus.INTERVIEWING,
            message=(
                f"Round {round_number}: "
                f"{len(questions_out)} clarification question(s). "
                "Submit answers via interview_answers in the next request."
            ),
            src=self._serialise_src(src),
            interview_result={
                "round": round_number,
                "questions": questions_out,
                "session": session.to_dict() if session else None,
            },
        )

    # ── Serialisation ─────────────────────────────────────────────────────

    @staticmethod
    def _serialise_src(src: SharedRequirementContext) -> Dict[str, Any]:
        """Convert SRC to a JSON-serialisable dict for the API response."""
        return src.to_dict()

    @staticmethod
    def _deserialise_src(data: Dict[str, Any]) -> SharedRequirementContext:
        """
        Restore a full SharedRequirementContext from a serialised dict.

        Reconstructs all named sections and interview session state so
        the pipeline can resume exactly where it left off.
        """
        from app.ree.models import (
            ProjectContext, BusinessContext, DomainContext,
            RequirementsSection, DiscussionNotes, QualityAssessment,
            DocumentSection, InputSourceRecord, InputSourceType,
            ReviewResult, ReviewVerdict, ConfidenceScore,
            AmbiguityIssue, ContradictionIssue, DuplicateIssue,
            InterviewSession, InterviewRound, InterviewQuestion, InterviewAnswer,
        )

        src = SharedRequirementContext()

        # ── Flat fields ──────────────────────────────────────────────────────
        src.raw_input = data.get("raw_input", "")
        src.input_sources = data.get("input_sources", [])
        src.parameters = data.get("parameters", {})
        src.missing_parameters = data.get("missing_parameters", [])
        src.clarification_questions = data.get("clarification_questions", [])
        src.interview_history = data.get("interview_history", [])
        src.interview_round = data.get("interview_round", 0)
        src.review_notes = data.get("review_notes", [])
        src.agent_outputs = data.get("agent_outputs", {})
        src.errors = data.get("errors", [])
        src.session_id = data.get("session_id", src.session_id)
        src.created_at = data.get("created_at", src.created_at)

        # ── Enums ────────────────────────────────────────────────────────────
        try:
            src.completeness = CompletenessLevel(
                data.get("completeness", CompletenessLevel.INCOMPLETE.value)
            )
        except ValueError:
            src.completeness = CompletenessLevel.INCOMPLETE

        try:
            src.status = REEStatus(data.get("status", REEStatus.PENDING.value))
        except ValueError:
            src.status = REEStatus.PENDING

        # ── ProjectContext ────────────────────────────────────────────────────
        pc_data = data.get("project_context", {})
        if pc_data:
            pc = ProjectContext()
            pc.normalized_text = pc_data.get("normalized_text", "")
            pc.estimated_tokens = pc_data.get("estimated_tokens", 0)
            pc.requires_chunking = pc_data.get("requires_chunking", False)
            pc.duplicate_blocks_removed = pc_data.get("duplicate_blocks_removed", 0)
            for s in pc_data.get("sections", []):
                pc.sections.append(DocumentSection(
                    title=s.get("title", "main"),
                    content=s.get("content", ""),
                    source=s.get("source", ""),
                    section_index=s.get("section_index", 0),
                ))
            for r in pc_data.get("input_sources", []):
                try:
                    st = InputSourceType(r.get("source_type", "unknown"))
                except ValueError:
                    st = InputSourceType.UNKNOWN
                pc.input_sources.append(InputSourceRecord(
                    label=r.get("label", ""),
                    source_type=st,
                    char_count=r.get("char_count", 0),
                    parse_error=r.get("parse_error"),
                ))
            src.project_context = pc

        # ── RequirementsSection ───────────────────────────────────────────────
        req_data = data.get("requirements", {})
        if req_data:
            src.requirements.parameters = req_data.get("parameters", {})

        # ── QualityAssessment ─────────────────────────────────────────────────
        qa_data = data.get("quality_assessment", {})
        if qa_data:
            qa = QualityAssessment()
            try:
                qa.completeness = CompletenessLevel(
                    qa_data.get("completeness", CompletenessLevel.INCOMPLETE.value)
                )
            except ValueError:
                qa.completeness = CompletenessLevel.INCOMPLETE
            qa.missing_critical = qa_data.get("missing_critical", [])
            qa.missing_important = qa_data.get("missing_important", [])
            qa.missing_optional = qa_data.get("missing_optional", [])
            qa.notes = qa_data.get("notes", [])
            qa.assessed_at = qa_data.get("assessed_at")
            src.quality_assessment = qa

        # ── DiscussionNotes ───────────────────────────────────────────────────
        dn_data = data.get("discussion_notes", {})
        if dn_data:
            src.discussion_notes.notes = dn_data.get("notes", [])

        # ── BusinessContext ───────────────────────────────────────────────────
        bc_data = data.get("business_context", {})
        if bc_data:
            bc = BusinessContext()
            bc.domain = bc_data.get("domain")
            bc.domain_keywords = bc_data.get("domain_keywords", [])
            bc.business_objectives = bc_data.get("business_objectives", [])
            bc.stakeholders = bc_data.get("stakeholders", [])
            bc.constraints = bc_data.get("constraints", [])
            for attr in ("kpis", "pain_points", "assumptions"):
                if attr in bc_data:
                    setattr(bc, attr, bc_data[attr])
            src.business_context = bc

        # ── DomainContext ─────────────────────────────────────────────────────
        dc_data = data.get("domain_context", {})
        if dc_data:
            dc = DomainContext()
            dc.system_type = dc_data.get("system_type")
            dc.similar_systems = dc_data.get("similar_systems", [])
            dc.architecture_patterns = dc_data.get("architecture_patterns", [])
            dc.technology_signals = dc_data.get("technology_signals", [])
            for attr in ("domain_constraints", "compliance", "scale", "risks"):
                if attr in dc_data:
                    setattr(dc, attr, dc_data[attr])
            src.domain_context = dc

        # ── ReviewResult ──────────────────────────────────────────────────────
        rr_data = data.get("review_result")
        if rr_data and isinstance(rr_data, dict):
            try:
                verdict = ReviewVerdict(rr_data.get("verdict", ReviewVerdict.NEED_CLARIFICATION.value))
            except ValueError:
                verdict = ReviewVerdict.NEED_CLARIFICATION

            conf_data = rr_data.get("confidence", {})
            confidence = ConfidenceScore(
                overall=float(conf_data.get("overall", 0.0)),
                completeness=float(conf_data.get("completeness", 0.0)),
                clarity=float(conf_data.get("clarity", 0.0)),
                consistency=float(conf_data.get("consistency", 0.0)),
                specificity=float(conf_data.get("specificity", 0.0)),
            )

            ambiguities = [
                AmbiguityIssue(
                    field=a.get("field", ""),
                    description=a.get("description", ""),
                    severity=a.get("severity", "medium"),
                )
                for a in rr_data.get("ambiguities", [])
                if isinstance(a, dict)
            ]
            contradictions = [
                ContradictionIssue(
                    field_a=c.get("field_a", ""),
                    field_b=c.get("field_b", ""),
                    description=c.get("description", ""),
                )
                for c in rr_data.get("contradictions", [])
                if isinstance(c, dict)
            ]
            duplicates = [
                DuplicateIssue(
                    field=d.get("field", ""),
                    duplicate_items=d.get("duplicate_items", []),
                    canonical=d.get("canonical", ""),
                )
                for d in rr_data.get("duplicates", [])
                if isinstance(d, dict)
            ]

            src.review_result = ReviewResult(
                verdict=verdict,
                confidence=confidence,
                missing_items=rr_data.get("missing_items", []),
                ambiguities=ambiguities,
                contradictions=contradictions,
                duplicates=duplicates,
                review_summary=rr_data.get("review_summary", ""),
                reviewed_at=rr_data.get("reviewed_at"),
            )

        # ── InterviewSession ──────────────────────────────────────────────────
        is_data = data.get("interview_session")
        if is_data and isinstance(is_data, dict):
            session = InterviewSession()
            for round_data in is_data.get("rounds", []):
                if not isinstance(round_data, dict):
                    continue

                questions = [
                    InterviewQuestion(
                        question_id=q.get("question_id", ""),
                        question=q.get("question", ""),
                        rationale=q.get("rationale", ""),
                        target_section=q.get("target_section", "requirements"),
                        target_field=q.get("target_field"),
                        options=q.get("options", []),
                        priority=q.get("priority", "medium"),
                    )
                    for q in round_data.get("questions", [])
                    if isinstance(q, dict)
                ]
                answers = [
                    InterviewAnswer(
                        question_id=a.get("question_id", ""),
                        answer=a.get("answer", ""),
                        answered_at=a.get("answered_at", ""),
                    )
                    for a in round_data.get("answers", [])
                    if isinstance(a, dict)
                ]

                ir = InterviewRound(
                    round_number=round_data.get("round_number", 1),
                    questions=questions,
                    answers=answers,
                    started_at=round_data.get("started_at", ""),
                    completed_at=round_data.get("completed_at"),
                    updated_sections=round_data.get("updated_sections", []),
                )
                session.add_round(ir)

            src.interview_session = session

        return src
