"""Shared Design Context (SDC) models and registry."""

from .design_generation_context import DesignGenerationContext
from .base_section import BaseSection

try:
    from .models import (
        BackendLLDSection,
        ChangeRecord,
        CloudDesignSection,
        DatabaseLLDSection,
        FrontendLLDSection,
        HLDSection,
        JustificationReportsSection,
        ProjectMetadataSection,
        RequirementAnalysisSection,
        SecurityDesignSection,
        TechnologyRecommendationsSection,
        ValidationResultsSection,
    )
except Exception:
    pass

__all__ = [
    "DesignGenerationContext",
    "BaseSection",
]
