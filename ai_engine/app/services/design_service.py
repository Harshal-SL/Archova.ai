"""
Design generation service using Qdrant-based RAG.

Provides a clean interface for HLD and LLD generation with architecture retrieval.
"""

import logging
from pathlib import Path

from app.config import settings
from backend.rag import (
    QdrantManager,
    IngestionPipeline,
    RAGRetriever,
    QueryBuilder,
    QueryPlan,
    ContextBuilder,
    RAGValidator,
)
from app.services.design_generator import (
    build_hld_prompt,
    build_lld_prompt,
    compact_hld,
    generate_design_from_ollama,
)
from app.services.design_validator import normalize_design_output


logger = logging.getLogger(__name__)


# Global Qdrant manager instance
_QDRANT_MANAGER: QdrantManager | None = None
_RAG_RETRIEVER: RAGRetriever | None = None


def _get_qdrant_manager() -> QdrantManager:
    """Get or create the Qdrant manager instance."""
    global _QDRANT_MANAGER
    if _QDRANT_MANAGER is None:
        try: 
            _QDRANT_MANAGER = QdrantManager(
                url=settings.qdrant_url,
                collection_name=settings.qdrant_collection_name,
            )
            logger.info(f"Initialized Qdrant manager at {settings.qdrant_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant manager: {e}")
            raise
    return _QDRANT_MANAGER


def _get_retriever() -> RAGRetriever:
    """Get or create the RAG retriever instance."""
    global _RAG_RETRIEVER
    if _RAG_RETRIEVER is None:
        manager = _get_qdrant_manager()
        _RAG_RETRIEVER = RAGRetriever(qdrant_manager=manager)
        logger.info("Initialized RAG retriever")
    return _RAG_RETRIEVER


def reindex_corpus() -> dict:
    """
    Reindex the RAG corpus from markdown files into Qdrant.
    
    Returns:
        Dictionary with ingestion statistics.
    
    Raises:
        RuntimeError: If indexing fails.
    """
    logger.info("Starting corpus reindexing")
    
    try:
        manager = _get_qdrant_manager()
        pipeline = IngestionPipeline(qdrant_manager=manager)
        
        # Ingest all documents
        stats = pipeline.ingest_all(force_recreate=True)
        
        logger.info(f"Reindexing completed: {stats['vectors_uploaded']} vectors uploaded")
        
        return {
            "status": "ok",
            "files_loaded": stats["files_loaded"],
            "chunks_created": stats["chunks_created"],
            "vectors_uploaded": stats["vectors_uploaded"],
            "embedding_time_s": stats["embedding_time"],
            "upload_time_s": stats["upload_time"],
            "total_time_s": stats["total_time"],
        }
    except Exception as e:
        logger.error(f"Reindexing failed: {e}")
        raise RuntimeError(f"Cannot reindex corpus: {e}") from e


def run_design_pipeline(parameters: dict) -> dict:
    """
    Generate HLD and LLD for a system design using architecture retrieval.
    
    Args:
        parameters: Design requirements dictionary.
    
    Returns:
        Dictionary with generated HLD and LLD sections.
    
    Raises:
        RuntimeError: If pipeline execution fails.
    """
    if not isinstance(parameters, dict) or not parameters:
        raise RuntimeError("parameters must be a non-empty object.")
    
    logger.info("Starting design pipeline")
    
    try:
        retriever = _get_retriever()
        manager = _get_qdrant_manager()
        
        # Ensure collection exists
        if not manager.collection_exists():
            logger.warning("Collection does not exist, reindexing corpus")
            reindex_corpus()
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # RETRIEVAL PHASE
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        # Build architecture-aware query plan (expansion + intent detection)
        plan = QueryBuilder.plan_from_requirements(parameters)
        
        logger.debug(
            f"Query plan: intents={plan.detected_intents}, "
            f"categories={len(plan.target_categories)}, "
            f"expansions={len(plan.expanded_queries)}"
        )
        
        # Retrieve with MMR, diversity cap, and optional reranking
        all_hits, retrieval_report = retriever.retrieve_from_plan(
            plan=plan,
            top_k=settings.rag_retrieval_k,
            threshold=settings.rag_similarity_threshold,
        )
        
        logger.info(
            f"Retrieved {len(all_hits)} hits from "
            f"{retrieval_report.final_count} final documents"
        )
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # HLD GENERATION
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        context_builder = ContextBuilder(max_tokens=3000)
        hld_context = context_builder.build_context(all_hits[:10])
        
        logger.debug(f"HLD context size: {len(hld_context)} chars")
        
        hld_prompt = build_hld_prompt(parameters, hld_context, "")
        
        try:
            hld_result = generate_design_from_ollama(
                prompt=hld_prompt,
                ollama_generate_url=settings.ollama_generate_url,
                model=settings.rag_generation_model,
                timeout_seconds=settings.ollama_timeout_seconds,
                num_predict=settings.rag_hld_num_predict,
                num_ctx=settings.rag_num_ctx,
                max_retries=settings.rag_generation_retries,
            )
            logger.info("HLD generation completed")
        except RuntimeError as e:
            logger.warning(f"HLD generation failed: {e}, using fallback")
            return _fallback_design(parameters, all_hits)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # LLD GENERATION (per section)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        hld_summary = compact_hld(hld_result, max_tokens=400)
        lld_sections = {}
        
        sections = ["frontend", "backend", "database", "cloud", "security"]
        
        for section in sections:
            logger.debug(f"Generating LLD for {section}")
            
            # Section-specific query plan for refinement
            section_query = f"{plan.primary_query} {section} implementation details"
            section_plan = QueryBuilder.plan(section_query)
            
            section_hits, _ = retriever.retrieve_from_plan(
                section_plan,
                top_k=6,
                threshold=settings.rag_similarity_threshold,
            )
            
            section_context = context_builder.build_context(section_hits)
            
            lld_prompt = build_lld_prompt(parameters, hld_summary, section, section_context)
            
            try:
                lld_section_result = generate_design_from_ollama(
                    prompt=lld_prompt,
                    ollama_generate_url=settings.ollama_generate_url,
                    model=settings.rag_generation_model,
                    timeout_seconds=settings.ollama_timeout_seconds,
                    num_predict=settings.rag_lld_num_predict,
                    num_ctx=settings.rag_num_ctx,
                    max_retries=settings.rag_generation_retries,
                )
                lld_sections[section] = lld_section_result.get(section, {})
            except RuntimeError as e:
                logger.warning(f"LLD generation for {section} failed: {e}")
                lld_sections[section] = {}
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # ASSEMBLE FINAL DESIGN
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        design = {
            "hld": hld_result,
            "lld": {section: lld_sections.get(section, {}) for section in sections},
        }
        
        # Normalize output
        normalized = normalize_design_output(design)
        
        logger.info("Design pipeline completed successfully")
        return normalized
    
    except Exception as e:
        logger.error(f"Design pipeline failed: {e}")
        raise


