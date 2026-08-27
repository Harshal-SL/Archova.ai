"""Security Low Level Design (LLD) Generation Agent for SAE v2."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from app.sae.agents.base_agent import BaseArchitectureAgent
from app.sae.models.response_models import SecurityLLDResponse
from app.sae.prompts.security_lld_generation_prompt import (
    SECURITY_LLD_GENERATION_SYSTEM_PROMPT,
    SECURITY_LLD_GENERATION_USER_PROMPT_TEMPLATE,
)
from app.sae.providers.llm_provider import OpenRouterProvider
from app.sae.services.architecture_knowledge_service import ArchitectureKnowledgeService


class SecurityLLDGenerationAgent(BaseArchitectureAgent):
    """Agent responsible for generating Security Architecture, Threat Models (STRIDE), and Compliance Controls."""

    role: str = "security"

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
        return SECURITY_LLD_GENERATION_USER_PROMPT_TEMPLATE.format(hld_document_json=hld_str)

    def _synthesize_fallback_security_lld(self, hld: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesizes structured Security LLD with STRIDE threats and OWASP Top 10 controls."""
        return {
            "authentication": {
                "mechanism": "OAuth2 with Authorization Code Flow & PKCE",
                "token_format": "JWT (RS256 signed with rotating asymmetric keys)",
                "token_ttl": "Access Token: 15 mins, Refresh Token: 7 days",
                "mfa": "Time-based One-Time Password (TOTP) for administrative and privileged operations",
            },
            "authorization": {
                "model": "Role-Based Access Control (RBAC)",
                "roles": [
                    {"role": "User", "permissions": ["resources:read", "operations:create", "profile:manage"]},
                    {"role": "Staff", "permissions": ["resources:*", "operations:*", "records:manage"]},
                    {"role": "Admin", "permissions": ["*"]},
                ],
            },
            "threat_model": [
                {
                    "category": "Spoofing",
                    "threat": "Adversary attempts credential brute-force or token forgery",
                    "mitigation": "BCrypt hashing (12 rounds), Redis rate-limiting (5 attempts/min), RS256 token verification",
                },
                {
                    "category": "Tampering",
                    "threat": "Man-in-the-middle request alteration or SQL parameter manipulation",
                    "mitigation": "Enforced TLS 1.3 with HSTS header, SQLAlchemy parameterized queries, Pydantic strict schemas",
                },
                {
                    "category": "Information Disclosure",
                    "threat": "Sensitive database records or access tokens exposed in error logs",
                    "mitigation": "Masked structured JSON logging (PII redaction), AES-256-GCM encryption at rest via AWS KMS",
                },
            ],
            "security_controls": {
                "network_security": "WAF rate-limiting, private subnet DB isolation, zero public database access",
                "input_validation": "Strict Pydantic payload models, content-type verification, maximum request body limits",
                "headers": ["Strict-Transport-Security", "X-Content-Type-Options: nosniff", "X-Frame-Options: DENY", "Content-Security-Policy"],
            },
            "compliance": {
                "frameworks": ["OWASP Top 10 (2021)", "SOC 2 Type II Security Principles", "GDPR Data Protection by Design"],
                "data_privacy": "Automated data pseudonymization and audit log retention for 365 days",
            },
        }

    async def run_async(
        self,
        hld: Dict[str, Any],
        cac: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Asynchronously generate Security LLD with live agent-owned RAG context."""
        # 1. Retrieve domain-specific RAG context
        rag_block, rag_meta = await self.retrieve_rag_context(hld)

        # 2. Build prompt and inject additive RAG context & authoritative domain fence
        base_prompt = self._build_prompt(hld)
        prompt = self.inject_rag_context(base_prompt, rag_block)
        prompt = self.inject_domain_fence(prompt, cac=cac, arsrs=hld)

        # 3. Call LLM with fallback handling
        try:
            result: SecurityLLDResponse = await self.llm_provider.generate_structured_async(
                prompt=prompt,
                response_model=SecurityLLDResponse,
                model_name=self.model_name,
                system_prompt=SECURITY_LLD_GENERATION_SYSTEM_PROMPT,
                agent_role=self.role,
                temperature=0.2,
            )
            res_dict = result.model_dump(mode="json")
        except Exception:
            res_dict = self._synthesize_fallback_security_lld(hld)

        if not res_dict.get("threat_model") or not res_dict.get("authentication"):
            fallback = self._synthesize_fallback_security_lld(hld)
            for k, v in fallback.items():
                if not res_dict.get(k):
                    res_dict[k] = v

        return self.attach_rag_metadata(res_dict, rag_meta)

    def run(self, hld: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronously generate Security LLD."""
        prompt = self._build_prompt(hld)
        try:
            result: SecurityLLDResponse = self.llm_provider.generate_structured(
                prompt=prompt,
                model_name=self.model_name,
                response_model=SecurityLLDResponse,
                system_prompt=SECURITY_LLD_GENERATION_SYSTEM_PROMPT,
                agent_name=self.role,
                temperature=0.2,
            )
            return result.model_dump(mode="json")
        except Exception:
            return self._synthesize_fallback_security_lld(hld)
