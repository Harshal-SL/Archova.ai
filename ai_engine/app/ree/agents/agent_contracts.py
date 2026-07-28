"""
Agent Contracts, Schemas, and Contract Validator

Single source of truth for agent output schemas, required fields, optional fields,
forbidden fields, and contract validation across all REE agents.
"""

from typing import Any, Dict, List, Set
import logging

logger = logging.getLogger(__name__)


class AgentSchema:
    def __init__(
        self,
        agent_name: str,
        required: List[str],
        optional: List[str],
        forbidden: List[str],
        canonical_map: Dict[str, str] = None,
    ):
        self.agent_name = agent_name
        self.required = required
        self.optional = optional
        self.forbidden = forbidden
        self.canonical_map = canonical_map or {}

    @property
    def valid_fields(self) -> Set[str]:
        return set(self.required) | set(self.optional)


# ── Business Analyst Contract Schema ──────────────────────────────────────────

BUSINESS_ANALYST_SCHEMA = AgentSchema(
    agent_name="BusinessAnalyst",
    required=["business_goals", "business_rules", "constraints", "stakeholders"],
    optional=["kpis", "pain_points", "priorities", "scope", "assumptions"],
    forbidden=[
        "functional_requirements", "non_functional_requirements", "actors",
        "modules", "api_contracts", "inputs", "outputs", "industry",
        "domain_concepts", "compliance"
    ],
    canonical_map={
        "business_goals": "business_goals", "business_goal": "business_goals", "goals": "business_goals",
        "business_objectives": "business_goals", "business_objective": "business_goals", "objectives": "business_goals",
        "business_rules": "business_rules", "business_rule": "business_rules", "rules": "business_rules",
        "constraints": "constraints", "constraint": "constraints",
        "stakeholders": "stakeholders", "stakeholder": "stakeholders",
        "kpis": "kpis", "kpi": "kpis", "metrics": "kpis",
        "pain_points": "pain_points", "pain_point": "pain_points",
        "priorities": "priorities", "priority": "priorities",
        "scope": "scope",
        "assumptions": "assumptions", "assumption": "assumptions",
    }
)


# ── Requirement Engineer Contract Schema ──────────────────────────────────────

REQUIREMENT_ENGINEER_SCHEMA = AgentSchema(
    agent_name="RequirementEngineer",
    required=["functional_requirements", "actors"],
    optional=[
        "non_functional_requirements", "modules", "api_contracts",
        "inputs", "outputs", "workflows", "integrations", "constraints"
    ],
    forbidden=[
        "business_goals", "business_rules", "stakeholders", "kpis",
        "industry", "domain_concepts", "compliance"
    ],
    canonical_map={
        "functional_requirements": "functional_requirements", "functional_requirement": "functional_requirements", "features": "functional_requirements", "requirements": "functional_requirements",
        "non_functional_requirements": "non_functional_requirements", "non_functional": "non_functional_requirements", "nfr": "non_functional_requirements",
        "actors": "actors", "actor": "actors", "user_roles": "actors", "roles": "actors",
        "modules": "modules", "module": "modules", "components": "modules",
        "api_contracts": "api_contracts", "apis": "api_contracts", "endpoints": "api_contracts",
        "inputs": "inputs", "input": "inputs",
        "outputs": "outputs", "output": "outputs",
        "workflows": "workflows", "workflow": "workflows",
        "integrations": "integrations", "integration": "integrations",
        "constraints": "constraints",
    }
)


# ── Domain Expert Contract Schema ─────────────────────────────────────────────

DOMAIN_EXPERT_SCHEMA = AgentSchema(
    agent_name="DomainExpert",
    required=["industry", "domain_constraints"],
    optional=[
        "domain_concepts", "compliance", "scale", "architecture_patterns",
        "risks", "domain_terminology", "domain_entities", "domain_assumptions", "domain_relationships"
    ],
    forbidden=[
        "functional_requirements", "non_functional_requirements", "business_goals",
        "business_rules", "api_contracts", "modules", "actors"
    ],
    canonical_map={
        "industry": "industry", "domain": "industry",
        "domain_concepts": "domain_concepts", "domain_concept": "domain_concepts", "terminology": "domain_concepts",
        "domain_constraints": "domain_constraints", "domain_constraint": "domain_constraints", "constraints": "domain_constraints",
        "compliance": "compliance", "regulations": "compliance", "standards": "compliance",
        "scale": "scale", "capacity": "scale",
        "architecture_patterns": "architecture_patterns", "patterns": "architecture_patterns",
        "risks": "risks", "risk": "risks",
    }
)


# ── Contract Validator ────────────────────────────────────────────────────────

class ContractValidator:
    """
    Dedicated Contract Validator between LLM JSON response and Shared Requirement Context.
    Enforces required, optional, and forbidden field contracts without hardcoded if/else chains.
    """

    @staticmethod
    def validate(raw_dict: Dict[str, Any], schema: AgentSchema) -> Dict[str, Any]:
        """
        Validate and filter a parsed JSON dictionary against an AgentSchema.
        """
        if not isinstance(raw_dict, dict):
            logger.warning("ContractValidator [%s]: Raw input is not a dict (%s)", schema.agent_name, type(raw_dict).__name__)
            return {}

        # Unwrap top-level wrapper objects e.g. {"value": {...}}, {"data": {...}}, {"result": {...}}
        if "value" in raw_dict and isinstance(raw_dict["value"], dict):
            raw_dict = raw_dict["value"]
        elif len(raw_dict) == 1:
            single_key, single_val = next(iter(raw_dict.items()))
            k_low = str(single_key).lower().strip()
            if isinstance(single_val, dict) and k_low in ("data", "result", "response", "output", "json", "payload"):
                raw_dict = single_val

        validated: Dict[str, Any] = {}

        for key, value in raw_dict.items():
            k_lower = str(key).lower().strip()
            if k_lower in ("value", "ai_suggestion"):
                continue

            canon = schema.canonical_map.get(k_lower, k_lower)

            if canon in schema.forbidden or k_lower in schema.forbidden:
                logger.warning(
                    "ContractValidator [%s]: Forbidden field '%s' ignored under contract boundaries",
                    schema.agent_name, key
                )
                continue

            if canon in schema.required or canon in schema.optional:
                logger.info("Accepted optional field: %s", canon)
                validated[canon] = value
            else:
                logger.warning("ContractValidator [%s]: Field '%s' is not in contract schema — ignoring", schema.agent_name, key)

        # Ensure required keys exist
        missing_required = [f for f in schema.required if f not in validated]
        if missing_required:
            logger.info("ContractValidator [%s]: Missing required contract field(s) %s — initializing defaults", schema.agent_name, missing_required)
            for m in missing_required:
                validated[m] = {"value": [], "ai_suggestion": []} if m != "industry" else {"value": "", "ai_suggestion": ""}

        return validated
