"""Deterministic selector for relevant Real-World Reference Systems.

Matches target architecture requirements (domain, FRs, NFRs, scale profile)
against ReferenceDocs without calling an LLM.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from Validator_Engine_v2.config import config
from Validator_Engine_v2.real_world.corpus_loader import ReferenceDoc, DOMAIN_KEYWORDS, PATTERN_KEYWORDS


class SelectedSystem(BaseModel):
    """A reference system selected for real-world benchmark evaluation."""

    doc: ReferenceDoc
    score: float
    match_reasons: List[str] = Field(default_factory=list)
    scale_note: Optional[str] = None


class SystemSelector:
    """Selects top K reference systems based on domain, NFR overlap, and scale."""

    def __init__(self, top_k: Optional[int] = None) -> None:
        self.top_k = top_k if top_k is not None else config.REAL_WORLD_TOP_K

    def select(
        self,
        docs: List[ReferenceDoc],
        arsrs: Dict[str, Any],
        hld: Optional[Dict[str, Any]] = None,
    ) -> List[SelectedSystem]:
        """Select top K reference systems for the given ARSRS / architecture."""
        if not docs:
            return []

        if not isinstance(arsrs, dict):
            arsrs = {}
        if not isinstance(hld, dict):
            hld = {}

        # 1. Extract target domain, requirements, and scale signals from ARSRS
        target_name = (arsrs.get("system_name") or arsrs.get("title") or "").lower()
        target_domain = (arsrs.get("domain") or "").lower()

        # Extract terms from functional & non-functional requirements
        target_terms: set[str] = set()
        frs = arsrs.get("functional_requirements", [])
        if isinstance(frs, list):
            for item in frs:
                txt = (item.get("description") or item.get("statement") or str(item)).lower()
                for word in re.findall(r"\b[a-z]{4,}\b", txt):
                    target_terms.add(word)

        nfrs = arsrs.get("non_functional_requirements", [])
        target_qps = 0
        target_users = 0
        if isinstance(nfrs, list):
            for item in nfrs:
                txt = (item.get("description") or item.get("statement") or str(item)).lower()
                for word in re.findall(r"\b[a-z]{4,}\b", txt):
                    target_terms.add(word)

                # Check scale indicators
                qps_match = re.search(r"(\d+[\d,]*)\s*(?:qps|requests|tps)", txt)
                if qps_match:
                    try:
                        target_qps = int(qps_match.group(1).replace(",", ""))
                    except ValueError:
                        pass

                user_match = re.search(r"(\d+[\d,]*)\s*(?:users|dau|concurrent)", txt)
                if user_match:
                    try:
                        target_users = int(user_match.group(1).replace(",", ""))
                    except ValueError:
                        pass

        # Also extract target architecture keywords
        combined_target_text = f"{target_name} {target_domain} " + " ".join(target_terms)

        scored_systems: List[Tuple[float, ReferenceDoc, List[str], Optional[str]]] = []

        for doc in docs:
            score = 0.0
            reasons: List[str] = []
            scale_note: Optional[str] = None

            # A. Domain match (Weight: 3.0)
            doc_tags = set(doc.tags)
            domain_matched = False
            for d in DOMAIN_KEYWORDS:
                if d in target_domain or d in target_name:
                    if d in doc_tags:
                        domain_matched = True
                        score += 3.0
                        reasons.append(f"Domain match on '{d}'")
                        break

            # Fallback domain check: title match
            if not domain_matched and any(w in doc.system_name.lower() for w in target_domain.split()):
                score += 2.0
                reasons.append(f"System name domain alignment '{doc.system_name}'")

            # B. Keyword & NFR term overlap (Weight: 1.0)
            matched_patterns = []
            for p in PATTERN_KEYWORDS:
                if p in combined_target_text and p in doc_tags:
                    matched_patterns.append(p)
                    score += 0.5

            if matched_patterns:
                reasons.append(f"Pattern overlap: {', '.join(matched_patterns[:4])}")

            # Overlap with doc headings
            heading_words = set()
            for s in doc.sections:
                for w in s["heading"].split():
                    if len(w) >= 4:
                        heading_words.add(w)

            overlap_count = len(target_terms.intersection(heading_words))
            if overlap_count > 0:
                score += min(overlap_count * 0.2, 2.0)
                reasons.append(f"{overlap_count} requirement term overlaps")

            # C. Scale Proximity & Planetary Scale Note (Weight: 1.0)
            doc_scale_high = (
                any(
                    term in doc.system_name.lower() or term in doc.path.lower()
                    for term in ("netflix", "google", "youtube", "tiktok", "twitter", "uber", "cloudflare", "amazon", "global", "high-volume", "hyperscale", "planetary")
                )
                or any("scale hint" in str(s.get("content", "")).lower() for s in doc.sections)
            )

            if doc_scale_high:
                if target_qps > 50000 or target_users > 1000000:
                    score += 1.0
                    reasons.append("High scale architecture alignment")
                else:
                    score += 0.2
                    scale_note = (
                        f"{doc.system_name} operates at a scale substantially higher than the target system. "
                        "Evaluated strictly for transferable core architectural patterns rather than "
                        "planetary infrastructure requirements."
                    )
            else:
                score += 0.5

            if not reasons:
                reasons.append("Baseline engineering standard reference")

            scored_systems.append((score, doc, reasons, scale_note))

        # Sort descending by score
        scored_systems.sort(key=lambda x: x[0], reverse=True)

        selected: List[SelectedSystem] = []
        for s_score, s_doc, s_reasons, s_note in scored_systems[: self.top_k]:
            selected.append(
                SelectedSystem(
                    doc=s_doc,
                    score=round(s_score, 2),
                    match_reasons=s_reasons,
                    scale_note=s_note,
                )
            )

        return selected
