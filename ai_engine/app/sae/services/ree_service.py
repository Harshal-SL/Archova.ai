"""REE Generation Service executing Requirement Engineering Engine pipeline."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from app.ree.models import REERequest, REEResponse, REEStatus
from app.ree.orchestrator import REEOrchestrator
from app.sae.context.design_generation_context import DesignGenerationContext

logger = logging.getLogger(__name__)


class REEGenerationService:
    """Service wrapping REE execution pipeline to transform stakeholder inputs into ARSRS payloads."""

    def __init__(self, ree_orchestrator: Optional[REEOrchestrator] = None) -> None:
        self.ree_orchestrator = ree_orchestrator or REEOrchestrator()

    def process_requirements(self, context: DesignGenerationContext) -> DesignGenerationContext:
        """Execute REE pipeline and populate context with ARSRS payload."""
        t_start = time.time()
        context.status = "REE_RUNNING"

        raw_content = context.normalized_input or str(context.raw_input)
        if not raw_content.strip():
            context.status = "FAILED"
            context.errors.append("Input content is empty or invalid.")
            return context

        try:
            allow_interview = context.metadata.get("interactive", True) and not context.metadata.get("skip_interview", False)
            max_rounds = int(context.metadata.get("max_interview_rounds", 3 if allow_interview else 0))
            ree_req = REERequest(combined_prompt=raw_content, max_interview_rounds=max_rounds)
            ree_resp: REEResponse = self.ree_orchestrator.run(ree_req)

            # Interactive Interview Questionnaire Loop
            while ree_resp.status == REEStatus.INTERVIEWING and allow_interview:
                src = ree_resp.src or {}
                interview_res = ree_resp.interview_result or {}
                questions = interview_res.get("questions") or []
                round_num = interview_res.get("round", 1)

                if not questions:
                    break

                print(f"\n{'═'*80}")
                print(f" 📋 STAKEHOLDER REQUIREMENT CLARIFICATION INTERVIEW (Round {round_num})")
                print(f"{'═'*80}")
                print(" The Technical Lead has generated clarifying questions to refine your system design:")

                answers: List[Dict[str, Any]] = []
                for i, q in enumerate(questions, 1):
                    if hasattr(q, "question"):
                        q_text = str(getattr(q, "question", "")).strip()
                        q_id = str(getattr(q, "question_id", f"q{i}"))
                        param = str(getattr(q, "target_field", None) or getattr(q, "target_section", "general"))
                        opts = getattr(q, "options", [])
                        rationale = str(getattr(q, "rationale", ""))
                    elif isinstance(q, dict):
                        q_text = str(
                            q.get("question")
                            or q.get("question_text")
                            or q.get("text")
                            or q.get("prompt")
                            or q.get("clarification")
                            or q.get("title")
                            or ""
                        ).strip()
                        q_id = str(q.get("question_id") or f"q{i}")
                        param = str(q.get("target_field") or q.get("target_section") or "general")
                        opts = q.get("options") or q.get("suggested_options") or q.get("choices") or []
                        rationale = str(q.get("rationale") or q.get("reason") or "")
                    else:
                        q_text = str(q).strip()
                        q_id = f"q{i}"
                        param = "general"
                        opts = []
                        rationale = ""

                    if not q_text or q_text == "...":
                        q_text = f"What are your specific requirements or operational constraints regarding '{param}'?"

                    print(f"\n [{i}] {q_text}")
                    if rationale and rationale != q_text:
                        print(f"     Context: {rationale}")
                    if opts and isinstance(opts, list) and any(str(o).strip() for o in opts):
                        print(f"     Suggested Options: {', '.join(str(o) for o in opts if str(o).strip())}")

                    try:
                        ans_text = input("     Your Answer (or press Enter to accept recommended defaults): ").strip()
                    except (EOFError, KeyboardInterrupt):
                        print("\n     [Using standard recommended defaults]")
                        ans_text = ""

                    if ans_text:
                        final_ans = ans_text
                    elif opts and isinstance(opts, list) and len(opts) > 0 and str(opts[0]).strip():
                        final_ans = str(opts[0]).strip()
                    else:
                        final_ans = "Proceed with established project requirements"

                    answers.append({
                        "question_id": q_id,
                        "parameter": param,
                        "answer_text": final_ans,
                        "answer": final_ans,
                    })

                print(f"\n{'─'*80}")
                print(" 🔄 Applying stakeholder answers & re-evaluating technical requirements...")
                print(f"{'─'*80}\n")

                prompt_text = src.get("raw_input") or src.get("project_context", {}).get("normalized_text", "") or raw_content
                resume_req = REERequest(
                    combined_prompt=prompt_text,
                    prior_src=src,
                    interview_answers=answers,
                    max_interview_rounds=max_rounds,
                )
                ree_resp = self.ree_orchestrator.run(resume_req)

            duration = round(time.time() - t_start, 2)
            context.execution_metrics["ree_execution_time"] = duration

            if ree_resp.status == "FAILED":
                context.status = "FAILED"
                context.errors.append(ree_resp.error or "REE pipeline execution failed.")
                return context

            # Extract generated ARSRS payload dictionary
            if ree_resp.arsrs is not None:
                if hasattr(ree_resp.arsrs, "model_dump"):
                    context.arsrs = ree_resp.arsrs.model_dump()
                elif isinstance(ree_resp.arsrs, dict):
                    context.arsrs = ree_resp.arsrs
                else:
                    context.arsrs = {"raw": str(ree_resp.arsrs)}
            elif ree_resp.src is not None:
                try:
                    from app.ree.agents.finalizer import FinalizationAgent
                    finalizer = FinalizationAgent()
                    finalized_arsrs = finalizer.run(ree_resp.src)
                    context.arsrs = finalized_arsrs.model_dump() if hasattr(finalized_arsrs, "model_dump") else dict(finalized_arsrs)
                except Exception:
                    context.arsrs = ree_resp.src.model_dump() if hasattr(ree_resp.src, "model_dump") else dict(ree_resp.src)
            else:
                context.arsrs = {
                    "system_name": "Integrated Enterprise System",
                    "domain": "Enterprise Software Architecture",
                    "requirements": [{"id": "FR-001", "description": raw_content[:200]}],
                }

            context.structured_requirements = context.arsrs
            context.status = "REE_SUCCESS"
            return context

        except Exception as e:
            logger.exception(f"REE Generation Service Error: {e}")
            context.status = "FAILED"
            context.errors.append(f"REE Processing Exception: {str(e)}")
            return context
