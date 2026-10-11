"""Adversarial Red-Team Architecture Reviewer.

Performs rigorous adversarial critique, identifying Single Points of Failure (SPOFs),
scalability bottlenecks, cascading failure vectors, concurrency race conditions,
and security blind spots across the architecture package.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from Validator_Engine.models.finding_models import (
    FindingCategory,
    FindingSeverity,
    ValidationFinding,
)
from Validator_Engine.models.input_models import ArchitecturePackageInput
from Validator_Engine.models.report_models import RedTeamReviewReport

logger = logging.getLogger(__name__)


class RedTeamReviewer:
    """Deterministic & Adversarial Architecture Stress Tester."""

    def __init__(self) -> None:
        pass

    def review(
        self,
        package: ArchitecturePackageInput,
        structural_report: Optional[Any] = None,
        consistency_report: Optional[Any] = None,
    ) -> RedTeamReviewReport:
        """Execute comprehensive adversarial red-team stress testing on the architecture package."""
        findings: List[ValidationFinding] = []
        spofs: List[Dict[str, Any]] = []
        bottlenecks: List[Dict[str, Any]] = []
        unresolved_risks: List[Dict[str, Any]] = []
        untested_assumptions: List[Dict[str, Any]] = []

        hld = package.get_hld()
        backend_lld = package.get_backend_lld()
        db_lld = package.get_database_lld()
        sec_lld = package.get_security_lld()
        cloud_lld = package.get_cloud_lld()
        domain = package.get_domain().lower()

        all_text = json.dumps(
            {
                "hld": hld,
                "backend": backend_lld,
                "db": db_lld,
                "security": sec_lld,
                "cloud": cloud_lld,
            },
            default=str,
        ).lower()

        # 1. Single Point of Failure (SPOF) Analysis
        spofs = self._detect_spofs(hld=hld, backend_lld=backend_lld, db_lld=db_lld, cloud_lld=cloud_lld, all_text=all_text)
        for spof in spofs:
            findings.append(
                ValidationFinding(
                    id=spof["id"],
                    category=FindingCategory.SPOF,
                    severity=FindingSeverity(spof.get("severity", "CRITICAL")),
                    affected_component=spof["component"],
                    explanation=spof["description"],
                    evidence=spof.get("evidence", ""),
                    recommendation=spof["remediation"],
                )
            )

        # 2. Scalability Bottleneck Analysis
        bottlenecks = self._detect_scalability_bottlenecks(
            domain=domain,
            backend_lld=backend_lld,
            db_lld=db_lld,
            cloud_lld=cloud_lld,
            all_text=all_text,
        )
        for bn in bottlenecks:
            findings.append(
                ValidationFinding(
                    id=bn["id"],
                    category=FindingCategory.SCALABILITY_BOTTLENECK,
                    severity=FindingSeverity(bn.get("severity", "HIGH")),
                    affected_component=bn["component"],
                    explanation=bn["description"],
                    evidence=bn.get("evidence", ""),
                    recommendation=bn["remediation"],
                )
            )

        # 3. Cascading Failure & Coupling Analysis
        cascading = self._detect_cascading_failure_risks(hld=hld, backend_lld=backend_lld, all_text=all_text)
        for casc in cascading:
            unresolved_risks.append(casc)
            findings.append(
                ValidationFinding(
                    id=casc["id"],
                    category=FindingCategory.RESILIENCE_GAP,
                    severity=FindingSeverity.HIGH,
                    affected_component=casc["component"],
                    explanation=casc["description"],
                    evidence=casc.get("evidence", ""),
                    recommendation=casc["remediation"],
                )
            )

        # 4. Security & Isolation Blind Spots
        sec_risks = self._detect_security_blindspots(sec_lld=sec_lld, backend_lld=backend_lld, cloud_lld=cloud_lld, all_text=all_text)
        for sec_risk in sec_risks:
            unresolved_risks.append(sec_risk)
            findings.append(
                ValidationFinding(
                    id=sec_risk["id"],
                    category=FindingCategory.SECURITY_DEFECT,
                    severity=FindingSeverity(sec_risk.get("severity", "HIGH")),
                    affected_component=sec_risk["component"],
                    explanation=sec_risk["description"],
                    evidence=sec_risk.get("evidence", ""),
                    recommendation=sec_risk["remediation"],
                )
            )

        # 5. Concurrency Race Conditions (e.g. Double-booking in reservation systems)
        if "parking" in domain or "reservation" in domain:
            concurrency_risks = self._detect_reservation_concurrency_risks(backend_lld=backend_lld, db_lld=db_lld, all_text=all_text)
            for cr in concurrency_risks:
                unresolved_risks.append(cr)
                findings.append(
                    ValidationFinding(
                        id=cr["id"],
                        category=FindingCategory.RESILIENCE_GAP,
                        severity=FindingSeverity.HIGH,
                        affected_component=cr["component"],
                        explanation=cr["description"],
                        evidence=cr.get("evidence", ""),
                        recommendation=cr["remediation"],
                    )
                )

        # 6. Untested Assumptions & Hedged Statements
        untested_assumptions = self._detect_untested_assumptions(all_text=all_text)
        for assum in untested_assumptions:
            findings.append(
                ValidationFinding(
                    id=assum["id"],
                    category=FindingCategory.UNTESTED_ASSUMPTION,
                    severity=FindingSeverity.MEDIUM,
                    affected_component="system_assumptions",
                    explanation=assum["description"],
                    evidence=assum.get("evidence", ""),
                    recommendation=assum["remediation"],
                )
            )

        # Calculate Verdict & Score
        critical_count = len([f for f in findings if f.severity == FindingSeverity.CRITICAL])
        high_count = len([f for f in findings if f.severity == FindingSeverity.HIGH])

        if critical_count > 0:
            verdict = "REJECTED"
            score = max(0.20, round(0.60 - (0.15 * critical_count) - (0.05 * high_count), 2))
        elif high_count > 2:
            verdict = "NEEDS_REMEDIATION"
            score = max(0.40, round(0.80 - (0.08 * high_count), 2))
        elif high_count > 0:
            verdict = "APPROVED_WITH_CONDITIONS"
            score = max(0.65, round(0.90 - (0.05 * high_count), 2))
        else:
            verdict = "APPROVED"
            score = 1.0

        return RedTeamReviewReport(
            verdict=verdict,
            is_valid=verdict in ("APPROVED", "APPROVED_WITH_CONDITIONS"),
            score=score,
            single_points_of_failure=spofs,
            scalability_bottlenecks=bottlenecks,
            unresolved_risks=unresolved_risks,
            untested_assumptions=untested_assumptions,
            findings=findings,
        )

    def _detect_spofs(
        self,
        hld: Dict[str, Any],
        backend_lld: Dict[str, Any],
        db_lld: Dict[str, Any],
        cloud_lld: Dict[str, Any],
        all_text: str,
    ) -> List[Dict[str, Any]]:
        """Identify Single Points of Failure across tiers."""
        spofs: List[Dict[str, Any]] = []

        # Database SPOF: inspect database tier configuration
        db_repl = json.dumps(db_lld.get("backup_and_replication", {}), default=str).lower()
        cloud_db = json.dumps(cloud_lld.get("database", {}), default=str).lower()
        db_tier_text = f"{db_repl} {cloud_db}"

        has_db_standby = any(k in db_tier_text for k in ["multi-az", "synchronous replication", "standby", "patroni", "aurora", "replication group", "read replicas"])
        if not has_db_standby:
            spofs.append({
                "id": "SPOF-001",
                "title": "Single Database Instance without Automated Standby Failover",
                "component": "database_lld / cloud_lld.database",
                "description": "The primary database runs as a standalone single instance without Multi-AZ synchronous standby or automated failover.",
                "severity": "CRITICAL",
                "evidence": "No primary-standby replication or Multi-AZ RDS failover declared in database or cloud tier.",
                "remediation": "Deploy database in Multi-AZ configuration with automated failover and read-replica offloading.",
            })

        # Ingress / Gateway SPOF
        networking = json.dumps(cloud_lld.get("networking", {}), default=str).lower()
        has_gateway_ha = any(k in networking for k in ["alb", "nlb", "load balancer", "ingress-nginx", "cloudflare", "multi-az"])
        if not has_gateway_ha:
            spofs.append({
                "id": "SPOF-002",
                "title": "Single Ingress Gateway / Load Balancer",
                "component": "cloud_lld.networking",
                "description": "API traffic passes through a single gateway instance without high-availability load balancing.",
                "severity": "HIGH",
                "evidence": "No Application Load Balancer declared in cloud networking configuration.",
                "remediation": "Deploy redundant Application Load Balancers (ALB) across multiple Availability Zones.",
            })

        return spofs

    def _detect_scalability_bottlenecks(
        self,
        domain: str,
        backend_lld: Dict[str, Any],
        db_lld: Dict[str, Any],
        cloud_lld: Dict[str, Any],
        all_text: str,
    ) -> List[Dict[str, Any]]:
        """Identify bottlenecks in compute, persistence, and state management."""
        bottlenecks: List[Dict[str, Any]] = []

        # Synchronous IoT Sensor Ingestion Bottleneck
        if "parking" in domain or "iot" in domain:
            has_queue = any(k in all_text for k in ["mqtt", "kafka", "rabbitmq", "sqs", "kinesis", "broker", "buffer"])
            if not has_queue:
                bottlenecks.append({
                    "id": "BOTTLENECK-IOT-001",
                    "title": "Synchronous HTTP Ingestion of High-Frequency IoT Sensor Data",
                    "component": "backend_lld.api_endpoints",
                    "description": "High-frequency parking lot sensor updates and ALPR camera events hit transactional synchronous HTTP endpoints directly, risking thread pool exhaustion and DB lock contention during rush hours.",
                    "severity": "HIGH",
                    "evidence": "API routes use unary HTTP endpoints without message broker buffering.",
                    "remediation": "Decouple sensor ingestion using MQTT or Kafka buffer queue with batch database persistence.",
                })

        # Database Indexing Bottleneck
        db_tables = db_lld.get("tables", [])
        has_indexes = False
        if isinstance(db_tables, list) and len(db_tables) > 0:
            for t in db_tables:
                if isinstance(t, dict) and (t.get("indexes") or t.get("indices") or "index" in json.dumps(t).lower()):
                    has_indexes = True
                    break

        if not has_indexes and len(db_tables) > 0:
            bottlenecks.append({
                "id": "BOTTLENECK-DB-001",
                "title": "Missing Database Indexes on Foreign Keys and Query Lookup Columns",
                "component": "database_lld.tables",
                "description": "Database tables have no explicit B-Tree/Composite index definitions on lookup fields (e.g. slot availability, license plate numbers).",
                "severity": "MEDIUM",
                "evidence": "Table schemas lack 'indexes' field or index definitions.",
                "remediation": "Add composite indexes on (parking_lot_id, status) and license_plate lookup columns.",
            })

        return bottlenecks

    def _detect_cascading_failure_risks(
        self,
        hld: Dict[str, Any],
        backend_lld: Dict[str, Any],
        all_text: str,
    ) -> List[Dict[str, Any]]:
        """Identify tightly coupled synchronous RPC chains prone to cascading failures."""
        risks: List[Dict[str, Any]] = []

        services = hld.get("major_services", []) or backend_lld.get("services", [])
        has_circuit_breaker = any(k in all_text for k in ["circuit breaker", "resilience4j", "tenacity", "hystrix", "timeout", "deadline"])

        if len(services) >= 3 and not has_circuit_breaker:
            risks.append({
                "id": "CASCADE-001",
                "title": "Tightly Coupled Synchronous Inter-Service Chains without Circuit Breakers",
                "component": "hld.communication_patterns / backend_lld.services",
                "description": "Multiple microservices communicate synchronously via HTTP/REST without circuit breakers, risking thread pool exhaustion on downstream degradation.",
                "severity": "HIGH",
                "evidence": f"{len(services)} services communicating without circuit breaker patterns.",
                "remediation": "Introduce Circuit Breakers with fast timeouts, fallbacks, and event-driven async messaging.",
            })

        return risks

    def _detect_reservation_concurrency_risks(
        self,
        backend_lld: Dict[str, Any],
        db_lld: Dict[str, Any],
        all_text: str,
    ) -> List[Dict[str, Any]]:
        """Identify concurrency race conditions in inventory / slot reservation."""
        risks: List[Dict[str, Any]] = []

        has_locking = any(k in all_text for k in ["select for update", "distributed lock", "redlock", "optimistic lock", "concurrency locking", "atomic hold"])
        if not has_locking:
            risks.append({
                "id": "RACE-RESERVATION-001",
                "title": "Unprotected Slot Reservation Concurrency (Double-Booking Risk)",
                "component": "backend_lld.services / database_lld.tables",
                "description": "Parking slot reservations execute standard non-locking read-then-write transactions, enabling two simultaneous drivers to claim the same parking slot (classic TOCTOU race condition).",
                "severity": "HIGH",
                "evidence": "No SELECT FOR UPDATE, Redis distributed lock, or atomic hold mechanism found in backend or DB LLD.",
                "remediation": "Enforce atomic reservation holds using Redis distributed locking (Redlock) or PostgreSQL SELECT FOR UPDATE row locking with a 10-minute hold expiration timer.",
            })

        return risks

    def _detect_security_blindspots(
        self,
        sec_lld: Dict[str, Any],
        backend_lld: Dict[str, Any],
        cloud_lld: Dict[str, Any],
        all_text: str,
    ) -> List[Dict[str, Any]]:
        """Identify missing security defenses (rate limiting, secrets management, CORS)."""
        risks: List[Dict[str, Any]] = []

        # Rate Limiting
        has_rate_limiting = any(k in all_text for k in ["rate limit", "rate-limit", "throttling", "token bucket", "waf rate"])
        if not has_rate_limiting:
            risks.append({
                "id": "SEC-RISK-001",
                "title": "Missing Ingress Rate Limiting / API Throttling",
                "component": "security_lld / cloud_lld.networking",
                "description": "Public API endpoints lack rate limiting or DDoS protection, exposing the system to resource exhaustion.",
                "severity": "HIGH",
                "evidence": "No rate limiting or throttling policies specified in security_lld or API gateway.",
                "remediation": "Configure Redis-backed sliding window rate limiting at API Gateway (e.g., 100 req/min/IP).",
            })

        return risks

    def _detect_untested_assumptions(self, all_text: str) -> List[Dict[str, Any]]:
        """Identify hedged language, unverified sizing, and hand-waving assumptions."""
        assumptions: List[Dict[str, Any]] = []
        hedged_patterns = [
            ("initial estimate", "Workload capacity sizing is marked as an unverified initial estimate."),
            ("requires load testing", "Performance throughput is assumed without load test validation."),
            ("to be determined", "Key architectural parameter marked as TBD."),
            ("potential consideration", "Crucial resilience feature deferred as a potential consideration."),
        ]

        for phrase, reason in hedged_patterns:
            if phrase in all_text:
                assumptions.append({
                    "id": f"ASSUM-{len(assumptions)+1:03d}",
                    "title": f"Hedged Assumption: '{phrase}'",
                    "component": "architecture_specification",
                    "description": reason,
                    "severity": "MEDIUM",
                    "evidence": f"Found text match for '{phrase}' in package.",
                    "remediation": "Conduct explicit workload profiling and formalize concrete capacity metrics.",
                })

        return assumptions
