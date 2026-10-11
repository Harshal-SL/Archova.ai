"""Validator Engine - Standalone AI Architecture Verification & Quality Assessment Engine."""

from Validator_Engine.engine import ValidatorEngine
from Validator_Engine.models.finding_models import (
    FindingCategory,
    FindingSeverity,
    ValidationFinding,
)
from Validator_Engine.models.input_models import ArchitecturePackageInput
from Validator_Engine.models.output_models import ValidatedArchitectureResponse

__version__ = "1.0.0"

__all__ = [
    "ValidatorEngine",
    "ArchitecturePackageInput",
    "ValidatedArchitectureResponse",
    "ValidationFinding",
    "FindingSeverity",
    "FindingCategory",
]
