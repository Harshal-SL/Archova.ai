"""
Requirement Engineer Agent

Single responsibility:
  Extract and enrich the technical requirements dimension of the SRC.

Covers:
  - Functional Requirements
  - Non-Functional Requirements
  - Actors / User Roles
  - System Modules
  - API contracts (endpoints, request/response shapes)
  - Constraints
  - Third-party Integrations
  - User Workflows / Use Cases

Reads from:
  SRC.project_context.normalized_text   (primary input text)
  SRC.requirements.parameters           (existing extracted params to enrich)

Writes to:
  SRC.requirements.parameters           (enriched requirement fields)
  SRC.discussion_notes                  (reasoning notes)

Never touches:
  SRC.business_context    (Business Analyst's territory)
  SRC.domain_context      (Domain Expert's territory)
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from app.ree.models import SharedRequirementContext, REEStatus
from app.ree.agents.base_agent import BaseAIAgent
from app.ree.agents.agent_contracts import ContractValidator, REQUIREMENT_ENGINEER_SCHEMA
from app.ree.llm.model_registry import Capability

logger = logging.getLogger(__name__)

_AGENT_NAME = "RequirementEngineer"

# ── Prompt ────────────────────────────────────────────────────────────────────

_PROMPT_TEMPLATE = """\
AGENCY CONTRACT: Requirement Engineer

RESPONSIBILITY:
You are the Requirement Engineer. Your responsibility is to identify system capabilities, user roles, technical components, system inputs, system outputs, and API contracts, converting them into implementation-ready technical requirement specifications.

WHAT TO EXTRACT (OWNED FIELDS):
1. functional_requirements — System capabilities and actions (what the system must do).
2. non_functional_requirements — Technical quality attributes (performance, scalability, security, availability, latency).
3. actors — System user roles and external human/system actors.
4. modules — Major software building blocks and system components.
5. api_contracts — Key API endpoints (HTTP method, path, purpose).
6. inputs — System inputs, incoming data formats, and payloads.
7. outputs — System outputs, reports, and outgoing notifications.

WHAT NOT TO EXTRACT (DO NOT GENERATE):
- Business goals, KPIs, business objectives, ROI (Owned by Business Analyst).
- Stakeholders, business rules, business constraints (Owned by Business Analyst).
- Domain concepts, terminology, domain entities, compliance (Owned by Domain Expert).
- Risk analysis or architectural decisions.

PROJECT DESCRIPTION:
{project_text}

ALREADY EXTRACTED (do not repeat, only enrich or fill gaps):
{existing_params}

