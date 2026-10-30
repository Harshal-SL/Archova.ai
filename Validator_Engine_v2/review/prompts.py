"""Prompt builder and truncation handling for LLM review.

Builds single comprehensive prompt covering:
- Layer 2: Requirement-intent satisfaction
- Layer 3: Standards conformance (ISO 42010, ISO 25010, IEEE 1016, ISO 25012, ASVS, STRIDE)
- Layer 4: Real-World Architecture Benchmark (Transferable reference patterns & failure modes)
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

SYSTEM_PROMPT = """You are an independent, highly experienced principal software architecture reviewer.
Your mission is to perform rigorous architectural auditing of a software architecture artifact against formal requirements, industry standards, and concrete engineering checklists.

AUDIT PRINCIPLES:
1. PENALIZE GENERIC STATEMENTS: Statements like "use caching", "ensure high availability", or "apply rate limiting" without named entities, specific numeric parameters, or requirement IDs must receive scores 0-2 on Specificity.
2. ZERO HALLUCINATION: Never invent components, endpoints, tables, or mechanisms absent from the provided artifact.
3. VERIFIABLE EVIDENCE REQUIREMENT:
   - Every dimension with score >= 3 MUST include an `evidence_path` (either a valid JSON pointer like `/api_endpoints/0/path` or an exact quoted snippet <= 200 chars copied verbatim from the artifact).
   - Every finding MUST include an `evidence_path` locating the defect in the artifact.
   - For real-world benchmark patterns with status 'ALIGNED', 'PARTIAL', or 'JUSTIFIED_DIVERGENCE', `evidence_path` is REQUIRED.
   - For status 'NOT_APPLICABLE', `requirement_refs` (e.g. ['FR-001', 'NFR-001']) is REQUIRED justifying why the capability is not needed at this scale.
4. STRICT PURE JSON OUTPUT: Return ONLY valid JSON. Your response must begin immediately with the '{' character and end with '}'. Do not write any conversational text, introductory thoughts, markdown blocks, or commentary. Keep all rationales and fixes strictly under 150 characters.

