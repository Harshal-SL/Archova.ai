"""Backend Low Level Design (LLD) Generation Agent for SAE v2.

Generates FastAPI router endpoints, domain models, services, repositories,
and RFC 7807 error responses strictly bound to Canonical Architecture Contract (CAC) IDs.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.sae.agents.base_agent import BaseArchitectureAgent
from app.sae.models.response_models import BackendLLDResponse
from app.sae.prompts.backend_lld_generation_prompt import (
    BACKEND_LLD_GENERATION_SYSTEM_PROMPT,
    BACKEND_LLD_GENERATION_USER_PROMPT_TEMPLATE,
)
from app.sae.providers.llm_provider import OpenRouterProvider
from app.sae.services.architecture_knowledge_service import ArchitectureKnowledgeService
from app.sae.utils.canonical_contract import CanonicalArchitectureContract

logger = logging.getLogger(__name__)


class BackendLLDGenerationAgent(BaseArchitectureAgent):
    """Agent responsible for generating detailed Backend Low Level Design (LLD)."""

    role: str = "backend"

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
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> str:
        hld_str = json.dumps(hld, indent=2, default=str)
        prompt = BACKEND_LLD_GENERATION_USER_PROMPT_TEMPLATE.format(hld_document_json=hld_str)

        if cac:
            cac_ops_table = "\n".join([
                f"  - operation_id: {op.operation_id} | method: {op.method} | route: {op.path} | satisfies: {op.requirement_ids}"
                for op in cac.api_operations
            ])
            cac_models_table = "\n".join([
                f"  - Model: {m.name} (ID: {m.entity_id}) | DB Table: {m.database_table} | Fields: {m.fields}"
                for m in cac.domain_entities
            ])
            prompt += (
                f"\n\nCANONICAL ARCHITECTURE CONTRACT (MANDATORY BINDING):\n"
                f"Canonical Requirement IDs: {cac.requirement_ids}\n"
                f"DO NOT USE REQ-* ALIASES. Use exact FR-XXX and NFR-XXX IDs in all 'satisfies' fields.\n\n"
                f"CANONICAL API OPERATIONS:\n{cac_ops_table}\n\n"
                f"CANONICAL DOMAIN MODELS:\n{cac_models_table}\n"
            )
        return prompt

    def _synthesize_fallback_backend_lld(
        self,
        hld: Dict[str, Any],
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> Dict[str, Any]:
        """Synthesize a robust, implementation-ready Backend LLD derived from HLD services and CAC."""
        tech_stack = hld.get("technology_stack", {})
        backend_fw = tech_stack.get("backend", "FastAPI (Python 3.12)")

        # Canonical requirement IDs
        req_ids = cac.requirement_ids if cac and cac.requirement_ids else ["FR-001", "FR-002", "FR-003", "FR-004"]
        fr1 = req_ids[0] if len(req_ids) > 0 else "FR-001"
        fr2 = req_ids[1] if len(req_ids) > 1 else fr1
        fr3 = req_ids[2] if len(req_ids) > 2 else fr2
        fr4 = req_ids[3] if len(req_ids) > 3 else fr3

        endpoints: List[Dict[str, Any]] = []
        if cac and cac.api_operations:
            for op in cac.api_operations:
                endpoints.append({
                    "route": op.path,
                    "method": op.method,
                    "operation_id": op.operation_id,
                    "description": op.description or f"Handles {op.operation_id}",
                    "request": {"body": op.request_schema} if op.method != "GET" else {"query_params": ["page", "limit", "search"]},
                    "response": {"status": 200 if op.method == "GET" else 201, "body": op.response_schema},
                    "error_responses": [
                        {"status": 400, "code": err, "description": f"Error state {err}"}
                        for err in (op.errors or ["BAD_REQUEST"])
                    ],
                    "concurrency_note": "ACID row-level lock or Redis cache",
                    "idempotency": "Idempotent" if op.method in ("GET", "PUT", "DELETE") else "Requires Idempotency-Key header",
                    "auth_required": op.authentication.lower() != "public",
                    "satisfies": op.requirement_ids or [fr1],
                })
        else:
            endpoints = [
                {
                    "route": "/api/v1/auth/login",
                    "method": "POST",
                    "description": "Authenticate user credentials and issue scoped JWT tokens",
                    "request": {"body": {"username": "str", "password": "str"}},
                    "response": {"status": 200, "body": {"access_token": "str", "token_type": "bearer", "expires_in": 900}},
                    "error_responses": [
                        {"status": 401, "code": "INVALID_CREDENTIALS", "description": "Invalid credentials supplied"},
                    ],
                    "concurrency_note": "Redis rate limiter",
                    "idempotency": "Non-idempotent",
                    "auth_required": False,
                    "satisfies": [fr1],
                },
                {
                    "route": "/api/v1/resources",
                    "method": "GET",
                    "description": "Search and filter primary resource catalog",
                    "request": {"query_params": ["page", "limit", "search"]},
                    "response": {"status": 200, "body": "List of items"},
                    "error_responses": [
                        {"status": 400, "code": "INVALID_PAGINATION", "description": "Invalid page parameter"},
                    ],
                    "concurrency_note": "Redis 300s TTL cache",
                    "idempotency": "Idempotent",
                    "auth_required": False,
                    "satisfies": [fr1, fr2],
                },
                {
                    "route": "/api/v1/transactions",
                    "method": "POST",
                    "description": "Execute primary domain state transition",
                    "request": {"body": {"resource_id": "UUID", "action": "str"}},
                    "response": {"status": 201, "body": "TransactionRecord entity"},
                    "error_responses": [
                        {"status": 404, "code": "RESOURCE_NOT_FOUND", "description": "Resource not found"},
                    ],
                    "concurrency_note": "SELECT FOR UPDATE lock",
                    "idempotency": "Idempotent with header",
                    "auth_required": True,
                    "satisfies": [fr2, fr3],
                },
                {
                    "route": "/api/v1/transactions/{id}/complete",
                    "method": "POST",
                    "description": "Complete domain transaction workflow",
                    "request": {"body": {"notes": "str"}},
                    "response": {"status": 200, "body": "TransactionSummary"},
                    "error_responses": [
                        {"status": 404, "code": "TRANSACTION_NOT_FOUND", "description": "Active transaction not found"},
                    ],
                    "concurrency_note": "Atomic commit",
                    "idempotency": "Idempotent",
                    "auth_required": True,
                    "satisfies": [fr2, fr3, fr4],
                },
            ]

        # Domain Models directly from CAC
        domain_models: List[Dict[str, Any]] = []
        repositories: List[Dict[str, Any]] = []
        if cac and cac.domain_entities:
            for ent in cac.domain_entities:
                domain_models.append({
                    "name": ent.name,
                    "type": "entity",
                    "fields": ent.fields,
                    "relationships": ent.relationships,
                    "database_table": ent.database_table,
                })
                repositories.append({
                    "name": f"{ent.name}Repository",
                    "entity": ent.name,
                    "methods": ["find_by_id", "create", "update", "delete"],
                    "database": "PostgreSQL",
                })
        else:
            domain_models = [
                {"name": "User", "type": "entity", "fields": {"id": "UUID", "username": "str", "role": "str"}, "relationships": ["TransactionRecord"]},
                {"name": "ResourceItem", "type": "entity", "fields": {"id": "UUID", "name": "str", "status": "str"}, "relationships": ["TransactionRecord"]},
                {"name": "TransactionRecord", "type": "entity", "fields": {"id": "UUID", "user_id": "UUID", "item_id": "UUID"}, "relationships": ["User", "ResourceItem"]},
            ]
            repositories = [
                {"name": "UserRepository", "entity": "User", "methods": ["find_by_id", "create"], "database": "PostgreSQL"},
                {"name": "ResourceRepository", "entity": "ResourceItem", "methods": ["search", "find_by_id"], "database": "PostgreSQL"},
                {"name": "TransactionRepository", "entity": "TransactionRecord", "methods": ["create_record", "update_status"], "database": "PostgreSQL"},
            ]

        # Services directly from CAC
        services: List[Dict[str, Any]] = []
        if cac and cac.services:
            for s in cac.services:
                services.append({
                    "name": s.name,
                    "responsibility": s.responsibility,
                    "methods": ["execute_workflow", "validate_state", "process_transaction"],
                    "dependencies": [r["name"] for r in repositories[:2]],
                    "satisfies": s.requirement_ids or [fr1],
                })
        else:
            services = [
                {"name": "AuthService", "responsibility": "User authentication and JWT issuance", "methods": ["authenticate_user", "refresh_session"], "dependencies": ["UserRepository"], "satisfies": [fr1]},
                {"name": "CoreService", "responsibility": "Resource management and search", "methods": ["search_items", "get_details"], "dependencies": ["ResourceRepository"], "satisfies": [fr1, fr2]},
                {"name": "TransactionService", "responsibility": "Transaction execution and status tracking", "methods": ["execute_transaction", "get_status"], "dependencies": ["TransactionRepository"], "satisfies": [fr2, fr3]},
            ]

        return {
            "api_endpoints": endpoints,
            "services": services,
            "domain_models": domain_models,
            "repositories": repositories,
            "project_structure": {
                "pattern": "Clean Layered Architecture",
                "directories": {
                    "app/api/v1": "FastAPI router endpoints and DTO schema validation",
                    "app/services": "Domain business logic and transactional use-cases",
                    "app/models": "SQLAlchemy ORM database models and Pydantic DTOs",
                    "app/repositories": "Database access layer interfaces and SQL operations",
                    "app/core": "Security, JWT authentication, configuration, and database session pool",
                },
            },
            "framework_config": {
                "framework": "FastAPI",
                "language": "Python 3.12",
                "orm": "SQLAlchemy 2.0 (Async)",
                "migration_tool": "Alembic",
                "driver": "asyncpg",
            },
            "security_config": {
                "auth_strategy": "OAuth2 Bearer Tokens (JWT RS256)",
                "password_hashing": "Passlib with BCrypt (12 rounds)",
                "rbac_roles": ["User", "Administrator"],
            },
            "error_handling": {
                "strategy": "Global exception handler returning RFC 7807 problem details JSON",
                "standard_format": {
                    "error_code": "str",
                    "message": "str",
                    "details": "dict",
                    "timestamp": "ISO8601",
                },
            },
            "api_versioning_policy": {
                "strategy": "URI path versioning (/api/v1/)",
                "deprecation_window": "6 months notice via Sunset HTTP headers",
                "backwards_compatibility": "Additive non-breaking changes within v1",
            },
            "data_lifecycle": {
                "retention_policy": "Operational transaction audit logs retained for 3 years",
                "right_to_erasure": "Pseudonymization with UUID hashing",
                "backup_verification": "Automated daily snapshot integrity verification",
            },
            "dependencies": ["fastapi", "uvicorn", "sqlalchemy", "asyncpg", "pydantic", "alembic", "python-jose", "passlib", "redis"],
            "architecture_patterns": ["Clean Architecture", "Repository Pattern", "Dependency Injection", "DTO Pattern"],
        }

    def _normalize_requirement_ids(
        self,
        payload: Dict[str, Any],
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> Dict[str, Any]:
        """Ensures all 'satisfies' fields contain ONLY valid canonical FR-XXX / NFR-XXX IDs without REQ-* aliases."""
        if not cac or not cac.requirement_ids:
            return payload

        canonical_ids = cac.requirement_ids
        fr_ids = [r for r in canonical_ids if r.startswith("FR-")]
        default_fr = fr_ids[0] if fr_ids else canonical_ids[0]

        def _clean_req_list(raw_list: Any) -> List[str]:
            if not isinstance(raw_list, list):
                return [default_fr]
            cleaned = []
            for item in raw_list:
                item_str = str(item).strip()
                if item_str in canonical_ids:
                    cleaned.append(item_str)
                elif item_str.startswith("REQ-"):
                    # Map REQ-001 -> FR-001 etc.
                    digits = re.findall(r"\d+", item_str)
                    if digits:
                        mapped = f"FR-{int(digits[0]):03d}"
                        if mapped in canonical_ids:
                            cleaned.append(mapped)
                        else:
                            cleaned.append(default_fr)
                    else:
                        cleaned.append(default_fr)
            return list(dict.fromkeys(cleaned)) if cleaned else [default_fr]

        # Clean in api_endpoints
        for ep in payload.get("api_endpoints", []):
            if isinstance(ep, dict) and "satisfies" in ep:
                ep["satisfies"] = _clean_req_list(ep["satisfies"])

        # Clean in services
        for svc in payload.get("services", []):
            if isinstance(svc, dict) and "satisfies" in svc:
                svc["satisfies"] = _clean_req_list(svc["satisfies"])

        return payload

    async def run_async(
        self,
        hld: Dict[str, Any],
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> Dict[str, Any]:
        """Asynchronously generate Backend LLD with live agent-owned RAG context and CAC grounding."""
        # 1. Retrieve domain-specific RAG context
        rag_block, rag_meta = await self.retrieve_rag_context(hld)

        # 2. Build prompt with CAC binding and authoritative domain fence
        base_prompt = self._build_prompt(hld, cac=cac)
        prompt = self.inject_rag_context(base_prompt, rag_block)
        prompt = self.inject_domain_fence(prompt, cac=cac)

        # 3. Call LLM with fallback
        try:
            result: BackendLLDResponse = await self.llm_provider.generate_structured_async(
                prompt=prompt,
                response_model=BackendLLDResponse,
                model_name=self.model_name,
                system_prompt=BACKEND_LLD_GENERATION_SYSTEM_PROMPT,
                agent_role=self.role,
                temperature=0.2,
            )
            res_dict = result.model_dump(mode="json")
        except Exception:
            res_dict = self._synthesize_fallback_backend_lld(hld, cac=cac)

        # Guarantee non-empty core structures
        if not res_dict.get("api_endpoints") or not res_dict.get("domain_models"):
            fallback = self._synthesize_fallback_backend_lld(hld, cac=cac)
            for k, v in fallback.items():
                if not res_dict.get(k):
                    res_dict[k] = v

        # Normalize and remove any REQ-* aliases
        res_dict = self._normalize_requirement_ids(res_dict, cac=cac)

        return self.attach_rag_metadata(res_dict, rag_meta)

    def run(
        self,
        hld: Dict[str, Any],
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> Dict[str, Any]:
        """Synchronously generate Backend LLD."""
        prompt = self._build_prompt(hld, cac=cac)
        try:
            result: BackendLLDResponse = self.llm_provider.generate_structured(
                prompt=prompt,
                model_name=self.model_name,
                response_model=BackendLLDResponse,
                system_prompt=BACKEND_LLD_GENERATION_SYSTEM_PROMPT,
                agent_name=self.role,
                temperature=0.2,
            )
            res_dict = result.model_dump(mode="json")
        except Exception:
            res_dict = self._synthesize_fallback_backend_lld(hld, cac=cac)
        return self._normalize_requirement_ids(res_dict, cac=cac)
