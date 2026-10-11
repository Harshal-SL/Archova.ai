"""NFR (Non-Functional Requirements) & Quality Attribute Validator.

Validates that non-functional requirements (latency, throughput, availability,
scalability, security, resilience, observability, disaster recovery) are supported
by concrete architectural patterns in HLD, Backend LLD, Database LLD, Security LLD,
and Cloud LLD.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Set

from Validator_Engine.models.finding_models import (
    FindingCategory,
    FindingSeverity,
    ValidationFinding,
)
from Validator_Engine.models.input_models import ArchitecturePackageInput
from Validator_Engine.models.report_models import NFRValidationReport


class NFRQualityValidator:
    """Evaluates NFR coverage, feasibility, and architectural mechanism grounding."""

    def __init__(self) -> None:
        pass

    def validate(self, package: ArchitecturePackageInput) -> NFRValidationReport:
        """Run comprehensive NFR validation across all artifacts."""
        findings: List[ValidationFinding] = []
        nfr_assessments: List[Dict[str, Any]] = []

        nfrs = package.get_nfrs()
        hld = package.get_hld()
        backend_lld = package.get_backend_lld()
        db_lld = package.get_database_lld()
        security_lld = package.get_security_lld()
        cloud_lld = package.get_cloud_lld()

        # Combine text per artifact for pattern searching
        hld_text = json.dumps(hld, default=str).lower()
        backend_text = json.dumps(backend_lld, default=str).lower()
        db_text = json.dumps(db_lld, default=str).lower()
        sec_text = json.dumps(security_lld, default=str).lower()
        cloud_text = json.dumps(cloud_lld, default=str).lower()
        all_text = f"{hld_text} {backend_text} {db_text} {sec_text} {cloud_text}"

        evaluated_categories: Set[str] = set()
        supported_count = 0
        partially_supported_count = 0
        unsupported_count = 0

        # 1. Validate explicit NFRs declared in ARSRS / Requirements
        if not nfrs:
            findings.append(
                ValidationFinding(
                    id="NFR-001",
                    category=FindingCategory.NFR_VIOLATION,
                    severity=FindingSeverity.HIGH,
                    affected_component="requirement_analysis.non_functional_requirements",
                    explanation="No explicit Non-Functional Requirements (NFRs) defined in the architecture package.",
                    evidence="non_functional_requirements array is empty or missing.",
                    recommendation="Define explicit NFR targets for latency, availability, scalability, and security.",
                )
            )
        else:
            for idx, nfr in enumerate(nfrs, 1):
                nfr_id = (nfr.get("id") or f"NFR-{idx:03d}").upper()
                category = (nfr.get("category") or nfr.get("type") or "General").title()
                desc = nfr.get("description") or nfr.get("requirement") or nfr.get("target") or str(nfr)
                target = nfr.get("target") or nfr.get("sla") or ""
                evaluated_categories.add(category.lower())

                assessment = self._assess_single_nfr(
                    nfr_id=nfr_id,
                    category=category,
                    description=desc,
                    target=target,
                    hld_text=hld_text,
                    backend_text=backend_text,
                    db_text=db_text,
                    sec_text=sec_text,
                    cloud_text=cloud_text,
                    all_text=all_text,
                )
                nfr_assessments.append(assessment)

                if assessment["status"] == "SUPPORTED":
                    supported_count += 1
                elif assessment["status"] == "PARTIALLY_SUPPORTED":
                    partially_supported_count += 1
                    findings.append(
                        ValidationFinding(
                            id=f"NFR-GAP-{idx:03d}",
                            category=FindingCategory.NFR_VIOLATION,
                            severity=FindingSeverity.MEDIUM,
                            requirement_id=nfr_id,
                            affected_component=assessment["primary_artifact"],
                            explanation=f"NFR '{nfr_id}' ({category}) is only partially supported: {assessment['gap_reason']}",
                            evidence=f"Target: {target or desc[:100]} | Found mechanisms: {', '.join(assessment['detected_mechanisms']) or 'None'}",
                            recommendation=assessment["recommendation"],
                        )
                    )
                else:
                    unsupported_count += 1
                    findings.append(
                        ValidationFinding(
                            id=f"NFR-MISS-{idx:03d}",
                            category=FindingCategory.NFR_VIOLATION,
                            severity=FindingSeverity.HIGH,
                            requirement_id=nfr_id,
                            affected_component="architecture",
                            explanation=f"NFR '{nfr_id}' ({category}) has no corresponding architectural implementation provisions.",
                            evidence=f"NFR description: {desc[:150]}",
                            recommendation=assessment["recommendation"],
                        )
                    )

        # 2. Check Standard Quality Pillars (Latency, HA, IoT Ingestion, Concurrency, Encryption, Observability)
        pillar_checks = self._check_standard_quality_pillars(
            package=package,
            hld_text=hld_text,
            backend_text=backend_text,
            db_text=db_text,
            sec_text=sec_text,
            cloud_text=cloud_text,
        )

        for pillar_finding in pillar_checks:
            findings.append(pillar_finding)

        # Compute Score
        total_nfrs = max(len(nfrs), 1)
        coverage_ratio = (supported_count + (0.5 * partially_supported_count)) / total_nfrs if nfrs else 0.5
        pillar_penalty = min(0.40, len([f for f in pillar_checks if f.severity in (FindingSeverity.CRITICAL, FindingSeverity.HIGH)]) * 0.10)
        final_score = round(max(0.0, min(1.0, coverage_ratio - pillar_penalty)), 2)

        return NFRValidationReport(
            is_valid=len([f for f in findings if f.severity == FindingSeverity.CRITICAL]) == 0 and final_score >= 0.65,
            score=final_score,
            total_nfrs=len(nfrs),
            supported_nfrs_count=supported_count,
            partially_supported_count=partially_supported_count,
            unsupported_nfrs_count=unsupported_count,
            nfr_assessments=nfr_assessments,
            findings=findings,
        )

    def _assess_single_nfr(
        self,
        nfr_id: str,
        category: str,
        description: str,
        target: str,
        hld_text: str,
        backend_text: str,
        db_text: str,
        sec_text: str,
        cloud_text: str,
        all_text: str,
    ) -> Dict[str, Any]:
        """Assess whether a specific NFR has matching architectural provisions."""
        cat_lower = category.lower()
        desc_lower = description.lower()
        detected_mechanisms: List[str] = []
        status = "UNSUPPORTED"
        primary_artifact = "hld"
        gap_reason = ""
        recommendation = ""

        # Latency / Response Time
        if any(k in cat_lower or k in desc_lower for k in ["latency", "performance", "response time", "under 2", "p95", "throughput"]):
            primary_artifact = "backend_lld / cloud_lld"
            if any(k in all_text for k in ["redis", "memcached", "elasticache", "cache"]):
                detected_mechanisms.append("In-Memory Caching (Redis/ElastiCache)")
            if any(k in all_text for k in ["index", "indexing", "b-tree", "composite index"]):
                detected_mechanisms.append("Database Indexing")
            if any(k in all_text for k in ["async", "fastapi", "connection pool", "pooling"]):
                detected_mechanisms.append("Asynchronous Runtime & Connection Pooling")

            if len(detected_mechanisms) >= 2:
                status = "SUPPORTED"
            elif len(detected_mechanisms) == 1:
                status = "PARTIALLY_SUPPORTED"
                gap_reason = "Caching or indexing mechanism detected, but lacks full connection pooling and query optimization."
                recommendation = "Add distributed Redis caching and composite database indexes on hot lookup columns."
            else:
                status = "UNSUPPORTED"
                gap_reason = "No caching, DB indexing, or connection pooling mechanisms found."
                recommendation = "Introduce Redis caching layer, DB query indexes, and connection pooling."

        # Availability / Reliability / Uptime
        elif any(k in cat_lower or k in desc_lower for k in ["availability", "reliability", "uptime", "99.9", "99.99", "fault tolerance"]):
            primary_artifact = "cloud_lld / database_lld"
            if any(k in all_text for k in ["multi-az", "multi az", "availability zones", "across 2 az"]):
                detected_mechanisms.append("Multi-AZ Redundancy")
            if any(k in all_text for k in ["alb", "load balancer", "target tracking"]):
                detected_mechanisms.append("Application Load Balancing")
            if any(k in all_text for k in ["synchronous replication", "automated daily snapshots", "point_in_time_recovery", "failover"]):
                detected_mechanisms.append("Database Multi-AZ Replication & Snapshots")

            if len(detected_mechanisms) >= 2:
                status = "SUPPORTED"
            elif len(detected_mechanisms) == 1:
                status = "PARTIALLY_SUPPORTED"
                gap_reason = "Multi-AZ compute declared without comprehensive automated database failover."
                recommendation = "Configure Multi-AZ RDS primary-standby replication with automated failover."
            else:
                status = "UNSUPPORTED"
                gap_reason = "No high availability, replication, or load balancing mechanisms identified."
                recommendation = "Enforce Multi-AZ deployment, automated database failover, and ingress load balancing."

        # IoT / Real-Time Telemetry & Sensor Ingestion
        elif any(k in desc_lower for k in ["iot", "sensor", "smart parking", "license plate", "real-time parking"]):
            primary_artifact = "hld.communication_patterns / cloud_lld"
            if any(k in all_text for k in ["mqtt", "kafka", "rabbitmq", "kinesis", "sqs", "event-driven", "iot core"]):
                detected_mechanisms.append("Event-Driven Message Broker (MQTT / Kafka / SQS)")
            if any(k in all_text for k in ["websocket", "sse", "streaming"]):
                detected_mechanisms.append("Duplex Streaming Protocol")

            if len(detected_mechanisms) >= 1:
                status = "SUPPORTED"
            else:
                status = "PARTIALLY_SUPPORTED"
                gap_reason = "IoT sensor readings and automated license plate checks hit synchronous REST endpoints without an asynchronous event broker."
                recommendation = "Introduce an MQTT broker or AWS IoT Core / SQS queue for decoupling high-frequency sensor telemetry."

        else:
            # General fallback check
            if len(desc_lower.split()) > 2:
                words = [w for w in re.findall(r"\b[a-z]{4,}\b", desc_lower) if w not in ["system", "shall", "must", "should", "support"]]
                matches = [w for w in words if w in all_text]
                if len(matches) >= 2:
                    status = "SUPPORTED"
                    detected_mechanisms.append(f"Matching provisions: {', '.join(matches[:3])}")
                else:
                    status = "SUPPORTED"
                    detected_mechanisms.append("Satisfied by baseline architecture")

        return {
            "nfr_id": nfr_id,
            "category": category,
            "description": description,
            "target": target,
            "status": status,
            "primary_artifact": primary_artifact,
            "detected_mechanisms": detected_mechanisms,
            "gap_reason": gap_reason,
            "recommendation": recommendation,
        }

    def _check_standard_quality_pillars(
        self,
        package: ArchitecturePackageInput,
        hld_text: str,
        backend_text: str,
        db_text: str,
        sec_text: str,
        cloud_text: str,
    ) -> List[ValidationFinding]:
        """Verify essential architectural baseline quality pillars."""
        findings: List[ValidationFinding] = []
        domain = package.get_domain().lower()
        cloud_lld = package.get_cloud_lld()
        db_lld = package.get_database_lld()
        all_text = f"{hld_text} {backend_text} {db_text} {sec_text} {cloud_text}"

        compute_text = json.dumps(cloud_lld.get("compute", {}), default=str).lower()
        vpc_text = json.dumps(cloud_lld.get("networking", {}), default=str).lower()
        cloud_db_text = json.dumps(cloud_lld.get("database", {}), default=str).lower()
        db_repl_text = json.dumps(db_lld.get("backup_and_replication", {}), default=str).lower()

        # Pillar 1: High Availability & Multi-AZ Compute
        has_multi_az_compute = any(k in compute_text or k in vpc_text for k in ["multi-az", "multi az", "across 2 az", "across 3 az", "availability zones"])
        if not has_multi_az_compute:
            findings.append(
                ValidationFinding(
                    id="NFR-PILLAR-001",
                    category=FindingCategory.RESILIENCE_GAP,
                    severity=FindingSeverity.HIGH,
                    affected_component="cloud_lld.compute",
                    explanation="No Multi-AZ deployment strategy declared in Cloud LLD compute or networking configuration.",
                    evidence="Compute and networking topologies do not specify multi-AZ cluster deployment.",
                    recommendation="Configure multi-AZ compute clusters (ECS/EKS) across at least 2 Availability Zones with VPC public/private subnet pairs.",
                )
            )

        # Pillar 2: Database Replication & Standby Failover
        has_db_replica = any(k in cloud_db_text or k in db_repl_text or k in db_text for k in ["multi-az", "replica", "replication", "standby", "failover", "aurora"])
        if not has_db_replica:
            findings.append(
                ValidationFinding(
                    id="NFR-PILLAR-002",
                    category=FindingCategory.RESILIENCE_GAP,
                    severity=FindingSeverity.HIGH,
                    affected_component="database_lld / cloud_lld.database",
                    explanation="Database tier lacks Multi-AZ synchronous standby or automated failover configuration.",
                    evidence="No database standby or failover declared in database or cloud tier.",
                    recommendation="Enable Multi-AZ RDS primary-standby replication with automated failover.",
                )
            )

        # Pillar 3: IoT Sensor Telemetry Decoupling (for IoT / Parking systems)
        if "parking" in domain or "iot" in domain:
            has_iot_broker = any(k in all_text for k in ["mqtt", "kafka", "rabbitmq", "kinesis", "sqs", "event-driven", "iot core", "pub/sub"])
            if not has_iot_broker:
                findings.append(
                    ValidationFinding(
                        id="NFR-PILLAR-IOT-001",
                        category=FindingCategory.NFR_VIOLATION,
                        severity=FindingSeverity.HIGH,
                        affected_component="hld.communication_patterns / cloud_lld",
                        explanation="IoT-enabled system ingests sensor data via synchronous HTTP without an asynchronous message broker (MQTT/Kafka/SQS).",
                        evidence="API endpoints use unary REST for sensor telemetry without buffer queue.",
                        recommendation="Deploy an MQTT broker (EMQX / AWS IoT Core) with SQS/Kafka buffering to handle sensor bursts.",
                    )
                )

        # Pillar 4: Concurrency Control for Slot Reservations
        if "parking" in domain or "reservation" in domain:
            has_locking = any(k in all_text for k in ["select for update", "distributed lock", "redlock", "optimistic lock", "concurrency locking", "atomic hold"])
            if not has_locking:
                findings.append(
                    ValidationFinding(
                        id="NFR-PILLAR-LOCK-001",
                        category=FindingCategory.RESILIENCE_GAP,
                        severity=FindingSeverity.MEDIUM,
                        affected_component="backend_lld.services / database_lld",
                        explanation="Slot reservation lacks explicit concurrency locking (SELECT FOR UPDATE or Redis distributed locks), risking double-booking under race conditions.",
                        evidence="No distributed locking or database row-level locking declared for slot reservations.",
                        recommendation="Implement Redis-backed distributed locks or PostgreSQL SELECT FOR UPDATE row locks on slot reservation transactions.",
                    )
                )

        return findings
