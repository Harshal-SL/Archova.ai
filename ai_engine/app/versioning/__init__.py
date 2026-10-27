"""Version Management & Delta Evolution Engine for Archova.ai Architecture Packages."""

from app.versioning.contracts import (
    ArchitecturePatch,
    ArchitectureDiff,
    PatchVerificationResult,
    VerificationViolation,
    ColumnAddition,
    ExistingServiceEndpointAddition,
)
from app.versioning.patcher import ArchitecturePatcher
from app.versioning.verifier import ArchitectureVerifier
from app.versioning.differ import ArchitectureDiffer
from app.versioning.prompt_builder import DeltaPromptBuilder
from app.versioning.version_manager import VersionManager

__all__ = [
    "ArchitecturePatch",
    "ArchitectureDiff",
    "PatchVerificationResult",
    "VerificationViolation",
    "ColumnAddition",
    "ExistingServiceEndpointAddition",
    "ArchitecturePatcher",
    "ArchitectureVerifier",
    "ArchitectureDiffer",
    "DeltaPromptBuilder",
    "VersionManager",
]
