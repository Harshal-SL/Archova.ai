import json
import re
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral"
MAX_RETRIES = 2

# All fields that must appear in the output
FIELDS = [
    "goal",
    "core_objectives",
    "system_type",
    "actors",
    "functional_requirements",
    "inputs",
    "outputs",
    "external_services",
    "system_behaviour",
    "non_functional_requirements",
    "free_constraint",
]

_PROMPT_TEMPLATE = """\
You are a senior software requirements analyst.

Extract structured system requirements from the given text.

Rules:
- Extract explicit requirements only.
- If a parameter is missing set value to null.
- Provide ai_suggestion for every missing or null value.
- If the text contains phrases like "free", "free tier", "deploy for free", or "no cost",
  set free_constraint.value = true. Otherwise set free_constraint.value = null and suggest
  free deployment options in ai_suggestion.
- Do NOT include explanations, markdown fences, or any text outside the JSON.
- Return ONLY a valid JSON object matching this exact schema:

{{
  "goal":                        {{"value": null, "ai_suggestion": null}},
  "core_objectives":             {{"value": [],   "ai_suggestion": []}},
  "system_type":                 {{"value": null, "ai_suggestion": null}},
  "actors":                      {{"value": [],   "ai_suggestion": []}},
  "functional_requirements":     {{"value": [],   "ai_suggestion": []}},
  "inputs":                      {{"value": [],   "ai_suggestion": []}},
  "outputs":                     {{"value": [],   "ai_suggestion": []}},
  "external_services":           {{"value": [],   "ai_suggestion": []}},
  "system_behaviour":            {{"value": null, "ai_suggestion": null}},
  "non_functional_requirements": {{"value": [],   "ai_suggestion": []}},
  "free_constraint":             {{"value": null, "ai_suggestion": []}}
}}

Input:
{chunk}"""


def _empty_result() -> dict:
    return {
        "goal":                        {"value": None, "ai_suggestion": None},
        "core_objectives":             {"value": None, "ai_suggestion": []},
        "system_type":                 {"value": None, "ai_suggestion": None},
        "actors":                      {"value": None, "ai_suggestion": []},
        "functional_requirements":     {"value": None, "ai_suggestion": []},
        "inputs":                      {"value": None, "ai_suggestion": []},
        "outputs":                     {"value": None, "ai_suggestion": []},
        "external_services":           {"value": None, "ai_suggestion": []},
        "system_behaviour":            {"value": None, "ai_suggestion": None},
        "non_functional_requirements": {"value": None, "ai_suggestion": []},
        "free_constraint":             {"value": None, "ai_suggestion": []},
    }


def _parse_json(raw: str) -> dict | None:
    """Parse model output. Returns None if parsing fails (triggers retry)."""
    raw = re.sub(r"```(?:json)?", "", raw).strip()
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        return None
    try:
        data = json.loads(match.group())
        # Validate top-level shape — every field must be a dict with value/ai_suggestion
        for f in FIELDS:
            if f not in data or not isinstance(data[f], dict):
                return None
        return {f: data[f] for f in FIELDS}
    except json.JSONDecodeError:
        return None


def extract_from_chunk(chunk: str) -> dict:
    """Send one chunk to Mistral via HTTP and return a partial requirements dict."""
    prompt = _PROMPT_TEMPLATE.format(chunk=chunk)
    payload = {"model": MODEL, "prompt": prompt, "stream": False}

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
            resp.raise_for_status()
            raw = resp.json().get("response", "")
            result = _parse_json(raw)
            if result is not None:
                return result
            # JSON invalid — retry with explicit reminder appended
            payload["prompt"] = prompt + "\n\nIMPORTANT: Return ONLY the JSON object, no other text."
        except Exception:
            pass

    return _empty_result()
