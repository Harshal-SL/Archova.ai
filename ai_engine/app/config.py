from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _default_rag_data_root() -> str:
    rag_root = _PROJECT_ROOT / "data" / "RAG"
    if rag_root.exists():
        return str(rag_root)
    return str(_PROJECT_ROOT / "data")


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str
    ollama_generate_url: str
    llm_model: str
    llm_max_retries: int
    ollama_timeout_seconds: int

    rag_generation_model: str
    rag_generation_retries: int
    rag_embedding_model: str
    rag_collection_name: str
    rag_data_root: str
    rag_persist_dir: str
    rag_existing_design_folder: str

    rag_chunk_size: int
    rag_chunk_overlap: int
    rag_retrieval_k: int
    rag_context_docs: int
    rag_context_char_budget: int
    rag_existing_design_boost: float


def _build_settings() -> Settings:
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    llm_model = os.getenv("LLM_MODEL", "mistral")

    return Settings(
        ollama_base_url=ollama_base_url,
        ollama_generate_url=os.getenv("OLLAMA_URL", f"{ollama_base_url}/api/generate"),
        llm_model=llm_model,
        llm_max_retries=_int_env("LLM_MAX_RETRIES", 2),
        ollama_timeout_seconds=_int_env("OLLAMA_TIMEOUT_SECONDS", 240),  # 4 minutes max
        rag_generation_model=os.getenv("RAG_GENERATION_MODEL", llm_model),
        rag_generation_retries=_int_env("RAG_GENERATION_RETRIES", 0),  # No retries for speed
        rag_embedding_model=os.getenv("RAG_EMBEDDING_MODEL", "nomic-embed-text"),
        rag_collection_name=os.getenv("RAG_COLLECTION_NAME", "system_design_docs"),
        rag_data_root=os.getenv("RAG_DATA_ROOT", _default_rag_data_root()),
        rag_persist_dir=os.getenv("RAG_PERSIST_DIR", str(_PROJECT_ROOT / ".chroma")),
        rag_existing_design_folder=os.getenv("RAG_EXISTING_DESIGN_FOLDER", "Existing System Design"),
        rag_chunk_size=_int_env("RAG_CHUNK_SIZE", 1200),
        rag_chunk_overlap=_int_env("RAG_CHUNK_OVERLAP", 150),
        rag_retrieval_k=_int_env("RAG_RETRIEVAL_K", 3),  # Reduced from 5 to 3
        rag_context_docs=_int_env("RAG_CONTEXT_DOCS", 1),  # Reduced from 2 to 1
        rag_context_char_budget=_int_env("RAG_CONTEXT_CHAR_BUDGET", 1000),  # Reduced from 2000
        rag_existing_design_boost=_float_env("RAG_EXISTING_DESIGN_BOOST", 0.2),
    )


settings = _build_settings()
