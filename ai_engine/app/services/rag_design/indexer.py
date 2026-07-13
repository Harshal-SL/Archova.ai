from __future__ import annotations

import hashlib
from pathlib import Path

import chromadb
import requests

from .langchain_compat import Document


class ChromaDocumentIndex:
    def __init__(
        self,
        persist_dir: Path,
        collection_name: str,
        ollama_base_url: str,
        embedding_model: str,
        timeout_seconds: int,
    ) -> None:
        self._persist_dir = persist_dir
        self._persist_dir.mkdir(parents=True, exist_ok=True)

        self._collection_name = collection_name
        self._ollama_base_url = ollama_base_url.rstrip("/")
        self._embedding_model = embedding_model
        self._timeout_seconds = timeout_seconds

        self._client = chromadb.PersistentClient(path=str(self._persist_dir))
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        return int(self._collection.count())

    def reset_collection(self) -> None:
        try:
            self._client.delete_collection(name=self._collection_name)
        except Exception:
            pass

        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def index_documents(self, documents: list, batch_size: int = 32) -> int:
        if not documents:
            return 0

        indexed = 0
        for start in range(0, len(documents), batch_size):
            batch = documents[start : start + batch_size]
            indexed += self._upsert_batch(batch)

        return indexed

    def _upsert_batch(self, documents: list) -> int:
        rows = []
        for idx, doc in enumerate(documents):
            text = (doc.page_content or "").strip()
            if not text:
                continue

            metadata = self._normalize_metadata(doc.metadata or {})
            source_path = str(metadata.get("source_path", "unknown"))
            chunk_index = str(metadata.get("chunk_index", idx))
            row_id = hashlib.sha1(f"{source_path}:{chunk_index}:{idx}".encode("utf-8")).hexdigest()

            rows.append((row_id, text, metadata))

        if not rows:
            return 0

        ids = [row[0] for row in rows]
        texts = [row[1] for row in rows]
        metadatas = [row[2] for row in rows]
        embeddings = self._embed_texts(texts)

        self._collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )

        return len(rows)

    def query(self, query_text: str, n_results: int) -> list[dict]:
        if self.count() == 0:
            return []

        query_embedding = self._embed_texts([query_text])[0]
        response = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=max(1, n_results),
            include=["documents", "metadatas", "distances"],
        )

        documents = (response.get("documents") or [[]])[0]
        metadatas = (response.get("metadatas") or [[]])[0]
        distances = (response.get("distances") or [[]])[0]

        rows = []
        for doc, metadata, distance in zip(documents, metadatas, distances):
            safe_distance = float(distance if distance is not None else 1.0)
            similarity = 1.0 / (1.0 + max(0.0, safe_distance))
            rows.append(
                {
                    "text": doc or "",
                    "metadata": metadata or {},
                    "distance": safe_distance,
                    "similarity": similarity,
                }
            )

        return rows

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        batch_embeddings = self._try_embed_batch(texts)
        if batch_embeddings is not None:
            return batch_embeddings

        return self._embed_one_by_one(texts)

    def _try_embed_batch(self, texts: list[str]) -> list[list[float]] | None:
        embed_url = f"{self._ollama_base_url}/api/embed"
        payload = {"model": self._embedding_model, "input": texts}

        try:
            response = requests.post(embed_url, json=payload, timeout=self._timeout_seconds)
            if response.status_code >= 400:
                return None

            body = response.json()
            embeddings = body.get("embeddings")
            if isinstance(embeddings, list) and embeddings and isinstance(embeddings[0], list):
                return embeddings

            data = body.get("data")
            if isinstance(data, list):
                vectors = [item.get("embedding") for item in data if isinstance(item, dict)]
                if vectors and all(isinstance(vector, list) for vector in vectors):
                    return vectors
        except Exception:
            return None

        return None

    def _embed_one_by_one(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        embed_url = f"{self._ollama_base_url}/api/embeddings"

        for text in texts:
            payload = {"model": self._embedding_model, "prompt": text}
            response = requests.post(embed_url, json=payload, timeout=self._timeout_seconds)
            response.raise_for_status()
            body = response.json()

            vector = body.get("embedding")
            if not isinstance(vector, list):
                raise RuntimeError("Ollama embeddings response did not contain a valid 'embedding' vector.")

            embeddings.append(vector)

        return embeddings

    @staticmethod
    def _normalize_metadata(metadata: dict) -> dict:
        normalized = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                normalized[key] = value
            else:
                normalized[key] = str(value)
        return normalized
