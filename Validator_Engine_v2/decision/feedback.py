"""Correction Feedback Generator.

Synthesizes structured, actionable feedback per rejected/provisional artifact
containing failed dimensions, missing mechanisms, finding details, real-world benchmark gaps,
and concrete remediation instructions.
"""

from __future__ import annotations

from typing import Any, Dict, List
from Validator_Engine_v2.schemas import ArtifactResult


def build_artifact_feedback(result: ArtifactResult) -> Dict[str, Any]:
    """Build structured feedback dictionary for a single artifact."""
    failed_dims: List[str] = []
    missing_items: List[str] = []

    for d in result.dimensions:
        if d.score < 3:
            failed_dims.append(d.id)
            for m in d.missing:
                if m and m not in missing_items:
                    missing_items.append(m)

    findings_payload = []
    for f in result.findings:
        findings_payload.append({
            "id": f.id,
            "rule_id": f.rule_id,
            "severity": f.severity,
            "message": f.message,
            "evidence_path": f.evidence_path,
            "fix": f.suggested_fix or "Remediate architectural non-conformance.",
        })

    # Real-world benchmark gaps
    real_world_gaps = []
    if result.real_world:
        for a in result.real_world.assessments:
            if a.status in ("MISSING", "PARTIAL"):
                real_world_gaps.append({
                    "pattern_name": a.pattern_name,
                    "reference_system": a.system_name,
                    "why_applicable": a.justification,
                    "what_to_add": (
                        f"Address '{a.pattern_name}' capability at this system's scale and operational profile. "
                        f"Do not replicate {a.system_name}'s high-scale infrastructure; tie the design to requirement IDs."
                    ),
                    "requirement_refs": a.requirement_refs,
                })

    instruction = (
        f"Regenerate '{result.artifact}' artifact to resolve validation failures. "
        "Replace generic statements with concrete specifics tied to requirement IDs. "
        "Ensure all required mechanisms (e.g. concurrency locking, idempotency keys, "
        "data integrity constraints, error models) are explicitly and verifiably declared. "
        "Address identified real-world transferable capabilities at this system's stated scale "
        "without copying the reference companies' planetary infrastructure."
    )

    return {
        "artifact": result.artifact,
        "score": result.score,
        "rubric_score": result.rubric_score,
        "real_world_score": result.real_world.score if result.real_world else None,
        "verdict": result.verdict,
        "failed_dimensions": failed_dims,
        "missing": missing_items,
        "findings": findings_payload,
        "real_world_gaps": real_world_gaps,
        "instruction": instruction,
    }


def build_all_feedback(results: Dict[str, ArtifactResult]) -> Dict[str, Any]:
    """Build feedback for all non-accepted artifacts."""
    feedback_per_art: Dict[str, Any] = {}
    for art, res in results.items():
        if res.verdict != "ACCEPTED":
            feedback_per_art[art] = build_artifact_feedback(res)

    return {
        "requires_regeneration": len(feedback_per_art) > 0,
        "rejected_artifacts": list(feedback_per_art.keys()),
        "feedback": feedback_per_art,
    }
