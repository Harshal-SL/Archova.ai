"""Utility functions for compact prompt formatting and token-budget optimization."""

import json
from typing import Any


def to_compact_json(data: Any, max_len: int = 5000) -> str:
    """Serialize object into compact minified JSON string bounded by a max character length."""
    if not data:
        return "{}"

    # Unwrap inner section payload if wrapped in document container
    if isinstance(data, dict):
        for inner_key in ["hld", "backend_lld", "database_lld", "frontend_lld", "security", "cloud", "requirement_analysis", "technology_recommendation", "technology_recommendations", "architecture_decision_plan"]:
            if inner_key in data and isinstance(data[inner_key], dict):
                data = data[inner_key]
                break

    try:
        raw_str = json.dumps(data, separators=(",", ":"), default=str)
    except Exception:
        raw_str = str(data)

    if len(raw_str) > max_len:
        return raw_str[:max_len] + "... [truncated]"

    return raw_str


def repair_json_string(text: str) -> str:
    """Attempt simple local JSON string repairs for common LLM syntax errors."""
    import re
    cleaned = text.strip()

    # Strip markdown block if present
    if cleaned.startswith("```"):
        first_line_end = cleaned.find("\n")
        if first_line_end != -1:
            cleaned = cleaned[first_line_end + 1 :]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

    # Strip trailing quotes/brackets after closing braces, e.g. ]}"] or }"]
    cleaned = re.sub(r'\]\}\"\]', '}]', cleaned)
    cleaned = re.sub(r'\}\"\]', '}', cleaned)
    cleaned = re.sub(r'\]\"\}', '}', cleaned)
    cleaned = re.sub(r'\}\"\s*$', '}', cleaned)

    # Clean up unquoted ellipses or angle bracket placeholders if copied from prompts
    cleaned = re.sub(r',\s*\.\.\.\s*([\}\]])', r'\1', cleaned)
    cleaned = re.sub(r'\[\s*\.\.\.\s*\]', '[]', cleaned)
    cleaned = re.sub(r':\s*\.\.\.', ': "not_specified"', cleaned)
    cleaned = re.sub(r'\[<[^>]+>\]', '[]', cleaned)
    cleaned = re.sub(r':\s*<[^>]+>', ': null', cleaned)

    try:
        json.loads(cleaned, strict=False)
        return cleaned
    except Exception:
        pass

    # Right-to-left scan for exact valid JSON boundary
    start = cleaned.find("{")
    if start != -1:
        search_str = cleaned[start:]
        idx = search_str.rfind("}")
        while idx > 0:
            candidate = search_str[: idx + 1]
            try:
                json.loads(candidate, strict=False)
                return candidate
            except Exception:
                # Try simple comma, trailing bracket & control char repair on candidate
                try:
                    rep = re.sub(r'[\}\]\s]+$', '}', candidate)
                    rep = re.sub(r",\s*([\}\]])", r"\1", rep)
                    json.loads(rep, strict=False)
                    return rep
                except Exception:
                    pass
                try:
                    rep = re.sub(r'\]\}\"\]', '}]', candidate)
                    rep = re.sub(r'\}\"\]', '}', rep)
                    rep = re.sub(r",\s*([\}\]])", r"\1", rep)
                    json.loads(rep, strict=False)
                    return rep
                except Exception:
                    pass
            idx = search_str.rfind("}", 0, idx)

    # Standard fallback repairs
    if start != -1:
        end = cleaned.rfind("}")
        if end > start:
            cleaned = cleaned[start : end + 1]

    cleaned = re.sub(r",\s*([\}\]])", r"\1", cleaned)
    cleaned = re.sub(r'"\s*\n\s*"', '",\n"', cleaned)
    cleaned = re.sub(r'\}\s*[\r\n]+\s*\{', '},\n{', cleaned)
    cleaned = re.sub(r'\]\s*[\r\n]+\s*\[', '],\n[', cleaned)
    cleaned = re.sub(r'"\s*[\r\n]+\s*\{', '",\n{', cleaned)
    cleaned = re.sub(r'\}\s*[\r\n]+\s*"', '},\n"', cleaned)

    try:
        json.loads(cleaned, strict=False)
        return cleaned
    except Exception:
        pass

    # Strip extra closing braces if count of } > count of {
    while cleaned.count("}") > cleaned.count("{") and cleaned.endswith("}"):
        cleaned = cleaned[:-1].strip()

    # Iterative trailing bracket trimming fallback if json parsing fails
    for _ in range(15):
        try:
            json.loads(cleaned, strict=False)
            return cleaned
        except Exception:
            if cleaned.endswith("}") and cleaned.count("}") > cleaned.count("{"):
                cleaned = cleaned[:-1].strip()
            elif cleaned.endswith("]") and cleaned.count("]") > cleaned.count("["):
                cleaned = cleaned[:-1].strip()
            elif cleaned.endswith(",") or cleaned.endswith(":") or cleaned.endswith('"'):
                cleaned = cleaned[:-1].strip()
            else:
                break

    # Auto-repair truncated JSON (EOF while parsing list/object)
    open_curly = cleaned.count("{") - cleaned.count("}")
    open_square = cleaned.count("[") - cleaned.count("]")

    if open_curly > 0 or open_square > 0:
        cleaned = re.sub(r"[,:\s]+$", "", cleaned)
        if cleaned.count('"') % 2 != 0:
            cleaned += '"'
        cleaned += "]" * max(0, open_square)
        cleaned += "}" * max(0, open_curly)

    return cleaned


