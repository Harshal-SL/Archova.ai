from .extractor import FIELDS, _empty_result

# Fields where both value AND ai_suggestion are lists
_LIST_FIELDS = {
    "core_objectives",
    "actors",
    "functional_requirements",
    "inputs",
    "outputs",
    "external_services",
    "non_functional_requirements",
}

# free_constraint.value is boolean (true | null); ai_suggestion is a list
_BOOL_VALUE_LIST_SUGGESTION_FIELDS = {"free_constraint"}


def _union(existing: list | None, incoming) -> list:
    """Deduplicated union preserving insertion order."""
    if isinstance(incoming, str):
        incoming = [incoming]
    if not isinstance(incoming, list):
        return list(existing or [])
    base = list(existing or [])
    for item in incoming:
        # Keep this check list-based so unhashable items (e.g. dicts)
        # from model output don't crash the merge.
        if item not in base:
            base.append(item)
    return base


def merge_results(results: list[dict]) -> dict:
    """
    Merge partial extraction results from multiple chunks.

    Each field is a dict {"value": ..., "ai_suggestion": ...}.

    Rules:
      - list fields                        -> union of values and suggestions, deduped
      - string fields                      -> first non-null value/suggestion wins
      - bool-value / list-suggestion fields -> first non-null boolean wins for value,
                                              union list for ai_suggestion
    """
    merged = _empty_result()

    for result in results:
        for field in FIELDS:
            incoming = result.get(field)
            if not isinstance(incoming, dict):
                continue

            inc_val = incoming.get("value")
            inc_sug = incoming.get("ai_suggestion")
            current = merged[field]

            if field in _LIST_FIELDS:
                if inc_val is not None:
                    current["value"] = _union(current.get("value"), inc_val)
                if inc_sug is not None:
                    current["ai_suggestion"] = _union(current.get("ai_suggestion"), inc_sug)

            elif field in _BOOL_VALUE_LIST_SUGGESTION_FIELDS:
                # value: first non-null boolean wins
                if current["value"] is None and inc_val is not None:
                    current["value"] = inc_val
                # ai_suggestion: union list
                if inc_sug is not None:
                    current["ai_suggestion"] = _union(current.get("ai_suggestion"), inc_sug)

            else:  # plain string fields: first non-null wins
                if current["value"] is None and inc_val is not None:
                    current["value"] = inc_val
                if current["ai_suggestion"] is None and inc_sug is not None:
                    current["ai_suggestion"] = inc_sug

    return merged
