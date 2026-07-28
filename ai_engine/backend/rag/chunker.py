"""
Document chunking for RAG ingestion.

Splits documents into semantic chunks while preserving metadata
for each chunk. Uses a pure-Python recursive character splitter
to avoid langchain_text_splitters as an additional dependency.
"""

import logging
from typing import List

from langchain_core.documents import Document

from .config import CHUNK_SIZE, CHUNK_OVERLAP


logger = logging.getLogger(__name__)

# Ordered separators for recursive splitting
_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """
    Recursively split text into chunks using a list of separators.

    Args:
        text: Input text.
        chunk_size: Maximum chunk length in characters.
        chunk_overlap: Overlap in characters between adjacent chunks.

    Returns:
        List of text chunks.
    """
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    for sep in _SEPARATORS:
        if sep and sep in text:
            parts = text.split(sep)
            chunks: List[str] = []
            current = ""

            for part in parts:
                candidate = current + (sep if current else "") + part
                if len(candidate) <= chunk_size:
                    current = candidate
                else:
                    if current.strip():
                        chunks.append(current)
                    # Handle oversized parts recursively with the next separator
                    if len(part) > chunk_size:
                        sub = _split_text(part, chunk_size, chunk_overlap)
                        if sub:
                            # Start the next current with overlap from the last sub
                            overlap_text = sub[-1][-chunk_overlap:] if chunk_overlap else ""
                            chunks.extend(sub[:-1])
                            current = overlap_text + (sep if overlap_text else "") + "" if not sub else sub[-1]
                        else:
                            current = part
                    else:
                        # Carry overlap from previous chunk
                        overlap_text = current[-chunk_overlap:] if chunk_overlap and current else ""
                        current = (overlap_text + sep + part).lstrip(sep) if overlap_text else part

            if current.strip():
                chunks.append(current)

            if chunks:
                return chunks

    # No separator found — hard cut with overlap
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - chunk_overlap
    return chunks


def chunk_documents(
    documents: List[Document],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[Document]:
    """
    Split documents into chunks using recursive character splitting.

    Each output chunk preserves the source document's metadata and
    receives a ``chunk_number`` and ``total_chunks`` counter.

    Args:
        documents: List of LangChain Document objects.
        chunk_size: Maximum size of each chunk in characters.
        chunk_overlap: Number of overlapping characters between chunks.

    Returns:
        List of chunked Document objects with preserved metadata.
    """
    chunked_documents: List[Document] = []

    logger.info(
        f"Chunking {len(documents)} documents "
        f"(size={chunk_size}, overlap={chunk_overlap})"
    )

    for doc in documents:
        try:
            raw_chunks = _split_text(doc.page_content, chunk_size, chunk_overlap)

            for chunk_idx, chunk_text in enumerate(raw_chunks):
                chunked_documents.append(
                    Document(
                        page_content=chunk_text,
                        metadata={
                            **doc.metadata,
                            "chunk_number": chunk_idx,
                            "total_chunks": len(raw_chunks),
                        },
                    )
                )

            logger.debug(
                f"Chunked {doc.metadata.get('relative_path', '?')} "
                f"into {len(raw_chunks)} chunks"
            )

        except Exception as e:
            logger.error(
                f"Failed to chunk {doc.metadata.get('relative_path', 'unknown')}: {e}"
            )
            # Include the full document as a single chunk rather than dropping it
            doc.metadata["chunk_number"] = 0
            doc.metadata["total_chunks"] = 1
            chunked_documents.append(doc)

    logger.info(
        f"Created {len(chunked_documents)} chunks from {len(documents)} documents"
    )
    return chunked_documents
