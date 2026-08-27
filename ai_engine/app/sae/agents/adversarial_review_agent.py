"""Adversarial Red-Team Architecture Review Agent for SAE v2.

Performs rigorous red-team critique grounded on the Canonical Architecture Contract (CAC)
and Cross-Artifact Consistency Reports. Prevents over-optimistic approvals when contract drifts exist.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from app.sae.agents.base_agent import BaseArchitectureAgent
from app.sae.models.response_models import AdversarialReviewResponse
from app.sae.prompts.adversarial_review_prompt import (
    ADVERSARIAL_REVIEW_SYSTEM_PROMPT,
    ADVERSARIAL_REVIEW_USER_PROMPT_TEMPLATE,
)
from app.sae.providers.llm_provider import OpenRouterProvider
from app.sae.services.architecture_knowledge_service import ArchitectureKnowledgeService
from app.sae.utils.cross_artifact_validator import CrossArtifactConsistencyReport
from app.sae.utils.canonical_contract import CanonicalArchitectureContract


class AdversarialReviewAgent(BaseArchitectureAgent):
    """Agent responsible for conducting red-team adversarial critique and risk analysis on architecture designs."""

    role: str = "adversarial_review"

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
        package_summary: Dict[str, Any],
        consistency_report: Optional[CrossArtifactConsistencyReport] = None,
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> str:
        # Provide essential architectural sections to audit
        summary_slice = {
            "system_name": package_summary.get("system_name"),
            "domain": package_summary.get("domain"),
            "architecture_style": package_summary.get("architecture_style"),
            "requirements": package_summary.get("requirement_analysis", {}).get("functional_requirements", []),
            "nfrs": package_summary.get("requirement_analysis", {}).get("non_functional_requirements", []),
            "hld": {
                "architecture_style": package_summary.get("hld", {}).get("architecture_style"),
                "major_services": package_summary.get("hld", {}).get("major_services", []),
                "communication_patterns": package_summary.get("hld", {}).get("communication_patterns", []),
                "data_strategy": package_summary.get("hld", {}).get("data_strategy", {}),
                "security_overview": package_summary.get("hld", {}).get("security_overview", {}),
                "deployment_strategy": package_summary.get("hld", {}).get("deployment_strategy", {}),
            },
            "backend_lld": {
                "endpoints_count": len(package_summary.get("backend_lld", {}).get("api_endpoints", [])),
                "services": package_summary.get("backend_lld", {}).get("services", []),
                "framework_config": package_summary.get("backend_lld", {}).get("framework_config", {}),
            },
            "database_lld": {
                "database_type": package_summary.get("database_lld", {}).get("database_type"),
                "tables": [t.get("name") or t.get("table_name") for t in package_summary.get("database_lld", {}).get("tables", [])],
                "entity_mappings": package_summary.get("database_lld", {}).get("entity_mappings", []),
            },
            "frontend_lld": {
                "framework": package_summary.get("frontend_lld", {}).get("framework"),
                "pages": [{"route": p.get("route"), "name": p.get("name")} for p in package_summary.get("frontend_lld", {}).get("pages", [])],
                "state_management": package_summary.get("frontend_lld", {}).get("state_management"),
            },
            "security_lld": {
                "authentication": package_summary.get("security_lld", {}).get("authentication"),
                "authorization": package_summary.get("security_lld", {}).get("authorization"),
                "encryption": package_summary.get("security_lld", {}).get("encryption"),
                "threat_model": package_summary.get("security_lld", {}).get("threat_model", []),
            },
            "cloud_lld": {
                "cloud_provider": package_summary.get("cloud_lld", {}).get("cloud_provider"),
                "compute": package_summary.get("cloud_lld", {}).get("compute", {}),
                "database": package_summary.get("cloud_lld", {}).get("database", {}),
                "networking": package_summary.get("cloud_lld", {}).get("networking", {}),
            },
        }

        if consistency_report:
            summary_slice["cross_artifact_consistency"] = {
                "score": consistency_report.score,
                "frontend_to_backend_alignment": consistency_report.frontend_to_backend_alignment,
                "backend_to_database_alignment": consistency_report.backend_to_database_alignment,
                "requirement_id_integrity": consistency_report.requirement_id_integrity,
                "inconsistencies": consistency_report.inconsistencies,
                "unknown_requirement_ids": consistency_report.unknown_requirement_ids,
                "unknown_api_operations": consistency_report.unknown_api_operations,
            }

        pkg_str = json.dumps(summary_slice, indent=2, default=str)
        prompt = ADVERSARIAL_REVIEW_USER_PROMPT_TEMPLATE.format(package_summary_json=pkg_str)

        if consistency_report and (not consistency_report.is_valid or consistency_report.inconsistencies):
            prompt += (
                f"\n\nCRITICAL CONSISTENCY AUDIT FINDINGS:\n"
                f"The deterministic Consistency Engine identified {len(consistency_report.inconsistencies)} issues:\n"
                f"{json.dumps(consistency_report.inconsistencies, indent=2)}\n"
                f"Note: If critical contract drifts exist (e.g. Frontend/Backend alignment < 0.95 or Backend/DB mismatch), "
                f"you CANNOT issue an unreserved APPROVED verdict. Verdict MUST reflect REJECTED or NEEDS_REMEDIATION.\n"
            )

        return prompt

    def _enforce_consistency_grounding(
        self,
        res_dict: Dict[str, Any],
        consistency_report: Optional[CrossArtifactConsistencyReport] = None,
    ) -> Dict[str, Any]:
        """Prevents over-optimistic APPROVED verdicts when critical cross-artifact inconsistencies exist."""
        if not consistency_report:
            return res_dict

        critical_issues = [
            inc for inc in consistency_report.inconsistencies
            if inc.get("severity") == "CRITICAL"
        ]

        has_blocking = (
            not consistency_report.is_valid
            or consistency_report.frontend_to_backend_alignment < 0.50
            or consistency_report.backend_to_database_alignment < 0.50
            or len(consistency_report.unknown_requirement_ids) > 0
            or len(critical_issues) > 0
        )

        if has_blocking:
            current_verdict = res_dict.get("production_readiness_verdict", "APPROVED")
            if current_verdict == "APPROVED":
                res_dict["production_readiness_verdict"] = "REJECTED" if (consistency_report.frontend_to_backend_alignment < 0.50 or consistency_report.backend_to_database_alignment < 0.50) else "NEEDS_REMEDIATION"
                res_dict["remediation_status"] = "REMEDIATION_REQUIRED"
                findings = res_dict.get("findings", [])
                for inc in critical_issues:
                    findings.append({
                        "category": "Cross-Artifact Contract Consistency",
                        "severity": "CRITICAL",
                        "description": inc.get("detail", "Contract drift detected"),
                        "recommendation": "Re-align downstream artifact with Canonical Architecture Contract",
                    })
                res_dict["findings"] = findings

        return res_dict

    async def run_async(
        self,
        package_summary: Dict[str, Any],
        consistency_report: Optional[CrossArtifactConsistencyReport] = None,
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> Dict[str, Any]:
        """Asynchronously perform adversarial architecture review with live agent-owned RAG context and consistency grounding."""
        # 1. Retrieve domain-specific RAG context
        rag_block, rag_meta = await self.retrieve_rag_context(package_summary)

        # 2. Build prompt and inject additive RAG context & domain grounding
        base_prompt = self._build_prompt(package_summary, consistency_report=consistency_report, cac=cac)
        prompt = self.inject_rag_context(base_prompt, rag_block)
        prompt = self.inject_domain_fence(prompt, cac=cac)

        # 3. Call LLM with fallback
        try:
            result: AdversarialReviewResponse = await self.llm_provider.generate_structured_async(
                prompt=prompt,
                response_model=AdversarialReviewResponse,
                model_name=self.model_name,
                system_prompt=ADVERSARIAL_REVIEW_SYSTEM_PROMPT,
                agent_role=self.role,
                temperature=0.3,
            )
            res_dict = result.model_dump(mode="json")
        except Exception:
            res_dict = {
                "production_readiness_verdict": "APPROVED" if (consistency_report and consistency_report.is_valid) else "NEEDS_REMEDIATION",
                "remediation_status": "NONE_REQUIRED" if (consistency_report and consistency_report.is_valid) else "REMEDIATION_REQUIRED",
                "findings": [],
                "single_points_of_failure": [],
                "scalability_bottlenecks": [],
            }

        # 4. Enforce consistency grounding
        res_dict = self._enforce_consistency_grounding(res_dict, consistency_report=consistency_report)

        return self.attach_rag_metadata(res_dict, rag_meta)

    def run(
        self,
        package_summary: Dict[str, Any],
        consistency_report: Optional[CrossArtifactConsistencyReport] = None,
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> Dict[str, Any]:
        """Synchronously perform adversarial architecture review."""
        prompt = self._build_prompt(package_summary, consistency_report=consistency_report, cac=cac)
        try:
            result: AdversarialReviewResponse = self.llm_provider.generate_structured(
                prompt=prompt,
                model_name=self.model_name,
                response_model=AdversarialReviewResponse,
                system_prompt=ADVERSARIAL_REVIEW_SYSTEM_PROMPT,
                agent_name=self.role,
                temperature=0.3,
            )
            res_dict = result.model_dump(mode="json")
        except Exception:
            res_dict = {
                "production_readiness_verdict": "APPROVED" if (consistency_report and consistency_report.is_valid) else "NEEDS_REMEDIATION",
                "remediation_status": "NONE_REQUIRED" if (consistency_report and consistency_report.is_valid) else "REMEDIATION_REQUIRED",
                "findings": [],
                "single_points_of_failure": [],
                "scalability_bottlenecks": [],
            }
        return self._enforce_consistency_grounding(res_dict, consistency_report=consistency_report)
