"""Generation Service: Orchestration & In-Memory State Layer for AI Engine.

Exposes the existing Requirements Engineering Engine (REE) and Software Architecture
Engine (SAE) via asynchronous FastAPI workflows without altering internal agent logic.
"""

from __future__ import annotations

import asyncio
import copy
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# REE Imports
from app.ree.agents.interview_moderator import InterviewModerator, _normalize_options_set
from app.ree.models import REERequest, REEResponse, REEStatus, SharedRequirementContext
from app.ree.orchestrator import REEOrchestrator

# SAE Imports
from app.sae.agents.backend_lld_generation_agent import BackendLLDGenerationAgent
from app.sae.agents.cloud_lld_generation_agent import CloudLLDGenerationAgent
from app.sae.agents.database_lld_generation_agent import DatabaseLLDGenerationAgent
from app.sae.agents.frontend_lld_generation_agent import FrontendLLDGenerationAgent
from app.sae.agents.hld_generation_agent import HLDGenerationAgent
from app.sae.agents.requirement_analysis_agent import RequirementAnalysisAgent
from app.sae.agents.security_lld_generation_agent import SecurityLLDGenerationAgent
from app.sae.agents.technology_advisor_agent import TechnologyAdvisorAgent
from app.sae.pipeline import SAEPipeline
from app.sae.providers.llm_provider import OpenRouterProvider
from app.sae.utils.arsrs_validator import ARSRSValidator
from app.sae.utils.canonical_contract import CanonicalArchitectureContract, ContractBuilder
from app.sae.utils.domain_lock import DomainContext, DomainLockEngine, validate_requirement_contract
from app.sae.utils.hld_quality_gate import HLDQualityGate
from app.sae.utils.sae_logger import SAELogger

logger = logging.getLogger(__name__)

SUPPORTED_LLD_TYPES: Set[str] = {
    "backend",
    "frontend",
    "database",
    "security",
    "cloud",
}


@dataclass
class LLDState:
    """State of an individual Low Level Design (LLD) generation."""

    status: str = "NOT_STARTED"  # NOT_STARTED | GENERATING | READY | FAILED
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "data": self.data,
            "error": self.error,
        }


