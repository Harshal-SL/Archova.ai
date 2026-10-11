"""Standardized Finding and Defect Data Models."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FindingSeverity(str, Enum):
    """Severity levels for architectural validation findings."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class FindingCategory(str, Enum):
    """Categorization for architectural findings."""
    STRUCTURAL = "STRUCTURAL"
    REQUIREMENT_ALIGNMENT = "REQUIREMENT_ALIGNMENT"
    CROSS_ARTIFACT_CONSISTENCY = "CROSS_ARTIFACT_CONSISTENCY"
    NFR_FEASIBILITY = "NFR_FEASIBILITY"
    NFR_VIOLATION = "NFR_FEASIBILITY"
    SECURITY_COMPLIANCE = "SECURITY_COMPLIANCE"
    SECURITY_DEFECT = "SECURITY_COMPLIANCE"
    SINGLE_POINT_OF_FAILURE = "SINGLE_POINT_OF_FAILURE"
    SPOF = "SINGLE_POINT_OF_FAILURE"
    UNRESOLVED_RISK = "UNRESOLVED_RISK"
    RESILIENCE_GAP = "UNRESOLVED_RISK"
    SCALABILITY_BOTTLENECK = "UNRESOLVED_RISK"
    UNTESTED_ASSUMPTION = "UNRESOLVED_RISK"
    REAL_WORLD_CAUTION = "REAL_WORLD_CAUTION"
    ANTI_PATTERN = "REAL_WORLD_CAUTION"
    BEST_PRACTICE_VIOLATION = "REAL_WORLD_CAUTION"


class ValidationFinding(BaseModel):
    """Standardized finding representing an architectural defect, gap, or risk."""

    id: str = Field(..., description="Stable finding ID (e.g. FIND-001, SPOF-001)")
    category: FindingCategory = Field(default=FindingCategory.STRUCTURAL)
    severity: FindingSeverity = Field(default=FindingSeverity.MEDIUM)
    requirement_id: Optional[str] = Field(
        default=None,
        description="Associated requirement identifier (e.g. FR-001, NFR-002)",
    )
    affected_component: str = Field(
        ...,
        description="Name of the affected service, entity, API endpoint, or LLD section",
    )
    explanation: str = Field(
        ...,
        description="Detailed explanation of what is wrong and why it is an architectural issue",
    )
    evidence: str = Field(
        default="",
        description="Empirical evidence, RAG pattern citation, or code location",
    )
    recommendation: str = Field(
        default="",
        description="Actionable mitigation or architectural refactoring recommendation",
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category.value,
            "severity": self.severity.value,
            "requirement_id": self.requirement_id,
            "affected_component": self.affected_component,
            "explanation": self.explanation,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
        }
