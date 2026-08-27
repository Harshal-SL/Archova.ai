"""Architecture Knowledge RAG Service for SAE v2 Agents.

Provides agent-owned live semantic retrieval against the enterprise architectural
knowledge base in Qdrant (app/rag/).

Features:
  - Agent-owned, non-orchestrator-mediated retrieval
  - In-process query-result caching
  - Configurable similarity threshold filtering (default: 0.55)
  - Resilient retrieval timeouts with dedicated RAGTimeoutError and RAGUnavailableError
  - Zero-failure fallback semantics for agent resilience
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project venv dependencies (qdrant_client, sentence_transformers, torch)
# are accessible even if invoked via global python interpreter
for parent in Path(__file__).resolve().parents:
    venv_site = parent / "venv" / "Lib" / "site-packages"
    if venv_site.exists() and str(venv_site) not in sys.path:
        sys.path.insert(0, str(venv_site))
        break

logger = logging.getLogger(__name__)

MIN_SIMILARITY_THRESHOLD: float = 0.55
DEFAULT_RAG_TIMEOUT: float = 8.0


# ── Exceptions ────────────────────────────────────────────────────────────────

class RAGError(Exception):
    """Base exception for RAG retrieval operations."""
    pass


class RAGTimeoutError(RAGError):
    """Raised when RAG retrieval exceeds the allowed timeout duration."""
    pass


class RAGUnavailableError(RAGError):
    """Raised when Qdrant or embedding models are unreachable, offline, or fail."""
    pass


# ── Data Model ────────────────────────────────────────────────────────────────

@dataclass
class RetrievedChunk:
    """Standardized architectural knowledge chunk returned to agents."""

    text: str
    score: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "score": self.score,
            "source": self.source,
            "metadata": self.metadata,
        }


# ── Architecture Knowledge Service ───────────────────────────────────────────

class ArchitectureKnowledgeService:
    """Directly callable shared service for per-agent architectural RAG retrieval."""

    def __init__(
        self,
        min_similarity_threshold: float = MIN_SIMILARITY_THRESHOLD,
        default_timeout: float = DEFAULT_RAG_TIMEOUT,
        preload: bool = True,
    ) -> None:
        self.min_similarity_threshold = min_similarity_threshold
        self.default_timeout = default_timeout
        self._retriever: Optional[Any] = None
        self._cache: Dict[str, List[RetrievedChunk]] = {}
        self._init_failed: bool = False
        if preload:
            self.warmup()

    def _get_retriever(self) -> Any:
        """Lazy-initialize the RAG Retriever from app.rag."""
        if self._retriever is not None:
            return self._retriever
        if self._init_failed:
            raise RAGUnavailableError("Retriever initialization previously failed.")

        try:
            try:
                from app.rag.retriever import RAGRetriever as Retriever
            except ImportError:
                from app.rag.retriever import Retriever  # type: ignore

            self._retriever = Retriever()
            return self._retriever
        except Exception as e:
            self._init_failed = True
            logger.warning(f"Failed to initialize RAG Retriever: {e}")
            raise RAGUnavailableError(f"RAG Retriever unavailable: {e}") from e

    def warmup(self) -> None:
        """Pre-warm retriever and embedding model to eliminate cold-start latency."""
        try:
            retriever = self._get_retriever()
            from app.rag.embeddings import get_embedder
            get_embedder()
            logger.info("ArchitectureKnowledgeService warmed up successfully.")
        except Exception as e:
            logger.warning(f"RAG warm-up warning: {e}")

    def _cache_key(self, query: str, top_k: int, category_filter: Optional[str]) -> str:
        """Generate normalized cache key for retrieval query."""
        raw = f"{query.strip().lower()}|top_k={top_k}|cat={category_filter or ''}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def _sync_retrieve(
        self,
        query: str,
        top_k: int,
        category_filter: Optional[str],
    ) -> List[Any]:
        """Perform synchronous retrieval against Qdrant via Retriever."""
        retriever = self._get_retriever()
        return retriever.retrieve(
            query=query,
            top_k=top_k,
            category_filter=category_filter,
        )

    async def get_context(
        self,
        query: str,
        top_k: int = 5,
        min_score: Optional[float] = None,
        timeout: Optional[float] = None,
        category_filter: Optional[str] = None,
    ) -> List[RetrievedChunk]:
        """Asynchronously retrieve relevant architectural knowledge chunks for an agent.

        Args:
            query: Natural-language architectural search query built by the agent.
            top_k: Maximum number of knowledge chunks to return.
            min_score: Minimum similarity score threshold (default: 0.55).
            timeout: Maximum retrieval timeout in seconds (default: 8.0s).
            category_filter: Optional category restriction in Qdrant.

        Returns:
            List of RetrievedChunk objects meeting the similarity threshold.

        Raises:
            RAGTimeoutError: If retrieval exceeds the timeout window.
            RAGUnavailableError: If Qdrant or embedding model fails.
        """
        if not query or not query.strip():
            return []

        thr = min_score if min_score is not None else self.min_similarity_threshold
        t_out = timeout if timeout is not None else self.default_timeout
        cache_k = self._cache_key(query, top_k, category_filter)

        # 1. In-process cache check
        if cache_k in self._cache:
            logger.debug(f"RAG in-process cache hit for query: '{query[:40]}...'")
            return self._cache[cache_k]

        # 2. Execute retrieval with timeout in thread pool
        try:
            raw_hits = await asyncio.wait_for(
                asyncio.to_thread(self._sync_retrieve, query, top_k, category_filter),
                timeout=t_out,
            )
        except asyncio.TimeoutError as exc:
            logger.warning(f"RAG retrieval timed out after {t_out}s for query: '{query[:50]}...'")
            raise RAGTimeoutError(f"RAG retrieval timed out after {t_out}s") from exc
        except RAGUnavailableError:
            raise
        except Exception as exc:
            logger.warning(f"RAG retrieval failed for query '{query[:50]}...': {exc}")
            raise RAGUnavailableError(f"RAG retrieval error: {exc}") from exc

        # 3. Filter by similarity threshold & construct chunks
        chunks: List[RetrievedChunk] = []
        for hit in raw_hits:
            score = float(getattr(hit, "final_score", getattr(hit, "score", 0.0)))
            if score >= thr:
                text = getattr(hit, "text", str(hit))
                metadata = getattr(hit, "metadata", {}) or {}
                source = metadata.get("source_file") or metadata.get("source") or "Enterprise Architecture Corpus"
                chunks.append(
                    RetrievedChunk(
                        text=text,
                        score=round(score, 4),
                        source=str(source),
                        metadata=metadata,
                    )
                )

        # 4. Cache & return
        self._cache[cache_k] = chunks
        logger.info(
            f"RAG retrieval successful: {len(chunks)} chunks (top score: {chunks[0].score if chunks else 0.0}) "
            f"for query: '{query[:50]}...'"
        )
        return chunks

    def clear_cache(self) -> None:
        """Clear in-process query cache."""
        self._cache.clear()


# ── Global Singleton Helper ───────────────────────────────────────────────────

_global_service: Optional[ArchitectureKnowledgeService] = None


def get_architecture_knowledge_service() -> ArchitectureKnowledgeService:
    """Get or create the global shared ArchitectureKnowledgeService instance."""
    global _global_service
    if _global_service is None:
        _global_service = ArchitectureKnowledgeService()
    return _global_service
