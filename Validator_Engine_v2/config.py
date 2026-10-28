"""Configuration settings for Validator Engine v2.

All thresholds and environment variables are centralized here with safe defaults.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Pre-load Validator_Engine_v2/.env and root .env into environment
_MODULE_DIR = Path(__file__).resolve().parent
_LOCAL_ENV = _MODULE_DIR / ".env"
if _LOCAL_ENV.exists():
    load_dotenv(_LOCAL_ENV, override=False)
load_dotenv(".env", override=False)


class ValidatorConfig(BaseSettings):
    """Runtime configuration for Validator Engine v2."""

    model_config = SettingsConfigDict(
        env_file=[str(_LOCAL_ENV), ".env"],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server settings
    VALIDATOR_HOST: str = "0.0.0.0"
    VALIDATOR_PORT: int = 8002

    # Inbound security
    VALIDATOR_API_KEY_INBOUND: str = ""
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ]

    # External AI Engine
    AI_ENGINE_URL: str = "http://localhost:8000"

    # Reviewer LLM settings (OpenAI-compatible)
    # Strict Free-only policy: Free OpenRouter models only; no paid inference; no paid fallback.
    VALIDATOR_API_BASE: str = os.getenv("VALIDATOR_API_BASE", "https://openrouter.ai/api/v1")
    VALIDATOR_API_KEY: str = os.getenv("VALIDATOR_API_KEY") or os.getenv("OPENROUTER_API_KEY", "")
    VALIDATOR_MODEL: str = os.getenv("VALIDATOR_MODEL", "cohere/north-mini-code:free")
    VALIDATOR_FALLBACK_MODELS: str = os.getenv(
        "VALIDATOR_FALLBACK_MODELS",
        "nvidia/nemotron-3.5-lightning:free,openrouter/free,liquid/lfm-2.5-2.6b:free",
    )

    # Testing & Mock mode
    VALIDATOR_MOCK: str = os.getenv("VALIDATOR_MOCK", "1")  # Default to mock=1 in development/testing
    ALLOW_MOCK_ACCEPT: int = int(os.getenv("ALLOW_MOCK_ACCEPT", "0"))
    VALIDATOR_CONCURRENCY: int = int(os.getenv("VALIDATOR_CONCURRENCY", "1"))

    # Decision thresholds
    ACCEPT_THRESHOLD: int = 80
    MAX_ROUNDS: int = 2

    # Real-World Benchmark settings
    RW_WEIGHT: float = float(os.getenv("RW_WEIGHT", "0.35"))
    RW_WEIGHT_LOW_CONFIDENCE: float = float(os.getenv("RW_WEIGHT_LOW_CONFIDENCE", "0.15"))
    RW_MIN: int = int(os.getenv("RW_MIN", "60"))
    REAL_WORLD_TOP_K: int = int(os.getenv("REAL_WORLD_TOP_K", "3"))
    REAL_WORLD_CORPUS_PATH: str = os.getenv("REAL_WORLD_CORPUS_PATH", "ai_engine/data/RAG")
    REAL_WORLD_FOLDERS: str = os.getenv(
        "REAL_WORLD_FOLDERS",
        "category_10_real_world_systems,domain_architectures,category_11_failure_modes",
    )

    # Timeout limits
    LLM_TIMEOUT_SECONDS: float = 60.0
    ITERATION_TIMEOUT_SECONDS: float = 180.0
    RUN_TIMEOUT_SECONDS: float = 600.0

    def get_fallback_models(self) -> List[str]:
        """Return ordered list of configured free fallback models starting with primary."""
        models: List[str] = []
        if self.VALIDATOR_MODEL.strip():
            models.append(self.VALIDATOR_MODEL.strip())
        for m in self.VALIDATOR_FALLBACK_MODELS.split(","):
            clean = m.strip()
            if clean and clean not in models:
                models.append(clean)
        return models


# Global singleton settings
config = ValidatorConfig()
