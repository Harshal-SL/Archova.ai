"""
Embedding generation for RAG documents.

Uses SentenceTransformer to generate local embeddings for all chunks,
supporting semantic similarity search and retrieval.
"""

import logging
import os
import warnings
from typing import List

import numpy as np

# Suppress the HuggingFace Hub unauthenticated-request warning and
# the SentenceTransformers BertModel LOAD REPORT noise before import.
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
warnings.filterwarnings("ignore", message=".*unauthenticated requests.*")
warnings.filterwarnings("ignore", message=".*HF_TOKEN.*")

from sentence_transformers import SentenceTransformer  # noqa: E402

from .config import EMBEDDING_MODEL, EMBEDDING_DEVICE, EMBEDDING_BATCH_SIZE


logger = logging.getLogger(__name__)

# Global embedding model instance (lazy loaded)
_embedder: SentenceTransformer | None = None


def get_embedder() -> SentenceTransformer:
    """
    Get or initialize the embedding model.

    Returns:
        SentenceTransformer instance.

    Raises:
        RuntimeError: If the model fails to load.
    """
    global _embedder

    if _embedder is not None:
        return _embedder

    # Suppress the "BertModel LOAD REPORT" table printed by sentence-transformers
    logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
    logging.getLogger("transformers").setLevel(logging.ERROR)

    try:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _embedder = SentenceTransformer(
            EMBEDDING_MODEL,
            device=EMBEDDING_DEVICE,
        )
        logger.info(
            f"Embedding model loaded. "
            f"Dimension: {_embedder.get_sentence_embedding_dimension()}"
        )
        return _embedder
    except Exception as e:
        logger.error(f"Failed to load embedding model {EMBEDDING_MODEL}: {e}")
        raise RuntimeError(f"Cannot initialize embeddings: {e}") from e


def embed_texts(
    texts: List[str],
    batch_size: int = EMBEDDING_BATCH_SIZE,
    show_progress: bool = True,
) -> List[List[float]]:
    """
    Generate embeddings for a list of texts.
    
    Args:
        texts: List of text strings to embed.
        batch_size: Batch size for embedding generation.
        show_progress: Whether to show a progress bar.
    
    Returns:
        List of embedding vectors (each as a list of floats).
    
    Raises:
        ValueError: If texts list is empty.
    """
    if not texts:
        raise ValueError("Cannot embed an empty list of texts")
    
    embedder = get_embedder()
    
    logger.info(f"Embedding {len(texts)} texts with batch size {batch_size}")
    
    try:
        embeddings = embedder.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=False,  # Return as numpy for conversion to list
        )
        
        # Convert numpy arrays to Python lists for JSON serialization
        result = [emb.tolist() if isinstance(emb, np.ndarray) else list(emb) for emb in embeddings]
        
        logger.info(f"Generated embeddings for {len(result)} texts")
        return result
        
    except Exception as e:
        logger.error(f"Failed to embed texts: {e}")
        raise


def get_embedding_dimension() -> int:
    """
    Get the dimension of the embedding vectors.
    
    Returns:
        Number of dimensions in the embedding space.
    """
    embedder = get_embedder()
    return embedder.get_sentence_embedding_dimension()


def embed_text(text: str) -> List[float]:
    """
    Embed a single text string.
    
    Args:
        text: Text to embed.
    
    Returns:
        Embedding vector as a list of floats.
    """
    embeddings = embed_texts([text], show_progress=False)
    return embeddings[0]
