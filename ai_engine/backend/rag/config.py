"""
Centralised configuration for the Qdrant RAG system.

All tuneable values live here.  No magic numbers elsewhere.
"""

from pathlib import Path
import os

# ── Qdrant connection ──────────────────────────────────────────────────────────
# Set QDRANT_URL to a remote server; leave at default to use local on-disk mode.
QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")

_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
QDRANT_LOCAL_PATH: str = os.getenv(
    "QDRANT_LOCAL_PATH",
    str(_PROJECT_ROOT / ".qdrant_data"),
)

COLLECTION_NAME: str = "architecture_rag"
DISTANCE_METRIC: str = "Cosine"

# ── Embedding ─────────────────────────────────────────────────────────────────
EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
EMBEDDING_BATCH_SIZE: int = 64
EMBEDDING_DEVICE: str = "cpu"

# ── Chunking ──────────────────────────────────────────────────────────────────
CHUNK_SIZE: int = 600
CHUNK_OVERLAP: int = 100

# ── Core retrieval ────────────────────────────────────────────────────────────
TOP_K: int = 10          # Final results returned to the caller
FETCH_K: int = 50        # Candidates fetched before MMR / reranking
SIMILARITY_THRESHOLD: float = 0.3

# ── MMR (Max Marginal Relevance) ──────────────────────────────────────────────
# lambda=1.0 → pure relevance; lambda=0.0 → pure diversity
MMR_LAMBDA: float = float(os.getenv("MMR_LAMBDA", "0.7"))

# ── Per-document diversity ────────────────────────────────────────────────────
# Maximum chunks allowed from the same source_file
MAX_CHUNKS_PER_DOCUMENT: int = int(os.getenv("MAX_CHUNKS_PER_DOCUMENT", "1"))

# ── Reranking ─────────────────────────────────────────────────────────────────
ENABLE_RERANKING: bool = os.getenv("ENABLE_RERANKING", "false").lower() == "true"
RERANKER_MODEL: str = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-base")
RERANKER_TOP_K: int = int(os.getenv("RERANKER_TOP_K", "8"))

# ── Query expansion ───────────────────────────────────────────────────────────
ENABLE_QUERY_EXPANSION: bool = (
    os.getenv("ENABLE_QUERY_EXPANSION", "true").lower() == "true"
)
MAX_EXPANSION_QUERIES: int = int(os.getenv("MAX_EXPANSION_QUERIES", "3"))

# ── Category filtering ────────────────────────────────────────────────────────
ENABLE_CATEGORY_FILTER: bool = (
    os.getenv("ENABLE_CATEGORY_FILTER", "true").lower() == "true"
)

# ── Data paths ────────────────────────────────────────────────────────────────
RAG_DATA_ROOT: Path = _PROJECT_ROOT / "data" / "RAG"
CACHE_DIR: Path = Path.home() / ".cache" / "architecture_rag"

# ── Misc ──────────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
VECTOR_STORE_BATCH_SIZE: int = 64
ENABLE_PROGRESS_BAR: bool = True


def validate_config() -> None:
    """Raise ValueError if critical configuration is missing or invalid."""
    if not RAG_DATA_ROOT.exists():
        raise ValueError(f"RAG data root does not exist: {RAG_DATA_ROOT}")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
