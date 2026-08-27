"""Model Registry for capability-based LLM model resolution.

Maps capability names to model IDs strictly using centralized configuration in config/model_config.py.
Zero hardcoded model strings.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Dict, Optional

from app.config.model_config import MODEL_CONFIG, MODEL_MAP, get_model_for_capability

logger = logging.getLogger(__name__)


class Capability:
    """Canonical capability names used by agents across REE and SAE."""
    INPUT_UNDERSTANDING = "input_understanding"
    REASONING = "requirement_engineer"
    BUSINESS_ANALYSIS = "business_analysis"
    DOMAIN_REASONING = "domain_reasoning"
    GENERAL = "general"
    REVIEW = "review"
    INTERVIEW = "interview"
    DESIGN = "design"
    REQUIREMENT_ANALYSIS = "requirement_analysis"
    TECHNOLOGY_ADVISOR = "technology_advisor"
    ARCHITECTURE_PLANNING = "architecture_planning"
    HLD = "hld"
    BACKEND = "backend"
    DATABASE = "database"
    FRONTEND = "frontend"
    SECURITY = "security"
    CLOUD = "cloud"
    ARCHITECTURE_VALIDATION = "architecture_validation"
    DOCUMENTATION = "documentation"
    EVOLUTION = "evolution"


@dataclass
class ModelEntry:
    """Standardized model entry in the registry."""
    model_id: str
    is_paid: bool = False
    display_name: str = ""
    context_window: int = 128000


class ModelRegistry:
    """Resolves capability names to model IDs strictly via config/model_config.py."""

    class PolicyError(RuntimeError):
        """Raised when paid models are prohibited."""

    def __init__(self, allow_paid: bool = False) -> None:
        self._allow_paid = allow_paid
        self.reload()

    def reload(self) -> None:
        """Reload capability mappings dynamically from central model config."""
        raw = os.getenv("ALLOW_PAID_MODELS", "false").strip().lower()
        self._allow_paid = raw in ("true", "1", "yes")

    def resolve(self, capability: str) -> ModelEntry:
        """Resolve a capability to a ModelEntry via config/model_config.py."""
        model_id = get_model_for_capability(capability)
        return ModelEntry(
            model_id=model_id,
            is_paid=False,
            display_name=model_id,
            context_window=MODEL_CONFIG.max_tokens,
        )

    def resolve_model_id(self, capability: str) -> str:
        """Convenience method returning model_id string."""
        return self.resolve(capability).model_id

    def reject_if_paid(self, capability: str) -> None:
        """Enforce paid model policy check."""
        if self._allow_paid:
            return
        entry = self.resolve(capability)
        if entry.is_paid:
            raise self.PolicyError(
                f"Paid model requested for capability '{capability}' ({entry.model_id}) "
                "but ALLOW_PAID_MODELS=false."
            )

    @property
    def allow_paid(self) -> bool:
        return self._allow_paid

    def list_capabilities(self) -> Dict[str, str]:
        """Return dict of capability -> resolved model_id."""
        return {cap: get_model_for_capability(cap) for cap in MODEL_MAP}


# Singleton instance
model_registry = ModelRegistry()


def reload_registry() -> ModelRegistry:
    """Reload global model registry instance."""
    global model_registry
    model_registry.reload()
    return model_registry
