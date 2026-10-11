"""Actionable Architecture Remediation Engine.

Transforms validation findings (SPOFs, contract drifts, NFR gaps, security issues, domain drift)
into prioritized, executable remediation actions with concrete patch snippets and revalidation criteria.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set

from Validator_Engine.models.finding_models import FindingSeverity, ValidationFinding
from Validator_Engine.models.report_models import (
    ArchitectureCorrectionFeedback,
    CorrectionFeedbackItem,
    RemediationAction,
    RemediationPlan,
)

logger = logging.getLogger(__name__)


class RemediationEngine:
    """Orchestrates actionable remediation plan synthesis."""

    def __init__(self) -> None:
        pass

    def build_remediation_plan(
        self,
        findings: List[ValidationFinding],
        verdict: str = "APPROVED",
    ) -> RemediationPlan:
        """Create structured, prioritized remediation actions for all identified findings."""
        if not findings:
            return RemediationPlan(
                verdict="APPROVED",
                total_findings=0,
                total_findings_count=0,
                critical_findings_count=0,
                affected_components=[],
                actions=[],
                remediation_actions=[],
                suggested_patches={},
                remediation_summary="Architecture meets all validation gates. No corrective actions required.",
            )

        # Sort findings by severity: CRITICAL first, then HIGH, MEDIUM, LOW
        severity_rank = {
            FindingSeverity.CRITICAL: 0,
            FindingSeverity.HIGH: 1,
            FindingSeverity.MEDIUM: 2,
            FindingSeverity.LOW: 3,
        }
        sorted_findings = sorted(findings, key=lambda f: severity_rank.get(f.severity, 4))

        affected_components_set: Set[str] = set()
        actions: List[Dict[str, Any]] = []
        remediation_actions: List[RemediationAction] = []
        suggested_patches: Dict[str, Any] = {}

        critical_count = 0

        for idx, finding in enumerate(sorted_findings, 1):
            affected_components_set.add(finding.affected_component)
            action_id = f"REM-{idx:03d}"
            priority = "P0" if finding.severity == FindingSeverity.CRITICAL else "P1" if finding.severity == FindingSeverity.HIGH else "P2"
            if finding.severity == FindingSeverity.CRITICAL:
                critical_count += 1

            # Generate concrete configuration patch snippet based on component & finding category
            patch = self._generate_patch_snippet(finding)
            if patch:
                patch_key = f"{action_id}_{finding.affected_component.replace('.', '_').replace(' ', '_')}"
                suggested_patches[patch_key] = patch

            action_dict = {
                "action_id": action_id,
                "priority": priority,
                "finding_id": finding.id,
                "category": finding.category.value,
                "severity": finding.severity.value,
                "target_component": finding.affected_component,
                "issue_summary": finding.explanation,
                "recommendation": finding.recommendation,
                "revalidation_criteria": f"Verify {finding.affected_component} satisfies: {finding.recommendation}",
            }
            actions.append(action_dict)

            remediation_actions.append(
                RemediationAction(
                    action_id=action_id,
                    priority=priority,
                    finding_id=finding.id,
                    category=finding.category.value,
                    severity=finding.severity.value,
                    target_component=finding.affected_component,
                    target_artifact=self._map_target_artifact(finding.affected_component),
                    title=f"Remediate {finding.id} ({finding.affected_component})",
                    description=finding.explanation,
                    recommendation=finding.recommendation,
                    revalidation_criteria=f"Verify {finding.affected_component} satisfies: {finding.recommendation}",
                    recommended_patch=patch or {},
                )
            )

        final_verdict = (
            "REJECTED"
            if critical_count > 0
            else "NEEDS_REMEDIATION"
            if any(f.severity == FindingSeverity.HIGH for f in findings)
            else "APPROVED_WITH_CONDITIONS"
            if findings
            else "APPROVED"
        )

        summary_text = (
            f"Generated {len(actions)} prioritized remediation action(s) ({critical_count} Critical / P0, "
            f"{len([a for a in actions if a['priority'] == 'P1'])} High / P1) across {len(affected_components_set)} component(s)."
        )

        return RemediationPlan(
            verdict=final_verdict,
            total_findings=len(findings),
            total_findings_count=len(findings),
            critical_findings_count=critical_count,
            affected_components=sorted(list(affected_components_set)),
            actions=actions,
            remediation_actions=remediation_actions,
            suggested_patches=suggested_patches,
            remediation_summary=summary_text,
        )

    def _map_target_artifact(self, component: str) -> str:
        comp = component.lower()
        if "backend" in comp or "service" in comp or "endpoint" in comp:
            return "backend_lld"
        if "database" in comp or "table" in comp or "sql" in comp:
            return "database_lld"
        if "cloud" in comp or "compute" in comp or "vpc" in comp:
            return "cloud_lld"
        if "security" in comp or "auth" in comp:
            return "security_lld"
        if "frontend" in comp or "page" in comp or "ui" in comp:
            return "frontend_lld"
        return "hld"

    def _generate_patch_snippet(self, finding: ValidationFinding) -> Optional[Dict[str, Any]]:
        """Generate targeted configuration delta for specific defect categories."""
        comp = finding.affected_component.lower()
        expl = finding.explanation.lower()
        fid = finding.id.lower()

        # IoT Ingestion Patch
        if "iot" in expl or "sensor" in expl:
            return {
                "cloud_lld": {
                    "iot_ingestion": {
                        "protocol": "MQTT over TLS (Port 8883)",
                        "broker_service": "AWS IoT Core / EMQX Managed Broker",
                        "buffer_queue": "Amazon SQS FIFO Queue (Sensor Telemetry Buffer)",
                        "batch_consumer": "ECS Fargate Telemetry Consumer Task (Batch Size: 50 records)",
                    }
                },
                "backend_lld": {
                    "telemetry_service": {
                        "name": "IoTSensorIngestionWorker",
                        "mode": "Async Event-Driven Queue Consumer",
                        "persistence_mode": "Batch UPSERT into 'slots' table with Redis state invalidation",
                    }
                }
            }

        # Concurrency & Slot Reservation Locking Patch
        if "concurrency" in expl or "double-booking" in expl or "reservation" in expl:
            return {
                "backend_lld": {
                    "reservation_concurrency_policy": {
                        "lock_type": "Redis Redlock Distributed Locking with 10-minute hold TTL",
                        "database_fallback": "SELECT id, status FROM slots WHERE id = :slot_id FOR UPDATE NOWAIT",
                        "hold_duration_seconds": 600,
                        "expiration_worker": "Celery / Background Async Worker releasing unpaid holds every 60 seconds",
                    }
                }
            }

        # Domain Drift Table Remediation Patch
        if "domain-drift" in fid or "drift table" in expl:
            return {
                "database_lld": {
                    "schema_cleanup": {
                        "action": "DROP or EXCLUDE out-of-domain table",
                        "target_table": finding.affected_component.replace("Database Table: ", "").strip(),
                        "rationale": "Align schema with parking domain (slots, reservations, vehicles, payments)",
                    }
                }
            }

        # Database Indexing Patch
        if "index" in expl or "indexing" in expl:
            return {
                "database_lld": {
                    "indexes": [
                        {
                            "table": "slots",
                            "index_name": "idx_slots_parking_lot_status",
                            "columns": ["parking_lot_id", "status"],
                            "index_type": "B-Tree",
                        },
                        {
                            "table": "drivers",
                            "index_name": "idx_drivers_license_plate",
                            "columns": ["license_plate"],
                            "index_type": "B-Tree (Unique)",
                        },
                    ]
                }
            }

        # Multi-AZ Compute Patch
        if "compute" in comp or "spof-001" in fid:
            return {
                "cloud_lld": {
                    "compute": {
                        "high_availability": "Multi-AZ Deployment across 3 Availability Zones with Pod Anti-Affinity",
                        "autoscaling": {
                            "min_instances": 2,
                            "max_instances": 10,
                            "target_cpu_utilization": 70,
                        },
                    }
                }
            }

        # Database Replication & Failover Patch
        if "database" in comp or "db" in comp:
            return {
                "database_lld": {
                    "replication": {
                        "mode": "Primary-Standby Multi-AZ with Synchronous Replication",
                        "read_replicas_count": 2,
                        "failover_rto_seconds": 30,
                    }
                }
            }

        # Security Rate Limiting & TLS Patch
        if "security" in comp or "rate-limit" in expl:
            return {
                "security_lld": {
                    "ingress_protection": {
                        "tls_version": "TLS 1.3",
                        "rate_limiting": {
                            "algorithm": "Token Bucket",
                            "limit_per_minute": 120,
                            "burst_capacity": 30,
                        },
                        "hsts_enabled": True,
                    }
                }
            }

        return None

    def build_correction_feedback(
        self,
        package: Any,
        findings: List[ValidationFinding],
        real_world_report: Optional[Any] = None,
        attempt: int = 1,
    ) -> ArchitectureCorrectionFeedback:
        """Create structured correction feedback bundle instructing the AI Engine on targeted architectural repairs."""
        items: List[CorrectionFeedbackItem] = []
        affected_artifacts_set: Set[str] = set()

        # Filter actionable defects (CRITICAL, HIGH, and actionable MEDIUM findings)
        actionable_findings = [
            f for f in findings
            if f.severity in (FindingSeverity.CRITICAL, FindingSeverity.HIGH)
            or (f.severity == FindingSeverity.MEDIUM and f.recommendation)
        ]

        critical_count = len([f for f in actionable_findings if f.severity == FindingSeverity.CRITICAL])
        high_count = len([f for f in actionable_findings if f.severity == FindingSeverity.HIGH])

        for finding in actionable_findings:
            target_art = self._map_target_artifact(finding.affected_component)
            affected_artifacts_set.add(target_art)

            # RAG evidence: finding evidence or relevant retrieved evidence
            rag_ev = finding.evidence or ""
            if not rag_ev and real_world_report and hasattr(real_world_report, "matched_archetypes"):
                for m in getattr(real_world_report, "matched_archetypes", []):
                    if hasattr(m, "relevance_summary"):
                        rag_ev = m.relevance_summary
                        break

            patch = self._generate_patch_snippet(finding)

            item = CorrectionFeedbackItem(
                issue_id=finding.id,
                issue_identified=finding.explanation,
                missing_or_incorrect_detail=self._extract_missing_detail(finding),
                affected_artifact=target_art,
                affected_requirement_id=finding.requirement_id,
                affected_component=finding.affected_component,
                severity=finding.severity.value,
                recommended_correction=finding.recommendation,
                rag_evidence=rag_ev or "Referenced from enterprise architectural patterns in Category 10 & 11 knowledge base.",
                suggested_patch=patch or {},
            )
            items.append(item)

        pkg_id = getattr(package, "package_id", "arch_pkg")
        gen_id = getattr(package, "generation_id", pkg_id)

        summary = (
            f"Correction Feedback (Attempt {attempt}): {len(items)} actionable issue(s) identified "
            f"({critical_count} Critical, {high_count} High) affecting {len(affected_artifacts_set)} artifact(s): "
            f"{', '.join(sorted(list(affected_artifacts_set)))}."
        )

        return ArchitectureCorrectionFeedback(
            package_id=pkg_id,
            generation_id=gen_id,
            attempt=attempt,
            total_issues=len(items),
            critical_issues_count=critical_count,
            high_issues_count=high_count,
            items=items,
            affected_artifacts=sorted(list(affected_artifacts_set)),
            summary=summary,
        )

    def _extract_missing_detail(self, finding: ValidationFinding) -> str:
        """Derive explicit missing component or contract failure from finding."""
        comp = finding.affected_component
        expl = finding.explanation
        fid = finding.id.lower()

        if "race-reservation" in fid or "double-booking" in expl.lower() or "concurrency" in expl.lower():
            return "Missing distributed locking (Redis Redlock / SELECT FOR UPDATE) and atomic reservation hold mechanism in backend slot reservation service and database tables."
        if "spof-001" in fid or "single database" in expl.lower():
            return "Missing automated Multi-AZ standby failover and read-replica offloading in database configuration."
        if "bottleneck-iot" in fid or "sensor" in expl.lower():
            return "Missing asynchronous message broker buffering (MQTT / Kafka) for IoT sensor telemetry ingestion."
        if "bottleneck-db" in fid or "index" in expl.lower():
            return "Missing composite B-Tree database indexes on slot query lookup columns (parking_lot_id, status)."
        if "sec-risk" in fid or "rate limit" in expl.lower():
            return "Missing ingress API rate limiting and token bucket throttling in security tier."
        if "cascade" in fid or "circuit breaker" in expl.lower():
            return "Missing circuit breaker and fault isolation timeouts on synchronous inter-service communication."

        return f"Defect in {comp}: {expl}"

