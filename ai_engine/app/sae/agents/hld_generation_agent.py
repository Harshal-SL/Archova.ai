"""High Level Design (HLD) Generation Agent for SAE v2."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from app.sae.agents.base_agent import BaseArchitectureAgent
from app.sae.models.response_models import HLDResponse
from app.sae.prompts.hld_generation_prompt import (
    HLD_GENERATION_SYSTEM_PROMPT,
    HLD_GENERATION_USER_PROMPT_TEMPLATE,
)
from app.sae.providers.llm_provider import OpenRouterProvider
from app.sae.services.architecture_knowledge_service import ArchitectureKnowledgeService


from app.sae.utils.domain_lock import DomainContext


class HLDGenerationAgent(BaseArchitectureAgent):
    """Agent responsible for generating system High Level Design (HLD)."""

    role: str = "hld"

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

    def _build_prompt(
        self,
        req_analysis: Dict[str, Any],
        tech_rec: Dict[str, Any],
        adp: Dict[str, Any],
        domain_ctx: Optional[DomainContext] = None,
    ) -> str:
        base_str = HLD_GENERATION_USER_PROMPT_TEMPLATE.format(
            requirement_analysis_summary=json.dumps(req_analysis, indent=2, default=str),
            technology_recommendation_summary=json.dumps(tech_rec, indent=2, default=str),
            architecture_decision_summary=json.dumps(adp, indent=2, default=str),
        )
        if domain_ctx:
            return (
                f"{base_str}\n\n"
                f"=== LOCKED DOMAIN & CANONICAL REQUIREMENTS ===\n"
                f"Domain: {domain_ctx.domain_name}\n"
                f"System Name: {domain_ctx.system_name}\n"
                f"Canonical Requirements:\n{domain_ctx.get_requirements_summary()}\n"
                f"Every service MUST reference at least one canonical FR-XXX or NFR-XXX ID.\n"
            )
        return base_str

    async def run_async(
        self,
        req_analysis: Dict[str, Any],
        tech_rec: Dict[str, Any],
        adp: Dict[str, Any],
        domain_ctx: Optional[DomainContext] = None,
    ) -> Dict[str, Any]:
        """Asynchronously generate High Level Design with live agent-owned RAG context."""
        context = {
            "domain": domain_ctx.domain_name if domain_ctx else req_analysis.get("domain", ""),
            "system_name": domain_ctx.system_name if domain_ctx else req_analysis.get("system_name", ""),
            "architecture_style": adp.get("architecture_style", "Modular Monolith"),
            "modules": req_analysis.get("modules", []),
            "tech_stack": tech_rec,
        }

        # 1. Retrieve domain-specific RAG context
        rag_block, rag_meta = await self.retrieve_rag_context(context)

        # 2. Build prompt and inject additive RAG context & authoritative domain fence
        base_prompt = self._build_prompt(req_analysis, tech_rec, adp, domain_ctx)
        prompt = self.inject_rag_context(base_prompt, rag_block)
        prompt = self.inject_domain_fence(prompt, domain_ctx=domain_ctx)

        # 3. Call LLM
        result: HLDResponse = await self.llm_provider.generate_structured_async(
            prompt=prompt,
            response_model=HLDResponse,
            model_name=self.model_name,
            system_prompt=HLD_GENERATION_SYSTEM_PROMPT,
            agent_role=self.role,
            temperature=0.2,
        )

        res_dict = result.model_dump(mode="json")
        return self.attach_rag_metadata(res_dict, rag_meta)

    def run(
        self,
        req_analysis: Dict[str, Any],
        tech_rec: Dict[str, Any],
        adp: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Synchronously generate High Level Design."""
        prompt = self._build_prompt(req_analysis, tech_rec, adp)
        result: HLDResponse = self.llm_provider.generate_structured(
            prompt=prompt,
            model_name=self.model_name,
            response_model=HLDResponse,
            system_prompt=HLD_GENERATION_SYSTEM_PROMPT,
            agent_name=self.role,
            temperature=0.2,
        )
        return result.model_dump(mode="json")
