"""Centralized Model Configuration for REE and SAE pipelines.

Single source of truth for all LLM provider and model selections.
Reads environment variables from .env and applies automatic fallback to LLM_MODEL if specific capability model variables are empty.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv

# Load .env file from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
env_path = PROJECT_ROOT / ".env"
if not env_path.exists():
    env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)



@dataclass
class ModelConfig:
    """Centralized Model Configuration data structure."""

    provider: str
    api_key: str
    api_keys: List[str]
    default_model: str
    temperature: float
    max_tokens: int
    timeout: int
    model_map: Dict[str, str]


# Mapping between capability string names and corresponding .env environment variable keys
CAPABILITY_ENV_MAPPING: Dict[str, str] = {
    # REE Capabilities
    "input_understanding": "MODEL_INPUT_UNDERSTANDING",
    "requirement_engineer": "MODEL_REQUIREMENT_ENGINEER",
    "reasoning": "MODEL_REQUIREMENT_ENGINEER",  # Alias for REE Requirement Engineer
    "business_analysis": "MODEL_BUSINESS_ANALYST",
    "domain_reasoning": "MODEL_DOMAIN_EXPERT",
    "review": "MODEL_REQUIREMENT_REVIEW",
    "interview": "MODEL_INTERVIEW",
    # SAE Capabilities
    "requirement_analysis": "MODEL_REQUIREMENT_ANALYSIS",
    "technology_advisor": "MODEL_TECHNOLOGY_ADVISOR",
    "architecture_planning": "MODEL_ARCHITECTURE_PLANNING",
    "hld": "MODEL_HLD",
    "backend": "MODEL_BACKEND",
    "backend_lld": "MODEL_BACKEND",
    "database": "MODEL_DATABASE",
    "database_lld": "MODEL_DATABASE",
    "frontend": "MODEL_FRONTEND",
    "frontend_lld": "MODEL_FRONTEND",
    "security": "MODEL_SECURITY",
    "security_lld": "MODEL_SECURITY",
    "cloud": "MODEL_CLOUD",
    "cloud_lld": "MODEL_CLOUD",
    "architecture_validation": "MODEL_ARCHITECTURE_VALIDATION",
    "documentation": "MODEL_DOCUMENTATION",
    "evolution": "MODEL_EVOLUTION",
    "architecture_evolution": "MODEL_EVOLUTION",
}


def _resolve_model_map(default_model: str) -> Dict[str, str]:
    """Build capability to model resolution dictionary with fallback to default_model."""
    model_map: Dict[str, str] = {}
    for cap_name, env_key in CAPABILITY_ENV_MAPPING.items():
        val = os.getenv(env_key, "").strip()
        if val:
            model_map[cap_name] = val
        else:
            model_map[cap_name] = default_model
    return model_map


def load_central_model_config() -> ModelConfig:
    """Load central model configuration from .env with fallbacks."""
    provider = os.getenv("LLM_PROVIDER", "openrouter").strip()
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()

    # Load multiple API keys for parallel agent distribution
    api_keys: List[str] = []
    for i in range(1, 10):
        k = os.getenv(f"OPENROUTER_API_KEY_{i}", "").strip()
        if k:
            api_keys.append(k)
    if not api_keys and api_key:
        api_keys.append(api_key)

    default_model = os.getenv("LLM_MODEL", "nvidia/nemotron-3.5-lightning:free").strip()

    try:
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    except ValueError:
        temperature = 0.2

    try:
        max_tokens = int(os.getenv("LLM_MAX_TOKENS", "8192"))
    except ValueError:
        max_tokens = 8192

    try:
        timeout = int(os.getenv("LLM_TIMEOUT_SECONDS", os.getenv("LLM_TIMEOUT", "60")))
    except ValueError:
        timeout = 60

    model_map = _resolve_model_map(default_model)

    return ModelConfig(
        provider=provider,
        api_key=api_key,
        api_keys=api_keys,
        default_model=default_model,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        model_map=model_map,
    )


# Master Configuration Singleton & MODEL_MAP export
MODEL_CONFIG: ModelConfig = load_central_model_config()
MODEL_MAP: Dict[str, str] = MODEL_CONFIG.model_map


def get_model_for_capability(capability: str) -> str:
    """Resolve model string for a given capability, falling back to LLM_MODEL."""
    cap_key = capability.lower().strip()
    if cap_key in MODEL_MAP:
        return MODEL_MAP[cap_key]
    return MODEL_CONFIG.default_model


def validate_model_config(print_diagnostics: bool = True) -> bool:
    """Validate startup configuration and print diagnostic box."""
    cfg = load_central_model_config()
    is_valid = bool(cfg.api_key and cfg.default_model)

    if print_diagnostics:
        print("\n" + "=" * 60)
        print(" CENTRALIZED LLM MODEL CONFIGURATION DIAGNOSTICS")
        print("=" * 60)
        print(f" LLM Provider   : {cfg.provider.upper()}")
        print(f" Default Model  : {cfg.default_model}")
        print(f" API Key Status : {'[PRESENT]' if cfg.api_key else '[MISSING] (Fallback Mode Active)'}")
        print(f" Temperature    : {cfg.temperature}")
        print(f" Max Tokens     : {cfg.max_tokens}")
        print(f" Timeout        : {cfg.timeout}s")
        print("-" * 60)


        overrides = [
            f"{cap} -> {model}"
            for cap, model in cfg.model_map.items()
            if model != cfg.default_model
        ]
        if overrides:
            print(" Active Capability Model Overrides:")
            for ov in set(overrides):
                print(f"  • {ov}")
        else:
            print(" Active Capability Model Overrides: None (All capabilities using LLM_MODEL)")
        print("=" * 60 + "\n")

    return is_valid
