"""
Business Analyst Agent

Single responsibility:
  Analyse the business dimension of the project and populate the
  SRC.business_context section.

Covers:
  - Business Goals
  - Business Rules
  - Stakeholders (business roles, not system actors)
  - KPIs (Key Performance Indicators)
  - Pain Points / Problems being solved
  - Assumptions

Reads from:
  SRC.project_context.normalized_text   (primary input text)
  SRC.business_context                  (existing state to enrich)

Writes to:
  SRC.business_context                  (its exclusive section)
  SRC.discussion_notes                  (reasoning notes)

Never touches:
  SRC.requirements.parameters   (Requirement Engineer's territory)
  SRC.domain_context            (Domain Expert's territory)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.ree.models import SharedRequirementContext, BusinessContext
from app.ree.agents.base_agent import BaseAIAgent
from app.ree.agents.agent_contracts import ContractValidator, BUSINESS_ANALYST_SCHEMA
from app.ree.llm.model_registry import Capability

logger = logging.getLogger(__name__)

_AGENT_NAME = "BusinessAnalyst"

# ── Prompt ────────────────────────────────────────────────────────────────────

_PROMPT_TEMPLATE = """\
AGENCY CONTRACT: Business Analyst

RESPONSIBILITY:
You are the Business Analyst. Your responsibility is to analyze the business context, objectives, rules, constraints, stakeholders, priorities, and project scope.

WHAT TO EXTRACT (OWNED FIELDS):
1. business_goals — Strategic business outcomes and project objectives.
2. business_rules — Business policies, operational rules, and logic governing the business.
3. constraints — Business and financial constraints, budget/timeline boundaries.
4. stakeholders — Key business stakeholders and organizational groups (Product Owner, Operations, Executive).
5. kpis — Measurable success metrics (ROI, conversion rate, processing time, efficiency).
6. pain_points — Current business problems or operational inefficiencies being solved.
7. priorities — Critical business priorities, phase targets, and scoping boundaries.

WHAT NOT TO EXTRACT (DO NOT GENERATE):
- APIs, endpoints, HTTP methods (Owned by Requirement Engineer).
- System modules, code architecture, software building blocks (Owned by Requirement Engineer).
- Functional requirements or user system actions (Owned by Requirement Engineer).
- User actors or system user roles (Owned by Requirement Engineer).
- Domain terminology or technical domain standards (Owned by Domain Expert).

PROJECT DESCRIPTION:
{project_text}

ALREADY KNOWN BUSINESS CONTEXT:
{existing_context}

