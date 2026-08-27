"""Base Architecture Agent for SAE v2.

Provides agent-owned live RAG knowledge retrieval, domain-specific query construction,
and graceful fallback handling across all LLM-mode agents.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from app.rag.query_builder import build_query_for_role
from app.sae.providers.llm_provider import OpenRouterProvider
from app.sae.services.architecture_knowledge_service import (
    ArchitectureKnowledgeService,
    RAGTimeoutError,
    RAGUnavailableError,
    RetrievedChunk,
    get_architecture_knowledge_service,
)

logger = logging.getLogger(__name__)


class BaseArchitectureAgent:
    """Base class for all SAE v2 LLM-mode generation agents."""

    role: str = "base_agent"

    def __init__(
        self,
        llm_provider: Optional[OpenRouterProvider] = None,
        knowledge_service: Optional[ArchitectureKnowledgeService] = None,
        model_name: Optional[str] = None,
    ) -> None:
        self.llm_provider = llm_provider or OpenRouterProvider()
        self.knowledge_service = knowledge_service or get_architecture_knowledge_service()
        self.model_name = model_name

    async def retrieve_rag_context(
        self,
        context_payload: Dict[str, Any],
        top_k: int = 5,
        min_score: Optional[float] = None,
        timeout: Optional[float] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """Independently build domain query and retrieve architectural knowledge chunks from Qdrant.

        Returns:
            Tuple of:
              - formatted_rag_prompt_block (str): Additive context to inject into prompt (or empty string on fallback).
              - rag_metadata (dict): { used_rag, chunk_count, avg_similarity, fallback, query }
        """
        # 1. Agent-owned query construction from its role and input context
        query = build_query_for_role(self.role, context_payload)
        if not query:
            return "", {
                "used_rag": False,
                "chunk_count": 0,
                "avg_similarity": 0.0,
                "fallback": True,
                "query": "",
                "reason": "Empty query generated",
            }

        is_debug = getattr(self.llm_provider, "debug", False) or os.getenv("SAE_DEBUG", "false").lower() in ("true", "1", "yes")
        if is_debug:
            print(f"\n{'─'*78}\n📚 [DEBUG: RAG RETRIEVAL] Agent: {self.role}\n🔍 Query: {query}", flush=True)

        # 2. Query knowledge service directly (agent-owned, zero orchestrator mediation)
        try:
            chunks: List[RetrievedChunk] = await self.knowledge_service.get_context(
                query=query,
                top_k=top_k,
                min_score=min_score,
                timeout=timeout,
            )

            if not chunks:
                if is_debug:
                    print(f"⚠️ [DEBUG: RAG ZERO MATCHES] 0 chunks met min_score {min_score}. Falling back to static prompt.\n{'─'*78}\n", flush=True)
                if hasattr(self.llm_provider, "sae_logger") and self.llm_provider.sae_logger:
                    try:
                        self.llm_provider.sae_logger.log_rag_retrieval(
                            agent_role=self.role,
                            query=query,
                            chunks_count=0,
                            avg_similarity=0.0,
                            fallback=True,
                        )
                    except Exception:
                        pass
                logger.info(
                    f"[{self.role}] RAG returned 0 chunks meeting threshold {min_score} (rag_status='fallback_static')"
                )
                return "", {
                    "used_rag": False,
                    "chunk_count": 0,
                    "avg_similarity": 0.0,
                    "fallback": True,
                    "query": query,
                    "reason": "No chunks met similarity threshold",
                }

            # 3. Format additive context block
            avg_score = round(sum(c.score for c in chunks) / len(chunks), 4)
            formatted_lines = [
                "\n=== RETRIEVED ARCHITECTURAL KNOWLEDGE PATTERNS (Technical Guidance Only) ===",
                "IMPORTANT: Treat this technical RAG context ONLY as architectural implementation guidance",
                "(e.g. choice of libraries, caching strategies, security controls). Do NOT use this context",
                "to introduce additional business domain capabilities, entities, or requirements not present",
                "in the current Problem Statement and ARSRS.",
            ]
            for idx, c in enumerate(chunks, 1):
                formatted_lines.append(f"\n[Pattern {idx} | Source: {c.source} | Similarity: {c.score:.2f}]")
                formatted_lines.append(c.text.strip())
            formatted_lines.append("===============================================================================\n")

            rag_block = "\n".join(formatted_lines)
            rag_meta = {
                "used_rag": True,
                "chunk_count": len(chunks),
                "avg_similarity": avg_score,
                "fallback": False,
                "query": query,
            }

            top_sources = [f"{c.source} ({c.score:.2f})" for c in chunks]
            if hasattr(self.llm_provider, "sae_logger") and self.llm_provider.sae_logger:
                try:
                    self.llm_provider.sae_logger.log_rag_retrieval(
                        agent_role=self.role,
                        query=query,
                        chunks_count=len(chunks),
                        avg_similarity=avg_score,
                        fallback=False,
                        top_sources=top_sources,
                    )
                except Exception:
                    pass

            if is_debug:
                print(f"✅ [DEBUG: RAG SUCCESS] Retrieved {len(chunks)} chunks (avg_sim: {avg_score})", flush=True)
                for idx, c in enumerate(chunks, 1):
                    preview = c.text.strip().replace("\n", " ")
                    if len(preview) > 160:
                        preview = preview[:160] + "..."
                    print(f"  [{idx}] Score: {c.score:.2f} | Source: {c.source}\n      Text: {preview}", flush=True)
                print(f"{'─'*78}\n", flush=True)

            logger.info(
                f"[{self.role}] ✅ RAG context retrieved: {len(chunks)} chunks (avg_similarity: {avg_score}) "
                f"for query: '{query[:45]}...'"
            )
            return rag_block, rag_meta

        except (RAGTimeoutError, RAGUnavailableError) as err:
            if hasattr(self.llm_provider, "sae_logger") and self.llm_provider.sae_logger:
                try:
                    self.llm_provider.sae_logger.log_rag_retrieval(
                        agent_role=self.role,
                        query=query,
                        chunks_count=0,
                        avg_similarity=0.0,
                        fallback=True,
                    )
                except Exception:
                    pass
            if is_debug:
                print(f"⚠️ [DEBUG: RAG FALLBACK] {type(err).__name__}: {err}. Proceeding with static prompt.\n{'─'*78}\n", flush=True)
            logger.info(
                f"[{self.role}] ⚠️ RAG {type(err).__name__}: {err}. Proceeding with static prompt (rag_status='fallback_static')"
            )
            return "", {
                "used_rag": False,
                "chunk_count": 0,
                "avg_similarity": 0.0,
                "fallback": True,
                "query": query,
                "reason": str(err),
            }
        except Exception as err:
            if is_debug:
                print(f"⚠️ [DEBUG: RAG UNEXPECTED] {err}. Proceeding with static prompt.\n{'─'*78}\n", flush=True)
            logger.warning(
                f"[{self.role}] ⚠️ Unexpected RAG exception: {err}. Proceeding with static prompt (rag_status='fallback_static')"
            )
            return "", {
                "used_rag": False,
                "chunk_count": 0,
                "avg_similarity": 0.0,
                "fallback": True,
                "query": query,
                "reason": str(err),
            }

    def inject_rag_context(self, prompt: str, rag_block: str) -> str:
        """Additively append retrieved RAG context to the user prompt."""
        if not rag_block:
            return prompt
        return f"{prompt}\n\n{rag_block}"

    def inject_domain_fence(
        self,
        prompt: str,
        cac: Optional[Any] = None,
        domain_ctx: Optional[Any] = None,
        raw_prompt: str = "",
        arsrs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str:
        """Prepend authoritative architectural domain boundary fence to the prompt."""
        try:
            from app.sae.utils.domain_fence import build_domain_fence
            fence = build_domain_fence(cac=cac, domain_ctx=domain_ctx, raw_prompt=raw_prompt, arsrs=arsrs)
            if fence:
                return f"{fence}\n\n{prompt}"
        except Exception as e:
            logger.warning("Failed to build domain fence: %s", e)
        return prompt

    def attach_rag_metadata(self, result: Dict[str, Any], rag_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Attach rag_metadata to the resulting dictionary."""
        result["rag_metadata"] = rag_metadata
        return result

