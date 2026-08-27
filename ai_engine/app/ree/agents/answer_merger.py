"""Answer merger utility for REE interview session response merging."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.ree.agents.text_normalizer import (
    clean_conversational_prefix,
    split_semantic_boundaries,
)

logger = logging.getLogger(__name__)


# List parameter keys that store arrays of items
_LIST_PARAM_KEYS = {
    "functional_requirements",
    "non_functional_requirements",
    "actors",
    "constraints",
    "inputs",
    "outputs",
    "external_services",
    "core_objectives",
    "business_objectives",
    "modules",
    "api_contracts",
    "workflows",
    "stakeholders",
}


def _is_list_field(param_name: str, value: Any = None, suggestion: Any = None) -> bool:
    """Return True if parameter should be treated as a list of strings."""
    if param_name in _LIST_PARAM_KEYS:
        return True
    if isinstance(value, list) or isinstance(suggestion, list):
        return True
    if param_name.endswith("_requirements") or param_name.startswith("re_"):
        return True
    return False


def _is_semantic_duplicate(item: str, existing_items: List[str]) -> bool:
    """Check if item is semantically equivalent to any existing string in existing_items."""
    clean_item = clean_conversational_prefix(item).strip().lower()
    if not clean_item:
        return True

    for ex in existing_items:
        clean_ex = clean_conversational_prefix(str(ex)).strip().lower()
        if clean_item == clean_ex:
            return True
        if clean_item.rstrip("s") == clean_ex.rstrip("s"):
            return True

    return False


def is_suggested_template_option(text: str) -> bool:
    """Return True if text matches unconfirmed interview question suggested option templates."""
    if not text:
        return True
    clean = clean_conversational_prefix(text).strip().lower()
    suggestion_patterns = [
        "10k mau in 3 months",
        "specific user adoption target",
        "performance benchmark met (e.g.",
        "revenue or cost target achieved",
        "feature parity with existing system",
        "successful launch on schedule",
        "serve cached data — graceful degradation",
        "reject new requests — circuit breaker",
        "queue requests and retry — async resilience",
        "auto-scale to absorb the load",
        "fail fast with a clear error message",
    ]
    if any(pat in clean for pat in suggestion_patterns):
        return True
    if clean.startswith("e.g.") or clean.startswith("(e.g."):
        return True
    return False


def is_generic_placeholder(text: str) -> bool:
    """Return True if text is a generic placeholder rather than a substantive requirement."""
    if not text:
        return True
    if is_suggested_template_option(text):
        return True
    clean = clean_conversational_prefix(text).strip().lower()
    if clean in ["tbd", "unknown", "unspecified", "none", "n/a", "no", "yes", "default", "standard"]:
        return True
    if any(clean.startswith(prefix) for prefix in [
        "use standard",
        "standard production",
        "proceed with established",
        "proceed with requirements",
        "option a",
        "option b",
        "feature 1",
        "feature 2",
        "item 1",
    ]):
        return True
    return False


def merge_answers(
    parameters: Dict[str, Any],
    answers: List[Dict[str, str]],
) -> Dict[str, Any]:
    """
    Merge stakeholder interview answers into parameter structure.

    Preserves object structure: {"value": [...], "ai_suggestion": [...]}
    Appends new answers to existing lists with semantic deduplication.
    Never overwrites requirement lists with a plain string.
    """
    if not parameters:
        parameters = {}

    merged = dict(parameters)

    for item in answers:
        param_name = item.get("parameter") or item.get("param")
        answer_text = item.get("answer", "").strip()

        if not param_name or not answer_text:
            continue

        clean_ans = clean_conversational_prefix(answer_text)
        if not clean_ans or is_generic_placeholder(clean_ans):
            continue

        if param_name in merged:
            existing = merged[param_name]

            # ── Object Structure: {"value": ..., "ai_suggestion": ...} ────────
            if isinstance(existing, dict):
                val = existing.get("value")
                sug = existing.get("ai_suggestion")

                if _is_list_field(param_name, val, sug):
                    cur_list = list(val) if isinstance(val, list) else ([str(val)] if val else [])
                    new_items = split_semantic_boundaries(clean_ans)
                    if not new_items:
                        new_items = [clean_ans]

                    for new_item in new_items:
                        if not _is_semantic_duplicate(new_item, cur_list):
                            cur_list.append(clean_conversational_prefix(new_item))

                    existing["value"] = cur_list
                else:
                    # Scalar string field inside parameter object
                    cur_str = str(val).strip() if val is not None else ""
                    if not cur_str or cur_str.lower() in ["tbd", "unknown", "unspecified", "none"]:
                        existing["value"] = clean_ans
                    elif clean_ans.lower() not in cur_str.lower():
                        existing["value"] = f"{cur_str}; {clean_ans}"

                merged[param_name] = existing

            # ── Raw List Structure (backward-compat) ─────────────────────────
            elif isinstance(existing, list):
                new_items = split_semantic_boundaries(clean_ans)
                if not new_items:
                    new_items = [clean_ans]

                for new_item in new_items:
                    if not _is_semantic_duplicate(new_item, existing):
                        existing.append(clean_conversational_prefix(new_item))

                merged[param_name] = existing

            # ── Raw String Structure (backward-compat) ───────────────────────
            elif isinstance(existing, str):
                if not existing or existing.lower() in ["tbd", "unknown", "unspecified", "none"]:
                    merged[param_name] = clean_ans
                elif clean_ans.lower() not in existing.lower():
                    merged[param_name] = f"{existing}; {clean_ans}"

            else:
                if _is_list_field(param_name):
                    merged[param_name] = {"value": [clean_ans], "ai_suggestion": None}
                else:
                    merged[param_name] = {"value": clean_ans, "ai_suggestion": None}

        # ── Parameter Not in Merged ──────────────────────────────────────────
        else:
            if _is_list_field(param_name):
                new_items = split_semantic_boundaries(clean_ans)
                merged[param_name] = {
                    "value": new_items if new_items else [clean_ans],
                    "ai_suggestion": None,
                }
            else:
                merged[param_name] = {
                    "value": clean_ans,
                    "ai_suggestion": None,
                }

    return merged
