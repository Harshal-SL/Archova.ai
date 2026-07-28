"""
Qdrant vector store management.

Handles collection lifecycle: creation, deletion, querying, and statistics.
Uses the qdrant-client v1.x API (query_points instead of the removed search()).

Connection strategy (tried in order):
  1. Remote Qdrant server at QDRANT_URL  (if reachable within 3 s)
  2. Local on-disk Qdrant at QDRANT_LOCAL_PATH  (no server required)
"""

import atexit
import logging
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from .config import (
    COLLECTION_NAME,
    DISTANCE_METRIC,
    EMBEDDING_MODEL,
    QDRANT_LOCAL_PATH,
    QDRANT_URL,
)
from .embeddings import get_embedding_dimension


logger = logging.getLogger(__name__)

_DISTANCE_MAP: Dict[str, Distance] = {
    "Cosine": Distance.COSINE,
    "Euclidean": Distance.EUCLID,
    "DotProduct": Distance.DOT,
}


def _try_remote(url: str) -> Optional[QdrantClient]:
    """
    Attempt to connect to a remote Qdrant server.

    Returns a connected QdrantClient, or None if the server is unreachable.
    The version-compatibility warning is suppressed to keep output clean.
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = QdrantClient(url=url, check_compatibility=False, timeout=3)
            client.get_collections()          # real round-trip to confirm server is up
        logger.info(f"Connected to remote Qdrant at {url}")
        return client
    except Exception as exc:
        logger.debug(f"Remote Qdrant at {url} not reachable: {exc}")
        return None


def _open_local(path: str) -> QdrantClient:
    """
    Open (or create) a local on-disk Qdrant database.

    Data is persisted under *path* across runs. No external server required.
    """
    Path(path).mkdir(parents=True, exist_ok=True)
    client = QdrantClient(path=path)
    logger.info(f"Using local Qdrant storage at {path}")
    return client


class QdrantManager:
    """
    Manages Qdrant vector store operations with automatic remote/local selection.

    All search operations use the v1.x query_points() API.
    """

    def __init__(
        self,
        url: str = QDRANT_URL,
        collection_name: str = COLLECTION_NAME,
        local_path: str = QDRANT_LOCAL_PATH,
    ) -> None:
        """
        Initialise the manager.

        Args:
            url: Remote Qdrant server URL (tried first).
            collection_name: Name of the vector collection.
            local_path: Fallback on-disk storage directory.

        Raises:
            RuntimeError: If both remote and local modes fail.
        """
        self.collection_name = collection_name
        self.url = url
        self.local_path = local_path
        self.is_local = False

        client = _try_remote(url)
        if client is not None:
            self.client: QdrantClient = client
        else:
            logger.warning(
                f"Remote Qdrant not available at {url}. "
                f"Falling back to local storage: {local_path}"
            )
            try:
                self.client = _open_local(local_path)
                self.is_local = True
            except Exception as exc:
                raise RuntimeError(
                    f"Cannot initialise Qdrant "
                    f"(remote={url}, local={local_path}): {exc}"
                ) from exc

        # Ensure the client is closed cleanly before Python tears down,
        # preventing the portalocker/msvcrt teardown error on Windows.
        atexit.register(self._close)

    def _close(self) -> None:
        """Explicitly close the Qdrant client to release file locks before exit."""
        try:
            self.client.close()
        except Exception:
            pass

    # ── Collection lifecycle ──────────────────────────────────────────────────

    def collection_exists(self) -> bool:
        """Return True if the collection exists."""
        try:
            self.client.get_collection(self.collection_name)
            return True
        except Exception:
            return False

    def create_collection(self, force_recreate: bool = False) -> None:
        """
        Create the vector collection.

        Args:
            force_recreate: Delete and recreate when collection already exists.

        Raises:
            RuntimeError: If creation fails.
        """
        try:
            if self.collection_exists():
                if force_recreate:
                    logger.info(f"Deleting existing collection: {self.collection_name}")
                    self.delete_collection()
                else:
                    logger.info(f"Collection already exists: {self.collection_name}")
                    return

            dim = get_embedding_dimension()
            distance = _DISTANCE_MAP.get(DISTANCE_METRIC, Distance.COSINE)

            logger.info(
                f"Creating collection '{self.collection_name}' "
                f"(dim={dim}, distance={DISTANCE_METRIC})"
            )
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=dim, distance=distance),
            )
            logger.info(f"Collection '{self.collection_name}' created.")

        except Exception as exc:
            logger.error(f"Failed to create collection: {exc}")
            raise RuntimeError(f"Cannot create collection: {exc}") from exc

    def delete_collection(self) -> None:
        """
        Delete the vector collection.

        Raises:
            RuntimeError: If deletion fails.
        """
        try:
            if not self.collection_exists():
                logger.warning(f"Collection does not exist: {self.collection_name}")
                return
            self.client.delete_collection(self.collection_name)
            logger.info(f"Collection '{self.collection_name}' deleted.")
        except Exception as exc:
            logger.error(f"Failed to delete collection: {exc}")
            raise RuntimeError(f"Cannot delete collection: {exc}") from exc

    # ── Statistics ────────────────────────────────────────────────────────────

    def count_vectors(self) -> int:
        """
        Return the number of vectors in the collection.

        Raises:
            RuntimeError: If the collection does not exist.
        """
        if not self.collection_exists():
            raise RuntimeError(f"Collection does not exist: {self.collection_name}")
        try:
            return self.client.get_collection(self.collection_name).points_count or 0
        except Exception as exc:
            logger.error(f"Failed to count vectors: {exc}")
            raise

    def get_statistics(self) -> Dict[str, Any]:
        """
        Return collection statistics.

        Raises:
            RuntimeError: If the collection does not exist.
        """
        if not self.collection_exists():
            raise RuntimeError(f"Collection does not exist: {self.collection_name}")
        try:
            col = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "points_count": col.points_count or 0,
                "vectors_count": col.vectors_count or 0,
                "indexed_vectors_count": col.indexed_vectors_count or 0,
                "embedding_model": EMBEDDING_MODEL,
                "distance_metric": DISTANCE_METRIC,
                "mode": "local" if self.is_local else "remote",
                "storage": self.local_path if self.is_local else self.url,
            }
        except Exception as exc:
            logger.error(f"Failed to get statistics: {exc}")
            raise

    # ── Write ─────────────────────────────────────────────────────────────────

    def upsert_points(
        self,
        points: List[PointStruct],
        batch_size: int = 64,
    ) -> int:
        """
        Upsert points into the collection in batches.

        Args:
            points: PointStruct objects to upsert.
            batch_size: Points per upload batch.

        Returns:
            Total number of points upserted.

        Raises:
            RuntimeError: If upsert fails.
        """
        if not self.collection_exists():
            raise RuntimeError(f"Collection does not exist: {self.collection_name}")
        if not points:
            logger.warning("No points to upsert.")
            return 0

        try:
            total = 0
            for i in range(0, len(points), batch_size):
                batch = points[i : i + batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch,
                )
                total += len(batch)
                logger.debug(f"Upserted {total}/{len(points)} points")
            logger.info(f"Upserted {total} points successfully.")
            return total
        except Exception as exc:
            logger.error(f"Failed to upsert points: {exc}")
            raise RuntimeError(f"Cannot upsert points: {exc}") from exc

    # ── Search ────────────────────────────────────────────────────────────────

    def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors using the v1.x query_points() API.

        Args:
            query_vector: Query embedding vector.
            limit: Maximum results to return.
            score_threshold: Minimum similarity score passed to Qdrant directly.
            filter_dict: Optional payload field filters {field: exact_value}.

        Returns:
            List of dicts with keys ``id``, ``score``, ``payload``.

        Raises:
            RuntimeError: If the collection does not exist or search fails.
        """
        if not self.collection_exists():
            raise RuntimeError(f"Collection does not exist: {self.collection_name}")

        try:
            # Build metadata filter
            query_filter: Optional[Filter] = None
            if filter_dict:
                conditions = [
                    FieldCondition(key=k, match=MatchValue(value=v))
                    for k, v in filter_dict.items()
                ]
                query_filter = Filter(must=conditions)

            # query_points() replaced search() in qdrant-client v1.x
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False,
                score_threshold=score_threshold,
            )

            hits = [
                {
                    "id": point.id,
                    "score": point.score,
                    "payload": point.payload or {},
                }
                for point in response.points
            ]
            logger.debug(f"query_points returned {len(hits)} results.")
            return hits

        except Exception as exc:
            logger.error(f"Search failed: {exc}")
            raise RuntimeError(f"Cannot search: {exc}") from exc

    # ── Delete points ─────────────────────────────────────────────────────────

    def delete_points(self, point_ids: List[int]) -> int:
        """
        Delete specific points from the collection.

        Args:
            point_ids: IDs of points to delete.

        Returns:
            Number of points deleted.

        Raises:
            RuntimeError: If deletion fails.
        """
        if not self.collection_exists():
            raise RuntimeError(f"Collection does not exist: {self.collection_name}")
        if not point_ids:
            return 0
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=point_ids,
            )
            logger.info(f"Deleted {len(point_ids)} points.")
            return len(point_ids)
        except Exception as exc:
            logger.error(f"Failed to delete points: {exc}")
            raise RuntimeError(f"Cannot delete points: {exc}") from exc