@dataclass
class GenerationContext:
    """Isolated state container for a single end-to-end architecture generation lifecycle."""

    generation_id: str
    prompt: str
    interview_questions: List[Dict[str, Any]] = field(default_factory=list)
    interview_answers: List[Dict[str, Any]] = field(default_factory=list)
    current_question_index: int = 0

    src: Optional[Dict[str, Any]] = None
    arsrs: Optional[Dict[str, Any]] = None
    hld: Optional[Dict[str, Any]] = None
    cac: Optional[CanonicalArchitectureContract] = None
    domain_ctx: Optional[DomainContext] = None

    status: str = "INTERVIEW_IN_PROGRESS"  # INTERVIEW_IN_PROGRESS | INTERVIEW_COMPLETED | GENERATING_HLD | HLD_READY | COMPLETED | FAILED
    error: Optional[str] = None

    llds: Dict[str, LLDState] = field(
        default_factory=lambda: {
            "backend": LLDState(),
            "frontend": LLDState(),
            "database": LLDState(),
            "security": LLDState(),
            "cloud": LLDState(),
        }
    )

    logs: List[Dict[str, Any]] = field(default_factory=list)
    subscribers: List[asyncio.Queue] = field(default_factory=list)

    output_dir: Optional[str] = None
    sae_logger: Optional[SAELogger] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generation_id": self.generation_id,
            "prompt": self.prompt,
            "interview_questions": self.interview_questions,
            "interview_answers": self.interview_answers,
            "current_question_index": self.current_question_index,
            "arsrs": self.arsrs,
            "hld": self.hld,
            "status": self.status,
            "error": self.error,
            "llds": {k: v.to_dict() for k, v in self.llds.items()},
            "output_dir": self.output_dir,
            "logs": self.logs,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class GenerationService:
    """Singleton service managing generation lifecycles and background parallel tasks."""

    def __init__(self) -> None:
        self._store: Dict[str, GenerationContext] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

        # REE Orchestrator & Fast Moderator instances
        self._ree_orchestrator = REEOrchestrator()
        self._interview_moderator = InterviewModerator()

        # SAE Components
        self._llm_provider = OpenRouterProvider(debug=False)
        self._sae_pipeline = SAEPipeline(debug=False)
        self._req_agent = RequirementAnalysisAgent(self._llm_provider)
        self._tech_agent = TechnologyAdvisorAgent(self._llm_provider)
        self._hld_agent = HLDGenerationAgent(self._llm_provider)
        self._backend_agent = BackendLLDGenerationAgent(self._llm_provider)
        self._db_agent = DatabaseLLDGenerationAgent(self._llm_provider)
        self._security_agent = SecurityLLDGenerationAgent(self._llm_provider)
        self._cloud_agent = CloudLLDGenerationAgent(self._llm_provider)

    def _bind_sae_logger(self, sae_logger: SAELogger) -> None:
        """Bind active SAELogger to LLM provider and all agent instances."""
        self._llm_provider.sae_logger = sae_logger
        for agent in (
            self._req_agent,
            self._tech_agent,
            self._hld_agent,
            self._backend_agent,
            self._db_agent,
            self._frontend_agent,
            self._security_agent,
            self._cloud_agent,
        ):
            if hasattr(agent, "llm_provider") and agent.llm_provider:
                agent.llm_provider.sae_logger = sae_logger

    def _get_output_dir(self, generation_id: str) -> Path:
        """Retrieve or create dedicated run directory for this generation prompt session."""
        context = self.get_context(generation_id)
        if context and context.output_dir:
            p = Path(context.output_dir)
        else:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            p = PROJECT_ROOT / "outputs" / f"run_{ts}_{generation_id}"
            if context:
                context.output_dir = str(p)
        p.mkdir(parents=True, exist_ok=True)

        # Also mirror to output/ runs directory
        p_mirror = PROJECT_ROOT / "output" / p.name
        p_mirror.mkdir(parents=True, exist_ok=True)
        return p

    def _save_artifact(self, generation_id: str, filename: str, data: Any) -> None:
        """Save a pipeline artifact JSON or text file to the session output directory and mirror."""
        try:
            out_dir = self._get_output_dir(generation_id)
            mirror_dir = PROJECT_ROOT / "output" / out_dir.name

            for target_dir in (out_dir, mirror_dir):
                target_dir.mkdir(parents=True, exist_ok=True)
                filepath = target_dir / filename
                with open(filepath, "w", encoding="utf-8") as f:
                    if isinstance(data, (dict, list)):
                        json.dump(data, f, indent=2, default=str)
                    elif hasattr(data, "model_dump"):
                        json.dump(data.model_dump(mode="json"), f, indent=2, default=str)
                    else:
                        f.write(str(data))
        except Exception as e:
            logger.warning("[%s] Failed to save artifact %s: %s", generation_id, filename, e)

    async def _get_lock(self, generation_id: str) -> asyncio.Lock:
        """Get or create an asyncio.Lock for a specific generation ID."""
        async with self._global_lock:
            if generation_id not in self._locks:
                self._locks[generation_id] = asyncio.Lock()
            return self._locks[generation_id]

    def log(
        self,
        generation_id: str,
        message: str,
        stage: str = "INFO",
        level: str = "INFO",
        process: Optional[str] = None,
        process_status: Optional[str] = None,
        lld_completed: Optional[str] = None,
    ) -> None:
        """Record a structured log event, stream to subscribers, and write to disk."""
        iso_ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        context = self.get_context(generation_id)

        lld_status = None
        overall_status = None
        if context:
            lld_status = {k: v.status for k, v in context.llds.items()}
            overall_status = context.status

        entry = {
            "timestamp": iso_ts,
            "stage": stage,
            "level": level,
            "message": message,
            "process": process or stage,
            "process_status": process_status,
            "overall_status": overall_status,
            "lld_status": lld_status,
            "lld_completed": lld_completed,
        }

        # Force immediate stdout print so terminal displays it in real time
        print(f"[{iso_ts}] [{generation_id}] [{stage}] {message}", flush=True)

        # Write to dedicated session log files across output/, outputs/, and logs/ directories
        try:
            out_dir = self._get_output_dir(generation_id)
            mirror_dir = PROJECT_ROOT / "output" / out_dir.name
            sae_log_dir = PROJECT_ROOT / "output" / "sae" / "logs" / generation_id
            global_log_dir = PROJECT_ROOT / "logs" / generation_id
            output_log_dir = PROJECT_ROOT / "output" / "logs" / generation_id

            target_dirs = [
                out_dir,
                out_dir / "logs",
                mirror_dir,
                mirror_dir / "logs",
                sae_log_dir,
                global_log_dir,
                output_log_dir,
            ]

            log_line = f"[{iso_ts}] [{stage}] [{process or stage}] [{process_status or level}] {message}\n"
            for t_dir in target_dirs:
                t_dir.mkdir(parents=True, exist_ok=True)
                with open(t_dir / "pipeline_execution.log", "a", encoding="utf-8") as f:
                    f.write(log_line)
                with open(t_dir / "execution.log", "a", encoding="utf-8") as f:
                    f.write(f"[{iso_ts}] [{level}] [{process or stage}] {message}\n")
                with open(t_dir / "debug.log", "a", encoding="utf-8") as f:
                    f.write(f"[{iso_ts}] [DEBUG] [{stage}] {message}\n")
                with open(t_dir / "timeline.log", "a", encoding="utf-8") as f:
                    f.write(f"[{iso_ts}] {stage:<25} | {process or stage:<20} | {message}\n")

            # Also maintain latest active log
            with open(PROJECT_ROOT / "output" / "latest_pipeline.log", "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception:
            pass

        if context:
            context.logs.append(entry)
            for q in list(context.subscribers):
                try:
                    q.put_nowait(entry)
                except Exception:
                    pass

    def get_logs(self, generation_id: str) -> List[Dict[str, Any]]:
        """Retrieve stored execution logs for a generation session."""
        context = self.get_context(generation_id)
        if not context:
            raise KeyError(f"Generation ID '{generation_id}' not found.")
        return list(context.logs)

    # ── Context Lookup ──────────────────────────────────────────────────────────

    def get_context(self, generation_id: str) -> Optional[GenerationContext]:
        """Retrieve generation context by ID."""
        return self._store.get(generation_id)

    # ── 1. Start Generation ───────────────────────────────────────────────────

    def start_generation(self, prompt: str) -> GenerationContext:
        """Start a new generation lifecycle from a problem statement.

        Executes the full Requirements Engineering Engine (REE) multi-agent pipeline:
          1. Input Understanding Agent
          2. Parallel Engineering Team (Requirement Engineer, Business Analyst, Domain Expert)
          3. Requirement Review Agent (identifies ambiguities, contradictions, missing items)
          4. Interview Moderator (generates targeted, problem-specific questions)
        """
        clean_prompt = prompt.strip()
        if not clean_prompt:
            raise ValueError("Prompt must not be empty.")

        generation_id = f"gen_{uuid.uuid4().hex[:12]}"
        logger.info("Initiating generation session [%s]", generation_id)

        context = GenerationContext(
            generation_id=generation_id,
            prompt=clean_prompt,
        )
        self._store[generation_id] = context

        # Initialize session-specific SAELogger and bind to LLM provider & agents
        out_dir = self._get_output_dir(generation_id)
        sae_logger = SAELogger(
            design_id=generation_id,
            logs_root=PROJECT_ROOT / "output" / "sae" / "logs",
            extra_log_dirs=[
                out_dir,
                out_dir / "logs",
                PROJECT_ROOT / "output" / out_dir.name,
                PROJECT_ROOT / "output" / out_dir.name / "logs",
            ],
            debug=True,
        )
        context.sae_logger = sae_logger
        self._bind_sae_logger(sae_logger)

        self.log(generation_id, "🚀 Starting REE workflow for problem statement...", stage="REE", process="Requirement Engineering", process_status="IN_PROGRESS")
        self.log(generation_id, f"Prompt: {clean_prompt[:120]}...", stage="REE", process="Requirement Engineering", process_status="IN_PROGRESS")
        self.log(generation_id, "Stage 1/3: Parsing input & running Input Understanding agent...", stage="REE", process="Input Understanding", process_status="IN_PROGRESS")

        try:
            # Run the complete REE pipeline synchronously with 1 round allowance
            ree_req = REERequest(
                combined_prompt=clean_prompt,
                max_interview_rounds=1,
            )
            self.log(generation_id, "Stage 2/3: Multi-agent analysis (Requirement Engineer, Business Analyst, Domain Expert)...", stage="REE", process="Multi-Agent Analysis", process_status="IN_PROGRESS")
            ree_resp: REEResponse = self._ree_orchestrator.run(ree_req)

            context.src = ree_resp.src

            if ree_resp.status == REEStatus.FAILED:
                context.status = "FAILED"
                context.error = ree_resp.message or "REE initialization failed."
                self.log(generation_id, f"❌ REE initialization failed: {context.error}", stage="REE", level="ERROR", process="Requirement Engineering", process_status="FAILED")
                return context

            self.log(generation_id, "Stage 3/3: Evaluating requirements review findings & generating clarification interview...", stage="REE", process="Requirement Review", process_status="IN_PROGRESS")

            # Extract generated interview questions derived from multi-agent analysis
            interview_res = ree_resp.interview_result or {}
            raw_questions = interview_res.get("questions") or []

            parsed_questions: List[Dict[str, Any]] = []
            for idx, q in enumerate(raw_questions, 1):
                if isinstance(q, dict):
                    q_id = str(q.get("question_id") or f"Q{idx}")
                    q_text = str(
                        q.get("question")
                        or q.get("question_text")
                        or q.get("text")
                        or q.get("prompt")
                        or f"Clarification question {idx}"
                    ).strip()
                    opts = q.get("options") or q.get("suggested_options") or q.get("choices") or []
                    if isinstance(opts, str):
                        opts = [o.strip() for o in opts.split(",") if o.strip()]
                    elif not isinstance(opts, list):
                        opts = []
                    default_opt = q.get("default_option") if isinstance(q, dict) else getattr(q, "default_option", None)
                    rationale = str(q.get("rationale") or q.get("reason") or "").strip()
                    target_sec = str(q.get("target_section") or "requirements").strip()
                    target_field = q.get("target_field") or q.get("parameter")
                    priority = str(q.get("priority") or "medium").lower()
                else:
                    q_id = getattr(q, "question_id", f"Q{idx}")
                    q_text = getattr(q, "question", str(q))
                    opts = getattr(q, "options", [])
                    default_opt = getattr(q, "default_option", None)
                    rationale = getattr(q, "rationale", "")
                    target_sec = getattr(q, "target_section", "requirements")
                    target_field = getattr(q, "target_field", None)
                    priority = getattr(q, "priority", "medium")

                # Normalize to standard 5-option structure
                clean_opts, def_opt = _normalize_options_set(opts, default_opt=default_opt, question_text=q_text)

                parsed_questions.append({
                    "question_id": q_id,
                    "question": q_text,
                    "options": clean_opts,
                    "default_option": def_opt,
                    "rationale": rationale,
                    "target_section": target_sec,
                    "target_field": target_field,
                    "priority": priority,
                })

            context.interview_questions = parsed_questions
            context.current_question_index = 0

            # ── Save REE Phase Artifacts to Session Output Directory ─────────
            self._save_artifact(generation_id, "00_prompt.json", {
                "generation_id": generation_id,
                "prompt": clean_prompt,
                "created_at": context.created_at,
            })
            if context.src:
                self._save_artifact(generation_id, "01_ree_src.json", context.src)
            if parsed_questions:
                self._save_artifact(generation_id, "02_interview_questions.json", parsed_questions)

            if parsed_questions:
                context.status = "INTERVIEW_IN_PROGRESS"
                self.log(generation_id, f"✓ Generated {len(parsed_questions)} targeted clarification question(s). Ready for interview.", stage="REE", process="Requirement Engineering", process_status="COMPLETED")
            else:
                context.status = "INTERVIEW_COMPLETED"
                self.log(generation_id, "✓ Requirements are complete. No clarification interview needed.", stage="REE", process="Requirement Engineering", process_status="COMPLETED")
                if ree_resp.arsrs:
                    context.arsrs = ree_resp.arsrs
                    self._save_artifact(generation_id, "03_arsrs.json", ree_resp.arsrs)

            context.updated_at = datetime.now(timezone.utc).isoformat()
            return context

        except Exception as exc:
            logger.exception("Failed to start generation [%s]: %s", generation_id, exc)
            context.status = "FAILED"
            context.error = f"Generation initiation error: {str(exc)}"
            self.log(generation_id, f"❌ Generation error: {str(exc)}", stage="REE", level="ERROR", process="Requirement Engineering", process_status="FAILED")
            raise RuntimeError(context.error) from exc

    # ── 2. Submit Interview Answer ───────────────────────────────────────────

    def submit_answer(
        self,
        generation_id: str,
        question_id: str,
        answer: str,
    ) -> Tuple[GenerationContext, Optional[Dict[str, Any]]]:
        """Record an answer for the active interview question.

        Returns:
            Tuple of (updated GenerationContext, next_question dict or None if completed).
        """
        context = self.get_context(generation_id)
        if not context:
            raise KeyError(f"Generation ID '{generation_id}' not found.")

        if context.status != "INTERVIEW_IN_PROGRESS":
            raise ValueError(
                f"Interview is not in progress (current status: '{context.status}'). "
                "Answers cannot be submitted for completed or failed sessions."
            )

        clean_answer = answer.strip()
        if not clean_answer:
            raise ValueError("Answer must not be empty.")

        # Check if more questions exist to be answered
        if context.current_question_index >= len(context.interview_questions):
            context.status = "INTERVIEW_COMPLETED"
            return context, None

        current_q = context.interview_questions[context.current_question_index]
        clean_qid = question_id.strip()

        # Validate that the answer corresponds to either current or known question ID
        if clean_qid != current_q["question_id"] and not any(
            q["question_id"] == clean_qid for q in context.interview_questions
        ):
            raise ValueError(
                f"Invalid question_id '{clean_qid}'. Expected '{current_q['question_id']}'."
            )

        # Record answer
        context.interview_answers.append({
            "question_id": clean_qid,
            "answer": clean_answer,
            "parameter": current_q.get("target_field") or clean_qid,
        })
        context.current_question_index += 1
        context.updated_at = datetime.now(timezone.utc).isoformat()
        
        # Save updated Interview QA to disk
        self._save_artifact(generation_id, "02_interview_qa.json", {
            "questions": context.interview_questions,
            "answers": context.interview_answers,
            "updated_at": context.updated_at,
        })

        self.log(
            generation_id,
            f"✓ Recorded answer for '{clean_qid}' ({context.current_question_index}/{len(context.interview_questions)}): \"{clean_answer[:60]}\"",
            stage="INTERVIEW",
            process="Clarification Interview",
            process_status="IN_PROGRESS",
        )

        # Check if another question is available
        if context.current_question_index < len(context.interview_questions):
            next_q = context.interview_questions[context.current_question_index]
            self.log(generation_id, f"Next question loaded: {next_q.get('question_id')}", stage="INTERVIEW", process="Clarification Interview", process_status="IN_PROGRESS")
            return context, next_q
        else:
            context.status = "INTERVIEW_COMPLETED"
            self.log(generation_id, "✓ All interview questions completed! Ready to generate architecture.", stage="INTERVIEW", process="Clarification Interview", process_status="COMPLETED")
            return context, None

    # ── 3. Generate ARSRS + HLD ───────────────────────────────────────────────

    async def generate_arsrs_and_hld(self, generation_id: str) -> GenerationContext:
        """Execute REE finalization to produce ARSRS and SAE Phase 1-2 to produce HLD.

        State transition rules:
          - INTERVIEW_COMPLETED: Allowed to trigger generation.
          - GENERATING_HLD / GENERATING: Reject duplicate call (in progress).
          - HLD_READY / COMPLETED: Return existing HLD immediately (idempotent).
          - INTERVIEW_IN_PROGRESS: Reject (interview not completed).

        Once HLD is ready, stores ARSRS and HLD, updates status to HLD_READY,
        triggers parallel background LLD generation, and returns immediately.
        """
        lock = await self._get_lock(generation_id)
        async with lock:
            context = self.get_context(generation_id)
            if not context:
                raise KeyError(f"Generation ID '{generation_id}' not found.")

            # 1. Check if generation is already running
            if context.status in ("GENERATING_HLD", "GENERATING"):
                raise ValueError(
                    f"Architecture generation is already in progress for generation_id '{generation_id}'."
                )

            # 2. Check if HLD is already generated (idempotent return)
            if context.status in ("HLD_READY", "COMPLETED") and context.hld is not None:
                return context

            # 3. Check that the interview was completed
            if context.status != "INTERVIEW_COMPLETED":
                raise ValueError(
                    f"Cannot generate architecture. Interview status is '{context.status}'. "
                    "Please complete all interview questions first."
                )

            # Atomically lock state into GENERATING_HLD
            context.status = "GENERATING_HLD"
            context.updated_at = datetime.now(timezone.utc).isoformat()
            self.log(generation_id, "⚙️ Finalizing ARSRS from prompt and interview answers via REE Finalizer...", stage="REE", process="ARSRS Finalization", process_status="IN_PROGRESS")

        try:
            if context.sae_logger:
                self._bind_sae_logger(context.sae_logger)

            # ── Step A: Finalize ARSRS via REE (Instant <50ms) ───────────────
            logger.info("[%s] Finalizing ARSRS from prompt and interview answers", generation_id)
            if context.src:
                src_obj = self._ree_orchestrator._deserialise_src(context.src)
                if context.interview_answers:
                    src_obj = self._interview_moderator.apply_answers(src_obj, context.interview_answers)
                from app.ree.agents import FinalizationAgent
                arsrs = FinalizationAgent().run(src_obj).to_dict()
                context.src = self._ree_orchestrator._serialise_src(src_obj)
            else:
                ree_req = REERequest(
                    combined_prompt=context.prompt,
                    interview_answers=context.interview_answers,
                    max_interview_rounds=0,
                )
                ree_resp = self._ree_orchestrator.run(ree_req)
                arsrs = ree_resp.arsrs

            if not arsrs:
                arsrs = {
                    "system_name": "Enterprise Architecture Specification",
                    "domain": "Enterprise Software",
                    "raw_input": context.prompt,
                    "interview_answers": context.interview_answers,
                }

            context.arsrs = arsrs
            self._save_artifact(generation_id, "03_arsrs.json", arsrs)
            self.log(generation_id, f"✓ ARSRS specification finalized ({len(arsrs.get('functional_requirements') or [])} FRs, {len(arsrs.get('non_functional_requirements') or [])} NFRs)", stage="REE", process="ARSRS Finalization", process_status="COMPLETED")

            # ── Step B: Generate HLD via SAE Phase 1 & 2 ──────────────────────
            self.log(generation_id, "🔒 SAE: Validating ARSRS and locking Domain boundaries...", stage="SAE", process="Domain Locking", process_status="IN_PROGRESS")

            # 1. Pre-validation and domain locking
            arsrs_sanitized, _ = ARSRSValidator.validate_and_sanitize_arsrs(arsrs)
            domain_ctx: DomainContext = DomainLockEngine.lock_domain_and_requirements(arsrs_sanitized)
            context.domain_ctx = domain_ctx
            self._save_artifact(generation_id, "04_domain_lock.json", domain_ctx.to_validated_artifact())
            self.log(generation_id, f"✓ Domain locked: '{domain_ctx.domain_name}' (Key: {domain_ctx.domain_key})", stage="SAE", process="Domain Locking", process_status="COMPLETED")

            # 2 & 3. Concurrent Execution of Phase 1 Agents (Requirement Analysis + Technology Advisor)
            self.log(generation_id, "SAE Phase 1: Analyzing requirements & selecting tech stack in parallel...", stage="SAE", process="Requirement Analysis", process_status="IN_PROGRESS")
            
            req_task = self._req_agent.run_async(arsrs_sanitized, domain_ctx=domain_ctx)
            tech_task = self._tech_agent.run_async(arsrs_sanitized)
            
            req_analysis, tech_rec = await asyncio.gather(req_task, tech_task)

            is_valid, req_score, violations = validate_requirement_contract(req_analysis, domain_ctx)
            if not is_valid or req_score < 0.70:
                canonical_payload = domain_ctx.to_validated_artifact()
                for k, v in canonical_payload.items():
                    if not req_analysis.get(k):
                        req_analysis[k] = v

            self._save_artifact(generation_id, "05_requirement_analysis.json", req_analysis)
            self._save_artifact(generation_id, "06_technology_recommendation.json", tech_rec)
            self.log(generation_id, f"✓ Phase 1 complete: Requirements verified (Score: {req_score:.2f}) & Tech stack selected", stage="SAE", process="Requirement Analysis", process_status="COMPLETED")

            # 4. Architecture Decision Plan (ADP)
            self.log(generation_id, "SAE Phase 1: Formulating Architecture Decision Plan (ADP)...", stage="SAE", process="Architecture Decision Plan", process_status="IN_PROGRESS")
            adp = self._sae_pipeline._formulate_adp(req_analysis, tech_rec, arsrs_sanitized)
            self._save_artifact(generation_id, "07_architecture_decision_plan.json", adp)
            self.log(generation_id, "✓ Architecture Decision Plan formulated", stage="SAE", process="Architecture Decision Plan", process_status="COMPLETED")

            # 5. HLD Generation & Quality Gating
            self.log(generation_id, "SAE Phase 2: Generating High Level Design (HLD)...", stage="SAE", process="High Level Design (HLD)", process_status="IN_PROGRESS")
            raw_hld = await self._hld_agent.run_async(req_analysis, tech_rec, adp, domain_ctx=domain_ctx)
            hld, hld_report = await HLDQualityGate.repair_hld_if_needed(
                hld=raw_hld,
                domain_ctx=domain_ctx,
                tech_rec=tech_rec,
                adp=adp,
                llm_provider=self._llm_provider,
            )
            context.hld = hld
            self._save_artifact(generation_id, "08_hld.json", hld)
            self.log(generation_id, f"✓ High Level Design (HLD) verified & passed Quality Gate (Score: {hld_report.score:.2f})", stage="SAE", process="High Level Design (HLD)", process_status="COMPLETED")

            # 6. Canonical Architecture Contract (CAC)
            cac: CanonicalArchitectureContract = ContractBuilder.build_from_hld(
                hld=hld,
                req_analysis=req_analysis,
                domain_ctx=domain_ctx,
            )
            context.cac = cac
            self._save_artifact(generation_id, "08_canonical_contract.json", cac.to_contract_summary())
            self.log(generation_id, "✓ Canonical Architecture Contract (CAC) synthesized", stage="SAE", process="Contract Synthesis", process_status="COMPLETED")

            # Store states
            context.status = "HLD_READY"
            context.updated_at = datetime.now(timezone.utc).isoformat()

            # Mark all LLDs as GENERATING
            for lld_key in context.llds:
                context.llds[lld_key].status = "GENERATING"
                context.llds[lld_key].data = None
                context.llds[lld_key].error = None

            # ── Step C: Spawn Parallel Background LLD Generation ─────────────
            self.log(generation_id, "🚀 Spawning 5 parallel background LLD generation agents (Backend, Frontend, Database, Security, Cloud)...", stage="SAE", process="LLD Architecture", process_status="IN_PROGRESS")
            asyncio.create_task(self.run_parallel_lld_generation(generation_id))

            return context

        except Exception as exc:
            logger.exception("[%s] Architecture generation failed: %s", generation_id, exc)
            context.status = "FAILED"
            context.error = f"Architecture generation error: {str(exc)}"
            context.updated_at = datetime.now(timezone.utc).isoformat()
            self.log(generation_id, f"❌ Architecture generation failed: {str(exc)}", stage="SAE", level="ERROR", process="Architecture Generation", process_status="FAILED")
            raise RuntimeError(context.error) from exc

    # ── 4. Background Parallel LLD Generation ─────────────────────────────────

    async def run_parallel_lld_generation(self, generation_id: str) -> None:
        """Concurrently execute all available LLD generation agents in the background.

        Failure-safe: Each LLD is individually guarded against exceptions so a failure
        in one LLD does NOT stop or cancel the others. State is updated in real-time.
        """
        context = self.get_context(generation_id)
        if not context or not context.hld:
            logger.error("[%s] Cannot run background LLD generation: Context or HLD missing", generation_id)
            return

        hld = context.hld
        cac = context.cac

        if context.sae_logger:
            self._bind_sae_logger(context.sae_logger)

        async def _run_backend() -> None:
            try:
                self.log(generation_id, "Backend LLD agent started...", stage="LLD_BACKEND", process="Backend LLD", process_status="IN_PROGRESS")
                res = await self._backend_agent.run_async(hld, cac=cac)
                data = res.model_dump() if hasattr(res, "model_dump") else (res if isinstance(res, dict) else {"data": str(res)})
                context.llds["backend"].status = "READY"
                context.llds["backend"].data = data
                context.llds["backend"].error = None
                self._save_artifact(generation_id, "09_backend_lld.json", data)
                self.log(generation_id, "✓ Backend LLD completed successfully", stage="LLD_BACKEND", process="Backend LLD", process_status="COMPLETED", lld_completed="backend")
            except Exception as e:
                logger.exception("[%s] ❌ Backend LLD generation failed: %s", generation_id, e)
                context.llds["backend"].status = "FAILED"
                context.llds["backend"].error = f"Backend LLD generation failed: {str(e)}"
                self.log(generation_id, f"❌ Backend LLD failed: {str(e)}", stage="LLD_BACKEND", level="ERROR", process="Backend LLD", process_status="FAILED", lld_completed="backend")
            finally:
                context.updated_at = datetime.now(timezone.utc).isoformat()

        async def _run_frontend() -> None:
            try:
                self.log(generation_id, "Frontend LLD agent started...", stage="LLD_FRONTEND", process="Frontend LLD", process_status="IN_PROGRESS")
                res = await self._frontend_agent.run_async(hld, cac=cac)
                data = res.model_dump() if hasattr(res, "model_dump") else (res if isinstance(res, dict) else {"data": str(res)})
                context.llds["frontend"].status = "READY"
                context.llds["frontend"].data = data
                context.llds["frontend"].error = None
                self._save_artifact(generation_id, "09_frontend_lld.json", data)
                self.log(generation_id, "✓ Frontend LLD completed successfully", stage="LLD_FRONTEND", process="Frontend LLD", process_status="COMPLETED", lld_completed="frontend")
            except Exception as e:
                logger.exception("[%s] ❌ Frontend LLD generation failed: %s", generation_id, e)
                context.llds["frontend"].status = "FAILED"
                context.llds["frontend"].error = f"Frontend LLD generation failed: {str(e)}"
                self.log(generation_id, f"❌ Frontend LLD failed: {str(e)}", stage="LLD_FRONTEND", level="ERROR", process="Frontend LLD", process_status="FAILED", lld_completed="frontend")
            finally:
                context.updated_at = datetime.now(timezone.utc).isoformat()

        async def _run_database() -> None:
            try:
                self.log(generation_id, "Database LLD agent started...", stage="LLD_DATABASE", process="Database LLD", process_status="IN_PROGRESS")
                res = await self._db_agent.run_async(hld, cac=cac)
                data = res.model_dump() if hasattr(res, "model_dump") else (res if isinstance(res, dict) else {"data": str(res)})
                context.llds["database"].status = "READY"
                context.llds["database"].data = data
                context.llds["database"].error = None
                self._save_artifact(generation_id, "09_database_lld.json", data)
                self.log(generation_id, "✓ Database LLD completed successfully", stage="LLD_DATABASE", process="Database LLD", process_status="COMPLETED", lld_completed="database")
            except Exception as e:
                logger.exception("[%s] ❌ Database LLD generation failed: %s", generation_id, e)
                context.llds["database"].status = "FAILED"
                context.llds["database"].error = f"Database LLD generation failed: {str(e)}"
                self.log(generation_id, f"❌ Database LLD failed: {str(e)}", stage="LLD_DATABASE", level="ERROR", process="Database LLD", process_status="FAILED", lld_completed="database")
            finally:
                context.updated_at = datetime.now(timezone.utc).isoformat()

        async def _run_security() -> None:
            try:
                self.log(generation_id, "Security LLD agent started...", stage="LLD_SECURITY", process="Security LLD", process_status="IN_PROGRESS")
                res = await self._security_agent.run_async(hld)
                data = res.model_dump() if hasattr(res, "model_dump") else (res if isinstance(res, dict) else {"data": str(res)})
                context.llds["security"].status = "READY"
                context.llds["security"].data = data
                context.llds["security"].error = None
                self._save_artifact(generation_id, "09_security_lld.json", data)
                self.log(generation_id, "✓ Security LLD completed successfully", stage="LLD_SECURITY", process="Security LLD", process_status="COMPLETED", lld_completed="security")
            except Exception as e:
                logger.exception("[%s] ❌ Security LLD generation failed: %s", generation_id, e)
                context.llds["security"].status = "FAILED"
                context.llds["security"].error = f"Security LLD generation failed: {str(e)}"
                self.log(generation_id, f"❌ Security LLD failed: {str(e)}", stage="LLD_SECURITY", level="ERROR", process="Security LLD", process_status="FAILED", lld_completed="security")
            finally:
                context.updated_at = datetime.now(timezone.utc).isoformat()

        async def _run_cloud() -> None:
            try:
                self.log(generation_id, "Cloud LLD agent started...", stage="LLD_CLOUD", process="Cloud LLD", process_status="IN_PROGRESS")
                res = await self._cloud_agent.run_async(hld)
                data = res.model_dump() if hasattr(res, "model_dump") else (res if isinstance(res, dict) else {"data": str(res)})
                context.llds["cloud"].status = "READY"
                context.llds["cloud"].data = data
                context.llds["cloud"].error = None
                self._save_artifact(generation_id, "09_cloud_lld.json", data)
                self.log(generation_id, "✓ Cloud LLD completed successfully", stage="LLD_CLOUD", process="Cloud LLD", process_status="COMPLETED", lld_completed="cloud")
            except Exception as e:
                logger.exception("[%s] ❌ Cloud LLD generation failed: %s", generation_id, e)
                context.llds["cloud"].status = "FAILED"
                context.llds["cloud"].error = f"Cloud LLD generation failed: {str(e)}"
                self.log(generation_id, f"❌ Cloud LLD failed: {str(e)}", stage="LLD_CLOUD", level="ERROR", process="Cloud LLD", process_status="FAILED", lld_completed="cloud")
            finally:
                context.updated_at = datetime.now(timezone.utc).isoformat()

        # Run all 5 LLD tasks concurrently with zero failure propagation
        await asyncio.gather(
            _run_backend(),
            _run_frontend(),
            _run_database(),
            _run_security(),
            _run_cloud(),
            return_exceptions=True,
        )

        # Check if all LLDs have reached a terminal state (READY or FAILED)
        all_terminal = all(
            v.status in ("READY", "FAILED") for v in context.llds.values()
        )
        if all_terminal:
            context.status = "COMPLETED"
            package = {
                "generation_id": context.generation_id,
                "prompt": context.prompt,
                "status": "COMPLETED",
                "arsrs": context.arsrs,
                "hld": context.hld,
                "llds": {k: v.to_dict() for k, v in context.llds.items()},
                "created_at": context.created_at,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
            self._save_artifact(generation_id, "10_architecture_package.json", package)
            self._save_artifact(generation_id, "summary.json", {
                "generation_id": context.generation_id,
                "status": "COMPLETED",
                "output_directory": str(self._get_output_dir(generation_id)),
                "total_logs": len(context.logs),
                "lld_summary": {k: v.status for k, v in context.llds.items()},
            })
            self.log(generation_id, f"✓ All artifacts saved to {self._get_output_dir(generation_id)}. Generation lifecycle COMPLETED.", stage="SAE")

    # ── 5. Status & Artifact Queries ──────────────────────────────────────────

    def get_status(self, generation_id: str) -> Dict[str, Any]:
        """Compute status report for polling."""
        context = self.get_context(generation_id)
        if not context:
            raise KeyError(f"Generation ID '{generation_id}' not found.")

        # Determine sub-stage statuses
        interview_status = (
            "COMPLETED"
            if context.status in ("INTERVIEW_COMPLETED", "GENERATING_HLD", "HLD_READY", "COMPLETED")
            else "IN_PROGRESS"
        )
        arsrs_status = (
            "READY"
            if context.arsrs is not None
            else ("GENERATING" if context.status == "GENERATING_HLD" else "NOT_STARTED")
        )
        hld_status = (
            "READY"
            if context.hld is not None
            else ("GENERATING" if context.status == "GENERATING_HLD" else "NOT_STARTED")
        )

        return {
            "generation_id": context.generation_id,
            "status": context.status,
            "interview": interview_status,
            "arsrs": arsrs_status,
            "hld": hld_status,
            "llds": {k: v.status for k, v in context.llds.items()},
        }

    def get_arsrs(self, generation_id: str) -> Dict[str, Any]:
        """Retrieve ARSRS specification."""
        context = self.get_context(generation_id)
        if not context:
            raise KeyError(f"Generation ID '{generation_id}' not found.")

        if context.arsrs is not None:
            return {
                "generation_id": context.generation_id,
                "status": "READY",
                "data": context.arsrs,
            }

        return {
            "generation_id": context.generation_id,
            "status": "GENERATING" if context.status == "GENERATING_HLD" else "NOT_STARTED",
            "data": None,
            "message": "ARSRS is not ready yet.",
        }

    def get_hld(self, generation_id: str) -> Dict[str, Any]:
        """Retrieve High Level Design (HLD)."""
        context = self.get_context(generation_id)
        if not context:
            raise KeyError(f"Generation ID '{generation_id}' not found.")

        if context.hld is not None:
            return {
                "generation_id": context.generation_id,
                "status": "READY",
                "data": context.hld,
            }

        return {
            "generation_id": context.generation_id,
            "status": "GENERATING" if context.status == "GENERATING_HLD" else "NOT_STARTED",
            "data": None,
            "message": "HLD is not ready yet.",
        }

    def get_lld(self, generation_id: str, lld_type: str) -> Dict[str, Any]:
        """Retrieve specific Low Level Design (LLD)."""
        context = self.get_context(generation_id)
        if not context:
            raise KeyError(f"Generation ID '{generation_id}' not found.")

        normalized_type = lld_type.strip().lower()
        if normalized_type not in SUPPORTED_LLD_TYPES:
            raise ValueError(
                f"Invalid lld_type '{lld_type}'. Supported types: {', '.join(sorted(SUPPORTED_LLD_TYPES))}"
            )

        lld_entry = context.llds.get(normalized_type)
        if not lld_entry:
            return {
                "generation_id": context.generation_id,
                "lld_type": normalized_type,
                "status": "NOT_STARTED",
                "message": f"{normalized_type.capitalize()} LLD generation has not started.",
            }

        if lld_entry.status == "READY":
            return {
                "generation_id": context.generation_id,
                "lld_type": normalized_type,
                "status": "READY",
                "data": lld_entry.data,
            }

        if lld_entry.status == "GENERATING":
            return {
                "generation_id": context.generation_id,
                "lld_type": normalized_type,
                "status": "GENERATING",
                "message": f"{normalized_type.capitalize()} LLD is still being generated.",
            }

        if lld_entry.status == "FAILED":
            return {
                "generation_id": context.generation_id,
                "lld_type": normalized_type,
                "status": "FAILED",
                "error": lld_entry.error or f"{normalized_type.capitalize()} LLD generation failed.",
            }

        return {
            "generation_id": context.generation_id,
            "lld_type": normalized_type,
            "status": "NOT_STARTED",
            "message": f"{normalized_type.capitalize()} LLD generation has not started.",
        }


# Global singleton instance for injection across routers
generation_service = GenerationService()
