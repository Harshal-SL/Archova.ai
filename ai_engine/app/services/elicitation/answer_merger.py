# Parameters whose value is a list (vs a plain string or bool)
_LIST_PARAMS = {
    "core_objectives",
    "actors",
    "functional_requirements",
    "inputs",
    "outputs",
    "external_services",
    "non_functional_requirements",
}


def merge_answers(parameters: dict, answers: list[dict]) -> dict:
    """
    Fill missing parameter values using user-provided answers.

    Each answer item: {"parameter": "<key>", "answer": "<user answer>"}

    - List-type parameters: the answer string is split on commas into a list.
    - String-type parameters: the answer is stored as-is.
    - free_constraint: the answer is interpreted as a boolean string ("true"/"false")
      or left as a string if unrecognised.
    """
    # Deep-copy the top-level dicts so we don't mutate the original
    result = {k: dict(v) if isinstance(v, dict) else v for k, v in parameters.items()}

    for item in answers:
        param = item.get("parameter")
        answer = item.get("answer")

        if not param or answer is None or param not in result:
            continue

        if param in _LIST_PARAMS:
            if isinstance(answer, list):
                value = [str(a).strip() for a in answer if str(a).strip()]
            else:
                value = [a.strip() for a in str(answer).split(",") if a.strip()]

        elif param == "free_constraint":
            lower = str(answer).lower().strip()
            if lower in ("true", "yes", "1"):
                value = True
            elif lower in ("false", "no", "0"):
                value = False
            else:
                value = answer

        else:
            value = answer

        if isinstance(result[param], dict):
            result[param]["value"] = value
        else:
            result[param] = {"value": value}

    return result
