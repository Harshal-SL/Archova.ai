"""Testing Strategy Agent for SAE v2.

Generates comprehensive test plans, unit test matrix, integration boundaries,
and Schemathesis contract tests grounded directly on Canonical Architecture Contract (CAC) operation IDs.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from app.sae.agents.base_agent import BaseArchitectureAgent
from app.sae.models.response_models import TestingStrategyResponse
from app.sae.prompts.testing_strategy_prompt import (
    TESTING_STRATEGY_SYSTEM_PROMPT,
    TESTING_STRATEGY_USER_PROMPT_TEMPLATE,
)
from app.sae.providers.llm_provider import OpenRouterProvider
from app.sae.services.architecture_knowledge_service import ArchitectureKnowledgeService
from app.sae.utils.canonical_contract import CanonicalArchitectureContract


class TestingStrategyAgent(BaseArchitectureAgent):
    """Agent responsible for generating comprehensive testing strategy and QA plan."""

    role: str = "testing_strategy"

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
        hld: Dict[str, Any],
        backend_lld: Dict[str, Any],
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> str:
        hld_str = json.dumps(hld, indent=2, default=str)
        backend_str = json.dumps(backend_lld, indent=2, default=str)
        prompt = TESTING_STRATEGY_USER_PROMPT_TEMPLATE.format(
            hld_document_json=hld_str,
            backend_lld_json=backend_str,
        )

        if cac and cac.api_operations:
            cac_ops_table = "\n".join([
                f"  - operation_id: {op.operation_id} | method: {op.method} | path: {op.path} | satisfies: {op.requirement_ids}"
                for op in cac.api_operations
            ])
            prompt += f"\n\nCANONICAL API CONTRACT (MANDATORY TEST TARGETS):\nAll unit, integration, Schemathesis contract, and E2E journeys MUST target these exact operation IDs and routes:\n{cac_ops_table}\n"
        return prompt

    def _synthesize_fallback_testing(
        self,
        hld: Dict[str, Any],
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> Dict[str, Any]:
        """Synthesizes structured testing strategy aligned with CAC API operations."""
        canonical_paths = [op.path for op in cac.api_operations] if cac and cac.api_operations else ["/api/v1/auth/login", "/api/v1/items", "/api/v1/transactions"]
        e2e_steps = [
            f"Invoke {op.method} {op.path} ({op.operation_id})" for op in (cac.api_operations if cac else [])
        ] or ["Login user", "Search resources", "Execute transaction"]

        return {
            "coverage_targets": {
                "unit_test_line_coverage": ">= 80%",
                "integration_test_branch_coverage": ">= 70%",
                "critical_transaction_flows": "100% automated path coverage",
            },
            "unit_testing": {
                "framework": "pytest with pytest-asyncio and pytest-mock",
                "scope": [
                    "API route handlers and DTO validators",
                    "Domain service business rules and state machines",
                    "Security token validation and RBAC decorators",
                ],
                "execution_time_target": "< 30 seconds for complete unit suite",
            },
            "integration_testing": {
                "framework": "pytest with testcontainers-postgres and testcontainers-redis",
                "scope": [
                    f"API route handler end-to-end execution for {', '.join(canonical_paths[:3])}",
                    "ACID transaction rollback verification on simulated constraint failure",
                    "Redis cache hit/miss/invalidation lifecycles",
                ],
            },
            "contract_testing": {
                "tool": "Schemathesis (OpenAPI schema-based property testing)",
                "scope": [
                    f"Validate all {', '.join(canonical_paths)} endpoint responses against OpenAPI 3.1",
                    "Detect schema drift between client and backend",
                    "Negative property tests for RFC 7807 error responses",
                ],
            },
            "e2e_testing": {
                "framework": "Playwright (TypeScript)",
                "critical_journeys": [
                    {
                        "name": "Primary User Journey",
                        "steps": e2e_steps,
                    },
                ],
            },
            "load_testing": {
                "tool": "k6",
                "traffic_model": {
                    "concurrent_virtual_users": 500,
                    "peak_throughput_rps": 50,
                    "ramp_up_duration": "2 minutes",
                    "steady_state_duration": "10 minutes",
                },
                "pass_fail_criteria": [
                    "p95 response time <= 200ms for read queries",
                    "p99 response time <= 500ms for write mutations",
                    "Error rate (HTTP 5xx) < 0.1% under peak load",
                ],
            },
            "security_testing": {
                "tools": ["Bandit (AST analysis)", "OWASP ZAP (API scan)", "Trivy (Container scan)"],
                "schedule": "Automated on every pull request and nightly scheduled scan",
            },
            "ci_cd_test_gates": [
                "Pull Request Block: Unit tests pass + 80% coverage check",
                "Pre-Merge Block: Integration test suite with ephemeral Postgres passes",
                "Post-Deployment Gate: Automated smoke test suite verifies live health checks",
            ],
        }

    async def run_async(
        self,
        hld: Dict[str, Any],
        backend_lld: Dict[str, Any],
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> Dict[str, Any]:
        """Asynchronously generate Testing Strategy with live agent-owned RAG context and CAC grounding."""
        context = {
            "domain": hld.get("domain", "") or hld.get("system_name", ""),
            "hld": hld,
            "backend_lld": backend_lld,
        }

        # 1. Retrieve domain-specific RAG context
        rag_block, rag_meta = await self.retrieve_rag_context(context)

        # 2. Build prompt with CAC binding
        base_prompt = self._build_prompt(hld, backend_lld, cac=cac)
        prompt = self.inject_rag_context(base_prompt, rag_block)

        # 3. Call LLM with fallback
        try:
            result: TestingStrategyResponse = await self.llm_provider.generate_structured_async(
                prompt=prompt,
                response_model=TestingStrategyResponse,
                model_name=self.model_name,
                system_prompt=TESTING_STRATEGY_SYSTEM_PROMPT,
                agent_role=self.role,
                temperature=0.2,
            )
            res_dict = result.model_dump(mode="json")
        except Exception:
            res_dict = self._synthesize_fallback_testing(hld, cac=cac)

        if not res_dict.get("unit_testing") or not res_dict.get("integration_testing"):
            fallback = self._synthesize_fallback_testing(hld, cac=cac)
            for k, v in fallback.items():
                if not res_dict.get(k):
                    res_dict[k] = v

        return self.attach_rag_metadata(res_dict, rag_meta)

    def run(
        self,
        hld: Dict[str, Any],
        backend_lld: Dict[str, Any],
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> Dict[str, Any]:
        """Synchronously generate Testing Strategy."""
        prompt = self._build_prompt(hld, backend_lld, cac=cac)
        try:
            result: TestingStrategyResponse = self.llm_provider.generate_structured(
                prompt=prompt,
                model_name=self.model_name,
                response_model=TestingStrategyResponse,
                system_prompt=TESTING_STRATEGY_SYSTEM_PROMPT,
                agent_name=self.role,
                temperature=0.2,
            )
            return result.model_dump(mode="json")
        except Exception:
            return self._synthesize_fallback_testing(hld, cac=cac)
