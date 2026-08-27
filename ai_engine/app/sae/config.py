"""Centralized configuration for the AI Software Architecture Engine (SAE).

Delegates model resolution strictly to config/model_config.py.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from app.config.model_config import MODEL_CONFIG, get_model_for_capability

load_dotenv()


class DesignEngineConfig(BaseModel):
    """Configuration settings for the SAE Design Engine."""

    # OpenRouter LLM Settings
    OPENROUTER_API_KEY: str = Field(
        default_factory=lambda: MODEL_CONFIG.api_key or os.getenv("OPENROUTER_API_KEY", ""),
        description="OpenRouter API key"
    )
    OPENROUTER_BASE_URL: str = Field(
        default_factory=lambda: os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        description="OpenRouter base endpoint"
    )
    OPENROUTER_TIMEOUT_SECONDS: int = Field(
        default_factory=lambda: MODEL_CONFIG.timeout,
        description="HTTP request timeout in seconds"
    )
    OPENROUTER_MAX_RETRIES: int = Field(
        default_factory=lambda: int(os.getenv("OPENROUTER_MAX_RETRIES", "2")),
        description="Maximum retry count for OpenRouter calls"
    )

    # Capability Model Accessors
    @property
    def REQUIREMENT_ANALYSIS_MODEL(self) -> str:
        return get_model_for_capability("requirement_analysis")

    @property
    def TECHNOLOGY_ADVISOR_MODEL(self) -> str:
        return get_model_for_capability("technology_advisor")

    @property
    def ARCHITECTURE_PLANNER_MODEL(self) -> str:
        return get_model_for_capability("architecture_planning")

    @property
    def HLD_GENERATION_MODEL(self) -> str:
        return get_model_for_capability("hld")

    @property
    def HLD_VALIDATION_MODEL(self) -> str:
        return get_model_for_capability("hld")

    @property
    def BACKEND_LLD_MODEL(self) -> str:
        return get_model_for_capability("backend")

    @property
    def DATABASE_LLD_MODEL(self) -> str:
        return get_model_for_capability("database")

    @property
    def FRONTEND_LLD_MODEL(self) -> str:
        return get_model_for_capability("frontend")

    @property
    def SECURITY_LLD_MODEL(self) -> str:
        return get_model_for_capability("security")

    @property
    def CLOUD_LLD_MODEL(self) -> str:
        return get_model_for_capability("cloud")

    @property
    def ARCHITECTURE_VALIDATION_MODEL(self) -> str:
        return get_model_for_capability("architecture_validation")

    @property
    def ARCHITECTURE_MERGE_MODEL(self) -> str:
        return get_model_for_capability("documentation")

    @property
    def EVOLUTION_MODEL(self) -> str:
        return get_model_for_capability("evolution")

    # System Branding
    HTTP_REFERER: str = "https://ai-architecture-platform.local"
    X_TITLE: str = "AI Software Architecture Platform"


config = DesignEngineConfig()
