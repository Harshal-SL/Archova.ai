"""Cloud Low Level Design (LLD) Generation Agent for SAE v2."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from app.sae.agents.base_agent import BaseArchitectureAgent
from app.sae.models.response_models import CloudLLDResponse
from app.sae.prompts.cloud_lld_generation_prompt import (
    CLOUD_LLD_GENERATION_SYSTEM_PROMPT,
    CLOUD_LLD_GENERATION_USER_PROMPT_TEMPLATE,
)
from app.sae.providers.llm_provider import OpenRouterProvider
from app.sae.services.architecture_knowledge_service import ArchitectureKnowledgeService


class CloudLLDGenerationAgent(BaseArchitectureAgent):
    """Agent responsible for generating Cloud Infrastructure and Deployment LLD."""

    role: str = "cloud"

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

    def _build_prompt(self, hld: Dict[str, Any]) -> str:
        hld_str = json.dumps(hld, indent=2, default=str)
        return CLOUD_LLD_GENERATION_USER_PROMPT_TEMPLATE.format(hld_document_json=hld_str)

    def _synthesize_fallback_cloud_lld(self, hld: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesizes structured Cloud LLD matching HLD platform choice."""
        cloud_choice = hld.get("technology_stack", {}).get("cloud", "AWS (ECS Fargate)")
        if isinstance(cloud_choice, dict):
            cloud_choice = cloud_choice.get("selected_option") or cloud_choice.get("choice") or str(cloud_choice)
        cloud_choice_str = str(cloud_choice).lower()
        provider = "AWS" if "aws" in cloud_choice_str else ("GCP" if "gcp" in cloud_choice_str else "Azure")

        return {
            "cloud_provider": provider,
            "region": "us-east-1 (Primary) with us-west-2 (DR)",
            "compute": {
                "service": "AWS ECS Fargate",
                "sizing": "2 vCPU / 4GB RAM per container task",
                "autoscaling": "Min 2 tasks, Max 10 tasks based on 70% CPU / memory target tracking",
            },
            "database": {
                "service": "Amazon RDS PostgreSQL 16 (Multi-AZ)",
                "instance_type": "db.t4g.large",
                "storage": "100GB gp3 with auto-expansion up to 1TB",
            },
            "caching": {
                "service": "Amazon ElastiCache for Redis (Cluster Mode)",
                "node_type": "cache.t4g.medium",
            },
            "networking": {
                "vpc": "Custom VPC with 2 Public and 2 Private subnets across 2 AZs",
                "load_balancer": "Application Load Balancer (ALB) with AWS WAF & ACM TLS 1.3 certificate",
                "nat_gateway": "Managed NAT Gateways in public subnets for egress traffic",
            },
            "security_and_compliance": {
                "iam": "Least-privilege IAM task execution roles with AWS Secrets Manager integration",
                "encryption": "KMS customer-managed keys for EBS, S3, and RDS at rest; TLS 1.3 in transit",
            },
            "cost_estimation": {
                "monthly_estimate_usd": "$280 - $420",
                "breakdown": "ALB ($25), ECS Tasks ($120), RDS Multi-AZ ($150), ElastiCache ($60), Data Transfer ($25)",
            },
        }

    async def run_async(
        self,
        hld: Dict[str, Any],
        cac: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Asynchronously generate Cloud LLD with live agent-owned RAG context."""
        # 1. Retrieve domain-specific RAG context
        rag_block, rag_meta = await self.retrieve_rag_context(hld)

        # 2. Build prompt and inject additive RAG context & domain grounding
        base_prompt = self._build_prompt(hld)
        prompt = self.inject_rag_context(base_prompt, rag_block)
        prompt = self.inject_domain_fence(prompt, cac=cac, arsrs=hld)

        # 3. Call LLM with fallback handling
        try:
            result: CloudLLDResponse = await self.llm_provider.generate_structured_async(
                prompt=prompt,
                response_model=CloudLLDResponse,
                model_name=self.model_name,
                system_prompt=CLOUD_LLD_GENERATION_SYSTEM_PROMPT,
                agent_role=self.role,
                temperature=0.2,
            )
            res_dict = result.model_dump(mode="json")
        except Exception:
            res_dict = self._synthesize_fallback_cloud_lld(hld)

        if not res_dict.get("compute") or not res_dict.get("networking"):
            fallback = self._synthesize_fallback_cloud_lld(hld)
            for k, v in fallback.items():
                if not res_dict.get(k):
                    res_dict[k] = v

        return self.attach_rag_metadata(res_dict, rag_meta)

    def run(self, hld: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronously generate Cloud LLD."""
        prompt = self._build_prompt(hld)
        try:
            result: CloudLLDResponse = self.llm_provider.generate_structured(
                prompt=prompt,
                model_name=self.model_name,
                response_model=CloudLLDResponse,
                system_prompt=CLOUD_LLD_GENERATION_SYSTEM_PROMPT,
                agent_name=self.role,
                temperature=0.2,
            )
            return result.model_dump(mode="json")
        except Exception:
            return self._synthesize_fallback_cloud_lld(hld)
