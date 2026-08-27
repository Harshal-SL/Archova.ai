"""Requirement Analysis Agent for SAE v2."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from app.sae.agents.base_agent import BaseArchitectureAgent
from app.sae.models.response_models import RequirementAnalysisResponse
from app.sae.prompts.requirement_analysis_prompt import (
    REQUIREMENT_ANALYSIS_SYSTEM_PROMPT,
    REQUIREMENT_ANALYSIS_USER_PROMPT_TEMPLATE,
)
from app.sae.providers.llm_provider import OpenRouterProvider
from app.sae.services.architecture_knowledge_service import ArchitectureKnowledgeService
from app.sae.utils.domain_lock import DomainContext, DomainLockEngine, validate_requirement_contract

logger = logging.getLogger(__name__)


class RequirementAnalysisAgent(BaseArchitectureAgent):
    """Agent responsible for analyzing ARSRS specifications and extracting structured requirements."""

    role: str = "requirement_analysis"

    def __init__(
        self,
        llm_provider: Optional[OpenRouterProvider] = None,
        knowledge_service: Optional[ArchitectureKnowledgeService] = None,
        model_name: Optional[str] = None,
    ) -> None:
        super().__init__(
            llm_provider=llm_provider,
            knowledge_service=knowledge_service,
            model_name=model_name,
        )

    def _prune_arsrs(self, arsrs: Dict[str, Any]) -> Dict[str, Any]:
        """Extract essential requirement fields to preserve clarity."""
        pruned: Dict[str, Any] = {}
        if "project_profile" in arsrs and isinstance(arsrs["project_profile"], dict):
            pruned["project_profile"] = {
                k: v for k, v in arsrs["project_profile"].items()
                if k in ["goal", "system_type", "domain", "success_criteria"]
            }
        elif "goal" in arsrs:
            pruned["goal"] = arsrs["goal"]

        if "business_context" in arsrs and isinstance(arsrs["business_context"], dict):
            pruned["business_context"] = {
                k: v for k, v in arsrs["business_context"].items()
                if k in ["business_objectives", "stakeholders", "business_rules", "constraints", "assumptions"] and v
            }

        if "domain_context" in arsrs and isinstance(arsrs["domain_context"], dict):
            pruned["domain_context"] = {
                k: v for k, v in arsrs["domain_context"].items()
                if k in ["industry", "domain_concepts", "compliance"] and v
            }

        for key in [
            "modules",
            "workflows",
            "functional_requirements",
            "non_functional_requirements",
            "actors",
            "constraints",
            "success_criteria",
        ]:
            if key in arsrs and arsrs[key]:
                pruned[key] = arsrs[key]

        return pruned if pruned else arsrs

    def _build_prompt(self, arsrs: Dict[str, Any], domain_ctx: DomainContext) -> str:
        clean_arsrs = self._prune_arsrs(arsrs)
        arsrs_str = json.dumps(clean_arsrs, indent=2, default=str)
        canonical_str = domain_ctx.get_requirements_summary()
        return (
            f"{REQUIREMENT_ANALYSIS_USER_PROMPT_TEMPLATE.format(arsrs_content=arsrs_str)}\n\n"
            f"=== LOCKED DOMAIN CONTEXT ===\n"
            f"Domain: {domain_ctx.domain_name}\n"
            f"System Name: {domain_ctx.system_name}\n"
            f"Canonical Requirements:\n{canonical_str}\n"
        )

    async def run_async(
        self,
        arsrs: Dict[str, Any],
        domain_ctx: Optional[DomainContext] = None,
    ) -> Dict[str, Any]:
        """Asynchronously analyze ARSRS with locked domain and live agent-owned RAG context."""
        ctx = domain_ctx or DomainLockEngine.lock_domain_and_requirements(arsrs)
        clean_arsrs = self._prune_arsrs(arsrs)

        # 1. Retrieve domain-specific RAG context
        rag_block, rag_meta = await self.retrieve_rag_context(clean_arsrs)

        # 2. Build prompt and inject additive RAG context & domain grounding
        base_prompt = self._build_prompt(arsrs, ctx)
        prompt = self.inject_rag_context(base_prompt, rag_block)
        prompt = self.inject_domain_fence(prompt, domain_ctx=ctx, arsrs=arsrs)

        # 3. Call LLM
        result: RequirementAnalysisResponse = await self.llm_provider.generate_structured_async(
            prompt=prompt,
            response_model=RequirementAnalysisResponse,
            model_name=self.model_name,
            system_prompt=REQUIREMENT_ANALYSIS_SYSTEM_PROMPT,
            agent_role=self.role,
            temperature=0.1,
        )

        res_dict = result.model_dump(mode="json") if hasattr(result, "model_dump") else {}

        # 4. Strict Pipeline Contract Hydration & Quality Floor Guarantee
        # If the LLM dropped fields or failed to populate actors/modules/workflows, hydrate from validated canonical baseline.
        if not res_dict.get("functional_requirements") or len(res_dict.get("functional_requirements", [])) < 1:
            res_dict["functional_requirements"] = ctx.functional_requirements

        if not res_dict.get("non_functional_requirements") or len(res_dict.get("non_functional_requirements", [])) < 1:
            res_dict["non_functional_requirements"] = ctx.non_functional_requirements

        if not res_dict.get("actors") or len(res_dict.get("actors", [])) < 1:
            res_dict["actors"] = ctx.actors

        if not res_dict.get("modules") or len(res_dict.get("modules", [])) < 1:
            res_dict["modules"] = ctx.modules

        if not res_dict.get("constraints") or len(res_dict.get("constraints", [])) < 1:
            res_dict["constraints"] = ctx.constraints

        if not res_dict.get("assumptions") or len(res_dict.get("assumptions", [])) < 1:
            res_dict["assumptions"] = ctx.assumptions

        if not res_dict.get("key_workflows") or len(res_dict.get("key_workflows", [])) < 1:
            res_dict["key_workflows"] = ctx.key_workflows

        if not res_dict.get("domain_gap_analysis") or not isinstance(res_dict.get("domain_gap_analysis"), dict) or not res_dict.get("domain_gap_analysis", {}).get("checklist_status"):
            res_dict["domain_gap_analysis"] = ctx.domain_gap_analysis

        if not res_dict.get("domain_checklist"):
            res_dict["domain_checklist"] = ctx.domain_checklist

        res_dict["system_name"] = res_dict.get("system_name") or ctx.system_name
        res_dict["domain"] = ctx.domain_name
        res_dict["system_type"] = res_dict.get("system_type") or ctx.system_type

        return self.attach_rag_metadata(res_dict, rag_meta)

    def run(self, arsrs: Dict[str, Any], domain_ctx: Optional[DomainContext] = None) -> Dict[str, Any]:
        """Synchronously analyze ARSRS and return structured dict."""
        ctx = domain_ctx or DomainLockEngine.lock_domain_and_requirements(arsrs)
        prompt = self._build_prompt(arsrs, ctx)
        result: RequirementAnalysisResponse = self.llm_provider.generate_structured(
            prompt=prompt,
            model_name=self.model_name,
            response_model=RequirementAnalysisResponse,
            system_prompt=REQUIREMENT_ANALYSIS_SYSTEM_PROMPT,
            agent_name=self.role,
            temperature=0.1,
        )
        res_dict = result.model_dump(mode="json") if hasattr(result, "model_dump") else {}
        if not res_dict.get("functional_requirements"):
            res_dict["functional_requirements"] = ctx.functional_requirements
        if not res_dict.get("actors"):
            res_dict["actors"] = ctx.actors
        if not res_dict.get("modules"):
            res_dict["modules"] = ctx.modules
        return res_dict
