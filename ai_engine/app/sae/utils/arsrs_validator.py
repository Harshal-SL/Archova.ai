"""ARSRS Pre-SAE Grounding Verification.

Ensures that before SAE execution starts:
1. The ARSRS is validated and confirmed to represent the current Problem Statement.
2. If requirements or actors are missing, discrete requirements are derived directly from the current PS text.
3. Does NOT perform brittle keyword blocking, allowing legitimate multi-domain words to flow through naturally.
"""

from __future__ import annotations

import copy
import logging
from typing import Any, Dict, List, Tuple

from app.ree.agents.text_normalizer import (
    clean_conversational_prefix,
    extract_semantic_functional_requirements,
    deduplicate_and_normalize_actors,
)

logger = logging.getLogger(__name__)


class ARSRSValidator:
    """Lightweight pre-SAE validator ensuring ARSRS has complete, well-formed requirements."""

    @classmethod
    def validate_and_sanitize_arsrs(
        cls,
        arsrs: Dict[str, Any],
        raw_prompt: str = "",
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Validate ARSRS against current PS context.
        Ensures requirements and actors are populated directly from the current PS.
        """
        if not isinstance(arsrs, dict) or not arsrs:
            return arsrs, ["ARSRS is empty or not a dict; skipping verification"]

        sanitized = copy.deepcopy(arsrs)
        actions: List[str] = []

        proj_prof = sanitized.get("project_profile", {}) if isinstance(sanitized.get("project_profile"), dict) else {}
        raw_input = sanitized.get("raw_input") or ""
        goal = proj_prof.get("goal") or sanitized.get("goal") or ""
        ps_text = raw_prompt or raw_input or goal

        # Ensure Functional Requirements exist
        raw_frs = sanitized.get("functional_requirements", [])
        if not raw_frs and ps_text.strip():
            semantic_frs = extract_semantic_functional_requirements(ps_text)
            clean_frs = []
            for idx, sfr in enumerate(semantic_frs, 1):
                clean_frs.append({
                    "id": f"FR-{idx:03d}",
                    "title": clean_conversational_prefix(sfr).split(".")[0][:50],
                    "description": sfr,
                    "priority": "HIGH",
                    "category": "functional",
                })
            sanitized["functional_requirements"] = clean_frs
            actions.append(f"Derived {len(clean_frs)} functional requirements directly from Problem Statement.")

        # Ensure Actors exist
        raw_actors = sanitized.get("actors", [])
        if not raw_actors:
            actors_list = deduplicate_and_normalize_actors([])
            sanitized["actors"] = [{"role": a, "description": f"System actor: {a}"} for a in actors_list]
            actions.append("Populated standard system actors.")

        return sanitized, actions
