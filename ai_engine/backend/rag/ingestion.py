"""
RAG ingestion pipeline.

Orchestrates the full pipeline: load → metadata → chunk → embed → upload.
Includes progress tracking and detailed statistics reporting.
"""

import logging
import time
from typing import List, Optional
import uuid

from tqdm import tqdm
from qdrant_client.http.models import PointStruct

from .config import RAG_DATA_ROOT, VECTOR_STORE_BATCH_SIZE, ENABLE_PROGRESS_BAR
from .loader import load_documents, load_documents_by_category
from .chunker import chunk_documents
from .embeddings import embed_texts
from .qdrant_manager import QdrantManager


logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Orchestrates document ingestion into Qdrant with progress tracking.
    """
    
    def __init__(self, qdrant_manager: Optional[QdrantManager] = None):
        """
        Initialize the ingestion pipeline.
        
        Args:
            qdrant_manager: Qdrant manager instance (creates new if not provided).
        """
        self.manager = qdrant_manager or QdrantManager()
        self.stats = {
            "files_loaded": 0,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "vectors_uploaded": 0,
            "total_time": 0.0,
            "embedding_time": 0.0,
            "upload_time": 0.0,
        }
    
    def ingest_all(self, force_recreate: bool = False) -> dict:
        """
        Ingest all documents from the RAG corpus.
        
        Args:
            force_recreate: If True, delete and recreate the collection.
        
        Returns:
            Dictionary with ingestion statistics.
        """
        start_time = time.time()
        
        logger.info("Starting full ingestion pipeline")
        
        # Step 1: Create collection
        self.manager.create_collection(force_recreate=force_recreate)
        
        # Step 2: Load documents
        logger.info(f"Loading documents from {RAG_DATA_ROOT}")
        documents = load_documents(RAG_DATA_ROOT)
        self.stats["files_loaded"] = len(documents)
        
        if not documents:
            logger.warning("No documents loaded")
            return self.stats
        
        # Step 3: Chunk documents
        logger.info("Chunking documents")
        chunked_docs = chunk_documents(documents)
        self.stats["chunks_created"] = len(chunked_docs)
        
        # Step 4: Extract text for embedding
        chunk_texts = [doc.page_content for doc in chunked_docs]
        
        # Step 5: Generate embeddings
        logger.info(f"Generating embeddings for {len(chunk_texts)} chunks")
        embed_start = time.time()
        embeddings = embed_texts(
            chunk_texts,
            show_progress=ENABLE_PROGRESS_BAR,
        )
        embed_time = time.time() - embed_start
        self.stats["embedding_time"] = embed_time
        self.stats["embeddings_generated"] = len(embeddings)
        
        logger.info(f"Embedding completed in {embed_time:.2f}s")
        
        # Step 6: Build PointStruct objects
        logger.info("Building point structures for upload")
        points = []
        for idx, (doc, embedding) in enumerate(zip(chunked_docs, embeddings)):
            point = PointStruct(
                id=idx,
                vector=embedding,
                payload={
                    "text": doc.page_content,
                    **doc.metadata,
                },
            )
            points.append(point)
        
        # Step 7: Upload to Qdrant
        logger.info(f"Uploading {len(points)} vectors to Qdrant")
        upload_start = time.time()
        uploaded = self.manager.upsert_points(
            points,
            batch_size=VECTOR_STORE_BATCH_SIZE,
        )
        upload_time = time.time() - upload_start
        self.stats["upload_time"] = upload_time
        self.stats["vectors_uploaded"] = uploaded
        
        logger.info(f"Upload completed in {upload_time:.2f}s")
        
        # Final statistics
        self.stats["total_time"] = time.time() - start_time
        
        self._print_report()
        
        return self.stats
    
    def ingest_category(self, category: str, force_recreate: bool = False) -> dict:
        """
        Ingest documents from a specific category.
        
        Args:
            category: Category folder name.
            force_recreate: If True, recreate the collection.
        
        Returns:
            Dictionary with ingestion statistics.
        """
        start_time = time.time()
        
        logger.info(f"Starting category ingestion: {category}")
        
        # Create collection if needed
        if not self.manager.collection_exists():
            self.manager.create_collection(force_recreate=force_recreate)
        elif force_recreate:
            self.manager.create_collection(force_recreate=True)
        
        # Load category documents
        logger.info(f"Loading category: {category}")
        documents = load_documents_by_category(category, RAG_DATA_ROOT)
        self.stats["files_loaded"] = len(documents)
        
        if not documents:
            logger.warning(f"No documents in category: {category}")
            return self.stats
        
        # Chunk and embed
        chunked_docs = chunk_documents(documents)
        self.stats["chunks_created"] = len(chunked_docs)
        
        chunk_texts = [doc.page_content for doc in chunked_docs]
        
        embed_start = time.time()
        embeddings = embed_texts(chunk_texts, show_progress=ENABLE_PROGRESS_BAR)
        self.stats["embedding_time"] = time.time() - embed_start
        self.stats["embeddings_generated"] = len(embeddings)
        
        # Build and upload points
        points = []
        current_count = self.manager.count_vectors()
        
        for idx, (doc, embedding) in enumerate(zip(chunked_docs, embeddings)):
            point = PointStruct(
                id=current_count + idx,
                vector=embedding,
                payload={
                    "text": doc.page_content,
                    **doc.metadata,
                },
            )
            points.append(point)
        
        upload_start = time.time()
        uploaded = self.manager.upsert_points(points, batch_size=VECTOR_STORE_BATCH_SIZE)
        self.stats["upload_time"] = time.time() - upload_start
        self.stats["vectors_uploaded"] = uploaded
        
        self.stats["total_time"] = time.time() - start_time
        
        self._print_report()
        
        return self.stats
    
    def _print_report(self) -> None:
        """Print ingestion report to logger."""
        report = f"""
╔═══════════════════════════════════════════════════════════╗
║                  INGESTION REPORT                         ║
╠═══════════════════════════════════════════════════════════╣
║ Files Loaded              : {self.stats['files_loaded']:>6}               ║
║ Chunks Created            : {self.stats['chunks_created']:>6}               ║
║ Embeddings Generated      : {self.stats['embeddings_generated']:>6}               ║
║ Vectors Uploaded          : {self.stats['vectors_uploaded']:>6}               ║
╠═══════════════════════════════════════════════════════════╣
║ Embedding Time            : {self.stats['embedding_time']:>6.2f}s              ║
║ Upload Time               : {self.stats['upload_time']:>6.2f}s              ║
║ Total Time                : {self.stats['total_time']:>6.2f}s              ║
╠═══════════════════════════════════════════════════════════╣
║ Collection Statistics     :                               ║
"""
        
        try:
            stats = self.manager.get_statistics()
            report += f"║ - Total Vectors           : {stats['points_count']:>6}               ║\n"
        except Exception as e:
            logger.debug(f"Could not fetch collection stats: {e}")
        
        report += "╚═══════════════════════════════════════════════════════════╝"
        
        logger.info(report)
