"""
Domain Expert Agent

Single responsibility:
  Analyse the technical domain and populate SRC.domain_context.

Covers:
  - Industry / domain classification
  - Domain-specific constraints (regulatory, operational)
  - Compliance requirements (GDPR, HIPAA, PCI-DSS, SOC2, etc.)
  - Expected scale (users, transactions, data volume)
  - Recommended architecture patterns for this domain
  - Domain-specific risks

Reads from:
  SRC.project_context.normalized_text   (primary input text)
  SRC.domain_context                    (existing state to enrich)
  SRC.business_context.domain           (domain hint from BusinessAnalyst if available)

Writes to:
  SRC.domain_context                    (its exclusive section)
  SRC.discussion_notes                  (reasoning notes)

Never touches:
  SRC.requirements.parameters   (Requirement Engineer's territory)
  SRC.business_context          (Business Analyst's territory)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.ree.models import SharedRequirementContext, DomainContext
from app.ree.agents.base_agent import BaseAIAgent
from app.ree.agents.agent_contracts import ContractValidator, DOMAIN_EXPERT_SCHEMA
from app.ree.llm.model_registry import Capability

logger = logging.getLogger(__name__)

_AGENT_NAME = "DomainExpert"

# ── Prompt ────────────────────────────────────────────────────────────────────

_PROMPT_TEMPLATE = """\
AGENCY CONTRACT: Domain Expert

RESPONSIBILITY:
You are the Domain Expert. Your responsibility is to analyze domain concepts, terminology, domain entities, industry standards, regulatory compliance, domain assumptions, and domain relationships.

WHAT TO EXTRACT (OWNED FIELDS):
1. industry — Industry sector and core domain model (e.g. Education / Library Management, Fintech, Healthcare).
2. domain_concepts — Domain terminology, domain entities, and core concepts.
3. domain_constraints — Operational rules specific to the industry or technical domain.
4. compliance — Industry standards, regulatory compliance (FERPA, GDPR, HIPAA, PCI-DSS).
5. scale — Domain scale requirements (user load, request rate, data volume).
6. architecture_patterns — Recommended architectural patterns based on industry best practices.
7. risks — Operational, regulatory, data privacy, or domain-specific risks.

WHAT NOT TO EXTRACT (DO NOT GENERATE):
- Functional requirements or user actions (Owned by Requirement Engineer).
- Business goals, KPIs, business ROI objectives (Owned by Business Analyst).
- APIs, endpoints, HTTP methods (Owned by Requirement Engineer).
- System modules or UI features (Owned by Requirement Engineer).

PROJECT DESCRIPTION:
{project_text}

ALREADY KNOWN DOMAIN CONTEXT:
{existing_context}

