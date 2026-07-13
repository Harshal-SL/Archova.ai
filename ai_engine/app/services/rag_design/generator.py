from __future__ import annotations

import json
import re

import requests


def build_design_prompt(parameters: dict, retrieval_query: str, context_block: str) -> str:
    output_schema = {
        "design_output": {
            "high_level_design": {
                "system_name": "",
                "version": "",
                "description": "",
                "architecture": {
                    "type": "",
                    "pattern": [],
                    "deployment": "",
                },
                "actors": [
                    {
                        "actor": "",
                        "description": "",
                    }
                ],
                "core_components": [
                    {
                        "name": "",
                        "type": "",
                        "description": "",
                        "interacts_with": [],
                        "technology_options": [],
                    }
                ],
                "data_flow": [
                    {
                        "use_case": "",
                        "steps": [],
                    }
                ],
                "scalability": {
                    "approach": "",
                    "load_balancer": "",
                    "auto_scaling": True,
                },
                "security": {
                    "authentication": "",
                    "authorization": "",
                    "data_security": [],
                },
                "non_functional_requirements": {
                    "availability": "",
                    "latency": "",
                    "throughput": "",
                    "fault_tolerance": "",
                },
            },
            "low_level_design": {
                "system_name": "",
                "version": "",
                "components": [
                    {
                        "name": "",
                        "type": "",
                    }
                ],
            },
            "references": [],
            "assumptions": [],
        }
    }

    return f"""System architect. Generate minimal system design JSON.

RULES:
- ONLY JSON output, no text
- Max 10 words per field
- Max 2 items per array
- Under 1800 chars total

Schema:
{json.dumps(output_schema, indent=2)}

Requirements:
{json.dumps(parameters, indent=2)}

Context (use if relevant):
{context_block[:800]}

Output JSON now:"""


def _extract_json(raw: str) -> dict | None:
    cleaned = re.sub(r"```(?:json)?", "", raw).strip("` \n")
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if not match:
        return None

    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


def generate_design_from_ollama(
    prompt: str,
    ollama_generate_url: str,
    model: str,
    timeout_seconds: int,
    max_retries: int,
) -> dict:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,  # Lower temperature for faster, more focused output
            "num_predict": 1800,  # Reduced from 2500 for speed
            "num_ctx": 2048,  # Reduced context window
            "top_k": 20,  # More focused
            "top_p": 0.8,
        },
    }

    parse_error = None
    last_request_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            response = requests.post(ollama_generate_url, json=payload, timeout=timeout_seconds)
            response.raise_for_status()
            response_json = response.json()
            raw = response_json.get("response", "")
        except requests.RequestException as exc:
            last_request_error = exc
            continue

        parsed = _extract_json(raw)
        if parsed is not None:
            return parsed

        # If parsing failed, just return error (no retry for speed)
        parse_error = raw[:200]
        break

    if last_request_error is not None:
        raise RuntimeError(f"Ollama generation request failed: {last_request_error}")

    raise RuntimeError(f"Failed to parse valid JSON from Ollama response: {parse_error}")
