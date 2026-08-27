"""HLD Quality Gate & Self-Repair Engine for SAE v2.

Evaluates High Level Design semantic depth, service decomposition, requirement coverage,
and failure modes. Automatically triggers targeted self-healing repair if quality < 0.75.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from app.sae.utils.domain_lock import DomainContext

logger = logging.getLogger(__name__)


class HLDQualityReport(BaseModel):
    """Evaluation scorecard for HLD completeness and semantic quality."""
    score: float = Field(..., description="Semantic quality score 0.0 to 1.0")
    is_valid: bool = Field(..., description="True if score >= 0.75")
    service_count: int = 0
    service_names: List[str] = Field(default_factory=list)
    has_communication_patterns: bool = False
    has_data_strategy: bool = False
    has_security_overview: bool = False
    has_deployment_strategy: bool = False
    has_architecture_decisions: bool = False
    requirement_coverage_ratio: float = 0.0
    covered_requirements: List[str] = Field(default_factory=list)
    missing_criteria: List[str] = Field(default_factory=list)
    defects: List[str] = Field(default_factory=list)
    repaired: bool = False


class HLDQualityGate:
    """Semantic Quality Gate and Self-Repair Orchestrator for HLD."""

    @classmethod
    def evaluate_hld(
        cls,
        hld: Dict[str, Any],
        domain_ctx: DomainContext,
    ) -> HLDQualityReport:
        """Deterministically assess the semantic completeness and depth of HLD."""
        defects: List[str] = []
        missing: List[str] = []

        if not isinstance(hld, dict) or not hld:
            return HLDQualityReport(
                score=0.0,
                is_valid=False,
                missing_criteria=["HLD is completely empty"],
                defects=["Empty or null HLD dictionary payload"],
            )

        # 1. Evaluate Major Services
        services = hld.get("major_services", [])
        if not isinstance(services, list):
            services = []
        
        service_names = []
        for s in services:
            if isinstance(s, dict):
                sname = s.get("name") or s.get("service_name") or s.get("title") or ""
                if sname:
                    service_names.append(sname)
            elif isinstance(s, str) and len(s) > 3:
                service_names.append(s)

        svc_count = len(service_names)
        if svc_count < 3:
            defects.append(f"Insufficient service decomposition: found only {svc_count} services (expected >= 3)")
            missing.append("major_services decomposition")

        # 2. Check Communication & Data Strategy
        comm = hld.get("communication_patterns", [])
        has_comm = bool(comm and isinstance(comm, list) and len(comm) > 0)
        if not has_comm:
            defects.append("Missing communication_patterns defining inter-service protocols")
            missing.append("communication_patterns")

        data_strat = hld.get("data_strategy", {})
        has_data = bool(data_strat and isinstance(data_strat, dict) and any(v for v in data_strat.values()))
        if not has_data:
            defects.append("Missing data_strategy defining database and storage tier")
            missing.append("data_strategy")

        # 3. Check Security & Deployment
        sec_overview = hld.get("security_overview", {})
        has_sec = bool(sec_overview and isinstance(sec_overview, dict) and any(v for v in sec_overview.values()))
        if not has_sec:
            defects.append("Missing security_overview detailing authentication and protection")
            missing.append("security_overview")

        dep_strat = hld.get("deployment_strategy", {})
        has_dep = bool(dep_strat and isinstance(dep_strat, dict) and any(v for v in dep_strat.values()))
        if not has_dep:
            defects.append("Missing deployment_strategy defining container/cloud infrastructure")
            missing.append("deployment_strategy")

        decisions = hld.get("decisions", [])
        has_dec = bool(decisions and isinstance(decisions, list) and len(decisions) > 0)

        # 4. Check Requirement Coverage against Canonical IDs
        hld_text = json.dumps(hld, default=str)
        covered_reqs = []
        for req in domain_ctx.canonical_requirements:
            # Check by exact ID or key words in description
            if req.id in hld_text or any(kw.lower() in hld_text.lower() for kw in req.title.split() if len(kw) > 4):
                covered_reqs.append(req.id)

        total_reqs = len(domain_ctx.canonical_requirements)
        coverage_ratio = round(len(covered_reqs) / max(total_reqs, 1), 2)

        # 5. Check for Placeholder Penalties
        placeholder_hits = [
            p for p in ["tbd", "to be determined", "placeholder", "standard option", "generic option"]
            if p in hld_text.lower()
        ]
        if placeholder_hits:
            defects.append(f"Found placeholder phrases in HLD: {placeholder_hits}")

        # 6. Calculate Weighted Semantic Score
        weights = {
            "services": min(1.0, svc_count / 5.0) * 0.30,
            "data": (1.0 if has_data else 0.0) * 0.20,
            "comm": (1.0 if has_comm else 0.0) * 0.15,
            "sec": (1.0 if has_sec else 0.0) * 0.15,
            "dep": (1.0 if has_dep else 0.0) * 0.10,
            "coverage": coverage_ratio * 0.10,
        }
        raw_score = sum(weights.values())
        penalty = min(0.40, len(placeholder_hits) * 0.10)
        final_score = round(max(0.0, min(1.0, raw_score - penalty)), 2)

        return HLDQualityReport(
            score=final_score,
            is_valid=final_score >= 0.75,
            service_count=svc_count,
            service_names=service_names,
            has_communication_patterns=has_comm,
            has_data_strategy=has_data,
            has_security_overview=has_sec,
            has_deployment_strategy=has_dep,
            has_architecture_decisions=has_dec,
            requirement_coverage_ratio=coverage_ratio,
            covered_requirements=covered_reqs,
            missing_criteria=missing,
            defects=defects,
            repaired=False,
        )

    @classmethod
    def synthesize_domain_archetype_hld(
        cls,
        domain_ctx: DomainContext,
        tech_rec: Dict[str, Any],
        adp: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Synthesize a rich, deterministic domain archetype HLD when LLM generation is incomplete."""
        system_name = domain_ctx.system_name
        arch_style = adp.get("architecture_style") or "Modular Monolith"

        # Construct major services from domain taxonomy
        major_services = []
        for idx, svc_name in enumerate(domain_ctx.default_services, 1):
            major_services.append({
                "service_id": f"SVC-{idx:02d}",
                "name": svc_name,
                "responsibility": f"Handles core domain transactions and workflows for {svc_name.lower()}.",
                "database_binding": f"{svc_name.split()[0].lower()}_db_schema",
                "scaling_model": "Horizontal Stateless Pods (min 2, max 10)",
                "satisfies": [r.id for r in domain_ctx.canonical_requirements if svc_name.split()[0].lower() in r.description.lower()][:2] or [domain_ctx.canonical_requirements[0].id],
            })

        communication_patterns = [
            {
                "pattern": "Synchronous REST / JSON over TLS",
                "usage": "Client-to-Gateway and Gateway-to-Core Service request-response APIs",
                "protocol": "HTTP/2, OpenAPI 3.0",
                "resilience": "Circuit breaker (50% failure threshold), 2500ms timeout",
            },
            {
                "pattern": "Asynchronous Event Messaging",
                "usage": "Domain event notification reminders, transaction history audits, and background tasks",
                "protocol": "RabbitMQ / Redis PubSub",
                "resilience": "Dead-letter exchange with exponential retry backoff (3 attempts)",
            },
        ]

        data_strategy = {
            "primary_database": tech_rec.get("database", {}).get("selected", "PostgreSQL 16"),
            "caching_tier": tech_rec.get("cache", {}).get("selected", "Redis 7.2 Cluster"),
            "replication": "Primary-Replica configuration with automated failover and read-replica offloading",
            "migration_tool": "Alembic Versioned Migrations",
            "backup_policy": "Point-in-Time Recovery (PITR) with continuous WAL archiving and daily full snapshots",
        }

        security_overview = {
            "authentication": "Stateless JWT access tokens with Redis-backed refresh token rotation",
            "authorization": "Role-Based Access Control (RBAC) enforced at API Gateway and Service boundary",
            "data_protection": "AES-256 encryption at rest, TLS 1.3 encryption in transit",
            "audit_logging": "Immutable audit log trail for all administrative and modification transactions",
        }

        deployment_strategy = {
            "infrastructure": "Kubernetes Container Orchestration (EKS/GKE)",
            "ingress": "Ingress-NGINX with TLS Termination and Rate Limiting",
            "ci_cd": "GitHub Actions automated build, container vulnerability scan, and rolling deployment",
            "monitoring": "Prometheus metrics, Grafana dashboards, OpenTelemetry distributed tracing",
        }

        decisions = [
            {
                "id": "ADR-001",
                "title": f"Adoption of {arch_style} for {system_name}",
                "status": "ACCEPTED",
                "rationale": f"Provides optimal balance of modular boundary isolation, fast iteration, and manageable operational complexity for {domain_ctx.domain_name}.",
            },
            {
                "id": "ADR-002",
                "title": "Dual-Layer Caching and Read-Replica Offloading",
                "status": "ACCEPTED",
                "rationale": "Guarantees p95 read latency under 150ms while insulating primary transactional database from high-volume queries.",
            },
        ]

        return {
            "architecture_style": arch_style,
            "executive_summary": (
                f"{system_name} is designed as an enterprise-grade {arch_style} architecture for {domain_ctx.domain_name}. "
                f"The system isolates core domain workflows into resilient, independently deployable services backed by "
                f"{data_strategy['primary_database']} and {data_strategy['caching_tier']}."
            ),
            "business_goals": [
                f"Achieve 99.9% system availability for {domain_ctx.domain_name} operations.",
                "Ensure sub-250ms p95 response time under concurrent user load.",
                "Enforce strict transaction consistency and data auditability.",
            ],
            "major_services": major_services,
            "communication_patterns": communication_patterns,
            "data_strategy": data_strategy,
            "security_overview": security_overview,
            "deployment_strategy": deployment_strategy,
            "decisions": decisions,
            "diagrams": [
                {
                    "type": "C4_Container",
                    "title": f"{system_name} Container Architecture",
                    "description": "Visualizes client apps, API gateway, microservices, databases, and message queues.",
                }
            ],
            "technology_stack": tech_rec,
        }

    @classmethod
    async def repair_hld_if_needed(
        cls,
        hld: Dict[str, Any],
        domain_ctx: DomainContext,
        tech_rec: Dict[str, Any],
        adp: Dict[str, Any],
        llm_provider: Any = None,
    ) -> Tuple[Dict[str, Any], HLDQualityReport]:
        """Validate HLD quality and automatically repair if below threshold."""
        report = cls.evaluate_hld(hld, domain_ctx)
        
        if report.is_valid:
            return hld, report

        logger.warning(
            f"HLD failed quality gate (score: {report.score:.2f} < 0.75, defects: {report.defects}). Initiating self-healing repair..."
        )

        # 1. Generate synthesized domain archetype baseline
        archetype_hld = cls.synthesize_domain_archetype_hld(domain_ctx, tech_rec, adp)

        # 2. Merge existing valid fields from LLM with archetype baseline
        merged_hld = dict(archetype_hld)
        for k, v in hld.items():
            if v and v != "" and v != [] and v != {} and k != "rag_metadata":
                # If LLM generated a valid list/dict, preserve or enrich
                if isinstance(v, list) and len(v) >= 2:
                    merged_hld[k] = v
                elif isinstance(v, dict) and len(v) >= 2:
                    merged_hld[k] = {**merged_hld.get(k, {}), **v}
                elif isinstance(v, str) and len(v) > 20:
                    merged_hld[k] = v

        if "rag_metadata" in hld:
            merged_hld["rag_metadata"] = hld["rag_metadata"]

        # Re-evaluate repaired HLD
        repaired_report = cls.evaluate_hld(merged_hld, domain_ctx)
        repaired_report.repaired = True

        logger.info(
            f"HLD self-repair complete. Quality improved: {report.score:.2f} -> {repaired_report.score:.2f} (Status: {'PASS' if repaired_report.is_valid else 'DEGRADED'})"
        )

        return merged_hld, repaired_report
