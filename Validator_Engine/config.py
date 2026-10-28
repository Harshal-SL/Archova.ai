"""Configuration settings for the Validator Engine."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

_PACKAGE_ROOT = Path(__file__).resolve().parent
_WORKSPACE_ROOT = _PACKAGE_ROOT.parent

# Load .env if present in workspace root or ai_engine root
for env_candidate in [
    _WORKSPACE_ROOT / ".env",
    _WORKSPACE_ROOT / "ai_engine" / ".env",
    _PACKAGE_ROOT / ".env",
]:
    if env_candidate.exists():
        load_dotenv(dotenv_path=env_candidate, override=False)

# Qdrant & Vector DB
QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY")
QDRANT_LOCAL_PATH: str = os.getenv(
    "QDRANT_LOCAL_PATH",
    str(_WORKSPACE_ROOT / "ai_engine" / ".qdrant_data"),
)
QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION_NAME", "architecture_rag")

# Redis Cache
REDIS_URL: Optional[str] = os.getenv("REDIS_URL") or os.getenv("UPSTASH_REDIS_URL")

# RAG Knowledge Corpus
RAG_DATA_ROOT: Path = Path(
    os.getenv("RAG_DATA_ROOT", str(_WORKSPACE_ROOT / "ai_engine" / "data" / "RAG"))
)

# Similarity and Thresholds
EVIDENCE_SIMILARITY_THRESHOLD: float = float(
    os.getenv("EVIDENCE_SIMILARITY_THRESHOLD", "0.45")
)
EVIDENCE_TOP_K: int = int(os.getenv("EVIDENCE_TOP_K", "3"))

# LLM Gateway for Semantic Validation & Red-Team Audit
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openrouter")
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
VALIDATION_MODEL: str = os.getenv(
    "MODEL_ARCHITECTURE_VALIDATION",
    os.getenv("LLM_MODEL", "google/gemini-2.5-flash:free"),
)
