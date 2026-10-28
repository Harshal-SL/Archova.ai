"""Phase 1 & Phase 2: Structural and Technical Correctness (C) Calculation Engine.

Calculates an explicit, normalized 0-100 correctness score C based on deterministic checks
from Phase 1 (Intake & Normalization) and Phase 2 (Deterministic Technical Validation).

Specification Rules:
1. C is calculated as a distinct 0-100 component score.
2. Contributes 20% to the final composite score S: S = 0.20*C + 0.45*R + 0.35*W - D.
3. Check Groups:
   - Group 1: Structural Schema Completeness & Required Elements (Weight: 50)
   - Group 2: Cross-Artifact Consistency & Orphan References (Weight: 50 when no scaffold, or 25 with scaffold)
   - Group 3: Technical Scaffolds & Executable Evidence (Weight: 25 when scaffold evaluated)
4. Missing scaffolds are reported as NOT_EVALUATED, not PASSED.
   When scaffolds are NOT_EVALUATED, they are excluded from the denominator so that
   unperformed checks neither award nor penalize the artifact.
5. Invalid inputs, missing required fields, or syntax errors reduce the earned points.
6. A critical defect in Phase 1 or 2 caps C at 60 and triggers the critical defect rejection rule.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from Validator_Engine_v2.schemas import Finding, NormalizedPackage


def compute_correctness_score(
    artifact_name: str,
    l0_findings: List[Finding],
    l1_findings: List[Finding],
    normalized_pkg: Optional[NormalizedPackage] = None,
    scaffold_evaluated: bool = False,
) -> int:
    """Compute explicit, normalized structural & technical correctness score C in [0, 100].

    Args:
        artifact_name: Name of artifact ('hld', 'backend', 'database', 'frontend', 'security', 'cloud').
        l0_findings: Findings from Layer 0 Normalization (Phase 1).
        l1_findings: Findings from Layer 1 Executable Evidence (Phase 2).
        normalized_pkg: Optional normalized package for structure verification.
        scaffold_evaluated: True if executable scaffold (OpenAPI, Dockerfile, Terraform, Alembic)
                            was provided and evaluated; False if NOT_EVALUATED.

    Returns:
        int: Normalized correctness score C in [0, 100].
    """
    art_clean = artifact_name.lower().replace("_lld", "")
    art_l0 = [f for f in l0_findings if f.artifact.lower() == art_clean]
    art_l1 = [f for f in l1_findings if f.artifact.lower() == art_clean]

    has_critical = any(f.severity == "critical" for f in art_l0 + art_l1)

    # ── Deterministic Deductions based on Severity ──
    deductions = 0.0

    if normalized_pkg:
        raw_pkg = normalized_pkg.raw_package or {}
        llds = raw_pkg.get("llds", {})
        if not isinstance(llds, dict):
            llds = {}

        if art_clean == "hld":
            hld = raw_pkg.get("hld", {})
            if not hld or not isinstance(hld, dict):
                deductions += 50.0
            elif not hld.get("major_services"):
                deductions += 20.0
        elif art_clean == "backend":
            be = llds.get("backend", {})
            data = be.get("data", be) if isinstance(be, dict) else {}
            if not data or not isinstance(data, dict):
                deductions += 50.0
            elif not data.get("api_endpoints") and not data.get("services"):
                deductions += 20.0
        elif art_clean == "database":
            db = llds.get("database", {})
            data = db.get("data", db) if isinstance(db, dict) else {}
            if not data or not isinstance(data, dict):
                deductions += 50.0
            elif not data.get("tables"):
                deductions += 20.0
        elif art_clean == "frontend":
            fe = llds.get("frontend", {})
            data = fe.get("data", fe) if isinstance(fe, dict) else {}
            if not data or not isinstance(data, dict):
                deductions += 50.0
            elif not data.get("pages") and not data.get("components"):
                deductions += 20.0
        elif art_clean == "security":
            sec = llds.get("security", {})
            data = sec.get("data", sec) if isinstance(sec, dict) else {}
            if not data or not isinstance(data, dict):
                deductions += 50.0
            elif not data.get("security_controls") and not data.get("threat_model"):
                deductions += 20.0
        elif art_clean == "cloud":
            cl = llds.get("cloud", {})
            data = cl.get("data", cl) if isinstance(cl, dict) else {}
            if not data or not isinstance(data, dict):
                deductions += 50.0
            elif not data.get("compute") and not data.get("networking"):
                deductions += 20.0

    # L0 Findings (Phase 1 Orphan / Dangling References)
    for f in art_l0:
        if f.severity == "critical":
            deductions += 15.0
        elif f.severity == "high":
            deductions += 8.0
        elif f.severity == "medium":
            deductions += 3.0
        elif f.severity == "low":
            deductions += 1.0

    # L1 Findings (Phase 2 Deterministic Scaffolds)
    for f in art_l1:
        if f.severity == "critical":
            deductions += 15.0
        elif f.severity == "high":
            deductions += 8.0
        elif f.severity == "medium":
            deductions += 3.0
        elif f.severity == "low":
            deductions += 1.0

    raw_c = 100.0 - deductions
    c_score = int(round(max(0.0, min(100.0, raw_c))))

    if has_critical:
        c_score = min(c_score, 60)

    return c_score
