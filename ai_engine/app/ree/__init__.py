"""
Requirements Engineering Engine (REE)

Top-level package exposing the REE Orchestrator and data models.
"""

from .orchestrator import REEOrchestrator
from .models import (
    SharedRequirementContext,
    ArchitectureReadyStructuredRequirementSpec,
    StructuredRequirement,
    ARSRSProjectProfile,
    ARSRSBusinessContext,
    ARSRSDomainContext,
    ARSRSMetadata,
    REERequest,
    REEResponse,
    REEStatus,
    InterviewResult,
    ReviewResult,
    ReviewVerdict,
    ConfidenceScore,
    AmbiguityIssue,
    ContradictionIssue,
    DuplicateIssue,
)

__all__ = [
    "REEOrchestrator",
    "SharedRequirementContext",
    "ArchitectureReadyStructuredRequirementSpec",
    "StructuredRequirement",
    "ARSRSProjectProfile",
    "ARSRSBusinessContext",
    "ARSRSDomainContext",
    "ARSRSMetadata",
    "REERequest",
    "REEResponse",
    "REEStatus",
    "InterviewResult",
    "ReviewResult",
    "ReviewVerdict",
    "ConfidenceScore",
    "AmbiguityIssue",
    "ContradictionIssue",
    "DuplicateIssue",
]
