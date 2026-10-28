"""Deterministic scoring and findings generation for Real-World Benchmark.

Verifies pattern evidence against actual artifact data, computes normalized scores,
evaluates confidence levels, and produces stable Finding objects.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from Validator_Engine_v2.review.evidence import is_evidence_verified
from Validator_Engine_v2.schemas import (
    Finding,
    PatternAssessment,
    RealWorldResult,
    ReferenceSystemUsed,
    compute_finding_id,
)


def score_real_world_assessments(
    artifact_name: str,
    assessments: List[PatternAssessment],
    artifact_data: Dict[str, Any],
    references_used: List[ReferenceSystemUsed],
) -> Tuple[RealWorldResult, List[Finding]]:
    """Verify evidence, compute deterministic real-world score, and generate findings.

    Returns:
        RealWorldResult: Score, counts, verified assessments, and confidence.
        List[Finding]: Findings generated for MISSING and PARTIAL patterns.
    """
    if not assessments:
        res = RealWorldResult(
            artifact=artifact_name,
            score=None,
            confidence="unavailable",
            counts={
                "aligned": 0,
                "partial": 0,
                "missing": 0,
                "justified_divergence": 0,
                "not_applicable": 0,
                "downgraded_unverified": 0,
            },
            assessments=[],
            references_used=references_used,
        )
        return res, []

    verified_assessments: List[PatternAssessment] = []
    downgraded_count = 0

    # 1. Anti-hallucination evidence verification
    for a in assessments:
        item = a.model_copy()

        if item.status in ("ALIGNED", "PARTIAL", "JUSTIFIED_DIVERGENCE"):
            if not is_evidence_verified(item.evidence_path, artifact_data):
                # Downgrade to MISSING if evidence is missing or cannot be verified
                item.status = "MISSING"
                item.justification = (
                    f"[Unverified evidence: '{item.evidence_path}'] Downgraded to MISSING. {item.justification}"
                )[:200]
                item.evidence_path = None
                downgraded_count += 1

        elif item.status == "NOT_APPLICABLE":
            # NOT_APPLICABLE requires requirement_refs; otherwise downgrade to MISSING
            if not item.requirement_refs or len(item.requirement_refs) == 0:
                item.status = "MISSING"
                item.justification = (
                    f"[Missing requirement_refs for NOT_APPLICABLE] Downgraded to MISSING. {item.justification}"
                )[:200]
                downgraded_count += 1

        verified_assessments.append(item)

    # 2. Count statuses
    aligned = sum(1 for a in verified_assessments if a.status == "ALIGNED")
    partial = sum(1 for a in verified_assessments if a.status == "PARTIAL")
    missing = sum(1 for a in verified_assessments if a.status == "MISSING")
    justified = sum(1 for a in verified_assessments if a.status == "JUSTIFIED_DIVERGENCE")
    not_applicable = sum(1 for a in verified_assessments if a.status == "NOT_APPLICABLE")

    total = len(verified_assessments)
    applicable = total - not_applicable

    # 3. Compute score and confidence
    if applicable == 0:
        score: Optional[int] = None
        confidence = "unavailable"
    else:
        raw_score = (100 * aligned + 50 * partial + 80 * justified) / applicable
        score = int(round(raw_score + 1e-9))

        # Confidence: low if applicable < 3 or >50% patterns are NOT_APPLICABLE
        if applicable < 3 or (not_applicable / total) > 0.5:
            confidence = "low"
        else:
            confidence = "normal"

    counts = {
        "aligned": aligned,
        "partial": partial,
        "missing": missing,
        "justified_divergence": justified,
        "not_applicable": not_applicable,
        "downgraded_unverified": downgraded_count,
    }

    # 4. Generate stable findings for MISSING and PARTIAL patterns
    findings: List[Finding] = []
    for a in verified_assessments:
        if a.status in ("MISSING", "PARTIAL"):
            # Determine severity
            if a.status == "MISSING":
                severity = "high" if a.priority == 1 else "medium" if a.priority == 2 else "low"
            else:  # PARTIAL
                severity = "medium" if a.priority == 1 else "low"

            msg = (
                f"Missing real-world capability '{a.pattern_name}' from reference system {a.system_name}: "
                f"{a.justification}"
            )
            suggested_fix = (
                f"Address '{a.pattern_name}' capability appropriate to this system's scale and operational profile. "
                f"Do not replicate {a.system_name}'s high-scale infrastructure; tie the mechanism to requirement IDs."
            )

            f_id = compute_finding_id(
                rule_id=a.pattern_id,
                artifact=artifact_name,
                evidence_path=a.evidence_path,
                message=msg,
            )

            findings.append(
                Finding.create(
                    layer="REAL_WORLD",
                    rule_id=a.pattern_id,
                    artifact=artifact_name,
                    severity=severity,
                    message=msg,
                    evidence_path=a.evidence_path,
                    source=f"{a.system_name} reference",
                    suggested_fix=suggested_fix,
                    finding_id=f_id,
                )
            )

    result = RealWorldResult(
        artifact=artifact_name,
        score=score,
        confidence=confidence,
        counts=counts,
        assessments=verified_assessments,
        references_used=references_used,
    )

    return result, findings
