"""SAE v2 Models Package exporting lean response models."""

from .response_models import (
    BackendLLDResponse,
    CloudLLDResponse,
    DatabaseLLDResponse,
    FrontendLLDResponse,
    HLDResponse,
    RequirementAnalysisResponse,
    SecurityLLDResponse,
    SoftwareArchitecturePackageResponse,
    TechAdvisorResponse,
)

# Aliases for backward compatibility
SoftwareArchitecturePackage = SoftwareArchitecturePackageResponse
BackendLLDResult = BackendLLDResponse
HLDResult = HLDResponse
DatabaseLLDResult = DatabaseLLDResponse
FrontendLLDResult = FrontendLLDResponse
SecurityLLDResult = SecurityLLDResponse
CloudLLDResult = CloudLLDResponse

__all__ = [
    "RequirementAnalysisResponse",
    "TechAdvisorResponse",
    "HLDResponse",
    "BackendLLDResponse",
    "DatabaseLLDResponse",
    "FrontendLLDResponse",
    "SecurityLLDResponse",
    "CloudLLDResponse",
    "SoftwareArchitecturePackageResponse",
    "SoftwareArchitecturePackage",
    "HLDResult",
    "BackendLLDResult",
    "DatabaseLLDResult",
    "FrontendLLDResult",
    "SecurityLLDResult",
    "CloudLLDResult",
]
