"""Decision Scoring Engine: Computes weighted scores, deductions, caps, and verdicts.

Authoritative Specification:
Formula:
  Normal:         S = 0.20*C + 0.45*R + 0.35*W - D
  Low Confidence: S = 0.20*C + 0.65*R + 0.15*W - D

Where:
  C = Structural and Technical Correctness (0-100), calculated from Phase 1 & 2 checks.
  R = Architecture Quality Review (0-100), calculated from weighted 0-5 rubric dimensions.
  W = Real-World Architecture Suitability (0-100), calculated from applicable benchmark patterns.
  D = Additional verified defect penalties (0-100), avoiding double-counting of issues already in C, R, or W.

Rules:
- Low-confidence benchmark weighting switches W to 0.15 and R to 0.65.
- If the benchmark is unavailable, do NOT calculate a normal final score by treating missing W as zero;
  return PROVISIONAL.
- Critical-defect rule: Any critical defect caps score at 60 and forces REJECTED.
- ACCEPT rule:
    S >= ACCEPT_THRESHOLD (80)
    AND W >= RW_MIN (60)
    AND all mandatory checks complete
    AND no unresolved critical or high findings
    AND (reviewer_mode != 'mock' or ALLOW_MOCK_ACCEPT == 1).
- ACCEPT_WITH_WARNINGS:
    Acceptance criteria met, no critical or high findings, only non-critical (medium/low) issues remain.
- REJECTED:
    Critical defect exists or acceptance thresholds not met.
- PROVISIONAL:
    Mandatory validation stage cannot be completed (LLM unavailable or benchmark unavailable).
"""

from __future__ import annotations

from typing import Dict, List, Optional
from Validator_Engine_v2.config import config
from Validator_Engine_v2.decision.correctness import compute_correctness_score
from Validator_Engine_v2.schemas import ArtifactResult, Finding, NormalizedPackage, RealWorldResult


def compute_artifact_score(
    artifact_name: str,
    reviewer_result: ArtifactResult,
    l0_findings: List[Finding],
    l1_findings: List[Finding],
    real_world_result: Optional[RealWorldResult] = None,
    real_world_findings: Optional[List[Finding]] = None,
    reviewer_mode: str = "live",
    normalized_pkg: Optional[NormalizedPackage] = None,
    scaffold_evaluated: bool = False,
    additional_penalty_d: int = 0,
) -> ArtifactResult:
    """Compute explicit C, R, W, and D component scores, composite score S, and final verdict."""
    art_clean = artifact_name.lower().replace("_lld", "")
    art_l0 = [f for f in l0_findings if f.artifact.lower() == art_clean]
    art_l1 = [f for f in l1_findings if f.artifact.lower() == art_clean]
    rw_fnd = real_world_findings or []

    all_findings: List[Finding] = list(reviewer_result.findings) + art_l0 + art_l1 + rw_fnd

    # Check for critical and high findings across all layers
    has_critical = any(f.severity == "critical" for f in all_findings)
    has_high = any(f.severity == "high" for f in all_findings)

    # ── 1. Component C: Structural and Technical Correctness (0-100) ──
    c_score = compute_correctness_score(
        artifact_name=art_clean,
        l0_findings=l0_findings,
        l1_findings=l1_findings,
        normalized_pkg=normalized_pkg,
        scaffold_evaluated=scaffold_evaluated,
    )

    # ── 2. Component R: Architecture Quality Review (0-100) ──
    if reviewer_result.reviewer_status == "ok" and reviewer_result.dimensions:
        total_weight = sum(d.weight for d in reviewer_result.dimensions)
        if total_weight > 0:
            r_score = int(round(
                100.0 * sum(d.weight * (d.score / 5.0) for d in reviewer_result.dimensions) / total_weight
            ))
        else:
            r_score = 50
    elif reviewer_result.reviewer_status != "ok":
        r_score = 50
    else:
        r_score = reviewer_result.score

    r_score = max(0, min(100, r_score))

    # ── 3. Component W: Real-World Architecture Suitability (0-100) ──
    rw_score: Optional[int] = None
    rw_confidence: str = "unavailable"
    if real_world_result and real_world_result.score is not None:
        rw_score = real_world_result.score
        rw_confidence = real_world_result.confidence

    # ── 4. Penalty D: Additional verified defect penalties ──
    penalty_d = max(0, int(additional_penalty_d))

    # ── 5. Composite Score S Calculation ──
    benchmark_available = (rw_score is not None and rw_confidence != "unavailable")

    if benchmark_available:
        if rw_confidence == "low":
            # Low-confidence weighting: S = 0.20*C + 0.65*R + 0.15*W - D
            composite_raw = 0.20 * c_score + 0.65 * r_score + 0.15 * rw_score - penalty_d
        else:
            # Normal weighting: S = 0.20*C + 0.45*R + 0.35*W - D
            composite_raw = 0.20 * c_score + 0.45 * r_score + 0.35 * rw_score - penalty_d
        final_score = int(round(composite_raw))
    else:
        # Benchmark unavailable: cannot compute normal score treating W as 0
        final_score = int(round(0.20 * c_score + 0.80 * r_score - penalty_d))

    # Clamp to [0, 100]
    final_score = max(0, min(100, final_score))

    # ── 6. Critical-Defect Cap ──
    # Any critical finding caps score at 60 and forces REJECTED
    if has_critical:
        final_score = min(final_score, 60)

    # ── 7. Decision Precedence and Verdict Resolution ──
    if has_critical:
        verdict = "REJECTED"
    elif reviewer_result.reviewer_status != "ok":
        # Mandatory LLM review stage incomplete
        verdict = "PROVISIONAL"
    elif not benchmark_available:
        # Mandatory real-world benchmark unavailable
        verdict = "PROVISIONAL"
    elif has_high or final_score < config.ACCEPT_THRESHOLD or (rw_score is not None and rw_score < config.RW_MIN):
        verdict = "REJECTED"
    elif reviewer_mode == "mock" and not config.ALLOW_MOCK_ACCEPT:
        # Simulated offline mock inference cannot yield ACCEPTED without explicit test bypass
        verdict = "PROVISIONAL"
    elif len(all_findings) > 0:
        # Acceptance thresholds met, no critical or high defects, but non-critical issues remain
        verdict = "ACCEPTED_WITH_WARNINGS"
    else:
        verdict = "ACCEPTED"

    # Best & Weakest dimension
    best_dim = reviewer_result.best_dimension
    weakest_dim = reviewer_result.weakest_dimension
    if reviewer_result.dimensions:
        sorted_dims = sorted(reviewer_result.dimensions, key=lambda d: d.score)
        weakest_dim = sorted_dims[0].id
        best_dim = sorted_dims[-1].id

    return ArtifactResult(
        artifact=artifact_name,
        score=final_score,
        final_score=final_score,
        c_score=c_score,
        r_score=r_score,
        w_score=rw_score,
        penalty_d=penalty_d,
        rubric_score=r_score,
        real_world=real_world_result,
        verdict=verdict,
        dimensions=reviewer_result.dimensions,
        findings=all_findings,
        best_dimension=best_dim,
        weakest_dimension=weakest_dim,
        reviewer_status=reviewer_result.reviewer_status,
        dropped_unverified=reviewer_result.dropped_unverified,
        truncated=reviewer_result.truncated,
        model_used=reviewer_result.model_used,
    )
