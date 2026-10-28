"""Validation Pipeline: Drives Normalize -> Evidence -> Review -> Decision -> Correction loop.

Executes up to MAX_ROUNDS iterations. Persists reports to runs/{generation_id}.json
after EVERY iteration so the frontend can display real-time progress and crashes do not lose data.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from Validator_Engine_v2.ai_engine_client import AIEngineClient
from Validator_Engine_v2.config import config
from Validator_Engine_v2.decision.feedback import build_all_feedback
from Validator_Engine_v2.decision.history import diff_iteration_corrections
from Validator_Engine_v2.l0_normalize.normalizer import PackageNormalizer
from Validator_Engine_v2.l1_evidence.dockerfile_check import check_dockerfile
from Validator_Engine_v2.l1_evidence.migration_check import check_migration
from Validator_Engine_v2.l1_evidence.openapi_check import check_openapi
from Validator_Engine_v2.l1_evidence.terraform_check import check_terraform
from Validator_Engine_v2.real_world.comparator import PatternComparator
from Validator_Engine_v2.real_world.corpus_loader import CorpusLoader, ReferenceDoc
from Validator_Engine_v2.real_world.profile_extractor import ProfileExtractor, RealWorldPattern
from Validator_Engine_v2.real_world.selector import SystemSelector
from Validator_Engine_v2.review.reviewer import Reviewer
from Validator_Engine_v2.schemas import (
    ArtifactResult,
    Finding,
    Iteration,
    NormalizedPackage,
    ReferenceSystemUsed,
    Report,
)
from Validator_Engine_v2.storage.report_store import report_store

logger = logging.getLogger(__name__)


class PipelineState:
    """In-memory tracking of active background validation pipeline tasks."""

    def __init__(self) -> None:
        self.state: str = "idle"  # idle | running | completed | error
        self.current_step: str = ""
        self.iteration: int = 0
        self.error: Optional[str] = None
        self.started_at: Optional[str] = None
        self.finished_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "current_step": self.current_step,
            "iteration": self.iteration,
            "error": self.error,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


class ValidationPipeline:
    """Drives the multi-round validation and correction workflow."""

    def __init__(
        self,
        ai_engine_client: Optional[AIEngineClient] = None,
        reviewer: Optional[Reviewer] = None,
        normalizer: Optional[PackageNormalizer] = None,
        comparator: Optional[PatternComparator] = None,
    ) -> None:
        self.ai_client = ai_engine_client or AIEngineClient()
        self.reviewer = reviewer or Reviewer()
        self.normalizer = normalizer or PackageNormalizer()
        self.comparator = comparator or PatternComparator(llm_client=self.reviewer.llm_client)
        self.task_states: Dict[str, PipelineState] = {}

    def get_status(self, generation_id: str) -> Dict[str, Any]:
        """Return real-time state for polling UI."""
        st = self.task_states.get(generation_id)
        if st:
            return st.to_dict()
        persisted = report_store.load_report(generation_id)
        if persisted:
            return {
                "state": "completed",
                "current_step": "Validation completed",
                "iteration": len(persisted.get("iterations", [])),
                "error": None,
                "started_at": persisted.get("created_at"),
                "finished_at": persisted.get("iterations", [{}])[-1].get("finished_at") if persisted.get("iterations") else None,
            }
        return {
            "state": "idle",
            "current_step": "Not started",
            "iteration": 0,
            "error": None,
        }

    async def run_single_pass(
        self,
        package: Dict[str, Any],
        iteration_num: int = 1,
        patterns: Optional[List[RealWorldPattern]] = None,
        system_names_by_pattern: Optional[Dict[str, str]] = None,
        references_used: Optional[List[ReferenceSystemUsed]] = None,
        reviewer_mode: str = "live",
        artifacts_filter: Optional[Set[str]] = None,
        previous_results: Optional[Dict[str, ArtifactResult]] = None,
    ) -> Tuple[Dict[str, ArtifactResult], List[Finding], NormalizedPackage]:
        """Execute one complete validation pass: L0 -> L1 -> Consolidated LLM Review (L2-L4) -> L5 Decision."""
        # 1. Phase 1: Layer 0 Normalization
        normalized = self.normalizer.normalize(package)
        l0_findings = normalized.l0_findings

        # 2. Phase 2: Layer 1 Executable Evidence Checks
        l1_findings: List[Finding] = []
        scaffolds = normalized.scaffold_files
        scaffold_evaluated = bool(scaffolds)

        # OpenAPI Check (Backend)
        openapi_content = scaffolds.get("openapi.yaml") or scaffolds.get("scaffolds/openapi.yaml")
        op_findings, _ = check_openapi(openapi_content, normalized.endpoints)
        l1_findings.extend(op_findings)

        # Dockerfile Check (Cloud)
        dockerfile_content = scaffolds.get("Dockerfile") or scaffolds.get("scaffolds/Dockerfile")
        df_findings, _ = check_dockerfile(dockerfile_content)
        l1_findings.extend(df_findings)

        # Terraform Check (Cloud)
        terraform_content = scaffolds.get("terraform/main.tf") or scaffolds.get("scaffolds/terraform/main.tf") or scaffolds.get("main.tf")
        cloud_lld = normalized.raw_package.get("llds", {}).get("cloud", {})
        if isinstance(cloud_lld, dict) and "data" in cloud_lld:
            cloud_lld = cloud_lld["data"]
        tf_findings, _ = check_terraform(terraform_content, cloud_lld if isinstance(cloud_lld, dict) else {})
        l1_findings.extend(tf_findings)

        # Migration Check (Database)
        migration_content = (
            scaffolds.get("alembic/versions/0001_initial_schema.py")
            or scaffolds.get("scaffolds/alembic/versions/0001_initial_schema.py")
            or scaffolds.get("alembic_migration.py")
        )
        mg_findings, _ = check_migration(migration_content, normalized.tables)
        l1_findings.extend(mg_findings)

        # 3. Phase 3 & 4: Consolidated Concurrent Evaluation (Semaphore = 3)
        sem = asyncio.Semaphore(config.VALIDATOR_CONCURRENCY)

        pkg = normalized.raw_package
        hld = pkg.get("hld", {})
        llds = pkg.get("llds", {})
        if not isinstance(llds, dict):
            llds = {}

        def _unwrap(v: Any) -> Dict[str, Any]:
            if isinstance(v, dict) and "data" in v and isinstance(v["data"], dict):
                return v["data"]
            return v if isinstance(v, dict) else {}

        artifacts_to_evaluate = {
            "hld": hld,
            "backend": _unwrap(llds.get("backend")),
            "database": _unwrap(llds.get("database")),
            "frontend": _unwrap(llds.get("frontend")),
            "security": _unwrap(llds.get("security")),
            "cloud": _unwrap(llds.get("cloud")),
        }

        # Determine which artifacts to re-evaluate
        filter_set = {a.lower() for a in artifacts_filter} if artifacts_filter else set(artifacts_to_evaluate.keys())

        async def _eval_artifact(art_name: str, art_data: Dict[str, Any]) -> Tuple[str, ArtifactResult]:
            # If artifact is not in filter_set and was already evaluated, reuse previous result
            if art_name not in filter_set and previous_results and art_name in previous_results:
                return art_name, previous_results[art_name]

            async with sem:
                final_res = await self.reviewer.review_artifact(
                    artifact_name=art_name,
                    artifact_data=art_data,
                    normalized_pkg=normalized,
                    patterns=patterns,
                    system_names_by_pattern=system_names_by_pattern,
                    references_used=references_used,
                    l0_findings=l0_findings,
                    l1_findings=l1_findings,
                    scaffold_evaluated=scaffold_evaluated,
                    reviewer_mode=reviewer_mode,
                )
                return art_name, final_res

        eval_tasks = [
            _eval_artifact(name, data) for name, data in artifacts_to_evaluate.items()
        ]
        eval_tuples = await asyncio.gather(*eval_tasks)
        final_results = dict(eval_tuples)

        all_findings = list(l0_findings) + list(l1_findings)
        for res in final_results.values():
            for f in res.findings:
                if f not in all_findings:
                    all_findings.append(f)

        return final_results, all_findings, normalized

    async def execute_pipeline(
        self,
        generation_id: str,
        initial_package: Optional[Dict[str, Any]] = None,
    ) -> Report:
        """Run complete iterative pipeline with background status tracking and persistence."""
        state = PipelineState()
        state.state = "running"
        state.started_at = datetime.now(timezone.utc).isoformat()
        state.current_step = "Fetching initial architecture package"
        self.task_states[generation_id] = state

        reviewer_mode: str = "mock" if config.VALIDATOR_MOCK in ("1", "true", "mock") else "live"
        model_used: str = "mock" if reviewer_mode == "mock" else config.VALIDATOR_MODEL

        # 1. Fetch package if not provided
        current_package = initial_package
        if not current_package:
            state.current_step = "Connecting to AI Engine to retrieve package"
            current_package = await self.ai_client.fetch_package(generation_id)

        if not current_package:
            state.state = "error"
            state.error = f"Architecture package for generation '{generation_id}' not found."
            raise ValueError(state.error)

        # 2. Phase 4 Setup: Load real-world corpus and select reference systems once
        state.current_step = "Real-World Benchmark: Loading corpus and selecting reference systems"
        corpus_loader = CorpusLoader()
        corpus_docs = corpus_loader.load_corpus()
        corpus_status = "ok" if corpus_docs else "unavailable"

        selected_systems = []
        all_patterns: List[RealWorldPattern] = []
        system_names_by_pattern: Dict[str, str] = {}
        references_used: List[ReferenceSystemUsed] = []

        if corpus_docs:
            selector = SystemSelector(top_k=config.REAL_WORLD_TOP_K)
            arsrs_dict = current_package.get("arsrs", {})
            hld_dict = current_package.get("hld", {})
            selected_systems = selector.select(docs=corpus_docs, arsrs=arsrs_dict, hld=hld_dict)

            profile_extractor = ProfileExtractor(llm_client=self.reviewer.llm_client)
            for s in selected_systems:
                ref_item = ReferenceSystemUsed(
                    id=s.doc.id,
                    system_name=s.doc.system_name,
                    match_reasons=s.match_reasons,
                    scale_note=s.scale_note,
                    sources=s.doc.sources,
                )
                references_used.append(ref_item)

                profile = await profile_extractor.extract_profile(s.doc)
                if not profile.extraction_failed:
                    for p in profile.patterns:
                        all_patterns.append(p)
                        system_names_by_pattern[p.id] = s.doc.system_name

        iterations: List[Iteration] = []
        prev_iteration: Optional[Iteration] = None
        regenerated_artifacts: List[str] = []
        regenerated_with_feedback: bool = True
        artifacts_to_reval: Optional[Set[str]] = None

        max_rounds = config.MAX_ROUNDS

        for round_n in range(1, max_rounds + 1):
            state.iteration = round_n
            iter_start = datetime.now(timezone.utc).isoformat()

            state.current_step = f"Iteration {round_n}: Running 6-Phase validation & benchmarking"
            logger.info("[%s] Running validation iteration %d/%d", generation_id, round_n, max_rounds)

            results, _, normalized = await self.run_single_pass(
                package=current_package,
                iteration_num=round_n,
                patterns=all_patterns if corpus_docs else None,
                system_names_by_pattern=system_names_by_pattern,
                references_used=references_used,
                reviewer_mode=reviewer_mode,
                artifacts_filter=artifacts_to_reval,
                previous_results=prev_iteration.results if prev_iteration else None,
            )

            # Diff history against previous iteration
            corrections = []
            if prev_iteration:
                corrections = diff_iteration_corrections(
                    prev_iteration=prev_iteration,
                    curr_results=results,
                    regenerated_artifacts=regenerated_artifacts,
                    regenerated_with_feedback=regenerated_with_feedback,
                )

            iter_finish = datetime.now(timezone.utc).isoformat()
            iteration = Iteration(
                n=round_n,
                results=results,
                corrections=corrections,
                started_at=iter_start,
                finished_at=iter_finish,
            )
            iterations.append(iteration)
            prev_iteration = iteration

            # Check acceptance
            all_accepted = all(r.verdict in ("ACCEPTED", "ACCEPTED_WITH_WARNINGS") for r in results.values())
            has_provisional = any(r.verdict == "PROVISIONAL" for r in results.values())
            has_critical = any(
                any(f.severity == "critical" for f in r.findings)
                for r in results.values()
            )
            has_rejected_round = any(r.verdict == "REJECTED" for r in results.values())

            # Interim Scores
            interim_scores = {art: r.score for art, r in results.items()}
            overall_c = int(round(sum(r.c_score for r in results.values()) / len(results)))
            overall_r = int(round(sum(r.r_score for r in results.values()) / len(results)))
            w_scores = [r.w_score for r in results.values() if r.w_score is not None]
            overall_w = int(round(sum(w_scores) / len(w_scores))) if w_scores else None
            overall_d = int(round(sum(r.penalty_d for r in results.values()) / len(results)))
            overall_s = int(round(sum(r.score for r in results.values()) / len(results)))
            interim_scores["overall"] = overall_s
            interim_scores["c"] = overall_c
            interim_scores["r"] = overall_r
            interim_scores["w"] = overall_w
            interim_scores["d"] = overall_d

            # Determine Interim Status
            if has_critical:
                interim_status = "REJECTED"
            elif has_rejected_round:
                interim_status = "UNRESOLVED" if round_n == max_rounds else "REJECTED"
            elif has_provisional:
                interim_status = "PROVISIONAL"
            elif all_accepted:
                if reviewer_mode == "mock" and not config.ALLOW_MOCK_ACCEPT:
                    interim_status = "PROVISIONAL"
                elif any(r.verdict == "ACCEPTED_WITH_WARNINGS" for r in results.values()):
                    interim_status = "ACCEPTED_WITH_WARNINGS"
                else:
                    interim_status = "ACCEPTED"
            elif round_n == max_rounds:
                interim_status = "UNRESOLVED"
            else:
                interim_status = "REJECTED"

            interim_report = Report(
                generation_id=generation_id,
                iterations=iterations,
                final_status=interim_status,
                final_scores=interim_scores,
                overall_c=overall_c,
                overall_r=overall_r,
                overall_w=overall_w,
                overall_d=overall_d,
                model_used=model_used,
                reviewer_mode=reviewer_mode,
                corpus_status=corpus_status,
                references_used=references_used,
                config_snapshot={
                    "accept_threshold": config.ACCEPT_THRESHOLD,
                    "max_rounds": config.MAX_ROUNDS,
                    "validator_mock": config.VALIDATOR_MOCK,
                    "allow_mock_accept": config.ALLOW_MOCK_ACCEPT,
                    "rw_weight": config.RW_WEIGHT,
                    "rw_min": config.RW_MIN,
                },
                created_at=state.started_at or iter_start,
                final_package=current_package,
            )
            report_store.save_report(interim_report, final_package=current_package)

            if all_accepted:
                logger.info("[%s] All artifacts accepted on iteration %d!", generation_id, round_n)
                state.current_step = "All artifacts accepted successfully"
                break

            # If not accepted and rounds remain -> prepare targeted regeneration
            if round_n < max_rounds:
                state.current_step = f"Iteration {round_n}: Synthesizing correction feedback & regenerating defects"
                feedback_pkg = build_all_feedback(results)
                rejected_arts = feedback_pkg.get("rejected_artifacts", [])
                regenerated_artifacts = rejected_arts

                # Scoped revalidation rule:
                # If HLD fails, revalidate all artifacts.
                # If only LLDs fail, revalidate affected LLDs.
                if "hld" in rejected_arts:
                    artifacts_to_reval = {"hld", "backend", "database", "frontend", "security", "cloud"}
                else:
                    artifacts_to_reval = set(rejected_arts)

                updated_pkg, reg_with_fb = await self.ai_client.regeneration_adapter.regenerate(
                    generation_id=generation_id,
                    rejected_artifacts=rejected_arts,
                    feedback=feedback_pkg,
                    current_package=current_package,
                )
                current_package = updated_pkg
                regenerated_with_feedback = reg_with_fb

        # Determine Final Status
        last_results = iterations[-1].results
        all_accepted = all(r.verdict in ("ACCEPTED", "ACCEPTED_WITH_WARNINGS") for r in last_results.values())
        has_provisional = any(r.verdict == "PROVISIONAL" for r in last_results.values())
        has_critical = any(
            any(f.severity == "critical" for f in r.findings)
            for r in last_results.values()
        )
        has_rejected = any(r.verdict == "REJECTED" for r in last_results.values())

        if has_critical:
            final_status = "REJECTED"
        elif has_rejected:
            final_status = "UNRESOLVED"
        elif has_provisional:
            final_status = "PROVISIONAL"
        elif all_accepted:
            if reviewer_mode == "mock" and not config.ALLOW_MOCK_ACCEPT:
                final_status = "PROVISIONAL"
            elif any(r.verdict == "ACCEPTED_WITH_WARNINGS" for r in last_results.values()):
                final_status = "ACCEPTED_WITH_WARNINGS"
            else:
                final_status = "ACCEPTED"
        else:
            final_status = "UNRESOLVED"

        final_scores = {art: r.score for art, r in last_results.items()}
        overall_c = int(round(sum(r.c_score for r in last_results.values()) / len(last_results)))
        overall_r = int(round(sum(r.r_score for r in last_results.values()) / len(last_results)))
        w_scores = [r.w_score for r in last_results.values() if r.w_score is not None]
        overall_w = int(round(sum(w_scores) / len(w_scores))) if w_scores else None
        overall_d = int(round(sum(r.penalty_d for r in last_results.values()) / len(last_results)))
        overall_s = int(round(sum(r.score for r in last_results.values()) / len(last_results)))
        final_scores["overall"] = overall_s
        final_scores["c"] = overall_c
        final_scores["r"] = overall_r
        final_scores["w"] = overall_w
        final_scores["d"] = overall_d

        final_report = Report(
            generation_id=generation_id,
            iterations=iterations,
            final_status=final_status,
            final_scores=final_scores,
            overall_c=overall_c,
            overall_r=overall_r,
            overall_w=overall_w,
            overall_d=overall_d,
            model_used=model_used,
            reviewer_mode=reviewer_mode,
            corpus_status=corpus_status,
            references_used=references_used,
            config_snapshot={
                "accept_threshold": config.ACCEPT_THRESHOLD,
                "max_rounds": config.MAX_ROUNDS,
                "validator_mock": config.VALIDATOR_MOCK,
                "allow_mock_accept": config.ALLOW_MOCK_ACCEPT,
                "rw_weight": config.RW_WEIGHT,
                "rw_min": config.RW_MIN,
            },
            created_at=state.started_at or datetime.now(timezone.utc).isoformat(),
            final_package=current_package,
        )

        report_store.save_report(final_report, final_package=current_package)

        state.state = "completed"
        state.current_step = f"Validation completed with verdict: {final_status}"
        state.finished_at = datetime.now(timezone.utc).isoformat()

        return final_report


# Global singleton pipeline instance
pipeline_engine = ValidationPipeline()
