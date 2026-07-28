"""
RAG design module.

Re-exports the public pipeline API from the Qdrant-backed design service.
"""

from app.services.design_service import reindex_corpus, run_design_pipeline

__all__ = ["run_design_pipeline", "reindex_corpus"]
    