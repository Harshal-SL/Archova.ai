"""
Production-grade RAG retriever.

Pipeline (per query plan):
  1. Embed all queries concurrently  (query expansion)
  2. Search Qdrant per query  (category-filtered, fetches FETCH_K each)
  3. Merge results, deduplicate by chunk id
  4. Apply Max Marginal Relevance (MMR) for relevance + diversity
  5. Enforce per-document chunk cap  (MAX_CHUNKS_PER_DOCUMENT)
  6. Optional reranking with BAAI/bge-reranker-base
  7. Return top-K hits with a retrieval report
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .config import (
    ENABLE_RERANKING,
    FETCH_K,
    MAX_CHUNKS_PER_DOCUMENT,
    MMR_LAMBDA,
    RERANKER_MODEL,
    RERANKER_TOP_K,
    SIMILARITY_THRESHOLD,
    TOP_K,
)
from .embeddings import embed_text, embed_texts, get_embedder
from .qdrant_manager import QdrantManager
from .query_builder import QueryPlan


logger = logging.getLogger(__name__)


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class RetrievalHit:
    """Single retrieval result enriched with reranker score."""

    id: int
    text: str
    score: float                      # cosine similarity from Qdrant
    metadata: Dict[str, Any]
    reranker_score: Optional[float] = None   # set when reranking is enabled

    @property
    def final_score(self) -> float:
        """Reranker score when available, otherwise cosine score."""
        return self.reranker_score if self.reranker_score is not None else self.score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "score": self.score,
            "reranker_score": self.reranker_score,
            "metadata": self.metadata,
        }


@dataclass
class RetrievalReport:
    """Diagnostic report attached to every retrieval result."""

    query: str
    expanded_queries: List[str]
    detected_intents: List[str]
    target_categories: List[str]
    raw_candidates: int          # after merge + dedup
    after_mmr: int
    after_diversity: int
    after_reranking: int
    final_count: int
    chunks_per_document: Dict[str, int] = field(default_factory=dict)
    duplicates_removed: int = 0
    context_chars: int = 0

    def print(self) -> None:
        """Pretty-print the retrieval report."""
        w = 64
        sep = "─" * w
        print(f"\n{'═' * w}")
        print("  RETRIEVAL REPORT")
        print(f"{'═' * w}")
        print(f"  Query          : {self.query[:70]}")
        print(f"  Intents        : {', '.join(self.detected_intents)}")
        print(f"  Categories     : {len(self.target_categories)}")
        for cat in self.target_categories:
            print(f"                   · {cat}")
        print(f"  Expansions     : {len(self.expanded_queries)}")
        for q in self.expanded_queries:
            print(f"                   · {q[:60]}")
        print(sep)
        print(f"  Raw candidates : {self.raw_candidates}")
        print(f"  Duplicates rm  : {self.duplicates_removed}")
        print(f"  After MMR      : {self.after_mmr}")
        print(f"  After diversity: {self.after_diversity}")
        print(f"  After reranking: {self.after_reranking}")
        print(f"  Final hits     : {self.final_count}")
        print(sep)
        print("  Chunks per document:")
        for src, cnt in sorted(self.chunks_per_document.items(), key=lambda x: -x[1]):
            print(f"    {cnt:>3}  {src}")
        print(f"{'═' * w}\n")


# ── Reranker (optional) ───────────────────────────────────────────────────────

_reranker = None


def _get_reranker():
    """Lazy-load the cross-encoder reranker model."""
    global _reranker
    if _reranker is not None:
        return _reranker
    try:
        from sentence_transformers import CrossEncoder
        import logging as _log
        _log.getLogger("sentence_transformers").setLevel(_log.ERROR)
        _log.getLogger("transformers").setLevel(_log.ERROR)
        logger.info(f"Loading reranker model: {RERANKER_MODEL}")
        _reranker = CrossEncoder(RERANKER_MODEL)
        logger.info("Reranker loaded.")
        return _reranker
    except Exception as exc:
        logger.warning(f"Cannot load reranker '{RERANKER_MODEL}': {exc}. Reranking disabled.")
        return None


def _rerank(query: str, hits: List[RetrievalHit]) -> List[RetrievalHit]:
    """
    Score hits with a cross-encoder and re-sort.

    Returns the same hits with reranker_score set, sorted descending.
    """
    reranker = _get_reranker()
    if reranker is None:
        return hits

    pairs = [(query, h.text) for h in hits]
    try:
        scores = reranker.predict(pairs)
        for hit, sc in zip(hits, scores):
            hit.reranker_score = float(sc)
        return sorted(hits, key=lambda h: h.reranker_score, reverse=True)  # type: ignore[arg-type]
    except Exception as exc:
        logger.warning(f"Reranking failed: {exc}. Falling back to cosine scores.")
        return hits


# ── MMR ───────────────────────────────────────────────────────────────────────

def _cosine_sim(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _mmr(
    query_vec: List[float],
    candidate_vecs: List[List[float]],
    candidate_hits: List[RetrievalHit],
    top_k: int,
    lambda_: float,
) -> List[RetrievalHit]:
    """
    Max Marginal Relevance selection.

    Selects *top_k* hits that maximise:
        lambda * similarity(query, doc) - (1-lambda) * max_similarity(doc, selected)

    Args:
        query_vec: Embedded query vector.
        candidate_vecs: Embeddings of candidate hits.
        candidate_hits: Corresponding RetrievalHit objects.
        top_k: Number of hits to select.
        lambda_: Trade-off weight (1=pure relevance, 0=pure diversity).

    Returns:
        Diverse list of up to *top_k* RetrievalHit objects.
    """
    if not candidate_hits:
        return []

    remaining = list(range(len(candidate_hits)))
    selected_indices: List[int] = []

    for _ in range(min(top_k, len(candidate_hits))):
        best_idx = -1
        best_score = float("-inf")

        for idx in remaining:
            relevance = _cosine_sim(query_vec, candidate_vecs[idx])

            if not selected_indices:
                redundancy = 0.0
            else:
                redundancy = max(
                    _cosine_sim(candidate_vecs[idx], candidate_vecs[sel])
                    for sel in selected_indices
                )

            mmr_score = lambda_ * relevance - (1 - lambda_) * redundancy

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        if best_idx == -1:
            break

        selected_indices.append(best_idx)
        remaining.remove(best_idx)

    return [candidate_hits[i] for i in selected_indices]


# ── Per-document diversity cap ────────────────────────────────────────────────

def _apply_diversity_cap(
    hits: List[RetrievalHit],
    max_per_doc: int,
) -> List[RetrievalHit]:
    """
    Allow at most *max_per_doc* chunks from the same source_file.

    Preserves original ordering so the highest-scoring chunks are kept.
    """
    doc_counts: Dict[str, int] = {}
    filtered: List[RetrievalHit] = []

    for hit in hits:
        src = hit.metadata.get("source_file", hit.metadata.get("relative_path", "unknown"))
        count = doc_counts.get(src, 0)
        if count < max_per_doc:
            filtered.append(hit)
            doc_counts[src] = count + 1

    removed = len(hits) - len(filtered)
    if removed:
        logger.debug(f"Diversity cap: removed {removed} excess chunks")

    return filtered


# ── Main retriever ────────────────────────────────────────────────────────────

class RAGRetriever:
    """
    Production-grade retriever with query expansion, MMR, diversity cap,
    and optional cross-encoder reranking.
    """

    def __init__(
        self,
        qdrant_manager: Optional[QdrantManager] = None,
        top_k: int = TOP_K,
        fetch_k: int = FETCH_K,
        threshold: float = SIMILARITY_THRESHOLD,
        mmr_lambda: float = MMR_LAMBDA,
        max_chunks_per_doc: int = MAX_CHUNKS_PER_DOCUMENT,
        enable_reranking: bool = ENABLE_RERANKING,
        reranker_top_k: int = RERANKER_TOP_K,
    ) -> None:
        """
        Initialise the retriever.

        Args:
            qdrant_manager: Qdrant manager instance.
            top_k: Final number of hits to return.
            fetch_k: Candidates fetched per query before filtering.
            threshold: Minimum cosine similarity to include a hit.
            mmr_lambda: MMR relevance/diversity trade-off (0–1).
            max_chunks_per_doc: Max chunks from the same source file.
            enable_reranking: Whether to apply cross-encoder reranking.
            reranker_top_k: How many hits to keep after reranking.
        """
        self.manager = qdrant_manager or QdrantManager()
        self.top_k = top_k
        self.fetch_k = fetch_k
        self.threshold = threshold
        self.mmr_lambda = mmr_lambda
        self.max_chunks_per_doc = max_chunks_per_doc
        self.enable_reranking = enable_reranking
        self.reranker_top_k = reranker_top_k

    # ── Public API ────────────────────────────────────────────────────────────

    def retrieve_from_plan(
        self,
        plan: QueryPlan,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
        print_report: bool = False,
    ) -> tuple[List[RetrievalHit], RetrievalReport]:
        """
        Full retrieval pipeline driven by a QueryPlan.

        Args:
            plan: QueryPlan from QueryBuilder.
            top_k: Override default top_k.
            threshold: Override default threshold.
            print_report: If True, print the retrieval report to stdout.

        Returns:
            (hits, report) tuple.
        """
        k = top_k or self.top_k
        thr = threshold if threshold is not None else self.threshold

        # ── Step 1: embed all queries concurrently ────────────────────────────
        all_queries = plan.all_queries
        query_vecs = self._embed_queries_concurrent(all_queries)

        # ── Step 2: search Qdrant for each (query, category) pair ────────────
        raw_hits = self._search_all(
            queries=all_queries,
            query_vecs=query_vecs,
            categories=plan.target_categories,
            fetch_k=self.fetch_k,
            threshold=thr,
        )

        # ── Step 3: merge + deduplicate by point id ───────────────────────────
        merged, n_dupes = _dedup(raw_hits)
        logger.info(f"Merged {len(raw_hits)} → {len(merged)} unique hits")

        # ── Step 4: MMR (relevance + diversity via text embeddings) ───────────
        # Only run full MMR if candidate count is manageable.
        # For large pools, skip re-embedding and rely on diversity cap instead.
        MMR_EMBED_LIMIT = 40   # never re-embed more than this many chunks
        if len(merged) > k and len(merged) <= MMR_EMBED_LIMIT:
            primary_vec = query_vecs[0]
            candidate_vecs = self._embed_texts_for_mmr(merged)
            mmr_hits = _mmr(
                query_vec=primary_vec,
                candidate_vecs=candidate_vecs,
                candidate_hits=merged,
                top_k=min(k * 3, len(merged)),
                lambda_=self.mmr_lambda,
            )
        else:
            # Skip MMR re-embedding — scores are already sorted by cosine sim.
            # Diversity cap in Step 5 handles document-level redundancy.
            mmr_hits = merged[: k * 3]

        # ── Step 5: diversity cap ─────────────────────────────────────────────
        diverse_hits = _apply_diversity_cap(mmr_hits, self.max_chunks_per_doc)

        # ── Step 6: reranking (optional) ─────────────────────────────────────
        if self.enable_reranking and diverse_hits:
            reranked = _rerank(plan.primary_query, diverse_hits)
            reranked = reranked[: self.reranker_top_k]
        else:
            reranked = diverse_hits

        # ── Step 7: final top-K ───────────────────────────────────────────────
        final = sorted(reranked, key=lambda h: h.final_score, reverse=True)[:k]

        # ── Build report ──────────────────────────────────────────────────────
        doc_counts: Dict[str, int] = {}
        for h in final:
            src = h.metadata.get("source_file", "?")
            doc_counts[src] = doc_counts.get(src, 0) + 1

        report = RetrievalReport(
            query=plan.primary_query,
            expanded_queries=plan.expanded_queries,
            detected_intents=plan.detected_intents,
            target_categories=plan.target_categories,
            raw_candidates=len(merged),
            after_mmr=len(mmr_hits),
            after_diversity=len(diverse_hits),
            after_reranking=len(reranked),
            final_count=len(final),
            chunks_per_document=doc_counts,
            duplicates_removed=n_dupes,
        )

        if print_report:
            report.print()

        logger.info(
            f"retrieve_from_plan: {len(final)} hits "
            f"from {len(doc_counts)} distinct documents"
        )
        return final, report

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
        category_filter: Optional[str] = None,
        domain_filter: Optional[str] = None,
    ) -> List[RetrievalHit]:
        """
        Simple retrieval for a single query string.

        Used by rag_query.py and design_service.py for backward compatibility.

        Args:
            query: Query text.
            top_k: Maximum results.
            threshold: Minimum similarity score.
            category_filter: Restrict to one category.
            domain_filter: Restrict to one domain.

        Returns:
            List of RetrievalHit objects sorted by final_score.
        """
        from .query_builder import QueryBuilder  # avoid circular at module level

        plan = QueryBuilder.plan(query)

        # If a specific filter was requested, restrict categories
        if category_filter:
            plan.target_categories = [category_filter]
            plan.expanded_queries = []
        elif domain_filter:
            # domain filtering is not a Qdrant category — apply post-filter
            pass

        hits, _ = self.retrieve_from_plan(
            plan,
            top_k=top_k or self.top_k,
            threshold=threshold,
        )

        if domain_filter:
            hits = [h for h in hits if h.metadata.get("domain") == domain_filter]

        return hits

    def retrieve_by_category(
        self,
        query: str,
        categories: List[str],
        top_k: int = TOP_K,
        threshold: float = SIMILARITY_THRESHOLD,
    ) -> Dict[str, List[RetrievalHit]]:
        """
        Retrieve hits grouped by category.

        Kept for backward compatibility with design_service.py.
        """
        query_vec = embed_text(query)

        results: Dict[str, List[RetrievalHit]] = {}
        for category in categories:
            raw = self.manager.search(
                query_vector=query_vec,
                limit=top_k * 2,
                filter_dict={"category": category},
            )
            hits = [
                RetrievalHit(
                    id=r["id"],
                    text=r["payload"].pop("text", ""),
                    score=r["score"],
                    metadata=r["payload"],
                )
                for r in raw
                if r["score"] >= threshold
            ][:top_k]
            results[category] = hits

        return results

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _embed_queries_concurrent(self, queries: List[str]) -> List[List[float]]:
        """Embed multiple queries.  Batches them in one SentenceTransformer call."""
        try:
            vecs = embed_texts(queries, show_progress=False)
            return vecs
        except Exception as exc:
            logger.warning(f"Batch embedding failed ({exc}), falling back to sequential.")
            return [embed_text(q) for q in queries]

    def _embed_texts_for_mmr(self, hits: List[RetrievalHit]) -> List[List[float]]:
        """Embed hit texts for MMR.  Uses single batch call."""
        texts = [h.text for h in hits]
        try:
            return embed_texts(texts, show_progress=False)
        except Exception as exc:
            logger.warning(f"MMR embedding failed: {exc}")
            # Fallback: return zero-vectors — MMR degrades to top-K by score
            dim = get_embedder().get_sentence_embedding_dimension()
            return [[0.0] * dim for _ in hits]

    def _search_all(
        self,
        queries: List[str],
        query_vecs: List[List[float]],
        categories: List[str],
        fetch_k: int,
        threshold: float,
    ) -> List[RetrievalHit]:
        """
        Run one search per query vector sequentially.

        We search globally (no per-category filter) and post-filter by the
        allowed category set.  This avoids the N×M fan-out that causes lock
        contention on local Qdrant storage.

        Args:
            queries: Query strings (for logging).
            query_vecs: One embedding per query.
            categories: Allowed category names (empty = no filter).
            fetch_k: Candidates to fetch per query.
            threshold: Minimum cosine similarity.

        Returns:
            Flat, unsorted list of RetrievalHit objects.
        """
        category_set = set(categories)
        all_hits: List[RetrievalHit] = []

        for i, (query, vec) in enumerate(zip(queries, query_vecs)):
            try:
                raw = self.manager.search(
                    query_vector=vec,
                    limit=fetch_k,
                    filter_dict=None,   # global search — post-filter below
                )
            except Exception as exc:
                logger.warning(f"Search failed for query[{i}] '{query[:40]}': {exc}")
                continue

            for r in raw:
                if r["score"] < threshold:
                    continue
                payload = dict(r["payload"])
                cat = payload.get("category", "")
                if category_set and cat not in category_set:
                    continue
                text = payload.pop("text", "")
                all_hits.append(RetrievalHit(
                    id=r["id"],
                    text=text,
                    score=r["score"],
                    metadata=payload,
                ))

            logger.debug(
                f"Query[{i}] '{query[:40]}' → "
                f"{len([r for r in raw if r['score'] >= threshold])} raw hits"
            )

        return all_hits


# ── Helpers ────────────────────────────────────────────────────────────────────

def _dedup(hits: List[RetrievalHit]) -> tuple[List[RetrievalHit], int]:
    """
    Deduplicate by point id, keeping the highest-scoring instance.

    Returns (unique_hits_sorted_by_score, n_duplicates_removed).
    """
    best: Dict[int, RetrievalHit] = {}
    for hit in hits:
        existing = best.get(hit.id)
        if existing is None or hit.score > existing.score:
            best[hit.id] = hit

    unique = sorted(best.values(), key=lambda h: h.score, reverse=True)
    return unique, len(hits) - len(unique)
