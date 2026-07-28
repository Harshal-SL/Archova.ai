"""
LLM-based design generation utilities.

Provides functions for generating HLD and LLD prompts and calling Ollama.
This module is RAG-agnostic and can work with any retrieval backend.
"""

from __future__ import annotations

import json
import logging
import re

import requests


logger = logging.getLogger(__name__)


def build_hld_prompt(parameters: dict, context_arch: str, context_risks: str) -> str:
    """Build prompt for HLD generation.
    
    Args:
        parameters: Design requirements
        context_arch: Architecture knowledge context
        context_risks: Risk considerations context
    
    Returns:
        Prompt string for Ollama
    """
    
    hld_schema = {
        "high_level_design": {
            "system_name": "",
            "description": "",
            "architecture": {
                "type": "",
                "patterns": [],
                "deployment": ""
            },
            "actors": [
                {
                    "actor": "",
                    "description": ""
                }
            ],
            "core_components": [
                {
                    "name": "",
                    "type": "",
                    "description": "",
                    "interacts_with": [],
                    "technology_options": []
                }
            ],
            "data_flow": [
                {
                    "use_case": "",
                    "steps": []
                }
            ],
            "scalability": {
                "approach": "",
                "load_balancer": "",
                "auto_scaling": True
            },
            "security": {
                "authentication": "",
                "authorization": "",
                "data_security": []
            },
            "non_functional_requirements": {
                "availability": "",
                "latency": "",
                "throughput": "",
                "fault_tolerance": ""
            }
        }
    }

    return f"""You are a system architect. Generate a high-level design (HLD) in JSON format.

REQUIREMENTS:
{json.dumps(parameters, indent=2)}

ARCHITECTURE KNOWLEDGE:
{context_arch}

RISK CONSIDERATIONS:
{context_risks}

OUTPUT SCHEMA:
{json.dumps(hld_schema, indent=2)}

RULES:
- Output ONLY valid JSON matching the schema
- Provide full descriptive values (no word limits)
- Use retrieved knowledge to inform architecture decisions
- Include specific technology options and patterns
- Ensure all components interact logically

Generate the HLD JSON now:"""


def build_lld_prompt(parameters: dict, hld_summary: str, section: str, context: str) -> str:
    """Build prompt for one LLD section.
    
    Args:
        parameters: Design requirements
        hld_summary: Compact summary of HLD for consistency
        section: One of "frontend", "backend", "database", "cloud", "security"
        context: Retrieved technical knowledge
    
    Returns:
        Prompt string for Ollama
    """
    
    schemas = {
        "frontend": {
            "frontend": {
                "framework": "",
                "pages": [
                    {
                        "name": "",
                        "route": "",
                        "components": [],
                        "state": []
                    }
                ],
                "state_management": {
                    "tool": "",
                    "stores": []
                },
                "api_integration": [
                    {
                        "endpoint": "",
                        "method": "",
                        "purpose": ""
                    }
                ],
                "styling": {
                    "approach": "",
                    "library": ""
                }
            }
        },
        "backend": {
            "backend": {
                "framework": "",
                "architecture_pattern": "",
                "modules": [
                    {
                        "name": "",
                        "responsibility": "",
                        "dependencies": []
                    }
                ],
                "api_endpoints": [
                    {
                        "path": "",
                        "method": "",
                        "handler": "",
                        "request_body": {},
                        "response": {},
                        "authentication": ""
                    }
                ],
                "business_logic": [
                    {
                        "service": "",
                        "methods": [],
                        "dependencies": []
                    }
                ],
                "error_handling": {
                    "strategy": "",
                    "error_codes": []
                }
            }
        },
        "database": {
            "database": {
                "type": "",
                "schema": {
                    "tables": [
                        {
                            "name": "",
                            "columns": [
                                {
                                    "name": "",
                                    "type": "",
                                    "constraints": []
                                }
                            ],
                            "indexes": [],
                            "relationships": []
                        }
                    ]
                },
                "queries": [
                    {
                        "name": "",
                        "type": "",
                        "query": "",
                        "optimization": ""
                    }
                ],
                "migrations": {
                    "strategy": "",
                    "tool": ""
                },
                "backup": {
                    "frequency": "",
                    "retention": ""
                }
            }
        },
        "cloud": {
            "cloud": {
                "provider": "",
                "services": [
                    {
                        "name": "",
                        "purpose": "",
                        "configuration": {}
                    }
                ],
                "networking": {
                    "vpc": "",
                    "subnets": [],
                    "security_groups": []
                },
                "deployment": {
                    "strategy": "",
                    "ci_cd": "",
                    "environments": []
                },
                "monitoring": {
                    "tools": [],
                    "metrics": [],
                    "alerts": []
                },
                "cost_optimization": {
                    "strategies": []
                }
            }
        },
        "security": {
            "security": {
                "authentication": {
                    "method": "",
                    "provider": "",
                    "token_management": ""
                },
                "authorization": {
                    "model": "",
                    "roles": [],
                    "permissions": []
                },
                "data_protection": {
                    "encryption_at_rest": "",
                    "encryption_in_transit": "",
                    "key_management": ""
                },
                "api_security": {
                    "rate_limiting": "",
                    "input_validation": "",
                    "cors": ""
                },
                "compliance": {
                    "standards": [],
                    "audit_logging": ""
                },
                "threat_mitigation": {
                    "ddos_protection": "",
                    "waf": "",
                    "vulnerability_scanning": ""
                }
            }
        }
    }
    
    schema = schemas.get(section, {})
    section_title = section.upper()

    return f"""You are a system architect. Generate the {section_title} section of the low-level design (LLD) in JSON format.

HIGH-LEVEL DESIGN SUMMARY (for consistency):
{hld_summary}

REQUIREMENTS:
{json.dumps(parameters, indent=2)}

TECHNICAL KNOWLEDGE FOR {section_title}:
{context}

OUTPUT SCHEMA:
{json.dumps(schema, indent=2)}

RULES:
- Output ONLY valid JSON matching the schema
- Provide detailed, implementation-ready specifications
- Ensure consistency with the HLD summary
- Use retrieved knowledge to inform technical decisions
- Include specific technologies, configurations, and patterns

Generate the {section_title} LLD JSON now:"""


