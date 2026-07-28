"""
Model Registry

Maps capability names to OpenRouter model IDs.

Agents request a CAPABILITY (e.g. "reasoning"), never a concrete model.
The registry resolves the capability to the appropriate model based on
the current configuration (paid models allowed or not).

Rules:
  - ALLOW_PAID_MODELS=false  → only free-tier models are used
  - ALLOW_PAID_MODELS=true   → preferred models are used (may incur cost)
  - If a paid model is requested when ALLOW_PAID_MODELS=false → rejected,
    fallback to openrouter/auto (free)
  - Unknown capability → fallback to the default free model
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Dict, Optional

logger = logging.getLogger(__name__)


# ── Capability enum (string-based for easy env-var configuration) ─────────────


class Capability:
    """
    Canonical capability names used by agents.

    Agents set CAPABILITY = Capability.REASONING (etc.) on their class.
    The gateway resolves the capability to a concrete model at call time.
    """
    INPUT_UNDERSTANDING = "input_understanding"
    """Input understanding and text normalization (Input Understanding Agent)."""

    REASONING = "reasoning"
    """General reasoning and structured extraction (Requirement Engineer)."""

    BUSINESS_ANALYSIS = "business_analysis"
    """Business context analysis (Business Analyst)."""

    DOMAIN_REASONING = "domain_reasoning"
    """Technical domain and architecture reasoning (Domain Expert)."""

    GENERAL = "general"
    """Fallback for any capability not explicitly mapped."""

    REVIEW = "review"
    """Requirement review and quality assessment (Review Agent)."""

    INTERVIEW = "interview"
    """Adaptive stakeholder interview question generation (Interview Moderator)."""

    DESIGN = "design"
    """System architecture, HLD and LLD generation (Design Agent)."""


# ── Model entry ───────────────────────────────────────────────────────────────


@dataclass
class ModelEntry:
    """A model entry in the registry."""
    model_id: str
    is_paid: bool = False
    display_name: str = ""
    context_window: int = 8192


# ── Dynamic Model Resolution from Environment ──────────────────────────────────

def _get_env_model(primary_var: str, fallback_var: str = "LLM_MODEL") -> str:
    val = os.getenv(primary_var, "").strip()
    if val:
        return val
    val = os.getenv("OPENROUTER_MODEL_" + primary_var.replace("_MODEL", ""), "").strip()
    if val:
        return val
    return os.getenv(fallback_var, "").strip()


def _build_model_entries() -> Dict[str, ModelEntry]:
    fallback_id = _get_env_model("FALLBACK_MODEL", "LLM_MODEL") or "nvidia/nemotron-3-nano-30b-a3b:free"
    fallback_entry = ModelEntry(
        model_id=fallback_id,
        is_paid=False,
        display_name=fallback_id,
        context_window=128000,
    )

    cap_vars = {
        Capability.INPUT_UNDERSTANDING: "INPUT_UNDERSTANDING_MODEL",
        Capability.REASONING: "REQUIREMENT_ENGINEER_MODEL",
        Capability.BUSINESS_ANALYSIS: "BUSINESS_ANALYST_MODEL",
        Capability.DOMAIN_REASONING: "DOMAIN_EXPERT_MODEL",
        Capability.REVIEW: "REQUIREMENT_REVIEW_MODEL",
        Capability.INTERVIEW: "INTERVIEW_MODERATOR_MODEL",
        Capability.DESIGN: "DESIGN_MODEL",
    }

    entries: Dict[str, ModelEntry] = {}
    for cap, var_name in cap_vars.items():
        m_id = _get_env_model(var_name, "LLM_MODEL")
        entries[cap] = ModelEntry(
            model_id=m_id,
            is_paid=False,
            display_name=m_id,
            context_window=128000,
        )

    entries[Capability.GENERAL] = fallback_entry
    return entries


# ── Registry ──────────────────────────────────────────────────────────────────


class ModelRegistry:
    """
    Resolves a capability name to a concrete OpenRouter model ID strictly from environment variables.
    No hardcoded model names.
    """

    class PolicyError(RuntimeError):
        """Raised when a paid model is requested but not permitted."""

    def __init__(self, allow_paid: bool = False) -> None:
        self._allow_paid = allow_paid
        self.reload()

    def reload(self) -> None:
        """Reload capability mappings dynamically from os.environ."""
        self._entries = _build_model_entries()
        raw = os.getenv("ALLOW_PAID_MODELS", "false").strip().lower()
        self._allow_paid = raw in ("true", "1", "yes")

    def resolve(self, capability: str) -> ModelEntry:
        """
        Resolve a capability to a ModelEntry.
        Exclusively returns model resolved from environment variables.
        """
        capability = capability.lower().strip()
        fallback_id = _get_env_model("FALLBACK_MODEL", "LLM_MODEL")
        entry = self._entries.get(
            capability,
            ModelEntry(model_id=fallback_id, is_paid=False, display_name=fallback_id, context_window=128000),
        )
        if not entry.model_id:
            logger.error("ModelRegistry: no model resolved for capability %r (LLM_MODEL is unset)", capability)
            raise RuntimeError(f"No model configured for capability '{capability}'. Set LLM_MODEL or {capability.upper()}_MODEL in .env.")
        return entry

    def resolve_model_id(self, capability: str) -> str:
        """Convenience method — returns just the model_id string."""
        return self.resolve(capability).model_id

    def reject_if_paid(self, capability: str) -> None:
        """
        Raise PolicyError if the resolved model for this capability is paid
        and ALLOW_PAID_MODELS is false.
        """
        if self._allow_paid:
            return
        entry = self.resolve(capability)
        if entry.is_paid:
            raise self.PolicyError(
                f"Paid model requested for capability '{capability}' "
                f"({entry.model_id}) but ALLOW_PAID_MODELS=false. "
                "Set ALLOW_PAID_MODELS=true in .env to enable paid models."
            )

    @property
    def allow_paid(self) -> bool:
        return self._allow_paid

    def list_capabilities(self) -> Dict[str, str]:
        """Return a dict of capability → resolved model_id for logging."""
        return {cap: self.resolve_model_id(cap) for cap in self._entries}


# ── Module-level singleton ────────────────────────────────────────────────────


def _build_registry() -> ModelRegistry:
    raw = os.getenv("ALLOW_PAID_MODELS", "false").strip().lower()
    allow_paid = raw in ("true", "1", "yes")
    return ModelRegistry(allow_paid=allow_paid)


model_registry = _build_registry()


def reload_registry() -> ModelRegistry:
    """Reload the global model registry instance from environment variables."""
    global model_registry
    model_registry.reload()
    return model_registry