RULES:
- CRITICAL: Return ONLY a raw, valid JSON object starting with '{{' and ending with '}}'.
- Do NOT wrap the JSON in Markdown code fences (NO ```json).
- Do NOT include any preamble, intro, explanation, or postscript.
- If information cannot be inferred, return {{"value": [], "ai_suggestion": []}} for that key. Never fabricate information.
- Do NOT include any extra keys outside the schema.

OUTPUT SCHEMA:
{{
  "functional_requirements": {{
    "value": [],
    "ai_suggestion": []
  }},
  "non_functional_requirements": {{
    "value": [],
    "ai_suggestion": []
  }},
  "actors": {{
    "value": [],
    "ai_suggestion": []
  }},
  "modules": {{
    "value": [],
    "ai_suggestion": []
  }},
  "api_contracts": {{
    "value": [],
    "ai_suggestion": []
  }},
  "inputs": {{
    "value": [],
    "ai_suggestion": []
  }},
  "outputs": {{
    "value": [],
    "ai_suggestion": []
  }}
}}
"""

# ── Fallback (when LLM is unavailable) ───────────────────────────────────────

_EMPTY_OUTPUT: Dict[str, Any] = {
    "functional_requirements": {"value": [], "ai_suggestion": []},
    "non_functional_requirements": {"value": [], "ai_suggestion": []},
    "actors": {"value": [], "ai_suggestion": []},
    "modules": {"value": [], "ai_suggestion": []},
    "api_contracts": {"value": [], "ai_suggestion": []},
    "inputs": {"value": [], "ai_suggestion": []},
    "outputs": {"value": [], "ai_suggestion": []},
    "workflows": {"value": [], "ai_suggestion": []},
    "integrations": {"value": [], "ai_suggestion": []},
    "constraints": {"value": [], "ai_suggestion": []},
}


class RequirementEngineerAgent(BaseAIAgent):
    """
    AI specialist that focuses on technical requirement extraction.

    Reads the normalized project text and existing parameters from the SRC,
    calls the LLM with a focused requirement engineering prompt, and writes
    its findings into SRC.requirements.parameters and the extended fields
    (modules, api_contracts, workflows, integrations).
    """

    AGENT_NAME = _AGENT_NAME
    STAGE = "engineering"
    CAPABILITY = Capability.REASONING

    def run(self, src: SharedRequirementContext) -> SharedRequirementContext:
        """
        Run the Requirement Engineer's analysis pass.

        Args:
            src: Current SRC. Reads project_context and requirements.

        Returns:
            Updated SRC with requirements section enriched.
        """
        logger.info("%s: starting analysis", _AGENT_NAME)

        project_text = src.project_context.normalized_text or src.raw_input
        if not project_text.strip():
            self._add_note(src, "No project text available — skipping.")
            logger.warning("%s: project text is empty, skipping", _AGENT_NAME)
            return src

        # Build a compact summary of what's already extracted to avoid duplication
        existing_summary = self._summarise_existing(src.requirements.parameters)

        prompt = _PROMPT_TEMPLATE.format(
            project_text=project_text[:4000],   # cap to avoid exceeding context window
            existing_params=existing_summary,
        )

        result = self._call_llm(prompt, max_tokens=1800)

        if result is None:
            self._add_note(
                src,
                "LLM call failed or returned unparseable output. "
                "Requirements section not enriched by this agent."
            )
            logger.warning("%s: LLM call failed — using empty output", _AGENT_NAME)
            result = _EMPTY_OUTPUT

        # Validate and normalise the output shape
        result = self._normalise_output(result)

        # Write into SRC — only into the requirements section
        self._merge_into_requirements(src, result)

        # Persist the raw output for the Orchestrator's agent_outputs dict
        src.agent_outputs[_AGENT_NAME] = result

        note = self._build_note(result)
        self._add_note(src, note)
        logger.info("%s: complete — %s", _AGENT_NAME, note)

        return src

    # ── Merge ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _merge_into_requirements(
        src: SharedRequirementContext,
        result: Dict[str, Any],
    ) -> None:
        """
        Merge LLM output into SRC.requirements.parameters.

        Strategy:
          - Fields that map to existing parameters (functional_requirements,
            non_functional_requirements, actors): union new items into
            value and ai_suggestion lists.
          - New fields (modules, api_contracts, workflows, integrations,
            constraints): stored as new parameter keys.
          - Never overwrite a confirmed value[] that is already non-empty.
        """
        params = src.requirements.parameters

        _STANDARD_PARAM_MAP = {
            "functional_requirements": "functional_requirements",
            "non_functional_requirements": "non_functional_requirements",
            "actors": "actors",
            "constraints": "constraints",
            "integrations": "external_services",  # maps to existing field
        }

        _EXTENDED_FIELDS = ["modules", "api_contracts", "workflows"]

        for result_key, param_key in _STANDARD_PARAM_MAP.items():
            result_node = result.get(result_key, {})
            _union_into(params, param_key, result_node)

        for key in _EXTENDED_FIELDS:
            result_node = result.get(key, {})
            if isinstance(result_node, dict):
                param_key = f"re_{key}"
                _union_into(params, param_key, result_node)
                _union_into(params, key, result_node)

        # Sync system_behaviour from workflows or modules if present
        workflows_node = result.get("workflows", {})
        modules_node = result.get("modules", {})
        _union_into(params, "system_behaviour", workflows_node)
        _union_into(params, "system_behaviour", modules_node)

        # Sync back to flat parameters field
        src.parameters = params
        src.sync_requirements()

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _summarise_existing(parameters: dict) -> str:
        """
        Build a compact JSON summary of already-extracted parameters to
        include in the prompt so the LLM doesn't repeat what's already there.
        """
        summary: Dict[str, Any] = {}
        keys_of_interest = [
            "functional_requirements", "non_functional_requirements",
            "actors", "constraints", "external_services",
        ]
        for key in keys_of_interest:
            node = parameters.get(key)
            if isinstance(node, dict):
                val = node.get("value")
                if val:
                    summary[key] = val
        return json.dumps(summary, indent=2) if summary else "None extracted yet."

    @staticmethod
    def _normalise_output(raw: Any) -> Dict[str, Any]:
        """
        Contract-driven normalization using ContractValidator & REQUIREMENT_ENGINEER_SCHEMA.
        Accepts optional fields (inputs, outputs, modules, api_contracts, workflows, integrations, constraints)
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
                    raw_dict.setdefault("functional_requirements", []).append(item.strip())
            raw = raw_dict

        if isinstance(raw, str) and raw.strip():
            lines = [line.strip("- *").strip() for line in raw.splitlines() if line.strip()]
            raw = {"functional_requirements": lines}

        if isinstance(raw, dict):
            raw = ContractValidator.validate(raw, REQUIREMENT_ENGINEER_SCHEMA)
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
        counts = {
            k: len(result[k]["value"]) + len(result[k]["ai_suggestion"])
            for k in result
        }
        non_empty = {k: v for k, v in counts.items() if v > 0}
        if not non_empty:
            return "Analysis complete — no new items extracted."
        parts = ", ".join(f"{k}: {v}" for k, v in non_empty.items())
        return f"Analysis complete — new items: {parts}."


# ── Utilities ─────────────────────────────────────────────────────────────────

_RE_CANONICAL_KEYS: Dict[str, str] = {
    "functional_requirements": "functional_requirements",
    "functional_requirement": "functional_requirements",
    "functional": "functional_requirements",
    "features": "functional_requirements",
    "requirements": "functional_requirements",

    "non_functional_requirements": "non_functional_requirements",
    "non_functional_requirement": "non_functional_requirements",
    "non_functional": "non_functional_requirements",
    "nfr": "non_functional_requirements",
    "quality_attributes": "non_functional_requirements",
    "performance": "non_functional_requirements",
    "security": "non_functional_requirements",

    "actors": "actors",
    "actor": "actors",
    "user_roles": "actors",
    "user_role": "actors",
    "roles": "actors",
    "role": "actors",
    "users": "actors",

    "modules": "modules",
    "module": "modules",
    "components": "modules",
    "subsystems": "modules",

    "api_contracts": "api_contracts",
    "api_contract": "api_contracts",
    "apis": "api_contracts",
    "endpoints": "api_contracts",

    "constraints": "constraints",
    "constraint": "constraints",
    "limitations": "constraints",

    "integrations": "integrations",
    "integration": "integrations",
    "external_services": "integrations",
    "third_party": "integrations",

    "workflows": "workflows",
    "workflow": "workflows",
    "use_cases": "workflows",
    "user_flows": "workflows",
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


def _categorize_re_string(text: str) -> str:
    """Categorize an unlabelled requirement string based on keyword heuristics."""
    lower = text.lower()
    if any(k in lower for k in ["performance", "security", "latency", "availability", "scale", "uptime", "non-functional", "nfr"]):
        return "non_functional_requirements"
    if any(k in lower for k in ["user", "actor", "role", "admin", "student", "librarian"]):
        return "actors"
    if any(k in lower for k in ["api", "endpoint", "http", "get", "post", "put", "delete"]):
        return "api_contracts"
    if any(k in lower for k in ["module", "component", "subsystem"]):
        return "modules"
    if any(k in lower for k in ["integration", "external", "third-party", "third party"]):
        return "integrations"
    if any(k in lower for k in ["workflow", "flow", "step", "sequence"]):
        return "workflows"
    if any(k in lower for k in ["constraint", "limitation", "must be", "shall not"]):
        return "constraints"
    return "functional_requirements"


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


def _union_into(params: dict, key: str, new_node: Any) -> None:
    """
    Union new_node's value[] and ai_suggestion[] into params[key].
    Initialises the key if absent. Never overwrites existing confirmed values.
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