def sanitize_payload_for_model(data: Any, model_cls: Any) -> Any:
    """Recursively sanitize Python dict/list types to match Pydantic model expectations locally."""
    import typing
    from pydantic import BaseModel
    from app.sae.utils.enums import AgentRole

    valid_roles = {r.value for r in AgentRole}

    if isinstance(data, list):
        return [sanitize_payload_for_model(item, model_cls) for item in data]

    if not isinstance(data, dict):
        return data

    sanitized = {}
    fields = getattr(model_cls, "model_fields", {}) if hasattr(model_cls, "model_fields") else {}

    for k, v in data.items():
        field_info = fields.get(k)
        sub_model_cls = None
        if field_info:
            ann = getattr(field_info, "annotation", None)
            if isinstance(ann, type) and issubclass(ann, BaseModel):
                sub_model_cls = ann
            elif ann is not None:
                args = typing.get_args(ann)
                for arg in args:
                    if isinstance(arg, type) and issubclass(arg, BaseModel):
                        sub_model_cls = arg
                        break

        target_cls = sub_model_cls or model_cls

        if isinstance(v, dict):
            sanitized[k] = sanitize_payload_for_model(v, target_cls)
        elif isinstance(v, list):
            sanitized[k] = [sanitize_payload_for_model(item, target_cls) for item in v]
        elif k == "source" and isinstance(v, str) and v not in valid_roles:
            sanitized[k] = AgentRole.ARCHITECTURE_PLANNER.value
        else:
            sanitized[k] = v

    if fields:
        for field_name, field_info in fields.items():
            if field_name not in sanitized:
                continue

            val = sanitized[field_name]
            annotation = getattr(field_info, "annotation", None)
            annotation_str = str(annotation) if annotation else ""
            ann_lower = annotation_str.lower().strip()

            is_list_type = ann_lower.startswith("list") or "typing.list" in ann_lower
            is_dict_type = (ann_lower.startswith("dict") or "typing.dict" in ann_lower) and not is_list_type
            is_str_type = (ann_lower == "str" or "optional[str]" in ann_lower or ann_lower.startswith("str")) and not is_list_type and not is_dict_type

            # Case 1: Model expects dict/object, but received list
            if is_dict_type and isinstance(val, list):
                if all(isinstance(x, dict) and "key" in x and "value" in x for x in val):
                    sanitized[field_name] = {x["key"]: x["value"] for x in val}
                elif all(isinstance(x, dict) and "name" in x for x in val):
                    sanitized[field_name] = {x["name"]: x for x in val}
                else:
                    sanitized[field_name] = {f"item_{i}": item for i, item in enumerate(val)}

            # Case 2: Model expects str, but received dict, list, or primitive (int, float, bool)
            elif is_str_type and not isinstance(val, str) and val is not None:
                if isinstance(val, (dict, list)):
                    sanitized[field_name] = json.dumps(val, default=str)
                elif isinstance(val, (int, float, bool)):
                    sanitized[field_name] = str(val)

            # Case 3: Model expects list, but received single object, dict, or JSON-stringified list
            elif is_list_type:
                if isinstance(val, str) and val.strip().startswith("[") and val.strip().endswith("]"):
                    try:
                        parsed_list = json.loads(val)
                        if isinstance(parsed_list, list):
                            sanitized[field_name] = parsed_list
                    except Exception:
                        pass
                elif isinstance(val, dict):
                    sanitized[field_name] = [val]

                # Map common alternate key names in list of dict items
                if isinstance(sanitized.get(field_name), list):
                    is_str_element_list = "str" in ann_lower and "dict" not in ann_lower and "any" not in ann_lower and "union" not in ann_lower
                    new_list = []
                    for item in sanitized[field_name]:
                        if isinstance(item, dict):
                            if is_str_element_list:
                                extracted_str = item.get("description") or item.get("title") or item.get("risk") or item.get("name") or str(item)
                                new_list.append(extracted_str)
                            else:
                                if "description" in item and "message" not in item:
                                    item["message"] = item["description"]
                                if "issue" in item and "message" not in item:
                                    item["message"] = item["issue"]
                                new_list.append(item)
                        else:
                            new_list.append(item)
                    sanitized[field_name] = new_list

            # Case 4: Model expects dict, but received JSON-stringified dict
            elif is_dict_type and isinstance(val, str) and val.strip().startswith("{") and val.strip().endswith("}"):
                try:
                    parsed_dict = json.loads(val)
                    if isinstance(parsed_dict, dict):
                        sanitized[field_name] = parsed_dict
                except Exception:
                    pass

    return sanitized