EXACT OUTPUT FORMAT:
{
  "dimensions": [
    {"id": "dim_id", "score": 4, "evidence_path": "/path", "missing": [], "rationale": "Direct concise explanation"}
  ],
  "findings": []
}
"""


def compact_cac(cac: Any) -> Dict[str, Any]:
    """Extract a lightweight high-level summary of the CAC to keep prompt concise."""
    if not isinstance(cac, dict):
        return {}
    compacted: Dict[str, Any] = {}
    if "services" in cac and isinstance(cac["services"], list):
        compacted["services"] = [s.get("name") or s.get("id") for s in cac["services"] if isinstance(s, dict)][:5]
    elif "major_services" in cac and isinstance(cac["major_services"], list):
        compacted["services"] = [s.get("name") or s.get("id") for s in cac["major_services"] if isinstance(s, dict)][:5]
    if "endpoints" in cac and isinstance(cac["endpoints"], list):
        compacted["endpoints"] = [f"{e.get('method', '')} {e.get('path', '')}".strip() for e in cac["endpoints"] if isinstance(e, dict)][:5]
    if "entities" in cac and isinstance(cac["entities"], list):
        compacted["entities"] = [ent.get("name") for ent in cac["entities"] if isinstance(ent, dict)][:5]
    elif "database_entities" in cac and isinstance(cac["database_entities"], list):
        compacted["entities"] = [ent.get("name") for ent in cac["database_entities"] if isinstance(ent, dict)][:5]
    if not compacted:
        for k in list(cac.keys())[:3]:
            val = cac[k]
            if isinstance(val, list):
                compacted[k] = val[:3]
            elif isinstance(val, str):
                compacted[k] = val[:100] + ("..." if len(val) > 100 else "")
            elif isinstance(val, dict):
                compacted[k] = list(val.keys())[:3]
            else:
                compacted[k] = val
    return compacted


def truncate_artifact_if_needed(
    artifact_name: str,
    artifact_data: Dict[str, Any],
    max_chars: int = 4500,
) -> Tuple[Dict[str, Any], bool]:
    """If artifact exceeds budget (~1.2k tokens), select priority sections without breaking JSON structure."""
    serialized = json.dumps(artifact_data, ensure_ascii=False)
    if len(serialized) <= max_chars:
        return artifact_data, False

    # Extract priority keys per artifact rather than slicing text
    truncated_dict: Dict[str, Any] = {}
    priority_keys = {
        "hld": ["architecture_style", "executive_summary", "major_services", "communication_patterns", "data_strategy", "security_overview", "deployment_strategy"],
        "backend": ["api_endpoints", "services", "domain_models", "framework_config", "security_config", "error_handling"],
        "database": ["database_type", "tables", "relationships", "indexes", "locking_and_concurrency", "backup_strategy"],
        "frontend": ["framework", "pages", "components", "state_management", "routing", "api_integration"],
        "security": ["authentication", "authorization", "encryption", "threat_model", "security_controls"],
        "cloud": ["cloud_provider", "compute", "networking", "storage", "scaling_strategy", "disaster_recovery"],
    }.get(artifact_name, list(artifact_data.keys())[:5])

    for k in priority_keys:
        if k in artifact_data:
            val = artifact_data[k]
            # Cap list items to top 6 to fit LLM reasoning budget
            if isinstance(val, list):
                truncated_dict[k] = val[:6]
            elif isinstance(val, str) and len(val) > 350:
                truncated_dict[k] = val[:350] + "... [truncated]"
            else:
                truncated_dict[k] = val

    # Double check if still above max_chars
    trunc_serialized = json.dumps(truncated_dict, ensure_ascii=False)
    if len(trunc_serialized) > max_chars:
        final_dict: Dict[str, Any] = {}
        for k, v in truncated_dict.items():
            if isinstance(v, list):
                final_dict[k] = v[:4]
            elif isinstance(v, str) and len(v) > 200:
                final_dict[k] = v[:200] + "..."
            elif isinstance(v, dict):
                final_dict[k] = {sub_k: v[sub_k] for sub_k in list(v.keys())[:3]}
            else:
                final_dict[k] = v
        return final_dict, True

    return truncated_dict, True


def build_review_user_prompt(
    artifact_name: str,
    artifact_data: Dict[str, Any],
    requirements_summary: List[Dict[str, Any]],
    cac_summary: Dict[str, Any],
    reference_excerpts: str,
    rubric: Dict[str, Any],
    patterns: Optional[List[Any]] = None,
    system_names_by_pattern: Optional[Dict[str, str]] = None,
) -> Tuple[str, bool]:
    """Assemble the unified evaluation user prompt with rubric, reference excerpts, and real-world patterns."""
    safe_data, truncated = truncate_artifact_if_needed(artifact_name, artifact_data)

    dimensions_spec = []
    for d in rubric.get("dimensions", []):
        dimensions_spec.append(
            f"- ID: {d['id']}\n"
            f"  Label: {d['label']}\n"
            f"  Weight: {d['weight']}\n"
            f"  Standard/Source: {d.get('source', 'internal')}\n"
            f"  Description: {d.get('description', '')}"
        )

    # Compact requirements summary: keep ID, type, and trimmed text
    compact_reqs = []
    for r in (requirements_summary or [])[:5]:
        if isinstance(r, dict):
            text_val = r.get("text") or r.get("description") or ""
            compact_reqs.append({
                "id": r.get("id"),
                "type": r.get("type", "functional"),
                "text": text_val[:100] + ("..." if len(text_val) > 100 else "")
            })

    # Compact CAC summary
    compact_cac_data = compact_cac(cac_summary) if cac_summary else {}

    # Optional Real-World Reference Patterns section (cap to top 1 pattern to minimize prompt/output latency)
    patterns_section = ""
    patterns_schema = ""
    if patterns:
        p_list = []
        for p in patterns[:1]:
            p_dict = p.model_dump() if hasattr(p, "model_dump") else (p if isinstance(p, dict) else {})
            p_list.append({
                "id": p_dict.get("id"),
                "name": p_dict.get("name"),
                "description": (p_dict.get("description") or "")[:120],
                "category": p_dict.get("category"),
            })
        patterns_section = f"\n=== 6. APPLICABLE REAL-WORLD REFERENCE PATTERNS (Evaluate Alignment) ===\n{json.dumps(p_list, indent=2)}\n"
        patterns_schema = """,
  "assessments": [
    {
      "pattern_id": "<Pattern ID from section 6>",
      "status": "ALIGNED|PARTIAL|MISSING|JUSTIFIED_DIVERGENCE|NOT_APPLICABLE",
      "evidence_path": "/exact/json/pointer or exact quoted snippet <= 200 chars",
      "justification": "Concise reasoning <= 200 chars",
      "requirement_refs": ["<Requirement ID justifying NOT_APPLICABLE>"]
    }
  ]"""

    prompt = f"""EVALUATION TARGET: {artifact_name.upper()} ARTIFACT

=== 1. REQUIREMENTS CONTEXT (ARSRS) ===
{json.dumps(compact_reqs, indent=2)}

=== 2. CANONICAL ARCHITECTURE CONTRACT (CAC) SUMMARY ===
{json.dumps(compact_cac_data, indent=2) if compact_cac_data else "N/A (Independent artifact evaluation)"}

=== 3. APPLICABLE REFERENCE CHECKLIST EXCERPTS ===
{reference_excerpts or "No specialized reference checklists matched."}

=== 4. ARTIFACT UNDER REVIEW ({artifact_name.upper()}) ===
{json.dumps(safe_data, indent=2)}

=== 5. RUBRIC DIMENSIONS TO EVALUATE (Score 0-5 per dimension) ===
{chr(10).join(dimensions_spec)}
{patterns_section}
OUTPUT INSTRUCTION: Output RAW JSON ONLY matching this schema (no preamble, no commentary, start directly with opening brace):
{{
  "dimensions": [
    {{
      "id": "dimension_id_from_rubric",
      "score": 4,
      "evidence_path": "/exact/json/pointer or exact quoted string from artifact",
      "missing": ["List of any specific missing components or mechanisms"],
      "rationale": "Concise justification under 200 chars explaining why this score was awarded"
    }}
  ],
  "findings": [
    {{
      "rule_id": "REVIEW.DIMENSION_ID.DEFECT_CODE",
      "severity": "critical|high|medium|low",
      "message": "Specific actionable defect explanation",
      "evidence_path": "/exact/json/pointer or exact quoted snippet",
      "fix": "Actionable instructions to remediate this defect"
    }}
  ]{patterns_schema}
}}
"""
    return prompt, truncated