def _fallback_design(parameters: dict, hits: list) -> dict:
    """
    Generate a fallback design using retrieved knowledge when LLM generation fails.
    
    Args:
        parameters: Design requirements.
        hits: Retrieved relevant documents.
    
    Returns:
        Fallback design dictionary.
    """
    logger.warning("Using fallback design generation")
    
    context_builder = ContextBuilder(max_tokens=2000)
    context = context_builder.build_context(hits)
    
    return {
        "hld": {
            "overview": "Fallback design generated from retrieved architecture knowledge.",
            "context": context[:500],  # Include retrieved context
            "sections": [],
        },
        "lld": {
            section: {"code": "// Fallback LLD", "notes": "See HLD context for details"}
            for section in ["frontend", "backend", "database", "cloud", "security"]
        },
    }


def run_design_pipeline_from_arsrs(arsrs: dict) -> dict:
    """
    Generate HLD and LLD from an ARSRS dict produced by the REE pipeline.

    The ARSRS becomes the single source of truth for architecture generation.
    This function extracts the parameter dict from the ARSRS and delegates
    to the existing run_design_pipeline() so no downstream generator is rewritten.

    Args:
        arsrs: Serialised ARSRS dict from the REE Orchestrator response.

    Returns:
        Dictionary with generated HLD and LLD sections (same shape as
        run_design_pipeline).

    Raises:
        RuntimeError: If the ARSRS is invalid or pipeline execution fails.
    """
    if not isinstance(arsrs, dict) or not arsrs:
        raise RuntimeError("arsrs must be a non-empty dict.")

    logger.info(
        "Starting design pipeline from ARSRS — session_id=%s",
        arsrs.get("session_id", "unknown"),
    )

    # Build a rich parameters dict the existing pipeline understands.
    # Prefer the to_parameters_for_design() output when available;
    # fall back to the flat parameters dict stored directly in the ARSRS.
    parameters = arsrs.get("parameters", {})

    # Enrich the parameters with summary fields from the ARSRS so the
    # QueryBuilder and prompt builders have the best possible context.
    def _ensure(key: str, value) -> None:
        if value and (key not in parameters or not _get_param_value(parameters, key)):
            parameters[key] = {"value": value, "ai_suggestion": None}

    _ensure("goal",        arsrs.get("goal"))
    _ensure("system_type", arsrs.get("system_type") or
                           (arsrs.get("domain_context") or {}).get("system_type"))

    # Structured requirements → flat lists for prompt builders
    _ensure(
        "functional_requirements",
        [r.get("description", r.get("title", "")) for r in arsrs.get("functional_requirements", [])
         if isinstance(r, dict)]
        or arsrs.get("core_objectives"),
    )
    _ensure(
        "non_functional_requirements",
        [r.get("description", r.get("title", "")) for r in arsrs.get("non_functional_requirements", [])
         if isinstance(r, dict)],
    )
    _ensure(
        "actors",
        [r.get("title", "") for r in arsrs.get("actors", [])
         if isinstance(r, dict) and r.get("title")],
    )
    _ensure(
        "external_services",
        [r.get("title", "") for r in arsrs.get("integrations", [])
         if isinstance(r, dict) and r.get("title")],
    )

    # Architecture patterns from domain context → useful for RAG query expansion
    domain_ctx = arsrs.get("domain_context", {})
    if isinstance(domain_ctx, dict):
        patterns = domain_ctx.get("architecture_patterns", [])
        if patterns:
            _ensure("architecture_patterns", patterns)
        compliance = domain_ctx.get("compliance", [])
        if compliance:
            _ensure("compliance", compliance)

    if not parameters:
        raise RuntimeError(
            "ARSRS contains no usable parameters for architecture generation."
        )

    return run_design_pipeline(parameters)


def _get_param_value(parameters: dict, key: str):
    """Extract value from a {value, ai_suggestion} parameter node."""
    node = parameters.get(key)
    if isinstance(node, dict):
        return node.get("value")
    return node
