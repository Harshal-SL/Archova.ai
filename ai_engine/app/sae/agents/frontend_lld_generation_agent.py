"""Frontend Low Level Design (LLD) Generation Agent for SAE v2.

Grounds frontend UI pages, component tree, and API integration hooks directly
into the Canonical Architecture Contract (CAC) operation IDs and routes.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.sae.agents.base_agent import BaseArchitectureAgent
from app.sae.models.response_models import FrontendLLDResponse
from app.sae.prompts.frontend_lld_generation_prompt import (
    FRONTEND_LLD_GENERATION_SYSTEM_PROMPT,
    FRONTEND_LLD_GENERATION_USER_PROMPT_TEMPLATE,
)
from app.sae.providers.llm_provider import OpenRouterProvider
from app.sae.services.architecture_knowledge_service import ArchitectureKnowledgeService
from app.sae.utils.canonical_contract import CanonicalArchitectureContract


class FrontendLLDGenerationAgent(BaseArchitectureAgent):
    """Agent responsible for generating Frontend Low Level Design (LLD)."""

    role: str = "frontend"

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
        prompt = FRONTEND_LLD_GENERATION_USER_PROMPT_TEMPLATE.format(hld_document_json=hld_str)
        
        if cac and cac.api_operations:
            cac_ops_table = "\n".join([
                f"  - operation_id: {op.operation_id} | method: {op.method} | path: {op.path} | auth: {op.authentication} | satisfies: {op.requirement_ids}"
                for op in cac.api_operations
            ])
            prompt += f"\n\nCANONICAL API CONTRACT (MANDATORY BINDING):\nEvery frontend API integration and page action MUST map to these exact operations:\n{cac_ops_table}\n"
        return prompt

    def _synthesize_fallback_frontend_lld(
        self,
        hld: Dict[str, Any],
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> Dict[str, Any]:
        """Synthesizes structured Frontend LLD aligned directly with CAC operations."""
        system_name = cac.system_name if cac else "Enterprise System"
        fe_fw = hld.get("technology_stack", {}).get("frontend", "React (Next.js App Router) + TypeScript")

        # Dynamically derive pages and components from CAC operations and entities
        pages = [{"route": "/login", "name": "LoginPage", "description": "Authentication entry with role-based login form"}]
        components = [{"name": "Navbar", "props": {"user": "UserProfile | null"}, "description": "Global header with navigation links and auth state"}]

        if cac and cac.api_operations:
            seen_routes = set(["/login"])
            for op in cac.api_operations:
                clean_seg = [seg for seg in op.path.strip("/").split("/") if seg not in ("api", "v1")]
                if not clean_seg:
                    continue
                base_route = "/" + "/".join(clean_seg)
                # Convert path parameter {id} to Next.js route [id]
                nextjs_route = re.sub(r"\{([a-zA-Z0-9_]+)\}", r"[\1]", base_route)
                
                if nextjs_route not in seen_routes:
                    seen_routes.add(nextjs_route)
                    page_name = "".join(w.capitalize() for w in re.findall(r"[a-zA-Z0-9]+", op.operation_id)) + "Page"
                    pages.append({
                        "route": nextjs_route,
                        "name": page_name,
                        "description": op.description or f"Interface for {op.operation_id}",
                    })

            for ent in cac.domain_entities[:3]:
                components.append({
                    "name": f"{ent.name}Card",
                    "props": {"item": f"{ent.name}Data", "onSelect": "function"},
                    "description": f"Reusable presentation tile for {ent.name}",
                })
                components.append({
                    "name": f"{ent.name}FormModal",
                    "props": {"isOpen": "boolean", "onSubmit": "function"},
                    "description": f"Interactive form dialog for creating/editing {ent.name}",
                })
        else:
            pages.extend([
                {"route": "/dashboard", "name": "DashboardPage", "description": "User profile with operational alerts and activity metrics"},
                {"route": "/items", "name": "CatalogPage", "description": "Searchable, filterable catalog with pagination and card grid"},
            ])
            components.extend([
                {"name": "ItemCard", "props": {"item": "ItemData", "onAction": "function"}, "description": "Reusable presentation tile with status badge"},
                {"name": "FilterBar", "props": {"onFilter": "function"}, "description": "Debounced search input with category filter"},
            ])

        api_calls = []
        if cac and cac.api_operations:
            for op in cac.api_operations:
                api_calls.append(f"api.{op.operation_id}() -> {op.method} {op.path}")
        else:
            api_calls = ["api.loginUser() -> POST /api/v1/auth/login", "api.getItems() -> GET /api/v1/items"]

        return {
            "framework": fe_fw,
            "pages": pages,
            "components": components,
            "state_management": {
                "global_state": "Zustand (AuthSession, UIState)",
                "server_state": "TanStack Query (Cached API queries with automatic invalidation)",
                "form_state": "React Hook Form + Zod schema validation",
            },
            "routing": {
                "type": "Next.js App Router (File-based)",
                "middleware_guards": [
                    "authGuard (redirect unauthenticated users to /login)",
                    "roleGuard (enforce role-based access on protected routes)",
                ],
            },
            "api_integration": {
                "client": "Axios instance with centralized interceptor injecting Authorization Bearer token",
                "canonical_operations": api_calls,
                "error_handling": "Toast notification alerts and field-level form validation errors",
            },
            "styling_approach": {
                "framework": "TailwindCSS",
                "theme": "Clean minimalist aesthetic with consistent typography and color tokens",
            },
            "build_config": {
                "bundler": "Next.js Turbopack",
                "linter": "ESLint + Prettier",
            },
            "accessibility": {
                "standards": "WCAG 2.1 AA compliant",
                "features": [
                    "ARIA labels on all interactive elements",
                    "Full keyboard navigation support",
                    "Color contrast ratio >= 4.5:1",
                ],
            },
        }

    async def run_async(
        self,
        hld: Dict[str, Any],
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> Dict[str, Any]:
        """Asynchronously generate Frontend LLD with live agent-owned RAG context and CAC grounding."""
        # 1. Retrieve domain-specific RAG context
        rag_block, rag_meta = await self.retrieve_rag_context(hld)

        # 2. Build prompt with CAC binding and inject additive RAG context & domain fence
        base_prompt = self._build_prompt(hld, cac=cac)
        prompt = self.inject_rag_context(base_prompt, rag_block)
        prompt = self.inject_domain_fence(prompt, cac=cac)

        # 3. Call LLM with fallback handling
        try:
            result: FrontendLLDResponse = await self.llm_provider.generate_structured_async(
                prompt=prompt,
                response_model=FrontendLLDResponse,
                model_name=self.model_name,
                system_prompt=FRONTEND_LLD_GENERATION_SYSTEM_PROMPT,
                agent_role=self.role,
                temperature=0.2,
            )
            res_dict = result.model_dump(mode="json")
        except Exception as e:
            res_dict = self._synthesize_fallback_frontend_lld(hld, cac=cac)

        # Guarantee CAC API integration hooks
        if not res_dict.get("pages") or not res_dict.get("components"):
            fallback = self._synthesize_fallback_frontend_lld(hld, cac=cac)
            for k, v in fallback.items():
                if not res_dict.get(k):
                    res_dict[k] = v

        if cac and cac.api_operations:
            api_calls = [f"api.{op.operation_id}() -> {op.method} {op.path}" for op in cac.api_operations]
            if isinstance(res_dict.get("api_integration"), dict):
                res_dict["api_integration"]["canonical_operations"] = api_calls
            else:
                res_dict["api_integration"] = {
                    "client": "Axios client with Bearer auth",
                    "canonical_operations": api_calls,
                }

        return self.attach_rag_metadata(res_dict, rag_meta)

    def run(
        self,
        hld: Dict[str, Any],
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> Dict[str, Any]:
        """Synchronously generate Frontend LLD."""
        prompt = self._build_prompt(hld, cac=cac)
        try:
            result: FrontendLLDResponse = self.llm_provider.generate_structured(
                prompt=prompt,
                model_name=self.model_name,
                response_model=FrontendLLDResponse,
                system_prompt=FRONTEND_LLD_GENERATION_SYSTEM_PROMPT,
                agent_name=self.role,
                temperature=0.2,
            )
            return result.model_dump(mode="json")
        except Exception:
            return self._synthesize_fallback_frontend_lld(hld, cac=cac)
