import json
import re

import requests

from app.config import settings

OLLAMA_URL = settings.ollama_generate_url
MODEL = settings.llm_model
MAX_RETRIES = settings.llm_max_retries
TIMEOUT_SECONDS = settings.ollama_timeout_seconds

_PROMPT_TEMPLATE = """\
You are a software requirements analyst.

Some system parameters are missing.

Generate clarification questions for the user.

For each missing parameter:
- create a clear question
- provide 3 to 5 possible options

Missing parameters:
{missing_parameters}

System description:
{prompt}

Return JSON format only, no markdown, no extra text:
{{
 "questions": [
  {{
   "parameter": "",
   "question": "",
   "options": []
  }}
 ]
}}\
"""


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"```(?:json)?", "", raw).strip("`").strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in LLM response")
    data = json.loads(match.group())
    if "questions" not in data:
        raise ValueError("Missing 'questions' key in LLM response")
    return data


def generate_questions(missing_parameters: list[str], prompt: str) -> dict:
    llm_prompt = _PROMPT_TEMPLATE.format(
        missing_parameters="\n".join(f"- {p}" for p in missing_parameters),
        prompt=prompt,
    )
    payload = {
        "model": MODEL,
        "prompt": llm_prompt,
        "stream": False,
    }

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            raw = response.json().get("response", "")
            return _parse_json(raw)
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc
        except requests.RequestException as exc:
            raise RuntimeError(f"Ollama connection failed: {exc}") from exc

    raise RuntimeError(
        f"Failed to parse valid JSON from LLM after {MAX_RETRIES + 1} attempts: {last_error}"
    )
