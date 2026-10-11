"""Real-World Architecture Evidence & Benchmark Assessor.

Compares generated architectures against proven Category 10 real-world system patterns
(Airbnb, Uber, Stripe, WhatsApp, Shopify, etc.), performing structured comparative
evidence assessment, identifying trade-offs, and evaluating production anti-patterns.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from Validator_Engine.knowledge.knowledge_retriever import KnowledgeChunk, KnowledgeRetriever
from Validator_Engine.models.finding_models import (
    FindingCategory,
    FindingSeverity,
    ValidationFinding,
)
from Validator_Engine.models.input_models import ArchitecturePackageInput
from Validator_Engine.models.report_models import RealWorldArchetypeMatch, RealWorldEvidenceReport

logger = logging.getLogger(__name__)


def _split_words(text: str) -> str:
    """Split PascalCase/camelCase identifiers into space-separated lowercase words."""
    words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+", text)
    return " ".join(w.lower() for w in words if len(w) > 2)


class RealWorldAssessor:
    """Evaluates architectural designs against real-world production benchmarks."""

    def __init__(self, retriever: Optional[KnowledgeRetriever] = None) -> None:
        self.retriever = retriever or KnowledgeRetriever()

    def assess(self, package: ArchitecturePackageInput) -> RealWorldEvidenceReport:
        """Benchmark architecture against real-world systems in Category 10."""
        domain = package.get_domain()
        system_name = package.get_system_name()
        prompt = package.prompt or package.data.get("prompt", "")
        hld = package.get_hld()
        backend_lld = package.get_backend_lld()
        db_lld = package.get_database_lld()
        cloud_lld = package.get_cloud_lld()

        style = hld.get("architecture_style", "Microservices")
        services = hld.get("major_services", [])
        svc_names = [s.get("name", "") for s in services if isinstance(s, dict)] if isinstance(services, list) else []
        db_type = db_lld.get("database_type", "PostgreSQL / Relational")

        # Build expanded query with prompt, domain, split service names, and tech stack
        query = f"{prompt} {system_name} {domain} {style} {_split_words(' '.join(svc_names))} {db_type}"

        # 1. Retrieve top matching real-world systems
        matched = self.retriever.retrieve_real_world_systems(domain=domain, query=query, top_k=3)

        matched_systems: List[Dict[str, Any]] = []
        matched_archetypes: List[RealWorldArchetypeMatch] = []
        trade_offs: List[Dict[str, Any]] = []
        failure_modes: List[Dict[str, Any]] = []
        key_insights: List[str] = []
        findings: List[ValidationFinding] = []

        all_text = json.dumps(
            {
                "hld": hld,
                "backend": backend_lld,
                "db": db_lld,
                "cloud": cloud_lld,
            },
            default=str,
        ).lower()

        top_similarity = 0.0
        primary_archetype = f"{style} - {domain}"

        if matched:
            top_chunk, top_similarity = matched[0]
            primary_archetype = f"{top_chunk.title.replace('10.', '').strip()} Archetype"

            for chunk, score in matched:
                # Build Contextual Archetype Comparison
                comparison = self._build_contextual_comparison(chunk=chunk, domain=domain, package=package, all_text=all_text)
                matched_archetypes.append(comparison)

                matched_systems.append({
                    "system_name": chunk.title,
                    "chunk_id": chunk.chunk_id,
                    "similarity_score": score,
                    "definition": chunk.definition,
                    "decision_signals": chunk.decision_signals,
                    "real_world_examples": chunk.real_world_examples,
                    "advantages": chunk.advantages,
                    "disadvantages": chunk.disadvantages,
                })

                # Extract Trade-offs
                if chunk.advantages or chunk.disadvantages:
                    trade_offs.append({
                        "reference_system": chunk.title,
                        "pros": chunk.advantages[:3],
                        "cons_and_complexities": chunk.disadvantages[:3],
                    })

                # Check Anti-Patterns from benchmark against generated architecture
                for anti_pattern in chunk.anti_patterns:
                    is_detected, evidence = self._check_anti_pattern_match(anti_pattern, all_text, domain)
                    if is_detected:
                        findings.append(
                            ValidationFinding(
                                id=f"RW-ANTI-{len(findings)+1:03d}",
                                category=FindingCategory.ANTI_PATTERN,
                                severity=FindingSeverity.HIGH,
                                affected_component=f"benchmark.{chunk.title}",
                                explanation=f"Detected anti-pattern known from {chunk.title}: {anti_pattern}",
                                evidence=evidence,
                                recommendation=f"Align with standard {chunk.title} resilience guidelines: {comparison.recommended_guardrails[0] if comparison.recommended_guardrails else 'Add defensive isolation.'}",
                            )
                        )
                        failure_modes.append({
                            "reference_system": chunk.title,
                            "anti_pattern": anti_pattern,
                            "detected": True,
                            "evidence": evidence,
                        })

        # Key Insights synthesis
        if matched_archetypes:
            key_insights.append(f"Architecture exhibits primary alignment with {matched_archetypes[0].reference_system}.")
            if len(matched_archetypes) > 1:
                key_insights.append(f"Secondary architectural concerns benchmarked against {matched_archetypes[1].reference_system}.")

        # Compute benchmark score
        anti_penalty = min(0.40, len([f for f in findings if f.category == FindingCategory.ANTI_PATTERN]) * 0.15)
        benchmark_score = round(max(0.40, min(1.0, (0.65 + 0.35 * top_similarity) - anti_penalty)), 2)

        return RealWorldEvidenceReport(
            is_valid=len([f for f in findings if f.severity == FindingSeverity.CRITICAL]) == 0 and benchmark_score >= 0.50,
            has_evidence=len(matched_systems) > 0,
            score=benchmark_score,
            evidence_quality_score=benchmark_score,
            primary_archetype=primary_archetype,
            matched_systems=matched_systems,
            matched_archetypes=matched_archetypes,
            trade_off_analysis=trade_offs,
            failure_mode_risks=failure_modes,
            key_insights=key_insights,
            findings=findings,
        )

    def _build_contextual_comparison(
        self,
        chunk: KnowledgeChunk,
        domain: str,
        package: ArchitecturePackageInput,
        all_text: str,
    ) -> RealWorldArchetypeMatch:
        """Synthesize contextual similarities, differences, and guardrails."""
        chunk_title = chunk.title.replace("10.", "").strip()

        # Airbnb (Booking / Reservation Hold Archetype)
        if "airbnb" in chunk.title.lower() or "10.5" in chunk.chunk_id:
            return RealWorldArchetypeMatch(
                reference_system=chunk_title,
                domain="Marketplace Reservation & Inventory Contention",
                relevance_reason="Both systems handle concurrent contention over finite inventory units (parking slots vs room listings) requiring short-lived reservation holds and atomic state transitions.",
                structural_comparison="Similarities: Relational database (PostgreSQL) for transactional booking integrity and Redis for rapid availability queries. Differences: Smart Parking requires automated IoT hardware gate/sensor telemetry, whereas Airbnb operates on user booking workflows.",
                supporting_patterns=[
                    "Stateful reservation lifecycle (RESERVED -> OCCUPIED -> COMPLETED)",
                    "Redis cache layer for real-time slot availability queries",
                ],
                cautionary_failure_modes=[
                    "Confirming reservations without atomic concurrency locking (risk of double-booking)",
                    "Running heavy slot availability search directly on transactional booking tables",
                ],
                recommended_guardrails=[
                    "Implement atomic reservation holds with Redis distributed lock (Redlock) or SELECT FOR UPDATE",
                    "Configure 10-minute hold expiration worker to release unpaid reserved slots",
                ],
            )

        # Uber (Real-Time Location & Dispatch Archetype)
        elif "uber" in chunk.title.lower() or "10.23" in chunk.chunk_id:
            return RealWorldArchetypeMatch(
                reference_system=chunk_title,
                domain="Real-Time Telemetry & Dynamic Dispatch",
                relevance_reason="Both systems process dynamic location/state updates from moving vehicles and IoT hardware, requiring low-latency availability feeds and geo-indexed queries.",
                structural_comparison="Similarities: High-frequency state ingestion, driver/vehicle authorization, and dynamic availability pricing. Differences: Smart Parking manages fixed geographical slot boundaries rather than continuous spatial vehicle routing.",
                supporting_patterns=[
                    "Fast in-memory cache for live vehicle/slot state",
                    "Decoupled ingress gateway with rate limiting",
                ],
                cautionary_failure_modes=[
                    "Synchronous REST ingestion of high-frequency sensor updates causing thread pool exhaustion",
                    "Lack of spatial or composite indexes on location/lot lookup tables",
                ],
                recommended_guardrails=[
                    "Buffer high-frequency IoT sensor telemetry through MQTT / SQS queue",
                    "Add composite index on (parking_lot_id, status) for sub-50ms availability lookups",
                ],
            )

        # Stripe (Idempotent Payments & Financial Ledger Archetype)
        elif "stripe" in chunk.title.lower() or "10.6" in chunk.chunk_id or "paypal" in chunk.title.lower():
            return RealWorldArchetypeMatch(
                reference_system=chunk_title,
                domain="Financial Transactions & Payment Processing",
                relevance_reason="Both systems process monetary fee captures for reservations/parking durations, requiring strict transaction idempotency and audit logs.",
                structural_comparison="Similarities: Payment gateway integration, transaction records, and webhook confirmation callbacks. Differences: Parking fee calculations are time-elapsed metered charges based on entry/exit timestamps.",
                supporting_patterns=[
                    "Strict ACID PostgreSQL transactions for fee records",
                    "OAuth2 / JWT authorization with role-based access control",
                ],
                cautionary_failure_modes=[
                    "Missing idempotency keys on payment capture endpoints (risk of duplicate charges on network retries)",
                    "Synchronous blocking on third-party payment gateways during vehicle gate exit",
                ],
                recommended_guardrails=[
                    "Enforce Idempotency-Key headers on all digital payment routes",
                    "Perform asynchronous payment confirmation via webhooks with fallback reconciliation",
                ],
            )

        # Generic Archetype fallback
        return RealWorldArchetypeMatch(
            reference_system=chunk_title,
            domain=chunk.category.replace("_", " ").title(),
            relevance_reason=f"Reference architecture for {chunk.definition[:100]}...",
            structural_comparison=f"Shares distributed service partitioning and containerized cloud deployment principles.",
            supporting_patterns=chunk.advantages[:2],
            cautionary_failure_modes=chunk.anti_patterns[:2],
            recommended_guardrails=chunk.decision_signals[:2],
        )

    def _check_anti_pattern_match(self, anti_pattern: str, all_text: str, domain: str) -> tuple[bool, str]:
        """Heuristic check whether generated text triggers a known production anti-pattern."""
        ap_lower = anti_pattern.lower()

        # Check: Unprotected booking hold / double-booking
        if "atomic hold" in ap_lower or "confirming bookings" in ap_lower or "concurrency" in ap_lower:
            if "parking" in domain and not any(k in all_text for k in ["select for update", "distributed lock", "redlock", "optimistic lock"]):
                return True, "Parking slot reservation state machine lacks atomic hold/concurrency locking semantics."

        # Check: Storing raw binaries in primary database
        if "binary" in ap_lower or "blob" in ap_lower or "large media" in ap_lower:
            if any(k in all_text for k in ["store image in postgres", "store video in db", "blob column"]):
                return True, "Database tables store raw media binaries instead of S3/Object Storage."

        # Check: Unbounded retries
        if "unbounded retry" in ap_lower or "infinite retry" in ap_lower:
            if "retry forever" in all_text or "unlimited retry" in all_text:
                return True, "Found unconstrained retry loop without max attempt limits."

        return False, ""
