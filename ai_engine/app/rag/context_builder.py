"""
Context assembly for LLM prompt feeding.

Responsibilities:
  - Deduplicate chunks by text fingerprint
  - Sort by reranker score (or cosine score as fallback)
  - Group sections by category for readable LLM context
  - Enforce character / token budget
  - Produce plain-text context strings ready for prompt injection
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Optional

from .retriever import RetrievalHit


logger = logging.getLogger(__name__)

# Rough token estimate used for budget enforcement (chars ÷ CHARS_PER_TOKEN)
_CHARS_PER_TOKEN = 4


class ContextBuilder:
    """
    Assembles RetrievalHit objects into an LLM-ready context string.

    Features:
      - Text-level deduplication (SHA-1 of stripped, lowercased content)
      - Sorted by ``hit.final_score``  (reranker score when available)
      - Optional category grouping for structured context
      - Hard character / token budget
    """

    def __init__(
        self,
        max_tokens: int = 3000,
        max_chars: Optional[int] = None,
    ) -> None:
        """
        Args:
            max_tokens: Approximate token budget (1 token ≈ 4 chars).
            max_chars: Hard character limit (overrides max_tokens when set).
        """
        self.max_tokens = max_tokens
        self.max_chars = max_chars if max_chars is not None else max_tokens * _CHARS_PER_TOKEN

    # ── Primary methods ───────────────────────────────────────────────────────

    def build_context(self, hits: List[RetrievalHit]) -> str:
        """
        Build a flat context string from retrieved hits.

        Hits are deduplicated, sorted by score, and truncated to the
        character budget.  Each section includes a lightweight metadata
        header so the LLM understands the source.

        Args:
            hits: RetrievalHit objects (any order).

        Returns:
            Context string ready for prompt injection.
        """
        unique = _dedup_by_text(hits)
        sorted_hits = sorted(unique, key=lambda h: h.final_score, reverse=True)

        sections: List[str] = []
        total_chars = 0

        for hit in sorted_hits:
            header = _format_header(hit.metadata, hit.final_score)
            section = f"{header}\n\n{hit.text.strip()}\n\n---\n\n"
            if total_chars + len(section) > self.max_chars:
                logger.debug(
                    f"Context budget reached at {total_chars} chars "
                    f"({len(sections)} sections)"
                )
                break
            sections.append(section)
            total_chars += len(section)

        context = "".join(sections).rstrip()
        logger.info(
            f"Context: {len(sections)} sections, {total_chars} chars "
            f"(≈{total_chars // _CHARS_PER_TOKEN} tokens)"
        )
        return context

    def build_grouped_context(self, hits: List[RetrievalHit]) -> str:
        """
        Build a context string where chunks are grouped by category.

        Within each category, chunks are sorted by score.  The category
        order follows score of the top chunk in that category, so the
        most relevant category appears first.

        Args:
            hits: RetrievalHit objects (any order).

        Returns:
            Grouped context string.
        """
        unique = _dedup_by_text(hits)

        # Group by category
        groups: Dict[str, List[RetrievalHit]] = {}
        for hit in unique:
            cat = hit.metadata.get("category", "general")
            groups.setdefault(cat, []).append(hit)

        # Sort each group by score
        for cat in groups:
            groups[cat].sort(key=lambda h: h.final_score, reverse=True)

        # Order categories by their best hit score
        cat_order = sorted(
            groups.keys(),
            key=lambda c: groups[c][0].final_score,
            reverse=True,
        )

        sections: List[str] = []
        total_chars = 0

        for cat in cat_order:
            cat_header = f"## {cat.replace('_', ' ').title()}\n\n"
            if total_chars + len(cat_header) > self.max_chars:
                break
            sections.append(cat_header)
            total_chars += len(cat_header)

            for hit in groups[cat]:
                header = _format_header(hit.metadata, hit.final_score)
                section = f"{header}\n\n{hit.text.strip()}\n\n"
                if total_chars + len(section) > self.max_chars:
                    logger.debug("Context budget reached (grouped mode)")
                    return "".join(sections).rstrip()
                sections.append(section)
                total_chars += len(section)

            sections.append("---\n\n")
            total_chars += 5

        return "".join(sections).rstrip()

    def build_context_with_sources(
        self, hits: List[RetrievalHit]
    ) -> Dict[str, Any]:
        """
        Build context plus a structured source list.

        Returns:
            Dict with keys: ``context``, ``sources``, ``char_count``, ``hit_count``.
        """
        context = self.build_context(hits)
        unique = _dedup_by_text(hits)
        sorted_hits = sorted(unique, key=lambda h: h.final_score, reverse=True)

        sources = [
            {
                "title": h.metadata.get("title", "Unknown"),
                "category": h.metadata.get("category", "Unknown"),
                "relative_path": h.metadata.get("relative_path", "Unknown"),
                "score": round(h.final_score, 4),
            }
            for h in sorted_hits[:8]
        ]

        return {
            "context": context,
            "sources": sources,
            "char_count": len(context),
            "hit_count": len(hits),
        }

    def build_tiered_context(
        self,
        hits: List[RetrievalHit],
        tier_sizes: Optional[Dict[str, int]] = None,
    ) -> Dict[str, str]:
        """
        Split hits into high / medium / low relevance tiers.

        Useful when different prompt sections need different context densities.

        Args:
            hits: Sorted retrieval hits.
            tier_sizes: Dict with keys 'high', 'medium', 'low' (counts).

        Returns:
            Dict with 'high_relevance', 'medium_relevance', 'low_relevance' keys.
        """
        if tier_sizes is None:
            tier_sizes = {"high": 3, "medium": 5, "low": 10}

        sorted_hits = sorted(hits, key=lambda h: h.final_score, reverse=True)

        h = tier_sizes["high"]
        m = tier_sizes["medium"]

        return {
            "high_relevance": self.build_context(sorted_hits[:h]),
            "medium_relevance": self.build_context(sorted_hits[h: h + m]),
            "low_relevance": self.build_context(sorted_hits[h + m: h + m + tier_sizes["low"]]),
        }


# ── Helpers ────────────────────────────────────────────────────────────────────

def _text_fingerprint(text: str) -> str:
    """SHA-1 of stripped, lower-cased text for deduplication."""
    return hashlib.sha1(text.strip().lower().encode("utf-8")).hexdigest()


def _dedup_by_text(hits: List[RetrievalHit]) -> List[RetrievalHit]:
    """Remove hits with duplicate text, keeping the highest-scoring instance."""
    seen: Dict[str, float] = {}       # fingerprint → best score
    best: Dict[str, RetrievalHit] = {}

    for hit in hits:
        fp = _text_fingerprint(hit.text)
        if fp not in seen or hit.final_score > seen[fp]:
            seen[fp] = hit.final_score
            best[fp] = hit

    return list(best.values())


def _format_header(metadata: Dict[str, Any], score: float) -> str:
    """
    Format a concise metadata header for a context section.

    Example output::

        **Food Delivery**  [score: 0.7658]
        Category: domain_architectures  ·  Source: domain_architectures/food_delivery.md
    """
    title = metadata.get("title", "")
    category = metadata.get("category", "")
    rel_path = metadata.get("relative_path", "")

    line1 = f"**{title}**  [score: {score:.4f}]" if title else f"[score: {score:.4f}]"

    parts = []
    if category:
        parts.append(f"Category: {category}")
    if rel_path:
        parts.append(f"Source: {rel_path}")
    line2 = "  ·  ".join(parts)

    return f"{line1}\n{line2}" if line2 else line1
