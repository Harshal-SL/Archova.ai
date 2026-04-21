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

    return f"""You are a principal system architect.

Task:
Generate both high-level design (HLD) and detailed low-level design (LLD) for the requested system.
Use retrieved corpus evidence first. If evidence is incomplete, use explicit assumptions.
Keep output concise: each list should have at most 5 items and each text field should stay under 40 words.

Hard requirements:
1) Output MUST be valid JSON only. No markdown, no prose outside JSON.
2) Keep the exact schema keys shown below.
3) `high_level_design` must provide architecture and cross-cutting strategy.
4) `low_level_design` MUST be component-oriented under key `components` and follow the provided LLD template fields.
5) Include references with source file paths when possible.

Output schema:
{json.dumps(output_schema, indent=2)}

User parameters JSON:
{json.dumps(parameters, indent=2)}

Retrieval query summary:
{retrieval_query}

Retrieved context:
{context_block}
"""


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
        "options": {"temperature": 0.2, "num_predict": 1000},
    }

    parse_error = None
    last_request_error: Exception | None = None

    for _attempt in range(max_retries + 1):
        try:
            response = requests.post(ollama_generate_url, json=payload, timeout=timeout_seconds)
            response.raise_for_status()
            raw = response.json().get("response", "")
        except requests.RequestException as exc:
            last_request_error = exc
            continue

        parsed = _extract_json(raw)
        if parsed is not None:
            return parsed

        parse_error = raw
        payload["prompt"] = (
            prompt
            + "\n\nIMPORTANT: Return ONLY strict JSON matching the schema. No markdown or commentary."
        )

    if last_request_error is not None:
        raise RuntimeError(f"Ollama generation request failed: {last_request_error}")

    raise RuntimeError(f"Failed to parse valid JSON from Ollama response: {parse_error}")
