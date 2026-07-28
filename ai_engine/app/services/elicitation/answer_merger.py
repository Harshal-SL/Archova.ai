from app.ree.agents.text_normalizer import split_semantic_boundaries, clean_conversational_prefix

# Parameters whose value is a list (vs a plain string or bool)
_LIST_PARAMS = {
    "core_objectives",
    "business_objectives",
    "actors",
    "functional_requirements",
    "inputs",
    "outputs",
    "external_services",
    "non_functional_requirements",
    "constraints",
}


def merge_answers(parameters: dict, answers: list[dict]) -> dict:
    """
    Fill missing parameter values using user-provided answers.

    Each answer item: {"parameter": "<key>", "answer": "<user answer>"}

    - List-type parameters: split on semantic boundaries (newlines/semicolons), NEVER on commas alone.
    - String-type parameters: conversational prefixes stripped, stored cleanly.
    - free_constraint: boolean interpretation.
    """
    result = {k: dict(v) if isinstance(v, dict) else v for k, v in (parameters or {}).items()}

    for item in answers:
        param = item.get("parameter")
        answer = item.get("answer")

        if not param or answer is None:
            continue

        param_str = str(param).strip()
        if not param_str:
            continue

        if param_str in _LIST_PARAMS:
            if isinstance(answer, list):
                value = [clean_conversational_prefix(str(a)) for a in answer if str(a).strip()]
            elif isinstance(answer, str):
                value = split_semantic_boundaries(answer)
            else:
                value = [clean_conversational_prefix(str(answer))]

        elif param_str == "free_constraint":
            lower = str(answer).lower().strip()
            if lower in ("true", "yes", "1"):
                value = True
            elif lower in ("false", "no", "0"):
                value = False
            else:
                value = clean_conversational_prefix(str(answer))

        else:
            value = clean_conversational_prefix(str(answer)) if isinstance(answer, str) else answer

        if param_str in result and isinstance(result[param_str], dict):
            result[param_str]["value"] = value
        else:
            result[param_str] = {"value": value, "ai_suggestion": None}

    return result
