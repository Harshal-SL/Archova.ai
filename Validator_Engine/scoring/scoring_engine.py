"""Unified Multi-Dimensional Scoring and Quality Gating Engine.

Calculates balanced, non-contradictory scores across structural integrity, requirement
traceability, cross-artifact consistency, NFR adherence, real-world benchmark alignment,
and red-team resilience.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from Validator_Engine.models.finding_models import FindingSeverity, ValidationFinding
from Validator_Engine.models.report_models import (
    CrossArtifactConsistencyReport,
    NFRValidationReport,
    RealWorldEvidenceReport,
    RedTeamReviewReport,
    RequirementAlignmentReport,
    StructuralValidationReport,
    UnifiedScorecard,
)

logger = logging.getLogger(__name__)


class ScoringEngine:
    """Master Multi-Tier Architectural Quality Gating and Scoring Engine."""

    def __init__(self) -> None:
        pass

    def evaluate(
        self,
        structural_report: StructuralValidationReport,
        requirement_report: RequirementAlignmentReport,
        consistency_report: CrossArtifactConsistencyReport,
        nfr_report: NFRValidationReport,
        real_world_report: RealWorldEvidenceReport,
        red_team_report: RedTeamReviewReport,
        all_findings: Optional[List[ValidationFinding]] = None,
    ) -> UnifiedScorecard:
        """Compute holistic, non-contradictory scorecard and evaluate hard quality gates."""
        all_findings = all_findings or []

        # 1. Extract Component Scores
        structural_score = structural_report.score
        req_score = requirement_report.score
        cons_score = consistency_report.score
        nfr_score = nfr_report.score
        rw_score = real_world_report.score
        resilience_score = red_team_report.score

        per_section_scores = {
            "structural_completeness": structural_score,
            "requirement_alignment": req_score,
            "cross_artifact_consistency": cons_score,
            "nfr_adherence": nfr_score,
            "real_world_evidence": rw_score,
            "red_team_resilience": resilience_score,
        }

        # 2. Hard Gate Evaluations & Violations
        hard_gates: Dict[str, bool] = {}
        hard_gate_violations: List[str] = []

        # Gate 1: Structural Completeness (>= 0.70)
        gate_structural = structural_score >= 0.70 and structural_report.is_valid
        hard_gates["structural_quality_gate"] = gate_structural
        if not gate_structural:
            hard_gate_violations.append(
                f"Structural completeness ({structural_score*100:.0f}%) is below minimum threshold 70% or contains malformed elements."
            )

        # Gate 2: Requirement Traceability (>= 0.75)
        gate_req = requirement_report.traceability_ratio >= 0.75 and len(requirement_report.uncovered_requirement_ids) == 0
        hard_gates["requirement_traceability_gate"] = gate_req
        if not gate_req:
            hard_gate_violations.append(
                f"Requirement traceability ({requirement_report.traceability_ratio*100:.0f}%) has untraced or partially covered requirements: {requirement_report.uncovered_requirement_ids or 'Missing endpoint/table links'}."
            )

        # Gate 3: Cross-Artifact Consistency (>= 0.75 & no critical drifts)
        gate_alignment = (
            consistency_report.frontend_to_backend_alignment >= 0.80
            and consistency_report.backend_to_database_alignment >= 0.80
            and consistency_report.is_valid
        )
        hard_gates["cross_artifact_alignment_gate"] = gate_alignment
        if not gate_alignment:
            hard_gate_violations.append(
                f"Cross-artifact alignment failure (FE-BE: {consistency_report.frontend_to_backend_alignment*100:.0f}%, "
                f"BE-DB: {consistency_report.backend_to_database_alignment*100:.0f}%)."
            )

        # Gate 4: NFR Feasibility
        gate_nfr = nfr_report.unsupported_nfrs_count == 0 and nfr_report.score >= 0.65
        hard_gates["nfr_feasibility_gate"] = gate_nfr
        if not gate_nfr:
            hard_gate_violations.append(
                f"NFR validation detected {nfr_report.unsupported_nfrs_count} unsupported NFRs or low mechanism grounding ({nfr_report.score*100:.0f}%)."
            )

        # Gate 5: Red-Team Adversarial Verdict
        gate_red_team = red_team_report.verdict in ("APPROVED", "APPROVED_WITH_CONDITIONS")
        hard_gates["red_team_adversarial_gate"] = gate_red_team
        if not gate_red_team:
            hard_gate_violations.append(
                f"Adversarial Red-Team review returned '{red_team_report.verdict}' due to {len(red_team_report.single_points_of_failure)} SPOFs or critical bottlenecks."
            )

        # 3. Calculate Production Readiness
        critical_count = len([f for f in all_findings if f.severity == FindingSeverity.CRITICAL])
        high_count = len([f for f in all_findings if f.severity == FindingSeverity.HIGH])
        medium_count = len([f for f in all_findings if f.severity == FindingSeverity.MEDIUM])

        base_readiness = (
            (0.20 * structural_score)
            + (0.25 * req_score)
            + (0.20 * cons_score)
            + (0.15 * nfr_score)
            + (0.20 * resilience_score)
        )

        penalty = (critical_count * 0.20) + (high_count * 0.05) + (medium_count * 0.02)
        production_readiness = round(max(0.10, min(1.0, base_readiness - penalty)), 2)

        # 4. Calculate Overall Composite Score
        overall_composite = round(
            (0.15 * structural_score)
            + (0.25 * req_score)
            + (0.20 * cons_score)
            + (0.15 * nfr_score)
            + (0.10 * rw_score)
            + (0.15 * resilience_score),
            2,
        )

        # 5. Determine Unified Status
        hard_gates["zero_hard_gate_violations"] = len(hard_gate_violations) == 0

        if len(hard_gate_violations) == 0 and critical_count == 0 and high_count <= 1 and production_readiness >= 0.75:
            status = "HEALTHY"
        elif critical_count > 0 or red_team_report.verdict == "REJECTED" or production_readiness < 0.45:
            status = "NEEDS_REMEDIATION"
        elif len(hard_gate_violations) > 0 or high_count > 0 or production_readiness < 0.75:
            status = "DEGRADED"
        else:
            status = "HEALTHY"

        return UnifiedScorecard(
            status=status,
            overall_composite_score=overall_composite,
            structural_completeness=structural_score,
            artifact_quality_score=req_score,
            consistency_score=cons_score,
            requirement_alignment_score=req_score,
            production_readiness_score=production_readiness,
            traceability_score=requirement_report.traceability_ratio,
            evidence_support_score=rw_score,
            per_section_scores=per_section_scores,
            hard_gates=hard_gates,
            hard_gates_passed=len(hard_gate_violations) == 0,
            hard_gate_violations=hard_gate_violations,
            quality_indicators={
                "total_findings_count": len(all_findings),
                "critical_findings_count": critical_count,
                "high_findings_count": high_count,
                "medium_findings_count": medium_count,
                "untraced_requirements_count": len(requirement_report.untraced_requirement_ids),
                "spofs_count": len(red_team_report.single_points_of_failure),
                "bottlenecks_count": len(red_team_report.scalability_bottlenecks),
                "reference_archetype": real_world_report.primary_archetype,
            },
        )