RULES:
- CRITICAL: Return ONLY a raw, valid JSON object starting with '{{' and ending with '}}'.
- Do NOT wrap the JSON in Markdown code fences (NO ```json).
- Do NOT include any preamble, intro, explanation, or postscript.
- Extract business context, objectives, rules, and constraints ONLY for the system described in the CURRENT Problem Statement.
- Do NOT introduce business capabilities, rules, or constraints from other domains, previous runs, or generic industry templates.
- If information cannot be inferred from the current project description, return {{"value": [], "ai_suggestion": []}} for that key. Never fabricate information.
- Do NOT include any extra keys outside the schema.

OUTPUT SCHEMA:
{{
  "business_goals": {{
    "value": [],
    "ai_suggestion": []
  }},
  "business_rules": {{
    "value": [],
    "ai_suggestion": []
  }},
  "constraints": {{
    "value": [],
    "ai_suggestion": []
  }},
  "stakeholders": {{
    "value": [],
    "ai_suggestion": []
  }},
  "kpis": {{
    "value": [],
    "ai_suggestion": []
  }},
  "pain_points": {{
    "value": [],
    "ai_suggestion": []
  }},
  "priorities": {{
    "value": [],
    "ai_suggestion": []
  }}
}}
"""

_EMPTY_OUTPUT: Dict[str, Any] = {
    "business_goals": {"value": [], "ai_suggestion": []},
    "business_rules": {"value": [], "ai_suggestion": []},
    "constraints": {"value": [], "ai_suggestion": []},
    "stakeholders": {"value": [], "ai_suggestion": []},
    "kpis": {"value": [], "ai_suggestion": []},
    "pain_points": {"value": [], "ai_suggestion": []},
    "priorities": {"value": [], "ai_suggestion": []},
}


class BusinessAnalystAgent(BaseAIAgent):
    """
    AI specialist that analyses business context.

    Reads the normalized project text from the SRC and calls the LLM
    with a focused business analysis prompt. Writes its findings
    exclusively into SRC.business_context.
    """

    AGENT_NAME = _AGENT_NAME
    STAGE = "engineering"
    CAPABILITY = Capability.BUSINESS_ANALYSIS

    def run(self, src: SharedRequirementContext) -> SharedRequirementContext:
        """
        Run the Business Analyst's analysis pass.

        Args:
            src: Current SRC. Reads project_context and business_context.

        Returns:
            Updated SRC with business_context populated.
        """
        logger.info("%s: starting analysis", _AGENT_NAME)

        project_text = src.project_context.normalized_text or src.raw_input
        if not project_text.strip():
            self._add_note(src, "No project text available — skipping.")
            logger.warning("%s: project text is empty, skipping", _AGENT_NAME)
            return src

        # Build summary of already-known business context
        existing_summary = self._summarise_existing(src.business_context)

        prompt = _PROMPT_TEMPLATE.format(
            project_text=project_text[:4000],
            existing_context=existing_summary,
        )

        result = self._call_llm(prompt, max_tokens=1000, temperature=0.1)

        if result is None:
            self._add_note(
                src,
                "LLM API rate-limited or unavailable. "
                "Utilizing deterministic rule-based business context fallback."
            )
            logger.warning("%s: LLM call failed — using rule-based fallback", _AGENT_NAME)
            result = self._generate_rule_based_fallback(project_text)

        result = self._normalise_output(result)

        # Write into SRC — exclusively into business_context
        self._merge_into_business_context(src, result)

        # Store raw output
        src.agent_outputs[_AGENT_NAME] = result

        note = self._build_note(result)
        self._add_note(src, note)
        logger.info("%s: complete — %s", _AGENT_NAME, note)

        return src

    # ── Merge ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _merge_into_business_context(
        src: SharedRequirementContext,
        result: Dict[str, Any],
    ) -> None:
        """
        Merge LLM output into SRC.business_context and sync into SRC.parameters.
        """
        bc = src.business_context
        goals_node = result.get("business_goals", {})
        rules_node = result.get("business_rules", {})
        stakeholders_node = result.get("stakeholders", {})

        # business_goals → business_objectives
        bc.business_objectives = _merge_list(
            bc.business_objectives,
            goals_node,
        )

        # business_rules → constraints (business rules are constraints)
        bc.constraints = _merge_list(
            bc.constraints,
            rules_node,
        )

        # stakeholders
        bc.stakeholders = _merge_list(
            bc.stakeholders,
            stakeholders_node,
        )

        # Extended fields
        _set_extended(bc, "kpis", result.get("kpis", {}))
        _set_extended(bc, "pain_points", result.get("pain_points", {}))
        _set_extended(bc, "assumptions", result.get("assumptions", {}))

        # Sync into flat parameters for downstream agents and RequirementReviewAgent
        params = src.parameters
        _union_into(params, "core_objectives", goals_node)
        _union_into(params, "business_objectives", goals_node)
        if not src.get_parameter_value("goal") and bc.business_objectives:
            src.set_parameter_value("goal", bc.business_objectives[0])

        _union_into(params, "constraints", rules_node)
        _union_into(params, "stakeholders", stakeholders_node)
        if not src.get_parameter_value("actors") and bc.stakeholders:
            _union_into(params, "actors", stakeholders_node)

        src.sync_requirements()

    def _generate_rule_based_fallback(self, project_text: str) -> Dict[str, Any]:
        """Generate rule-based business context fallback when LLM API returns None."""
        return {
            "business_goals": ["Automate core processes and improve operational efficiency"],
            "business_rules": ["Validate authorization for sensitive actions"],
            "constraints": ["Regulatory compliance and data privacy standards"],
            "stakeholders": ["Business Owners", "System Administrators", "End Users"],
            "kpis": ["System Availability", "Response Latency", "User Throughput"],
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _summarise_existing(bc: BusinessContext) -> str:
        """Build a compact text summary of the existing business context."""
        parts: List[str] = []
        if bc.business_objectives:
            parts.append(f"Goals: {', '.join(bc.business_objectives[:3])}")
        if bc.stakeholders:
            parts.append(f"Stakeholders: {', '.join(bc.stakeholders[:3])}")
        if bc.constraints:
            parts.append(f"Constraints: {', '.join(bc.constraints[:3])}")
        return "; ".join(parts) if parts else "None known yet."

    @staticmethod
    def _normalise_output(raw: Any) -> Dict[str, Any]:
        """
        Contract-driven normalization using ContractValidator & BUSINESS_ANALYST_SCHEMA.
        Accepts optional fields (priorities, kpis, pain_points, scope, assumptions)
        without raising 'unexpected key' warnings.
        """
        result: Dict[str, Dict[str, List[str]]] = {
            key: {"value": [], "ai_suggestion": []}
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
                    raw_dict.setdefault("business_goals", []).append(item.strip())
            raw = raw_dict

        if isinstance(raw, str) and raw.strip():
            lines = [line.strip("- *").strip() for line in raw.splitlines() if line.strip()]
            raw = {"business_goals": lines}

        if isinstance(raw, dict):
            raw = ContractValidator.validate(raw, BUSINESS_ANALYST_SCHEMA)
            for key, val in raw.items():
                norm = _normalise_node(val)
                if key in result:
                    result[key]["value"].extend(norm["value"])
                    result[key]["ai_suggestion"].extend(norm["ai_suggestion"])
                else:
                    result[key] = norm

        final_result: Dict[str, Any] = {}
        for key in _EMPTY_OUTPUT:
            node = result.get(key, {"value": [], "ai_suggestion": []})
            final_result[key] = {
                "value": _dedupe(node.get("value", [])),
                "ai_suggestion": _dedupe(node.get("ai_suggestion", [])),
            }

        return final_result

    @staticmethod
    def _build_note(result: Dict[str, Any]) -> str:
        if not isinstance(result, dict):
            return "Analysis complete — no new business context extracted."
        counts = {}
        for k in _EMPTY_OUTPUT:
            node = result.get(k)
            if isinstance(node, dict):
                v_len = len(node.get("value", [])) if isinstance(node.get("value"), list) else 0
                s_len = len(node.get("ai_suggestion", [])) if isinstance(node.get("ai_suggestion"), list) else 0
                counts[k] = v_len + s_len
            else:
                counts[k] = 0

        non_empty = {k: v for k, v in counts.items() if v > 0}
        if not non_empty:
            return "Analysis complete — no new business context extracted."
        parts = ", ".join(f"{k}: {v}" for k, v in non_empty.items())
        return f"Analysis complete — new items: {parts}."


# ── Utilities ─────────────────────────────────────────────────────────────────

_CANONICAL_KEYS: Dict[str, str] = {
    "business_goals": "business_goals",
    "business_goal": "business_goals",
    "goals": "business_goals",
    "goal": "business_goals",
    "business_objectives": "business_goals",
    "business_objective": "business_goals",
    "objectives": "business_goals",
    "objective": "business_goals",

    "business_rules": "business_rules",
    "business_rule": "business_rules",
    "rules": "business_rules",
    "rule": "business_rules",
    "constraints": "business_rules",
    "constraint": "business_rules",
    "policies": "business_rules",
    "policy": "business_rules",

    "stakeholders": "stakeholders",
    "stakeholder": "stakeholders",
    "roles": "stakeholders",
    "role": "stakeholders",
    "users": "stakeholders",
    "user": "stakeholders",

    "kpis": "kpis",
    "kpi": "kpis",
    "metrics": "kpis",
    "metric": "kpis",
    "key_performance_indicators": "kpis",

    "pain_points": "pain_points",
    "pain_point": "pain_points",
    "painpoints": "pain_points",
    "problems": "pain_points",
    "problem": "pain_points",
    "issues": "pain_points",
    "issue": "pain_points",

    "assumptions": "assumptions",
    "assumption": "assumptions",
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


def _dedupe(items: List[str]) -> List[str]:
    """Deduplicate list items preserving order."""
    seen = set()
    res: List[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            res.append(item)
    return res


def _categorize_string(text: str) -> str:
    """Categorize an unlabelled string based on keyword heuristics."""
    lower = text.lower()
    if any(k in lower for k in ["rule", "policy", "constraint", "must be", "shall not"]):
        return "business_rules"
    if any(k in lower for k in ["stakeholder", "user", "role", "actor", "owner", "investor", "persona", "staff", "admin", "administrator", "manager", "operator", "member", "participant"]):
        return "stakeholders"
    if any(k in lower for k in ["kpi", "metric", "measure", "churn", "conversion", "revenue", "roi"]):
        return "kpis"
    if any(k in lower for k in ["pain", "problem", "issue", "bottleneck", "frustration", "challenge"]):
        return "pain_points"
    if "assumption" in lower:
        return "assumptions"
    return "business_goals"


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


def _set_extended(bc: BusinessContext, attr: str, node: Any) -> None:
    """
    Set or extend an extended attribute on the BusinessContext.

    BusinessContext does not define kpis/pain_points/assumptions as
    dataclass fields, so we attach them dynamically. The serialisation
    in to_dict() is handled by the extended_fields property below.
    """
    all_items = _merge_list(getattr(bc, attr, []), node)
    setattr(bc, attr, all_items)


def _union_into(params: dict, key: str, new_node: Any) -> None:
    """
    Union new_node's value[] and ai_suggestion[] into params[key].
    Initialises the key if absent.
    """
    if key not in params or not isinstance(params[key], dict):
        params[key] = {"value": [], "ai_suggestion": []}

    current = params[key]
    if not isinstance(current.get("value"), list):
        current["value"] = [] if current.get("value") is None else [str(current["value"])]
    if not isinstance(current.get("ai_suggestion"), list):
        current["ai_suggestion"] = []

    norm = _normalise_node(new_node)
    for item in norm["value"]:
        if item not in current["value"]:
            current["value"].append(item)
    for item in norm["ai_suggestion"]:
        if item not in current["ai_suggestion"] and item not in current["value"]:
            current["ai_suggestion"].append(item)