def _extract_json(raw: str) -> dict | None:
    """Extract first valid JSON object from text."""
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
    num_predict: int,
    num_ctx: int = 4096,
    max_retries: int = 1,
) -> dict:
    """Generate design section from Ollama with JSON parsing.
    
    Args:
        prompt: The prompt to send to Ollama
        ollama_generate_url: Ollama API endpoint URL
        model: Model name to use
        timeout_seconds: Request timeout
        num_predict: Max tokens to generate
        num_ctx: Context window size
        max_retries: Number of retries on parse failure
    
    Returns:
        Parsed JSON dictionary
    
    Raises:
        RuntimeError: If request fails or JSON cannot be parsed
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": num_predict,
            "num_ctx": num_ctx,
            "top_k": 40,
            "top_p": 0.9,
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
            logger.debug(f"Parsed JSON successfully on attempt {attempt + 1}")
            return parsed

        # Retry with repair prompt
        if attempt < max_retries:
            logger.debug(f"Attempt {attempt + 1} failed, retrying with repair prompt")
            repair_prompt = f"""The previous response was not valid JSON. Return only the JSON object, no other text:

{raw[:500]}

Return valid JSON now:"""
            payload["prompt"] = repair_prompt
            continue
        
        parse_error = raw[:200]
        break

    if last_request_error is not None:
        logger.error(f"Ollama request failed: {last_request_error}")
        raise RuntimeError(f"Ollama generation request failed: {last_request_error}") from last_request_error

    logger.error(f"Failed to parse JSON from Ollama response: {parse_error}")
    raise RuntimeError(f"Failed to parse valid JSON from Ollama response: {parse_error}")


def compact_hld(hld_result: dict, max_tokens: int = 400) -> str:
    """Create a compact summary of HLD for LLD context.
    
    Args:
        hld_result: Full HLD dictionary
        max_tokens: Approximate max tokens (1 token ≈ 4 chars)
    
    Returns:
        Compact JSON string for use in LLD prompts
    """
    try:
        hld = hld_result.get("high_level_design", {})
        
        compact = {
            "system_name": hld.get("system_name", ""),
            "architecture_type": hld.get("architecture", {}).get("type", ""),
            "patterns": hld.get("architecture", {}).get("patterns", [])[:3],
            "core_components": [
                {
                    "name": comp.get("name", ""),
                    "type": comp.get("type", ""),
                    "interacts_with": comp.get("interacts_with", [])[:3]
                }
                for comp in hld.get("core_components", [])[:5]
            ]
        }
        
        json_str = json.dumps(compact, indent=2)
        
        # Rough token limit (1 token ≈ 4 chars)
        max_chars = max_tokens * 4
        if len(json_str) > max_chars:
            json_str = json_str[:max_chars] + "..."
        
        return json_str
        
    except Exception as e:
        logger.warning(f"Failed to compact HLD: {e}")
        return "{}"