RULES:
- CRITICAL: Return ONLY a raw, valid JSON object starting with '{{' and ending with '}}'.
- Do NOT wrap the JSON in Markdown code fences (NO ```json).
- Do NOT include any preamble, intro, explanation, or postscript.
- Analyze industry, domain concepts, and standards ONLY for the system described in the CURRENT Problem Statement.
- Do NOT apply generic templates or introduce domain entities/terms from other unrelated domains.
- If information cannot be inferred, return {{"value": [], "ai_suggestion": []}} for list keys (or empty string for industry). Never fabricate information.
- Do NOT include any extra keys outside the schema.

OUTPUT SCHEMA:
{{
  "industry": {{
    "value": "",
    "ai_suggestion": ""
  }},
  "domain_concepts": {{
    "value": [],
    "ai_suggestion": []
  }},
  "domain_constraints": {{
    "value": [],
    "ai_suggestion": []
  }},
  "compliance": {{
    "value": [],
    "ai_suggestion": []
  }},
  "scale": {{
    "value": [],
    "ai_suggestion": []
  }},
  "architecture_patterns": {{
    "value": [],
    "ai_suggestion": []
  }},
  "risks": {{
    "value": [],
    "ai_suggestion": []
  }}
}}
"""

_EMPTY_OUTPUT: Dict[str, Any] = {
    "industry": {"value": "", "ai_suggestion": ""},
    "domain_concepts": {"value": [], "ai_suggestion": []},
    "domain_constraints": {"value": [], "ai_suggestion": []},
    "compliance": {"value": [], "ai_suggestion": []},
    "scale": {"value": [], "ai_suggestion": []},
    "architecture_patterns": {"value": [], "ai_suggestion": []},
    "risks": {"value": [], "ai_suggestion": []},
}


class DomainExpertAgent(BaseAIAgent):
    """
    AI specialist that analyses technical domain context.

    Reads the normalized project text from the SRC and calls the LLM
    with a focused domain expertise prompt. Writes its findings
    exclusively into SRC.domain_context.
    """

    AGENT_NAME = _AGENT_NAME
    STAGE = "engineering"
    CAPABILITY = Capability.DOMAIN_REASONING

    def run(self, src: SharedRequirementContext) -> SharedRequirementContext:
        """
        Run the Domain Expert's analysis pass.

        Args:
            src: Current SRC. Reads project_context and domain_context.

        Returns:
            Updated SRC with domain_context populated.
        """
        logger.info("%s: starting analysis", _AGENT_NAME)

        project_text = src.project_context.normalized_text or src.raw_input
        if not project_text.strip():
            self._add_note(src, "No project text available — skipping.")
            logger.warning("%s: project text is empty, skipping", _AGENT_NAME)
            return src

        # Build summary of existing domain context
        existing_summary = self._summarise_existing(src.domain_context)

        prompt = _PROMPT_TEMPLATE.format(
            project_text=project_text[:4000],
            existing_context=existing_summary,
        )

        result = self._call_llm(prompt, max_tokens=1000, temperature=0.1)

        if result is None:
            self._add_note(
                src,
                "LLM API rate-limited or unavailable. "
                "Utilizing deterministic rule-based domain context fallback."
            )
            logger.warning("%s: LLM call failed — using rule-based fallback", _AGENT_NAME)
            result = self._generate_rule_based_fallback(project_text)

        result = self._normalise_output(result)

        # Write into SRC — exclusively into domain_context
        self._merge_into_domain_context(src, result)

        # Store raw output
        src.agent_outputs[_AGENT_NAME] = result

        note = self._build_note(result)
        self._add_note(src, note)
        logger.info("%s: complete — %s", _AGENT_NAME, note)

        return src

    # ── Merge ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _merge_into_domain_context(
        src: SharedRequirementContext,
        result: Dict[str, Any],
    ) -> None:
        """
        Merge LLM output into SRC.domain_context and sync into SRC.parameters.
        """
        dc = src.domain_context

        # industry → industry & system_type
        industry_node = result.get("industry", {})
        industry_value = _to_scalar(industry_node.get("value", ""))
        industry_suggestion = _to_scalar(industry_node.get("ai_suggestion", ""))
        inferred_industry = industry_value or industry_suggestion or None

        if inferred_industry:
            if not getattr(dc, "industry", None):
                dc.industry = inferred_industry
            if not dc.system_type:
                dc.system_type = inferred_industry

        # architecture_patterns
        dc.architecture_patterns = _merge_list(
            dc.architecture_patterns,
            result.get("architecture_patterns", {}),
        )

        # Extended fields attached dynamically
        _set_extended(dc, "domain_constraints", result.get("domain_constraints", {}))
        _set_extended(dc, "compliance", result.get("compliance", {}))
        _set_extended(dc, "scale", result.get("scale", {}))
        _set_extended(dc, "risks", result.get("risks", {}))

        # ALSO sync into flat parameters for downstream agents and RequirementReviewAgent
        params = src.parameters
        if getattr(dc, "industry", None):
            _union_into(params, "industry", {"value": dc.industry, "ai_suggestion": None})
        if dc.system_type:
            _union_into(params, "system_type", {"value": dc.system_type, "ai_suggestion": None})

        _union_into(params, "constraints", result.get("domain_constraints", {}))
        _union_into(params, "constraints", result.get("compliance", {}))

        src.sync_requirements()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _generate_rule_based_fallback(self, project_text: str) -> Dict[str, Any]:
        """Generate rule-based domain context fallback when LLM API returns None."""
        return {
            "industry": "Software Engineering & Enterprise SaaS",
            "domain_constraints": ["High availability SLA and system fault tolerance"],
            "domain_concepts": ["Microservices Architecture", "Distributed Transaction Processing"],
            "compliance": ["GDPR / Data Privacy Standard"],
            "architecture_patterns": ["Layered Monolith / Microservices"],
        }

    @staticmethod
    def _summarise_existing(dc: DomainContext) -> str:
        """Build a compact text summary of the existing domain context."""
        parts: List[str] = []
        if dc.system_type:
            parts.append(f"System type: {dc.system_type}")
        if dc.architecture_patterns:
            parts.append(f"Patterns: {', '.join(dc.architecture_patterns[:3])}")
        if dc.similar_systems:
            parts.append(f"Similar systems: {', '.join(dc.similar_systems[:3])}")
        return "; ".join(parts) if parts else "None known yet."

    @staticmethod
    def _normalise_output(raw: Any) -> Dict[str, Any]:
        """
        Contract-driven normalization using ContractValidator & DOMAIN_EXPERT_SCHEMA.
        Accepts optional fields (domain_concepts, compliance, scale, architecture_patterns, risks)
        without raising 'unexpected key' warnings.
        """
        result: Dict[str, Any] = {
            key: {"value": "", "ai_suggestion": ""} if key == "industry" else {"value": [], "ai_suggestion": []}
            for key in _EMPTY_OUTPUT
        }

        if raw is None:
            logger.warning("%s: raw LLM response is None", _AGENT_NAME)
            return result

        if isinstance(raw, list):
            raw_dict: Dict[str, Any] = {}
            for item in raw:
                if isinstance(item, dict):
                    raw_dict.update(item)
                elif isinstance(item, str) and item.strip():
                    raw_dict.setdefault("domain_constraints", []).append(item.strip())
            raw = raw_dict

        if isinstance(raw, dict):
            raw = ContractValidator.validate(raw, DOMAIN_EXPERT_SCHEMA)
            for key, val in raw.items():
                if key == "industry":
                    norm = _normalise_node(val)
                    val_str = norm["value"][0] if norm["value"] else _to_scalar(val)
                    sug_str = norm["ai_suggestion"][0] if norm["ai_suggestion"] else ""
                    result["industry"] = {"value": val_str, "ai_suggestion": sug_str}
                elif key in result:
                    norm = _normalise_node(val)
                    result[key]["value"].extend(norm["value"])
                    result[key]["ai_suggestion"].extend(norm["ai_suggestion"])
                else:
                    norm = _normalise_node(val)
                    result[key] = norm

        final_result: Dict[str, Any] = {}
        for key in _EMPTY_OUTPUT:
            if key == "industry":
                final_result[key] = result.get(key, {"value": "", "ai_suggestion": ""})
            else:
                node = result.get(key, {"value": [], "ai_suggestion": []})
                final_result[key] = {
                    "value": _dedupe(node.get("value", [])),
                    "ai_suggestion": _dedupe(node.get("ai_suggestion", [])),
                }

        return final_result

    @staticmethod
    def _build_note(result: Dict[str, Any]) -> str:
        parts: List[str] = []
        industry = result.get("industry", {})
        if industry.get("value") or industry.get("ai_suggestion"):
            industry_val = industry.get("value") or industry.get("ai_suggestion")
            parts.append(f"industry: {industry_val}")
        for key in ["domain_constraints", "compliance", "scale", "architecture_patterns", "risks"]:
            node = result.get(key, {})
            count = len(node.get("value", [])) + len(node.get("ai_suggestion", []))
            if count:
                parts.append(f"{key}: {count}")
        if not parts:
            return "Analysis complete — no new domain context extracted."
        return "Analysis complete — " + ", ".join(parts) + "."


# ── Utilities ─────────────────────────────────────────────────────────────────

_DE_CANONICAL_KEYS: Dict[str, str] = {
    "industry": "industry",
    "domain": "industry",
    "system_type": "industry",
    "category": "industry",

    "domain_constraints": "domain_constraints",
    "domain_constraint": "domain_constraints",
    "constraints": "domain_constraints",
    "operational_rules": "domain_constraints",

    "compliance": "compliance",
    "compliance_requirements": "compliance",
    "regulations": "compliance",
    "regulatory": "compliance",

    "scale": "scale",
    "scale_analysis": "scale",
    "metrics": "scale",

    "architecture_patterns": "architecture_patterns",
    "architecture_pattern": "architecture_patterns",
    "patterns": "architecture_patterns",

    "risks": "risks",
    "risk": "risks",
    "domain_risks": "risks",
}


def _to_list(value: Any) -> List[str]:
    """Coerce any value to a list of non-empty strings."""
    if isinstance(value, list):
        res: List[str] = []
        for v in value:
            if isinstance(v, dict):
                val = (
                    v.get("value")
                    or v.get("text")
                    or v.get("item")
                    or v.get("name")
                    or v.get("description")
                )
                if val is not None and str(val).strip():
                    res.append(str(val).strip())
                else:
                    for sub_v in v.values():
                        if sub_v is not None and str(sub_v).strip():
                            res.append(str(sub_v).strip())
            elif v is not None and not isinstance(v, (list, dict)):
                s = str(v).strip()
                if s:
                    res.append(s)
        return res
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if value is not None and not isinstance(value, (dict, list)):
        s = str(value).strip()
        if s:
            return [s]
    return []


def _to_scalar(value: Any) -> str:
    """Coerce any value to a single string."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list) and value:
        return str(value[0]).strip()
    return ""


def _dedupe(items: List[str]) -> List[str]:
    """Deduplicate list items preserving order."""
    seen = set()
    res: List[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            res.append(item)
    return res


def _categorize_de_string(text: str) -> str:
    """Categorize an unlabelled domain string based on keyword heuristics."""
    lower = text.lower()
    if any(k in lower for k in ["compliance", "gdpr", "hipaa", "pci", "soc2", "wcag", "ferpa", "regulation"]):
        return "compliance"
    if any(k in lower for k in ["pattern", "microservices", "monolith", "event-driven", "mvc", "cqrs", "serverless"]):
        return "architecture_patterns"
    if any(k in lower for k in ["scale", "users", "rps", "throughput", "volume", "qps"]):
        return "scale"
    if any(k in lower for k in ["risk", "threat", "vulnerability", "fraud", "breach"]):
        return "risks"
    if any(k in lower for k in ["constraint", "rule", "policy", "must"]):
        return "domain_constraints"
    return "industry"


def _normalise_node(node: Any) -> Dict[str, List[str]]:
    """Defensively extract value and ai_suggestion lists from a section node."""
    values: List[str] = []
    suggestions: List[str] = []

    if isinstance(node, dict):
        has_val = "value" in node
        has_sug = "ai_suggestion" in node
        if has_val or has_sug:
            if has_val:
                values.extend(_to_list(node.get("value")))
            if has_sug:
                suggestions.extend(_to_list(node.get("ai_suggestion")))
        else:
            for k, v in node.items():
                values.extend(_to_list(v))
    elif isinstance(node, (list, str)):
        values.extend(_to_list(node))

    return {
        "value": _dedupe(values),
        "ai_suggestion": _dedupe(suggestions),
    }


def _merge_list(existing: List[str], new_node: Any) -> List[str]:
    """
    Union new items from value[] and ai_suggestion[] into an existing list.
    Returns updated list (deduped, preserving order).
    """
    result = list(existing)
    if isinstance(new_node, dict):
        val_items = new_node.get("value", [])
        sug_items = new_node.get("ai_suggestion", [])
    elif isinstance(new_node, (list, str)):
        val_items = new_node
        sug_items = []
    else:
        val_items = []
        sug_items = []

    for item in _to_list(val_items):
        if item not in result:
            result.append(item)
    for item in _to_list(sug_items):
        if item not in result:
            result.append(item)
    return result


def _set_extended(dc: DomainContext, attr: str, node: Any) -> None:
    """
    Set or extend an extended attribute on the DomainContext dynamically.
    """
    all_items = _merge_list(getattr(dc, attr, []), node)
    setattr(dc, attr, all_items)


def _union_into(params: dict, key: str, new_node: Any) -> None:
    """
    Union new_node's value[] and ai_suggestion[] into params[key].
    Initialises the key if absent.
    """
    if key not in params or not isinstance(params[key], dict):
        params[key] = {"value": [], "ai_suggestion": []}

    current = params[key]
    if not isinstance(current.get("value"), list):
        if current.get("value") is None:
            current["value"] = []
        elif isinstance(current.get("value"), str):
            current["value"] = [current["value"]] if current["value"] else []
        else:
            current["value"] = [str(current["value"])]
    if not isinstance(current.get("ai_suggestion"), list):
        current["ai_suggestion"] = []

    norm = _normalise_node(new_node)
    for item in norm["value"]:
        if item not in current["value"]:
            current["value"].append(item)

    for item in norm["ai_suggestion"]:
        if item not in current["ai_suggestion"] and item not in current["value"]:
            current["ai_suggestion"].append(item)

