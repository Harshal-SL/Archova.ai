"""
Document loader for RAG corpus.

Recursively loads markdown files from the RAG data directory,
preserving folder structure and generating LangChain Document objects.
"""

import logging
from pathlib import Path
from typing import List

from langchain_core.documents import Document

from .config import RAG_DATA_ROOT
from .metadata import extract_metadata_from_path


logger = logging.getLogger(__name__)


def load_documents(root: Path = RAG_DATA_ROOT) -> List[Document]:
    """
    Recursively load all markdown files from the RAG corpus.
    
    Args:
        root: Root directory of the RAG corpus.
    
    Returns:
        List of LangChain Document objects with preserved metadata.
    
    Raises:
        ValueError: If root directory does not exist.
    """
    if not root.exists():
        raise ValueError(f"RAG data root does not exist: {root}")
    
    documents: List[Document] = []
    md_files = sorted(root.rglob("*.md"))
    
    logger.info(f"Loading {len(md_files)} markdown files from {root}")
    
    for file_path in md_files:
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace").strip()
            if not text:
                logger.warning(f"Empty file: {file_path}")
                continue
            
            metadata = extract_metadata_from_path(file_path, root)
            
            doc = Document(
                page_content=text,
                metadata=metadata,
            )
            documents.append(doc)
            logger.debug(f"Loaded: {metadata['relative_path']}")
            
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            continue
    
    logger.info(f"Successfully loaded {len(documents)} documents")
    return documents


def load_documents_by_category(
    category: str,
    root: Path = RAG_DATA_ROOT,
) -> List[Document]:
    """
    Load documents from a specific category.
    
    Args:
        category: Category folder name (e.g., "technology_guides").
        root: Root directory of the RAG corpus.
    
    Returns:
        List of LangChain Document objects from the specified category.
    """
    category_path = root / category
    if not category_path.exists():
        logger.warning(f"Category does not exist: {category_path}")
        return []
    
    documents: List[Document] = []
    md_files = sorted(category_path.rglob("*.md"))
    
    logger.info(f"Loading {len(md_files)} documents from category: {category}")
    
    for file_path in md_files:
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace").strip()
            if not text:
                continue
            
            metadata = extract_metadata_from_path(file_path, root)
            
            doc = Document(
                page_content=text,
                metadata=metadata,
            )
            documents.append(doc)
            
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            continue
    
    logger.info(f"Loaded {len(documents)} documents from category: {category}")
    return documents
