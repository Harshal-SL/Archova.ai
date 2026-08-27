from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_env_file(override: bool = True) -> None:
    """Load key-value pairs from .env file into os.environ."""
    env_path = _PROJECT_ROOT / ".env"
    if not env_path.exists():
        return

    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path, override=override)
        return
    except ImportError:
        pass

    with open(env_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip("'\"")
            if key:
                if override or not os.getenv(key):
                    os.environ[key] = val


_load_env_file(override=True)


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
    rag_embed_model_local: str

    # ── OpenRouter ────────────────────────────────────────────────────────────
    openrouter_api_key: str
    openrouter_base_url: str
    allow_paid_models: bool
    openrouter_timeout_seconds: int
    llm_gateway_max_retries: int
    llm_gateway_json_retries: int
    fallback_model: str

    # Qdrant configuration
    qdrant_url: str
    qdrant_collection_name: str
    rag_similarity_threshold: float

    rag_data_root: str
    rag_existing_design_folder: str

    rag_chunk_size: int
    rag_chunk_overlap: int
    rag_retrieval_k: int
    rag_context_docs: int
    rag_context_char_budget: int
    rag_existing_design_boost: float

    rag_hld_num_predict: int
    rag_lld_num_predict: int
    rag_num_ctx: int


def _build_settings() -> Settings:
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    llm_model = os.getenv("LLM_MODEL", "")

    return Settings(
        ollama_base_url=ollama_base_url,
        ollama_generate_url=os.getenv("OLLAMA_URL", f"{ollama_base_url}/api/generate"),
        llm_model=llm_model,
        llm_max_retries=_int_env("LLM_MAX_RETRIES", 2),
        ollama_timeout_seconds=_int_env("OLLAMA_TIMEOUT_SECONDS", 240),
        rag_generation_model=os.getenv("RAG_GENERATION_MODEL", os.getenv("LLM_MODEL", "")),
        rag_generation_retries=_int_env("RAG_GENERATION_RETRIES", 0),
        rag_embedding_model=os.getenv("RAG_EMBEDDING_MODEL", "nomic-embed-text"),
        rag_embed_model_local=os.getenv("RAG_EMBED_MODEL_LOCAL", "BAAI/bge-small-en-v1.5"),
        # OpenRouter
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
        openrouter_base_url=os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ),
        allow_paid_models=False,
        openrouter_timeout_seconds=_int_env("OPENROUTER_TIMEOUT_SECONDS", 120),
        llm_gateway_max_retries=_int_env("LLM_GATEWAY_MAX_RETRIES", 2),
        llm_gateway_json_retries=_int_env("LLM_GATEWAY_JSON_RETRIES", 1),
        fallback_model=os.getenv("FALLBACK_MODEL", "").strip() or "nvidia/nemotron-3-nano-30b-a3b:free",
        # Qdrant configuration
        qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        qdrant_collection_name=os.getenv("QDRANT_COLLECTION_NAME", "architecture_rag"),
        rag_similarity_threshold=_float_env("RAG_SIMILARITY_THRESHOLD", 0.3),
        rag_data_root=os.getenv("RAG_DATA_ROOT", _default_rag_data_root()),
        rag_existing_design_folder=os.getenv("RAG_EXISTING_DESIGN_FOLDER", "Existing System Design"),
        rag_chunk_size=_int_env("RAG_CHUNK_SIZE", 600),
        rag_chunk_overlap=_int_env("RAG_CHUNK_OVERLAP", 100),
        rag_retrieval_k=_int_env("RAG_RETRIEVAL_K", 10),
        rag_context_docs=_int_env("RAG_CONTEXT_DOCS", 8),
        rag_context_char_budget=_int_env("RAG_CONTEXT_CHAR_BUDGET", 3000),
        rag_existing_design_boost=_float_env("RAG_EXISTING_DESIGN_BOOST", 0.2),
        rag_hld_num_predict=_int_env("RAG_HLD_NUM_PREDICT", 1200),
        rag_lld_num_predict=_int_env("RAG_LLD_NUM_PREDICT", 1500),
        rag_num_ctx=_int_env("RAG_NUM_CTX", 4096),
    )


settings = _build_settings()


def reload_settings() -> Settings:
    """Reload environment variables from .env and rebuild settings."""
    global settings
    _load_env_file(override=True)
    settings = _build_settings()
    return settings


def print_startup_env_diagnostics() -> None:
    """Print loaded model environment variables and central configuration validation."""
    from config.model_config import validate_model_config
    validate_model_config(print_diagnostics=True)


