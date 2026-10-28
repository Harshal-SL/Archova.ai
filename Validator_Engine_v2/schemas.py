"""Pydantic v2 schemas for Validator Engine v2.

Covers Finding, DimensionScore, ArtifactResult, Correction, Iteration, Report,
and NormalizedPackage representation.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


def compute_finding_id(rule_id: str, artifact: str, evidence_path: Optional[str] = None, message: str = "") -> str:
    """Stable finding identity for diffing across iterations.

    hash(rule_id + artifact + normalized evidence_path or message)
    """
    ev_or_msg = (evidence_path or message or "").strip()
    # Normalize whitespace to ensure stability
    normalized_key = re.sub(r"\s+", " ", ev_or_msg.lower())
    payload = f"{rule_id.strip()}:{artifact.strip().lower()}:{normalized_key}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"fnd_{digest}"


class Finding(BaseModel):
    """Architectural defect or standard violation."""

    id: str
    layer: Literal["L0", "L1", "REVIEW", "REAL_WORLD"]
    rule_id: str
    artifact: str  # "hld", "backend", "database", "frontend", "security", "cloud", "package", etc.
    severity: Literal["critical", "high", "medium", "low"]
    message: str
    evidence_path: Optional[str] = None
    source: str = "internal"  # "IEEE1016", "ISO25010", "ISO42010", "ISO25012", "ASVS", "STRIDE", "NIST-SSDF", "ATAM", "<System> reference", etc.
    suggested_fix: Optional[str] = None

    @classmethod
    def create(
        cls,
        layer: Literal["L0", "L1", "REVIEW", "REAL_WORLD"],
        rule_id: str,
        artifact: str,
        severity: Literal["critical", "high", "medium", "low"],
        message: str,
        evidence_path: Optional[str] = None,
        source: str = "internal",
        suggested_fix: Optional[str] = None,
        finding_id: Optional[str] = None,
    ) -> "Finding":
        f_id = finding_id or compute_finding_id(rule_id, artifact, evidence_path, message)
        return cls(
            id=f_id,
            layer=layer,
            rule_id=rule_id,
            artifact=artifact,
            severity=severity,
            message=message,
            evidence_path=evidence_path,
            source=source,
            suggested_fix=suggested_fix,
        )


class DimensionScore(BaseModel):
    """Score for a specific rubric dimension (0-5 scale)."""

    id: str
    label: str
    weight: float
    score: int = Field(..., ge=0, le=5)
    evidence_path: Optional[str] = None
    missing: List[str] = Field(default_factory=list)
    rationale: str = Field(..., max_length=200)

    @field_validator("rationale", mode="before")
    @classmethod
    def trim_rationale(cls, v: Any) -> str:
        s = str(v or "").strip()
        if len(s) > 200:
            return s[:197] + "..."
        return s


class ReferenceSystemUsed(BaseModel):
    """Reference architecture selected from the RAG corpus."""

    id: str
    system_name: str
    match_reasons: List[str] = Field(default_factory=list)
    scale_note: Optional[str] = None
    sources: List[str] = Field(default_factory=list)


class PatternAssessment(BaseModel):
    """Assessment of an individual real-world transferable pattern."""

    pattern_id: str
    system_name: str
    pattern_name: str
    category: str
    priority: int
    status: Literal["ALIGNED", "PARTIAL", "MISSING", "JUSTIFIED_DIVERGENCE", "NOT_APPLICABLE"]
    evidence_path: Optional[str] = None
    justification: str = ""
    requirement_refs: List[str] = Field(default_factory=list)


class RealWorldResult(BaseModel):
    """Real-World Benchmark score and pattern assessments for an artifact."""

    artifact: str
    score: Optional[int] = None
    confidence: Literal["normal", "low", "unavailable"] = "normal"
    counts: Dict[str, int] = Field(default_factory=dict)
    # counts keys: aligned, partial, missing, justified_divergence, not_applicable, downgraded_unverified
    assessments: List[PatternAssessment] = Field(default_factory=list)
    references_used: List[ReferenceSystemUsed] = Field(default_factory=list)


class ArtifactResult(BaseModel):
    """Validation verdict and scores for a single artifact."""

    artifact: str  # "hld", "backend", "database", "frontend", "security", "cloud"
    score: int = Field(..., ge=0, le=100)  # Final composite score S
    final_score: int = 0
    c_score: int = 100  # Phase 1 & 2: Structural and Technical Correctness (0-100)
    r_score: int = 100  # Phase 3: Architecture Quality Review (0-100)
    w_score: Optional[int] = None  # Phase 4: Real-World Architecture Suitability (0-100)
    penalty_d: int = 0  # Additional defect penalties D
    rubric_score: int = 0  # Backward-compatible alias for r_score
    real_world: Optional[RealWorldResult] = None
    verdict: Literal["ACCEPTED", "ACCEPTED_WITH_WARNINGS", "REJECTED", "PROVISIONAL"]
    dimensions: List[DimensionScore] = Field(default_factory=list)
    findings: List[Finding] = Field(default_factory=list)
    best_dimension: Optional[str] = None
    weakest_dimension: Optional[str] = None
    reviewer_status: Literal["ok", "unavailable", "partial"] = "ok"
    dropped_unverified: int = 0
    truncated: bool = False
    model_used: Optional[str] = None
    model_config = {"protected_namespaces": ()}

    def model_post_init(self, __context: Any) -> None:
        if self.final_score == 0 and self.score > 0:
            self.final_score = self.score
        elif self.final_score > 0 and self.score == 0:
            self.score = self.final_score
        if self.rubric_score == 0 and self.r_score > 0:
            self.rubric_score = self.r_score
        elif self.r_score == 0 and self.rubric_score > 0:
            self.r_score = self.rubric_score
        if self.w_score is None and self.real_world and self.real_world.score is not None:
            self.w_score = self.real_world.score


class Correction(BaseModel):
    """Audit record of a correction attempt between iterations."""

    artifact: str
    triggered_by: List[str] = Field(default_factory=list)  # finding ids
    action_summary: str
    score_before: int
    score_after: int
    resolved: List[str] = Field(default_factory=list)  # finding ids
    unresolved: List[str] = Field(default_factory=list)  # finding ids
    new_findings: List[str] = Field(default_factory=list)  # finding ids
    regenerated_with_feedback: bool = True
    patterns_resolved: List[str] = Field(default_factory=list)
    patterns_still_missing: List[str] = Field(default_factory=list)


class Iteration(BaseModel):
    """Single full validation cycle across all artifacts."""

    n: int
    results: Dict[str, ArtifactResult] = Field(default_factory=dict)
    corrections: List[Correction] = Field(default_factory=list)
    started_at: str
    finished_at: str


class Report(BaseModel):
    """Complete validation report spanning multiple iterations."""

    model_config = ConfigDict(protected_namespaces=())

    generation_id: str
    iterations: List[Iteration] = Field(default_factory=list)
    final_status: Literal["ACCEPTED", "ACCEPTED_WITH_WARNINGS", "REJECTED", "PROVISIONAL", "UNRESOLVED"]
    final_scores: Dict[str, Any] = Field(default_factory=dict)
    overall_c: int = 100
    overall_r: int = 100
    overall_w: Optional[int] = None
    overall_d: int = 0
    model_used: str
    models_used_per_artifact: Dict[str, str] = Field(default_factory=dict)
    reviewer_mode: Literal["live", "mock"] = "live"
    corpus_status: Literal["ok", "empty", "unavailable"] = "ok"
    references_used: List[ReferenceSystemUsed] = Field(default_factory=list)
    config_snapshot: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    final_package: Optional[Dict[str, Any]] = None


# ── Normalized Package Models (Layer 0) ─────────────────────────────────────────

class NormalizedRequirement(BaseModel):
    id: str
    text: str
    type: Literal["FR", "NFR"]
    target: Optional[str] = None


class NormalizedComponent(BaseModel):
    name: str
    responsibility: str
    artifact: str = "hld"


class NormalizedEndpoint(BaseModel):
    method: str
    path: str
    service: Optional[str] = None
    auth_required: bool = False


class NormalizedTable(BaseModel):
    name: str
    columns: List[str] = Field(default_factory=list)
    pks: List[str] = Field(default_factory=list)
    fks: List[Dict[str, str]] = Field(default_factory=list)


class NormalizedRoute(BaseModel):
    path: str
    component: Optional[str] = None
    linked_endpoint: Optional[str] = None


class NormalizedSecurityControl(BaseModel):
    control_id: str
    category: str
    description: str


class NormalizedPackage(BaseModel):
    generation_id: str
    system_name: str
    domain: str
    requirements: List[NormalizedRequirement] = Field(default_factory=list)
    components: List[NormalizedComponent] = Field(default_factory=list)
    endpoints: List[NormalizedEndpoint] = Field(default_factory=list)
    tables: List[NormalizedTable] = Field(default_factory=list)
    routes: List[NormalizedRoute] = Field(default_factory=list)
    security_controls: List[NormalizedSecurityControl] = Field(default_factory=list)
    scaffold_files: Dict[str, str] = Field(default_factory=dict)
    raw_package: Dict[str, Any] = Field(default_factory=dict)
    l0_findings: List[Finding] = Field(default_factory=list)
