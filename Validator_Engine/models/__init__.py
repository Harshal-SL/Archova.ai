"""Pydantic Models package for Validator Engine."""

from .finding_models import FindingCategory, FindingSeverity, ValidationFinding
from .input_models import ArchitecturePackageInput
from .output_models import (
    ExplainabilityBlock,
    ValidatedArchitectureResponse,
    ValidationBlock,
    ValidationSummary,
    ValidatorMetadata,
)
from .report_models import (
    ArchitectureCorrectionFeedback,
    CorrectionAttemptRecord,
    CorrectionFeedbackItem,
    CrossArtifactConsistencyReport,
    DecisionProvenanceItem,
    NFRValidationItem,
    NFRValidationReport,
    RealWorldArchetypeMatch,
    RealWorldEvidenceReport,
    RedTeamReviewReport,
    RemediationAction,
    RemediationPlan,
    RequirementAlignmentReport,
    RequirementTraceabilityItem,
    StructuralValidationReport,
    UnifiedScorecard,
)

__all__ = [
    "ArchitecturePackageInput",
    "FindingSeverity",
    "FindingCategory",
    "ValidationFinding",
    "StructuralValidationReport",
    "RequirementTraceabilityItem",
    "RequirementAlignmentReport",
    "CrossArtifactConsistencyReport",
    "NFRValidationItem",
    "NFRValidationReport",
    "RealWorldArchetypeMatch",
    "RealWorldEvidenceReport",
    "RedTeamReviewReport",
    "DecisionProvenanceItem",
    "RemediationAction",
    "RemediationPlan",
    "UnifiedScorecard",
    "ValidationSummary",
    "ValidationBlock",
    "ExplainabilityBlock",
    "ValidatorMetadata",
    "ValidatedArchitectureResponse",
    "CorrectionFeedbackItem",
    "ArchitectureCorrectionFeedback",
    "CorrectionAttemptRecord",
]
