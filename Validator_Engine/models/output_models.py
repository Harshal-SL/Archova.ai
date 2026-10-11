"""Validated Output JSON Contract Envelope."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from .finding_models import FindingSeverity, ValidationFinding
from .report_models import (
    CorrectionAttemptRecord,
    CrossArtifactConsistencyReport,
    DecisionProvenanceItem,
    NFRValidationReport,
    RealWorldEvidenceReport,
    RedTeamReviewReport,
    RemediationPlan,
    RequirementAlignmentReport,
    StructuralValidationReport,
    UnifiedScorecard,
)


class ValidationSummary(BaseModel):
    """Executive summary of the validation outcome."""
    model_config = ConfigDict(extra="allow")

    overall_score: float
    verdict: str  # APPROVED | APPROVED_WITH_CONDITIONS | NEEDS_REMEDIATION | REJECTED
    total_findings_count: int = 0
    critical_findings_count: int = 0
    high_findings_count: int = 0
    medium_findings_count: int = 0
    low_findings_count: int = 0
    is_valid: bool = True


class ValidationBlock(BaseModel):
    """Enriched multi-dimensional validation payload."""
    model_config = ConfigDict(extra="allow")

    status: str = "PASSED"  # HEALTHY | DEGRADED | NEEDS_REMEDIATION | FAILED
    summary: ValidationSummary
    scorecard: UnifiedScorecard
    structural_validation: StructuralValidationReport
    requirement_alignment: RequirementAlignmentReport
    cross_artifact_consistency: CrossArtifactConsistencyReport
    nfr_validation: NFRValidationReport
    red_team_review: RedTeamReviewReport
    findings: List[ValidationFinding] = Field(default_factory=list)


class ExplainabilityBlock(BaseModel):
    """Decision provenance and architecture rationale."""
    model_config = ConfigDict(extra="allow")

    decisions_provenance: List[DecisionProvenanceItem] = Field(default_factory=list)
    architecture_overview_rationale: str = ""


class ValidatorMetadata(BaseModel):
    """Validation execution and provenance metadata."""
    model_config = ConfigDict(extra="allow")

    validator_version: str = "1.0.0"
    package_id: str = ""
    system_name: str = ""
    domain: str = ""
    validated_at: str
    input_fingerprint: str = ""
    execution_duration_ms: float = 0.0


class ValidatedArchitectureResponse(BaseModel):
    """Canonical Validated Architecture JSON Output Contract."""
    model_config = ConfigDict(extra="allow")

    architecture: Dict[str, Any] = Field(
        ...,
        description="Preserved, untouched original AI Engine architecture JSON",
    )
    validation: ValidationBlock = Field(
        ...,
        description="Complete multi-dimensional validation results, scorecard, and findings",
    )
    evidence: RealWorldEvidenceReport = Field(
        ...,
        description="Real-world reference architecture comparisons and contextual evidence",
    )
    explainability: ExplainabilityBlock = Field(
        ...,
        description="Decision provenance and traceability matrix",
    )
    remediation: RemediationPlan = Field(
        ...,
        description="Targeted corrective remediation recommendations",
    )
    metadata: ValidatorMetadata = Field(
        ...,
        description="Validator metadata and execution details",
    )
    # Correction Feedback & Revalidation Workflow Attributes
    is_fully_validated: bool = Field(
        default=False,
        description="True if verdict is approved/healthy; false if unresolved defects remain",
    )
    attempt: int = Field(
        default=1,
        description="Current validation attempt number (1-based)",
    )
    max_retries: int = Field(
        default=2,
        description="Configured retry limit for AI Engine correction cycles",
    )
    correction_history: List[CorrectionAttemptRecord] = Field(
        default_factory=list,
        description="Audit trail of correction attempts, resolved issues, and regenerated artifacts",
    )

    # ── Convenient Direct Access Properties ──
    @property
    def package_id(self) -> str:
        return self.metadata.package_id

    @property
    def system_name(self) -> str:
        return self.metadata.system_name

    @property
    def domain(self) -> str:
        return self.metadata.domain

    @property
    def status(self) -> str:
        return self.validation.status

    @property
    def scorecard(self) -> UnifiedScorecard:
        return self.validation.scorecard

    @property
    def structural_validation(self) -> StructuralValidationReport:
        return self.validation.structural_validation

    @property
    def requirement_alignment(self) -> RequirementAlignmentReport:
        return self.validation.requirement_alignment

    @property
    def cross_artifact_consistency(self) -> CrossArtifactConsistencyReport:
        return self.validation.cross_artifact_consistency

    @property
    def nfr_validation(self) -> NFRValidationReport:
        return self.validation.nfr_validation

    @property
    def real_world_evidence(self) -> RealWorldEvidenceReport:
        return self.evidence

    @property
    def red_team_review(self) -> RedTeamReviewReport:
        return self.validation.red_team_review

    @property
    def decision_provenance(self) -> List[DecisionProvenanceItem]:
        return self.explainability.decisions_provenance

    @property
    def remediation_plan(self) -> RemediationPlan:
        return self.remediation

    @property
    def original_architecture(self) -> Dict[str, Any]:
        return self.architecture

    def to_dict(self) -> Dict[str, Any]:
        """Convert to standard JSON-serializable dictionary."""
        return self.model_dump(mode="json")
