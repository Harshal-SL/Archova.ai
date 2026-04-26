def detect_missing_parameters(parameters: dict) -> list[str]:
    """Return a list of parameter keys whose value is None."""
    missing = []
    for key, val in parameters.items():
        if isinstance(val, dict):
            if val.get("value") is None:
                missing.append(key)
        elif val is None:
            missing.append(key)
    return missing
