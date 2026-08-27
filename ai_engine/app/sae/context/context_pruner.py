"""ContextPruner module for extracting high-signal, compact prerequisite snippets per agent."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
from app.sae.utils.enums import AgentRole


class ContextPruner:
    """Prunes SharedDesignContext (SDC) payloads to pass ONLY essential prerequisite sections per agent."""

    @classmethod
    def summarize_section(cls, data: Any, max_len: int = 1500) -> str:
        """Extract minified compact JSON string bounded by max_len."""
        if not data:
            return "{}"

        if isinstance(data, dict):
            # Unwrap nested document wrapper if present
            for inner_key in [
                "hld", "backend_lld", "database_lld", "frontend_lld",
                "security_lld", "cloud_lld", "requirement_analysis",
                "technology_recommendation", "architecture_planning"
            ]:
                if inner_key in data and isinstance(data[inner_key], dict):
                    data = data[inner_key]
                    break

            # Filter out bulky raw metadata/documents/digests
            pruned_dict = {}
            for k, v in data.items():
                if k in ("documents", "checksums", "change_history", "agent_metadata_history", "raw_decisions"):
                    continue
                pruned_dict[k] = v
            data = pruned_dict

        try:
            raw_str = json.dumps(data, separators=(",", ":"), default=str)
        except Exception:
            raw_str = str(data)

        if len(raw_str) > max_len:
            return raw_str[:max_len] + "... [pruned]"
        return raw_str

    @classmethod
    def get_pruned_context_for_agent(cls, agent_role: AgentRole, context: Any) -> Dict[str, str]:
        """Return a mapping of section_name -> pruned_json_str containing ONLY required dependencies."""
        pruned_snippets: Dict[str, str] = {}

        def get_sec(key: str) -> Optional[Any]:
            if hasattr(context, "get_section_content"):
                return context.get_section_content(key)
            if hasattr(context, "sections") and key in context.sections:
                sec = context.sections[key]
                return getattr(sec, "content", sec)
            if isinstance(context, dict):
                return context.get(key)
            return None

        if agent_role == AgentRole.TECHNOLOGY_ADVISOR:
            req = get_sec("requirement_analysis")
            pruned_snippets["requirement_analysis"] = cls.summarize_section(req, max_len=1500)

        elif agent_role == AgentRole.ARCHITECTURE_PLANNER:
            req = get_sec("requirement_analysis")
            tech = get_sec("technology_recommendation")
            pruned_snippets["requirement_analysis"] = cls.summarize_section(req, max_len=1200)
            pruned_snippets["technology_recommendation"] = cls.summarize_section(tech, max_len=1200)

        elif agent_role == AgentRole.HLD:
            plan = get_sec("architecture_planning") or get_sec("architecture_decision_plan")
            tech = get_sec("technology_recommendation")
            pruned_snippets["architecture_planning"] = cls.summarize_section(plan, max_len=1500)
            pruned_snippets["technology_recommendation"] = cls.summarize_section(tech, max_len=1200)

        elif agent_role in (AgentRole.BACKEND, AgentRole.DATABASE, AgentRole.FRONTEND):
            hld = get_sec("hld")
            plan = get_sec("architecture_planning") or get_sec("architecture_decision_plan")
            tech = get_sec("technology_recommendation")
            req = get_sec("requirement_analysis")
            pruned_snippets["hld"] = cls.summarize_section(hld, max_len=1500)
            pruned_snippets["architecture_planning"] = cls.summarize_section(plan, max_len=1000)
            pruned_snippets["technology_recommendation"] = cls.summarize_section(tech, max_len=1000)
            pruned_snippets["requirement_analysis"] = cls.summarize_section(req, max_len=1000)

        elif agent_role == AgentRole.SECURITY:
            hld = get_sec("hld")
            backend = get_sec("backend_lld")
            database = get_sec("database_lld")
            frontend = get_sec("frontend_lld")
            pruned_snippets["hld"] = cls.summarize_section(hld, max_len=1200)
            pruned_snippets["backend_lld"] = cls.summarize_section(backend, max_len=1200)
            pruned_snippets["database_lld"] = cls.summarize_section(database, max_len=1000)
            pruned_snippets["frontend_lld"] = cls.summarize_section(frontend, max_len=1000)

        elif agent_role == AgentRole.CLOUD:
            hld = get_sec("hld")
            backend = get_sec("backend_lld")
            database = get_sec("database_lld")
            frontend = get_sec("frontend_lld")
            security = get_sec("security_lld")
            pruned_snippets["hld"] = cls.summarize_section(hld, max_len=1200)
            pruned_snippets["backend_lld"] = cls.summarize_section(backend, max_len=1000)
            pruned_snippets["database_lld"] = cls.summarize_section(database, max_len=1000)
            pruned_snippets["frontend_lld"] = cls.summarize_section(frontend, max_len=1000)
            pruned_snippets["security_lld"] = cls.summarize_section(security, max_len=1200)

        elif agent_role == AgentRole.ARCHITECTURE_VALIDATOR:
            for key in ["requirement_analysis", "technology_recommendation", "hld", "backend_lld", "database_lld", "frontend_lld", "security_lld", "cloud_lld"]:
                sec_val = get_sec(key)
                if sec_val:
                    pruned_snippets[key] = cls.summarize_section(sec_val, max_len=1000)

        return pruned_snippets
