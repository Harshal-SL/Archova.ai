"""Observability & SRE Agent for SAE v2.

Generates Prometheus metrics, Grafana dashboards, OpenTelemetry distributed tracing,
and Service Level Objectives (SLOs) bound strictly to Canonical Architecture Contract (CAC) operation paths.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from app.sae.agents.base_agent import BaseArchitectureAgent
from app.sae.models.response_models import ObservabilityResponse
from app.sae.prompts.observability_prompt import (
    OBSERVABILITY_SYSTEM_PROMPT,
    OBSERVABILITY_USER_PROMPT_TEMPLATE,
)
from app.sae.providers.llm_provider import OpenRouterProvider
from app.sae.services.architecture_knowledge_service import ArchitectureKnowledgeService
from app.sae.utils.canonical_contract import CanonicalArchitectureContract


class ObservabilityAgent(BaseArchitectureAgent):
    """Agent responsible for generating Observability, SLOs, and SRE reliability plans."""

    role: str = "observability"

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
        cloud_lld: Dict[str, Any],
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> str:
        hld_str = json.dumps(hld, indent=2, default=str)
        cloud_str = json.dumps(cloud_lld, indent=2, default=str)
        prompt = OBSERVABILITY_USER_PROMPT_TEMPLATE.format(
            hld_document_json=hld_str,
            cloud_lld_json=cloud_str,
        )

        if cac and cac.api_operations:
            cac_ops_table = "\n".join([
                f"  - operation_id: {op.operation_id} | method: {op.method} | path: {op.path}"
                for op in cac.api_operations
            ])
            prompt += f"\n\nCANONICAL API CONTRACT (MANDATORY MONITORED ROUTES):\nEvery SLO, SLI, and alert rule MUST monitor these exact URI paths (DO NOT INVENT ALTERNATE ROUTES):\n{cac_ops_table}\n"
        return prompt

    def _synthesize_fallback_observability(
        self,
        hld: Dict[str, Any],
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> Dict[str, Any]:
        """Synthesizes structured observability configuration with canonical SLO routes."""
        read_path = "/api/v1/resources"
        write_path = "/api/v1/transactions"

        if cac and cac.api_operations:
            for op in cac.api_operations:
                if op.method.upper() == "GET":
                    read_path = op.path
                elif op.method.upper() == "POST" and "auth" not in op.path:
                    write_path = op.path

        return {
            "service_level_objectives": [
                {
                    "name": "API Availability SLO",
                    "target": "99.9% uptime over rolling 30-day window",
                    "sli": "Fraction of non-5xx HTTP requests at API gateway / total requests",
                    "error_budget": "43.2 minutes of total downtime allowance per 30 days",
                },
                {
                    "name": "Read Path Latency SLO",
                    "target": f"95% of {read_path} queries return in <= 200ms",
                    "sli": f"Histogram timer measuring handler execution time for {read_path}",
                    "error_budget": "5% of queries allowed to exceed 200ms",
                },
                {
                    "name": "Transaction Success SLO",
                    "target": f"99.95% of {write_path} requests complete successfully",
                    "sli": f"Fraction of {write_path} mutations returning 2xx status",
                    "error_budget": "2.4 minutes of transaction error per 30 days",
                },
            ],
            "error_budgets": {
                "burn_rate_alert_threshold": "10x burn rate (1% of budget consumed in 1 hour) triggers P1 page",
                "budget_exhaustion_policy": "Feature freeze on non-critical deployments; sprint dedicated to reliability improvements",
            },
            "metrics": {
                "collector": "Prometheus with OpenTelemetry Python SDK for FastAPI",
                "golden_signals": [
                    {"signal": "Latency", "metric_name": "http_request_duration_seconds_bucket", "type": "Histogram"},
                    {"signal": "Traffic", "metric_name": "http_requests_total", "type": "Counter"},
                    {"signal": "Errors", "metric_name": "http_requests_total{status=~'5..'}", "type": "Counter"},
                    {"signal": "Saturation", "metric_name": "db_connection_pool_active_connections", "type": "Gauge"},
                    {"signal": "Cache Hit Ratio", "metric_name": "redis_cache_hits_total / (redis_cache_hits_total + redis_cache_misses_total)", "type": "Gauge"},
                ],
            },
            "logging_strategy": {
                "format": "JSON structured logs to stdout",
                "mandatory_fields": ["timestamp_utc", "level", "trace_id", "span_id", "service_name", "user_id", "route", "status_code", "duration_ms"],
                "retention": "30 days hot in Elasticsearch/CloudWatch, 365 days cold in S3 Glacier",
            },
            "distributed_tracing": {
                "standard": "W3C TraceContext headers (traceparent)",
                "sampling_rate": "100% on errors (HTTP >= 500) and 10% on success paths (HTTP 2xx/3xx)",
                "backend": "OpenTelemetry Collector exporting to Jaeger + AWS X-Ray",
            },
            "alerting_rules": [
                {
                    "name": "HighHTTPErrorRate",
                    "condition": "sum(rate(http_requests_total{status=~'5..'}[5m])) / sum(rate(http_requests_total[5m])) > 0.01",
                    "for": "2 minutes",
                    "severity": "CRITICAL",
                    "action": "PagerDuty on-call dispatch + Slack #critical-alerts notification",
                },
                {
                    "name": "DatabasePoolExhaustion",
                    "condition": "db_connection_pool_active_connections / db_connection_pool_max_connections > 0.85",
                    "for": "3 minutes",
                    "severity": "HIGH",
                    "action": "Slack #infra-alerts notification + auto-scale connection pool",
                },
            ],
            "dashboards": [
                {
                    "name": "Executive Service Health",
                    "widgets": ["Global RPS", "SLO Burn Rate", "p95 Latency by Endpoint", "Active 5xx Error Rate"],
                },
            ],
            "health_checks": {
                "liveness_probe": {"endpoint": "/live", "check": "In-process HTTP server responsive", "interval": "10s"},
                "readiness_probe": {"endpoint": "/ready", "check": "Postgres pool responsive + Redis ping", "interval": "15s"},
            },
        }

    async def run_async(
        self,
        hld: Dict[str, Any],
        cloud_lld: Dict[str, Any],
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> Dict[str, Any]:
        """Asynchronously generate Observability Plan with live agent-owned RAG context and CAC grounding."""
        context = {
            "domain": hld.get("domain", "") or hld.get("system_name", ""),
            "hld": hld,
            "cloud_lld": cloud_lld,
        }

        # 1. Retrieve domain-specific RAG context
        rag_block, rag_meta = await self.retrieve_rag_context(context)

        # 2. Build prompt with CAC binding and authoritative domain fence
        base_prompt = self._build_prompt(hld, cloud_lld, cac=cac)
        prompt = self.inject_rag_context(base_prompt, rag_block)
        prompt = self.inject_domain_fence(prompt, cac=cac)

        # 3. Call LLM with fallback
        try:
            result: ObservabilityResponse = await self.llm_provider.generate_structured_async(
                prompt=prompt,
                response_model=ObservabilityResponse,
                model_name=self.model_name,
                system_prompt=OBSERVABILITY_SYSTEM_PROMPT,
                agent_role=self.role,
                temperature=0.2,
            )
            res_dict = result.model_dump(mode="json")
        except Exception:
            res_dict = self._synthesize_fallback_observability(hld, cac=cac)

        if not res_dict.get("service_level_objectives") or not res_dict.get("metrics"):
            fallback = self._synthesize_fallback_observability(hld, cac=cac)
            for k, v in fallback.items():
                if not res_dict.get(k):
                    res_dict[k] = v

        # Re-align SLO SLIs with canonical paths if non-canonical routes were generated
        if cac and cac.api_operations:
            canonical_paths = [op.path for op in cac.api_operations]
            slos = res_dict.get("service_level_objectives", [])
            for slo in slos:
                if isinstance(slo, dict):
                    sli = slo.get("sli", "")
                    # If SLI references /api/v1/borrows or /api/v1/books, replace with matching canonical path
                    for op in cac.api_operations:
                        leaf = op.path.strip("/").split("/")[-1]
                        if leaf in sli:
                            slo["sli"] = sli.replace(f"/api/v1/{leaf}", op.path).replace(f"/api/v1/{leaf}s", op.path)

        return self.attach_rag_metadata(res_dict, rag_meta)

    def run(
        self,
        hld: Dict[str, Any],
        cloud_lld: Dict[str, Any],
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> Dict[str, Any]:
        """Synchronously generate Observability Plan."""
        prompt = self._build_prompt(hld, cloud_lld, cac=cac)
        try:
            result: ObservabilityResponse = self.llm_provider.generate_structured(
                prompt=prompt,
                model_name=self.model_name,
                response_model=ObservabilityResponse,
                system_prompt=OBSERVABILITY_SYSTEM_PROMPT,
                agent_name=self.role,
                temperature=0.2,
            )
            return result.model_dump(mode="json")
        except Exception:
            return self._synthesize_fallback_observability(hld, cac=cac)
