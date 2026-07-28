"""
Backend RAG module — production-grade Qdrant retrieval pipeline.

Exports every public symbol needed by the rest of the application.
"""

from .config import (
    QDRANT_URL,
    QDRANT_LOCAL_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K,
    FETCH_K,
    MMR_LAMBDA,
    MAX_CHUNKS_PER_DOCUMENT,
    ENABLE_RERANKING,
    ENABLE_QUERY_EXPANSION,
    ENABLE_CATEGORY_FILTER,
    RAG_DATA_ROOT,
)
from .loader import load_documents, load_documents_by_category
from .metadata import extract_metadata_from_path
from .chunker import chunk_documents
from .embeddings import get_embedder, embed_texts, embed_text, get_embedding_dimension
from .qdrant_manager import QdrantManager
from .ingestion import IngestionPipeline
from .retriever import RAGRetriever, RetrievalHit, RetrievalReport
from .query_builder import QueryBuilder, QueryPlan
from .context_builder import ContextBuilder
from .validator import RAGValidator


__all__ = [
    # Config
    "QDRANT_URL",
    "QDRANT_LOCAL_PATH",
    "COLLECTION_NAME",
    "EMBEDDING_MODEL",
    "CHUNK_SIZE",
    "CHUNK_OVERLAP",
    "TOP_K",
    "FETCH_K",
    "MMR_LAMBDA",
    "MAX_CHUNKS_PER_DOCUMENT",
    "ENABLE_RERANKING",
    "ENABLE_QUERY_EXPANSION",
    "ENABLE_CATEGORY_FILTER",
    "RAG_DATA_ROOT",
    # Loader
    "load_documents",
    "load_documents_by_category",
    # Metadata
    "extract_metadata_from_path",
    # Chunker
    "chunk_documents",
    # Embeddings
    "get_embedder",
    "embed_texts",
    "embed_text",
    "get_embedding_dimension",
    # Qdrant
    "QdrantManager",
    # Ingestion
    "IngestionPipeline",
    # Retrieval
    "RAGRetriever",
    "RetrievalHit",
    "RetrievalReport",
    # Query Builder
    "QueryBuilder",
    "QueryPlan",
    # Context Builder
    "ContextBuilder",
    # Validator
    "RAGValidator",
]
