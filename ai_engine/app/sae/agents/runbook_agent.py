"""Runbook & Incident Operations Agent for SAE v2."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from app.sae.agents.base_agent import BaseArchitectureAgent
from app.sae.models.response_models import RunbookResponse
from app.sae.prompts.runbook_prompt import (
    RUNBOOK_SYSTEM_PROMPT,
    RUNBOOK_USER_PROMPT_TEMPLATE,
)
from app.sae.providers.llm_provider import OpenRouterProvider
from app.sae.services.architecture_knowledge_service import ArchitectureKnowledgeService


class RunbookAgent(BaseArchitectureAgent):
    """Agent responsible for generating operational runbooks, incident triage guides, and disaster recovery procedures."""

    role: str = "runbooks"

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

    def _build_prompt(self, hld: Dict[str, Any], cloud_lld: Dict[str, Any], backend_lld: Dict[str, Any]) -> str:
        hld_str = json.dumps(hld, indent=2, default=str)
        cloud_str = json.dumps(cloud_lld, indent=2, default=str)
        backend_str = json.dumps(backend_lld, indent=2, default=str)
        return RUNBOOK_USER_PROMPT_TEMPLATE.format(
            hld_document_json=hld_str,
            cloud_lld_json=cloud_str,
            backend_lld_json=backend_str,
        )

    def _synthesize_fallback_runbooks(self, hld: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesizes standard SRE operational runbooks and disaster recovery procedures strictly matching schema."""
        sys_name = hld.get("system_name", "Enterprise Platform")
        return {
            "on_call_escalation": [
                {"tier": "Tier 1 (Automated)", "contact": "PagerDuty automated paging to Primary On-Call Engineer", "sla": "Respond within 5 minutes for P1, 15 minutes for P2"},
                {"tier": "Tier 2 (Secondary)", "contact": "Secondary On-Call Engineer paged if unacknowledged after 10 minutes", "sla": "Immediate escalation"},
                {"tier": "Tier 3 (Engineering Lead)", "contact": "Engineering Lead + Cloud Infrastructure Architect", "sla": "Incident unresolved after 30 minutes"},
            ],
            "incident_response_steps": [
                {"step": 1, "action": f"Acknowledge alert in PagerDuty & open dedicated incident channel for {sys_name}"},
                {"step": 2, "action": "Triage severity (P1: Customer-facing outage / P2: Degraded transaction latency / P3: Non-blocking warning)"},
                {"step": 3, "action": "Inspect CloudWatch/Prometheus dashboard for database pool saturation, memory spikes, or upstream HTTP 5xx errors"},
                {"step": 4, "action": "Execute immediate mitigation (traffic redirection, canary rollback, or cache pre-warming) before deep root-cause analysis"},
                {"step": 5, "action": "Post-incident review: file blameless post-mortem within 48 hours and log remediation Jira tickets"},
            ],
            "deployment_rollback_procedure": {
                "trigger": "Elevated HTTP 5xx rate (> 1%) or failed health checks (/ready probe failure > 3 consecutive attempts) post-deployment",
                "procedure": [
                    "1. Revert ECS Task Definition or Kubernetes Deployment to previous stable image tag",
                    "2. Re-route ALB / Ingress traffic immediately to previous revision containers",
                    "3. Run Alembic downgrade migration script if schema alterations were backward-incompatible",
                    "4. Verify /live and /ready endpoints return HTTP 200 across all active instances",
                ],
                "verification": "Check APM metrics: error rate must drop to < 0.05% within 3 minutes of rollback completion",
            },
            "backup_restore_drill": {
                "schedule": "Automated weekly restore drill to isolated staging sandbox",
                "rpo_target": "RPO <= 5 minutes (via automated Multi-AZ continuous WAL replication)",
                "rto_target": "RTO <= 15 minutes (via automated snapshot provisioner)",
                "procedure": [
                    "1. Pull latest daily RDS PostgreSQL automated snapshot from encrypted storage",
                    "2. Spin up temporary staging database instance from snapshot",
                    "3. Run automated integrity verification script checking row counts across core domain tables",
                    "4. Validate point-in-time recovery WAL replay to measure actual RTO/RPO",
                    "5. Tear down staging sandbox and archive compliance drill verification report",
                ],
            },
            "failover_procedure": {
                "database_failover": "Automatic Multi-AZ failover via AWS RDS within 60-120s with zero manual intervention",
                "application_failover": "ECS Auto-Recovery restarts failed container tasks across multiple Availability Zones",
                "traffic_routing": "Route53 DNS health checks failover traffic to healthy AZ target group",
            },
            "common_alerts_playbook": [
                {
                    "alert_name": "High HTTP 5xx Error Rate (> 1% over 5m)",
                    "severity": "CRITICAL",
                    "probable_cause": "Unhandled application exception, upstream gateway failure, or DB deadlock",
                    "mitigation_steps": "Scale container count from min 2 to 6; restart stalled workers; check error logs for stack traces",
                },
                {
                    "alert_name": "Database Connection Pool Saturation (> 85% capacity)",
                    "severity": "HIGH",
                    "probable_cause": "Slow queries (> 1000ms), unindexed joins, or sudden traffic surge",
                    "mitigation_steps": "Terminate long-running idle transactions via pg_terminate_backend; flush Redis cache; increase pool ceiling",
                },
                {
                    "alert_name": "Redis Cache Eviction Surge / Hit Rate Drop (< 80%)",
                    "severity": "MEDIUM",
                    "probable_cause": "High key churn, undersized memory limit, or cache stampede",
                    "mitigation_steps": "Scale ElastiCache node type; adjust TTL jitter on popular cache keys to prevent stampedes",
                },
            ],
            "data_retention_and_purge_flow": {
                "policy": "Operational audit logs retained for 90 days in S3 Glacier; customer PII purged upon account closure request (GDPR/FERPA)",
                "automated_job": "Daily Celery / AWS Lambda cron job querying soft-deleted user records past 30-day grace period",
                "verification": "Cryptographic audit log generated confirming irreversible anonymization of personal identifiers",
            },
        }

    async def run_async(self, hld: Dict[str, Any], cloud_lld: Dict[str, Any], backend_lld: Dict[str, Any]) -> Dict[str, Any]:
        """Asynchronously generate Runbooks with live agent-owned RAG context."""
        context = {
            "domain": hld.get("domain", "") or hld.get("system_name", ""),
            "hld": hld,
            "cloud_lld": cloud_lld,
            "backend_lld": backend_lld,
        }

        # 1. Retrieve domain-specific RAG context
        rag_block, rag_meta = await self.retrieve_rag_context(context)

        # 2. Build prompt and inject additive RAG context & domain grounding
        base_prompt = self._build_prompt(hld, cloud_lld, backend_lld)
        prompt = self.inject_rag_context(base_prompt, rag_block)
        prompt = self.inject_domain_fence(prompt, arsrs=hld)

        # 3. Call LLM with fallback handling
        try:
            result: RunbookResponse = await self.llm_provider.generate_structured_async(
                prompt=prompt,
                response_model=RunbookResponse,
                model_name=self.model_name,
                system_prompt=RUNBOOK_SYSTEM_PROMPT,
                agent_role=self.role,
                temperature=0.2,
            )
            res_dict = result.model_dump(mode="json")
        except Exception:
            res_dict = self._synthesize_fallback_runbooks(hld)

        if not res_dict.get("incident_response_steps") or not res_dict.get("deployment_rollback_procedure"):
            fallback = self._synthesize_fallback_runbooks(hld)
            for k, v in fallback.items():
                if not res_dict.get(k):
                    res_dict[k] = v

        return self.attach_rag_metadata(res_dict, rag_meta)

    def run(self, hld: Dict[str, Any], cloud_lld: Dict[str, Any], backend_lld: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronously generate Runbooks."""
        prompt = self._build_prompt(hld, cloud_lld, backend_lld)
        try:
            result: RunbookResponse = self.llm_provider.generate_structured(
                prompt=prompt,
                model_name=self.model_name,
                response_model=RunbookResponse,
                system_prompt=RUNBOOK_SYSTEM_PROMPT,
                agent_name=self.role,
                temperature=0.2,
            )
            return result.model_dump(mode="json")
        except Exception:
            return self._synthesize_fallback_runbooks(hld)
