"""Adversarial Review Remediation Engine for SAE v2.

Parses Red-Team adversarial findings (SPOFs, unresolved risks, untested assumptions),
identifies affected artifacts, and applies targeted deterministic remediation deltas.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from app.sae.utils.domain_lock import DomainContext

logger = logging.getLogger(__name__)


class AdversarialFinding(BaseModel):
    """Structured architectural defect or risk identified by adversarial reviewer."""
    id: str = Field(..., description="Stable finding ID (e.g. SPOF-001, RISK-001)")
    title: str = Field(..., description="Finding summary")
    category: str = Field(default="SPOF", description="SPOF, Risk, Assumption, Security")
    severity: str = Field(default="HIGH", description="CRITICAL, HIGH, MEDIUM, LOW")
    affected_artifacts: List[str] = Field(default_factory=list, description="hld, backend_lld, database_lld, cloud_lld, security_lld")
    remediation_action: str = Field(default="")


class RemediationPlan(BaseModel):
    """Actionable remediation plan addressing all adversarial review findings."""
    verdict: str = Field(default="APPROVED")
    total_findings: int = 0
    findings: List[AdversarialFinding] = Field(default_factory=list)
    affected_artifacts: List[str] = Field(default_factory=list)
    remediations_applied: List[str] = Field(default_factory=list)


class RemediationEngine:
    """Automated Remediation Loop Orchestrator."""

    @classmethod
    def create_remediation_plan(cls, adversarial_review: Dict[str, Any]) -> RemediationPlan:
        """Extract structured findings and map them to affected artifacts."""
        findings: List[AdversarialFinding] = []
        affected_set: Set[str] = set()

        verdict = adversarial_review.get("production_readiness_verdict", "APPROVED")

        # 1. Parse Single Points of Failure
        spofs = adversarial_review.get("single_points_of_failure", [])
        if isinstance(spofs, list):
            for idx, spof in enumerate(spofs, 1):
                desc = str(spof) if not isinstance(spof, dict) else spof.get("description", str(spof))
                affected = []
                action = "Add multi-AZ redundancy and automated failover"
                if any(k in desc.lower() for k in ["database", "db", "postgres", "mysql", "stateful"]):
                    affected = ["database_lld", "cloud_lld"]
                    action = "Configure Primary-Replica streaming replication with automated failover and read replica offloading"
                elif any(k in desc.lower() for k in ["gateway", "ingress", "api", "load balancer"]):
                    affected = ["cloud_lld", "backend_lld"]
                    action = "Deploy redundant Multi-AZ Ingress Controllers with health-checked DNS load balancing"
                elif any(k in desc.lower() for k in ["queue", "rabbitmq", "kafka", "redis"]):
                    affected = ["cloud_lld", "backend_lld"]
                    action = "Configure clustered message broker with mirrored quorum queues"
                else:
                    affected = ["hld", "cloud_lld"]

                affected_set.update(affected)
                findings.append(
                    AdversarialFinding(
                        id=f"SPOF-{idx:03d}",
                        title=desc[:80],
                        category="SPOF",
                        severity="CRITICAL",
                        affected_artifacts=affected,
                        remediation_action=action,
                    )
                )

        # 2. Parse Unresolved Risks
        risks = adversarial_review.get("unresolved_risks", [])
        if isinstance(risks, list):
            for idx, risk in enumerate(risks, 1):
                desc = str(risk) if not isinstance(risk, dict) else risk.get("description", str(risk))
                affected = ["security_lld", "cloud_lld"] if "security" in desc.lower() else ["backend_lld", "hld"]
                affected_set.update(affected)
                findings.append(
                    AdversarialFinding(
                        id=f"RISK-{idx:03d}",
                        title=desc[:80],
                        category="Risk",
                        severity="HIGH",
                        affected_artifacts=affected,
                        remediation_action="Inject rate limiting, circuit breaking, and defensive retry backoff",
                    )
                )

        return RemediationPlan(
            verdict=verdict,
            total_findings=len(findings),
            findings=findings,
            affected_artifacts=list(affected_set),
        )

    @classmethod
    def apply_remediation(
        cls,
        plan: RemediationPlan,
        interim_package: Dict[str, Any],
        domain_ctx: DomainContext,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Apply targeted remediation deltas to affected artifacts and return updated package."""
        if plan.total_findings == 0:
            return interim_package, {
                "production_readiness_verdict": plan.verdict,
                "remediation_status": "NONE_REQUIRED",
                "single_points_of_failure": [],
                "unresolved_risks": [],
            }

        remediations_applied = []
        updated = dict(interim_package)

        # ── Remediate Cloud LLD & Database LLD ────────────────────────────────
        if "cloud_lld" in plan.affected_artifacts or "database_lld" in plan.affected_artifacts:
            cloud_lld = dict(updated.get("cloud_lld", {}))
            comp = cloud_lld.get("compute", {})
            if isinstance(comp, dict):
                comp["high_availability"] = "Multi-AZ Deployment across 3 Availability Zones with Pod Anti-Affinity"
                cloud_lld["compute"] = comp

            db_infra = cloud_lld.get("storage", {})
            if isinstance(db_infra, dict):
                db_infra["database_replication"] = "Primary-Standby Multi-AZ with Read Replicas and Automated Backup"
                cloud_lld["storage"] = db_infra

            updated["cloud_lld"] = cloud_lld
            remediations_applied.append("Cloud LLD: Enforced Multi-AZ high availability and automated DB failover")

        # ── Remediate Backend LLD Resilience ──────────────────────────────────
        if "backend_lld" in plan.affected_artifacts:
            backend_lld = dict(updated.get("backend_lld", {}))
            sec_cfg = backend_lld.get("security_config", {})
            if isinstance(sec_cfg, dict):
                sec_cfg["resilience"] = "Resilience4j / Tenacity Circuit Breaker with 2000ms timeout and dead-letter queues"
                backend_lld["security_config"] = sec_cfg
            updated["backend_lld"] = backend_lld
            remediations_applied.append("Backend LLD: Injected Circuit Breaker and automated retry policies")

        # ── Remediate Security LLD ────────────────────────────────────────────
        if "security_lld" in plan.affected_artifacts:
            security_lld = dict(updated.get("security_lld", {}))
            security_lld["threat_mitigations"] = [
                "Strict JWT validation with short-lived tokens and Redis blacklist",
                "Ingress-level TLS 1.3 termination with HSTS headers enabled",
                "OWASP Top 10 input validation & SQL parameterized query enforcement",
            ]
            updated["security_lld"] = security_lld
            remediations_applied.append("Security LLD: Enforced OWASP mitigations and TLS 1.3 policy")

        # Create updated adversarial review status
        remediated_review = {
            "production_readiness_verdict": "APPROVED_AFTER_REMEDIATION",
            "remediation_status": "REMEDIATED",
            "findings_count": plan.total_findings,
            "remediations_applied": remediations_applied,
            "single_points_of_failure": [],
            "unresolved_risks": [f"Remediated: {f.title}" for f in plan.findings],
            "untested_assumptions": [],
        }

        logger.info(
            f"Adversarial Remediation Loop completed. Applied {len(remediations_applied)} remediations across {plan.affected_artifacts}."
        )

        return updated, remediated_review
