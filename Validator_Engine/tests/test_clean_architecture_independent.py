"""Fresh, Independent Clean Architecture Test.

Verifies that a newly created, valid architecture package passes validation
on its initial attempt without triggering unnecessary correction iterations
and without reusing any previously corrected generation run.
"""

import uuid
import pytest

from Validator_Engine.engine import ValidatorEngine
from ai_engine.app.services.generation_service import generation_service


@pytest.fixture
def independent_clean_package() -> dict:
    """Creates a completely fresh, uncorrected architecture package with a brand-new ID."""
    fresh_id = f"gen_independent_clean_{uuid.uuid4().hex[:12]}"

    return {
        "generation_id": fresh_id,
        "prompt": "Design a High-Throughput Real-Time Logistics and Fleet Telemetry Platform",
        "status": "COMPLETED",
        "arsrs": {
            "session_id": str(uuid.uuid4()),
            "system_name": "Logistics Fleet Telemetry Platform",
            "domain": "IoT & Smart Transportation / Parking",
            "functional_requirements": [
                {
                    "id": "FR-001",
                    "title": "Vehicle Telemetry Processing",
                    "description": "Ingest and process real-time vehicle GPS and diagnostics data.",
                },
                {
                    "id": "FR-002",
                    "title": "Fleet Dispatch Scheduling",
                    "description": "Dispatch and reserve fleet vehicles with atomic resource allocation.",
                },
            ],
            "non_functional_requirements": [
                {
                    "id": "NFR-001",
                    "category": "reliability",
                    "description": "High Availability 99.99% Multi-AZ SLA with automated failover under 30s.",
                },
                {
                    "id": "NFR-002",
                    "category": "security",
                    "description": "Strict mutual exclusion and rate limiting on dispatch endpoints.",
                },
            ],
            "business_context": {
                "business_rules": [
                    "Enforce strict concurrency locking on fleet vehicle assignment to avoid double-dispatch.",
                    "Validate driver authorization before dispatch.",
                ],
                "constraints": ["High availability SLA 99.99%", "Multi-AZ database deployment"],
            },
        },
        "hld": {
            "system_name": "Logistics Fleet Telemetry Platform",
            "architecture_style": "Event-Driven Microservices",
            "executive_summary": "High-throughput fleet telematics with event-driven streaming.",
            "major_services": [
                {"name": "TelemetryIngestionService", "responsibility": "MQTT telemetry ingestion"},
                {"name": "FleetDispatchService", "responsibility": "Vehicle dispatch and reservation"},
            ],
            "communication_patterns": ["gRPC for inter-service RPC", "Kafka for telemetry streams"],
            "data_strategy": "PostgreSQL Multi-AZ with Redis distributed cache",
        },
        "llds": {
            "backend": {
                "services": [
                    {
                        "name": "FleetDispatchService",
                        "endpoints": ["/api/v1/fleets/dispatch", "/api/v1/fleets/hold"],
                        "concurrency_policy": "Redis Redlock distributed locking with 10-minute hold TTL",
                    }
                ],
                "reservation_concurrency_policy": {
                    "lock_type": "Redis Redlock Distributed Locking with 10-minute hold TTL",
                    "database_fallback": "SELECT id, status FROM fleet_vehicles WHERE id = :vehicle_id FOR UPDATE NOWAIT",
                    "hold_duration_seconds": 600,
                    "concurrency_guarantee": "Strict mutual exclusion preventing duplicate dispatch.",
                },
                "api_endpoints": [
                    {
                        "path": "/api/v1/fleets/{vehicle_id}/hold",
                        "method": "POST",
                        "concurrency_lock": "Redis Redlock (vehicle_hold:{vehicle_id})",
                    }
                ],
            },
            "database": {
                "engine": "PostgreSQL 16",
                "tables": [
                    {
                        "name": "fleet_vehicles",
                        "columns": [
                            {"name": "id", "type": "UUID", "primary_key": True},
                            {"name": "status", "type": "VARCHAR(20)"},
                            {"name": "hold_expires_at", "type": "TIMESTAMP WITH TIME ZONE"},
                        ],
                        "indexes": [
                            {"name": "idx_fleet_status", "columns": ["status"], "type": "B-Tree"}
                        ],
                    }
                ],
                "locking_and_concurrency": {
                    "row_level_locking": "SELECT FOR UPDATE row-level lock during dispatch transactions",
                    "isolation_level": "READ COMMITTED with pessimistic row locks",
                },
                "backup_and_replication": {
                    "mode": "Primary-Standby Multi-AZ with Synchronous Replication",
                    "automated_failover": True,
                },
                "caching_strategy": {
                    "tier": "Amazon ElastiCache Redis Cluster",
                    "cache_ttl_seconds": 300,
                },
            },
            "cloud": {
                "provider": "AWS",
                "database": {
                    "engine": "Amazon RDS PostgreSQL Multi-AZ Deployment",
                    "standby_instance": True,
                    "read_replicas": 2,
                },
                "caching": {
                    "engine": "Amazon ElastiCache for Redis",
                    "multi_az": True,
                },
                "networking": {
                    "load_balancer": "Application Load Balancer Multi-AZ",
                    "multi_az": True,
                },
                "iot_ingestion": {
                    "broker": "AWS IoT Core (MQTT over TLS)",
                    "buffer_queue": "Amazon SQS FIFO Queue",
                },
            },
            "security": {
                "authentication": "JWT via Amazon Cognito / OAuth 2.0",
                "transport_security": {"tls_version": "TLS 1.3 Strict"},
                "ingress_rate_limiting": {
                    "algorithm": "Token Bucket (Redis-backed)",
                    "limit_per_minute": 300,
                },
            },
            "frontend": {
                "framework": "Next.js 16 App Router",
                "state_management": "Zustand",
                "real_time_updates": "Server-Sent Events (SSE) and WebSockets",
            },
        },
    }


def test_independent_clean_package_passes_initial_attempt_without_correction(independent_clean_package: dict):
    """Verifies that a fresh, independent valid package passes on Attempt 1 with zero correction iterations."""
    pkg_id = independent_clean_package["generation_id"]

    # 1. Direct validation via Validator Engine
    validator = ValidatorEngine()
    val_res = validator.validate(independent_clean_package, attempt=1, max_retries=2)

    assert val_res is not None
    assert val_res.is_fully_validated is True, f"Expected clean package to be fully validated. Status: {val_res.status}"
    assert val_res.validation.summary.critical_findings_count == 0
    assert val_res.validation.summary.high_findings_count == 0
    assert val_res.validation.summary.verdict in ("APPROVED", "APPROVED_WITH_CONDITIONS")

    # 2. Closed-loop validation workflow via GenerationService
    service_result = generation_service.validate_and_correct_package(independent_clean_package, max_retries=2)

    assert service_result is not None
    assert service_result.get("is_fully_validated") is True
    assert service_result.get("attempt") == 1
    assert service_result.get("validation", {}).get("summary", {}).get("verdict") in ("APPROVED", "APPROVED_WITH_CONDITIONS")

    # 3. Ensure ZERO correction cycles were triggered
    history = service_result.get("correction_history", [])
    assert len(history) == 0, f"Expected 0 correction cycles for fresh clean package, but got {len(history)}"

    # 4. Confirm independent generation identity was preserved
    assert service_result.get("metadata", {}).get("package_id") == pkg_id
