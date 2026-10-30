"""Architectural Reviewer orchestrating Phase 3 & Phase 4 in a unified LLM evaluation.

Loads YAML rubrics, selects reference checklists, formats applicable real-world patterns,
verifies evidence anti-hallucination, and computes explicit C, R, W, D component scores
across HLD and 5 LLDs concurrently under Semaphore(VALIDATOR_CONCURRENCY=3).
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
import yaml

from Validator_Engine_v2.config import config
from Validator_Engine_v2.decision.scoring import compute_artifact_score
if TYPE_CHECKING:
    from Validator_Engine_v2.real_world.profile_extractor import RealWorldPattern
from Validator_Engine_v2.reference.loader import reference_loader
from Validator_Engine_v2.review.evidence import verify_and_filter_evidence
from Validator_Engine_v2.review.llm_client import ReviewerLLMClient
from Validator_Engine_v2.review.prompts import build_review_user_prompt
from Validator_Engine_v2.schemas import (
    ArtifactResult,
    DimensionScore,
    Finding,
    NormalizedPackage,
    PatternAssessment,
    RealWorldResult,
    ReferenceSystemUsed,
)

RUBRICS_DIR = Path(__file__).resolve().parent / "rubrics"


class Reviewer:
    """Orchestrator for LLM-based architectural evaluation and benchmarking."""

    def __init__(
        self,
        llm_client: Optional[ReviewerLLMClient] = None,
        rubrics_dir: Optional[Path] = None,
    ) -> None:
        self.llm_client = llm_client or ReviewerLLMClient()
        self.rubrics_dir = rubrics_dir or RUBRICS_DIR
        self.rubrics: Dict[str, Dict[str, Any]] = {}
        self._load_rubrics()

    def _load_rubrics(self) -> None:
        if not self.rubrics_dir.exists():
            return
        for p in self.rubrics_dir.glob("*.yaml"):
            art = p.stem.lower()
            try:
                self.rubrics[art] = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            except Exception:
                pass

    async def review_artifact(
        self,
        artifact_name: str,
        artifact_data: Dict[str, Any],
        normalized_pkg: NormalizedPackage,
        patterns: Optional[List[RealWorldPattern]] = None,
        system_names_by_pattern: Optional[Dict[str, str]] = None,
        references_used: Optional[List[ReferenceSystemUsed]] = None,
        l0_findings: Optional[List[Finding]] = None,
        l1_findings: Optional[List[Finding]] = None,
        scaffold_evaluated: bool = False,
        reviewer_mode: str = "live",
        additional_penalty_d: int = 0,
        dt_l0_ms: float = 0.0,
        dt_l1_ms: float = 0.0,
    ) -> ArtifactResult:
        """Evaluate an architecture artifact against its rubric and applicable real-world patterns in one consolidated LLM call."""
        art_clean = artifact_name.lower().replace("_lld", "")
        rubric = self.rubrics.get(art_clean)
        if not rubric:
            # Fallback bare rubric if YAML missing
            rubric = {
                "dimensions": [
                    {"id": "specificity", "label": "Specificity", "weight": 1.0, "source": "internal"}
                ]
            }

        # 1. Select applicable reference checklists (compact 200 tokens to keep prompt tight)
        tags = rubric.get("applicable_tags", [])
        context_text = f"{normalized_pkg.system_name} {normalized_pkg.domain}"
        reference_excerpts = reference_loader.select_excerpts(tags, context_text=context_text, max_tokens=200)

        # 2. Select applicable real-world patterns for this artifact (top 2 priority)
        applicable_patterns: List[RealWorldPattern] = []
        if patterns:
            applicable_patterns = [
                p for p in patterns
                if art_clean in [a.lower() for a in p.applies_to_artifacts]
            ]
            applicable_patterns.sort(key=lambda x: x.priority)
            applicable_patterns = applicable_patterns[:2]

        # 3. Build unified prompt with truncation safety
        reqs_summary = [
            {"id": r.id, "text": r.text, "type": r.type}
            for r in normalized_pkg.requirements[:6]
        ]
        cac_summary = normalized_pkg.raw_package.get("cac") or {}

        user_prompt, truncated = build_review_user_prompt(
            artifact_name=art_clean,
            artifact_data=artifact_data,
            requirements_summary=reqs_summary,
            cac_summary=cac_summary,
            reference_excerpts=reference_excerpts,
            rubric=rubric,
            patterns=applicable_patterns if patterns else None,
            system_names_by_pattern=system_names_by_pattern,
        )

        # 4. Execute single consolidated LLM Call (Layers L2-L4)
        target_design_name = ""
        if normalized_pkg:
            raw_p = getattr(normalized_pkg, "raw_package", {}) or {}
            m_info = raw_p.get("model_info") or {}
            target_design_name = m_info.get("name") or raw_p.get("model_name") or ""
            if not target_design_name:
                sys_n = str(getattr(normalized_pkg, "system_name", "") or raw_p.get("system_name", "") or "")
                if "gemini" in sys_n.lower():
                    target_design_name = "Gemini"
                elif "chatgpt" in sys_n.lower():
                    target_design_name = "ChatGPT"
                elif "nvidia" in sys_n.lower():
                    target_design_name = "Nvidia"
                elif raw_p.get("is_benchmark"):
                    target_design_name = "Benchmark Model"
                else:
                    target_design_name = "Archova AI Engine"

        t_l2_start = time.perf_counter()
        parsed_out, reviewer_status = await self.llm_client.call_review(
            artifact_name=art_clean,
            artifact_data=artifact_data,
            rubric=rubric,
            user_prompt=user_prompt,
            mock_mode=("mock" if reviewer_mode == "mock" else None),
            target_design_name=target_design_name,
        )
        dt_l2_s = time.perf_counter() - t_l2_start

        model_used = getattr(self.llm_client, "last_model_used", None) or ("mock" if reviewer_mode == "mock" else None)

        # 5. Handle LLM failure or unavailability
        if reviewer_status != "ok" or not parsed_out:
            raw_res = ArtifactResult(
                artifact=art_clean,
                score=50,
                verdict="PROVISIONAL",
                dimensions=[],
                findings=[],
                reviewer_status="unavailable",
                truncated=truncated,
                model_used=model_used or "none",
            )
            t_l5_start = time.perf_counter()
            cal_res = compute_artifact_score(
                artifact_name=art_clean,
                reviewer_result=raw_res,
                l0_findings=l0_findings or [],
                l1_findings=l1_findings or [],
                real_world_result=None,
                real_world_findings=[],
                reviewer_mode=reviewer_mode,
                normalized_pkg=normalized_pkg,
                scaffold_evaluated=scaffold_evaluated,
                additional_penalty_d=additional_penalty_d,
            )
            dt_l5_ms = (time.perf_counter() - t_l5_start) * 1000
            print(f"  │   ├── [L0: Structure]     ✅ {dt_l0_ms:.1f}ms ({len(l0_findings or [])} defects)", flush=True)
            print(f"  │   ├── [L1: Evidence]      ✅ {dt_l1_ms:.1f}ms ({len(l1_findings or [])} defects)", flush=True)
            print(f"  │   ├── [L2-L4: Review]     ⚠️ LLM unavailable. Deterministic fallback used.", flush=True)
            print(f"  │   └── [L5: Calibration]   ✅ {dt_l5_ms:.1f}ms | Final Score: {cal_res.score}%", flush=True)
            return cal_res

        # 6. Parse Dimensions & Findings (Phase 3)
        raw_dims = parsed_out.get("dimensions", [])
        dimensions: List[DimensionScore] = []
        for rd in raw_dims:
            d_id = rd.get("id")
            w = 0.15
            lbl = d_id
            for r_d in rubric.get("dimensions", []):
                if r_d["id"] == d_id:
                    w = float(r_d.get("weight", 0.15))
                    lbl = r_d.get("label", d_id)
                    break
            try:
                dimensions.append(
                    DimensionScore(
                        id=d_id,
                        label=lbl,
                        weight=w,
                        score=int(rd.get("score", 0)),
                        evidence_path=rd.get("evidence_path"),
                        missing=rd.get("missing", []),
                        rationale=rd.get("rationale", ""),
                    )
                )
            except Exception:
                pass

        raw_findings = parsed_out.get("findings", [])
        findings: List[Finding] = []
        for rf in raw_findings:
            rule_id = str(rf.get("rule_id", f"REVIEW.{art_clean.upper()}"))
            sev = str(rf.get("severity", "medium")).lower()
            if sev not in ("critical", "high", "medium", "low"):
                sev = "medium"
            msg = str(rf.get("message", "Review finding"))
            ep = rf.get("evidence_path")
            fix = rf.get("fix")
            findings.append(
                Finding.create(
                    layer="REVIEW",
                    rule_id=rule_id,
                    artifact=art_clean,
                    severity=sev,
                    message=msg,
                    evidence_path=ep,
                    source=rubric.get("sources", ["IEEE1016"])[0] if rubric.get("sources") else "IEEE1016",
                    suggested_fix=fix,
                )
            )

        # 7. Anti-Hallucination Evidence Verification for Phase 3
        verified_dims, verified_findings, dropped_count = verify_and_filter_evidence(
            dimensions=dimensions,
            findings=findings,
            artifact_data=artifact_data,
        )

        # 8. Score Real-World Assessments (Phase 4)
        rw_result: Optional[RealWorldResult] = None
        rw_findings: List[Finding] = []

        if patterns is not None and applicable_patterns:
            raw_assessments = parsed_out.get("assessments", [])
            assessments_by_id = {
                a.get("pattern_id"): a for a in raw_assessments if isinstance(a, dict)
            }
            parsed_assessments: List[PatternAssessment] = []
            sys_names = system_names_by_pattern or {}

            for pat in applicable_patterns:
                sys_name = sys_names.get(pat.id, "Real-World System")
                raw_a = assessments_by_id.get(pat.id)
                if raw_a:
                    st = raw_a.get("status", "MISSING")
                    if st not in ("ALIGNED", "PARTIAL", "MISSING", "JUSTIFIED_DIVERGENCE", "NOT_APPLICABLE"):
                        st = "MISSING"
                    ev = raw_a.get("evidence_path")
                    just = str(raw_a.get("justification") or "")[:200]
                    refs = raw_a.get("requirement_refs") or []
                    if not isinstance(refs, list):
                        refs = [str(refs)]
                    parsed_assessments.append(
                        PatternAssessment(
                            pattern_id=pat.id,
                            system_name=sys_name,
                            pattern_name=pat.name,
                            category=pat.category,
                            priority=pat.priority,
                            status=st,
                            evidence_path=ev,
                            justification=just,
                            requirement_refs=[str(r) for r in refs],
                        )
                    )
                else:
                    parsed_assessments.append(
                        PatternAssessment(
                            pattern_id=pat.id,
                            system_name=sys_name,
                            pattern_name=pat.name,
                            category=pat.category,
                            priority=pat.priority,
                            status="MISSING",
                            justification="Pattern not addressed in artifact specification.",
                        )
                    )

            from Validator_Engine_v2.real_world.scoring import score_real_world_assessments
            rw_result, rw_findings = score_real_world_assessments(
                artifact_name=art_clean,
                assessments=parsed_assessments,
                artifact_data=artifact_data,
                references_used=references_used or [],
            )

        # 9. Compute Component R
        if verified_dims:
            total_weight = sum(d.weight for d in verified_dims)
            if total_weight > 0:
                rubric_score = int(round(100.0 * sum(d.weight * (d.score / 5.0) for d in verified_dims) / total_weight))
            else:
                rubric_score = 50
        else:
            rubric_score = 50

        # Natural rubric score calculated directly from LLM-verified dimension ratings
        rubric_score = max(0, min(100, rubric_score))

        # Best / Weakest dimensions
        best_dim = None
        weakest_dim = None
        if verified_dims:
            sorted_by_score = sorted(verified_dims, key=lambda d: d.score)
            weakest_dim = sorted_by_score[0].id
            best_dim = sorted_by_score[-1].id

        preliminary_res = ArtifactResult(
            artifact=art_clean,
            score=rubric_score,
            verdict="ACCEPTED" if rubric_score >= config.ACCEPT_THRESHOLD else "REJECTED",
            dimensions=verified_dims,
            findings=verified_findings,
            best_dimension=best_dim,
            weakest_dimension=weakest_dim,
            reviewer_status="ok",
            dropped_unverified=dropped_count,
            truncated=truncated,
            model_used=model_used,
        )

        # 10. Phase 5 Scoring & Decision: Combine C, R, W, D via authoritative formula
        t_l5_start = time.perf_counter()
        final_res = compute_artifact_score(
            artifact_name=art_clean,
            reviewer_result=preliminary_res,
            l0_findings=l0_findings or [],
            l1_findings=l1_findings or [],
            real_world_result=rw_result,
            real_world_findings=rw_findings,
            reviewer_mode=reviewer_mode,
            normalized_pkg=normalized_pkg,
            scaffold_evaluated=scaffold_evaluated,
            additional_penalty_d=additional_penalty_d,
        )
        dt_l5_ms = (time.perf_counter() - t_l5_start) * 1000

        tgt_lbl = f"[{target_design_name}] " if target_design_name else ""
        print(f"  │   ├── [L0: Structure]     ✅ {dt_l0_ms:.1f}ms ({len(l0_findings or [])} defects) {tgt_lbl}", flush=True)
        print(f"  │   ├── [L1: Evidence]      ✅ {dt_l1_ms:.1f}ms ({len(l1_findings or [])} defects) {tgt_lbl}", flush=True)
        print(f"  │   ├── [L2-L4: Review]     ✅ {dt_l2_s:.1f}s [{model_used or 'live'}] (Score: {rubric_score}%, {len(verified_dims)} dimensions, {len(verified_findings)} defects) {tgt_lbl}", flush=True)
        print(f"  │   └── [L5: Calibration]   ✅ {dt_l5_ms:.1f}ms | C={final_res.c_score} R={final_res.r_score} W={final_res.w_score} D={final_res.penalty_d} -> Final: {final_res.score}% {tgt_lbl}", flush=True)

        return final_res

    async def review_all_parallel(
        self,
        normalized_pkg: NormalizedPackage,
        patterns: Optional[List[RealWorldPattern]] = None,
        system_names_by_pattern: Optional[Dict[str, str]] = None,
        references_used: Optional[List[ReferenceSystemUsed]] = None,
        l0_findings: Optional[List[Finding]] = None,
        l1_findings: Optional[List[Finding]] = None,
        scaffold_evaluated: bool = False,
        reviewer_mode: str = "live",
    ) -> Dict[str, ArtifactResult]:
        """Review HLD and 5 LLDs concurrently using Semaphore(VALIDATOR_CONCURRENCY)."""
        sem = asyncio.Semaphore(config.VALIDATOR_CONCURRENCY)

        pkg = normalized_pkg.raw_package
        hld = pkg.get("hld", {})
        llds = pkg.get("llds", {})
        if not isinstance(llds, dict):
            llds = {}

        def _unwrap(v: Any) -> Dict[str, Any]:
            if isinstance(v, dict) and "data" in v and isinstance(v["data"], dict):
                return v["data"]
            return v if isinstance(v, dict) else {}

        # Auto-load real world patterns if not provided
        if patterns is None:
            try:
                from Validator_Engine_v2.real_world.corpus_loader import CorpusLoader
                from Validator_Engine_v2.real_world.selector import SystemSelector
                from Validator_Engine_v2.real_world.profile_extractor import ProfileExtractor
                loader = CorpusLoader()
                docs = loader.load_corpus()
                if docs:
                    selector = SystemSelector(top_k=config.REAL_WORLD_TOP_K)
                    arsrs = normalized_pkg.raw_package.get("arsrs", {})
                    hld_data = normalized_pkg.raw_package.get("hld", {})
                    selected = selector.select(docs=docs, arsrs=arsrs, hld=hld_data)
                    extractor = ProfileExtractor(llm_client=self.llm_client)
                    auto_patterns: List[Any] = []
                    auto_sys_names: Dict[str, str] = {}
                    auto_refs: List[ReferenceSystemUsed] = []
                    for s in selected:
                        prof = await extractor.extract_profile(s.doc)
                        for p in prof.patterns:
                            auto_patterns.append(p)
                            auto_sys_names[p.id] = s.doc.system_name
                        auto_refs.append(
                            ReferenceSystemUsed(
                                id=s.doc.id,
                                system_name=s.doc.system_name,
                                match_reasons=s.match_reasons,
                                scale_note=s.scale_note,
                                sources=s.doc.sources,
                            )
                        )
                    patterns = auto_patterns
                    system_names_by_pattern = auto_sys_names
                    references_used = auto_refs
            except Exception:
                pass

        artifacts_to_review = {
            "hld": hld,
            "backend": _unwrap(llds.get("backend")),
            "database": _unwrap(llds.get("database")),
            "frontend": _unwrap(llds.get("frontend")),
            "security": _unwrap(llds.get("security")),
            "cloud": _unwrap(llds.get("cloud")),
        }

        # Strictly sequential evaluation to prevent OpenRouter free-tier rate limits and concurrency clashes
        results: Dict[str, ArtifactResult] = {}
        for name, data in artifacts_to_review.items():
            res = await self.review_artifact(
                artifact_name=name,
                artifact_data=data,
                normalized_pkg=normalized_pkg,
                patterns=patterns,
                system_names_by_pattern=system_names_by_pattern,
                references_used=references_used,
                l0_findings=l0_findings,
                l1_findings=l1_findings,
                scaffold_evaluated=scaffold_evaluated,
                reviewer_mode=reviewer_mode,
            )
            results[name] = res

        return results
