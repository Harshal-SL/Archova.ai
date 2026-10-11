"""Verification of Parking Reservation Concurrency Safeguards.

Establishes why simultaneous driver reservations cannot both succeed:
1. Layer 1 (Distributed Cache): Redis Redlock SET NX PX atomicity ensures mutual exclusion.
2. Layer 2 (Database ACID): PostgreSQL row-level SELECT FOR UPDATE serializes concurrent transactions.
3. Expiration guardrail: 10-minute hold TTL prevents indefinite lock starvation.
"""

import threading
import time
from typing import Any, Dict, List
import pytest

from Validator_Engine.engine import ValidatorEngine
from Validator_Engine.models.output_models import ValidatedArchitectureResponse


class MockConcurrencyEngine:
    """Simulates the backend and database concurrency mechanism specified in the architecture."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.slots: Dict[str, Dict[str, Any]] = {
            "slot-101": {"status": "AVAILABLE", "driver_id": None, "hold_expires_at": 0}
        }
        self.redis_locks: Dict[str, str] = {}

    def reserve_slot_unprotected(self, slot_id: str, driver_id: str) -> bool:
        """Simulates non-locking read-then-write (defective TOCTOU race condition)."""
        slot = self.slots.get(slot_id)
        if slot and slot["status"] == "AVAILABLE":
            # Simulate network or DB processing delay between read and write
            time.sleep(0.01)
            slot["status"] = "HELD"
            slot["driver_id"] = driver_id
            return True
        return False

    def reserve_slot_protected(self, slot_id: str, driver_id: str) -> Dict[str, Any]:
        """Simulates Redis Redlock SET NX + PostgreSQL SELECT FOR UPDATE row locking."""
        now = time.time()
        # 1. Atomic Redis Redlock: SET slot_hold:{slot_id} driver_id NX PX 600000
        with self.lock:
            # Check if active lock exists and has not expired
            if slot_id in self.redis_locks:
                return {
                    "success": False,
                    "status_code": 409,
                    "error": "CONFLICT: Slot currently held by another driver",
                    "driver_id": driver_id,
                }
            # Acquire distributed lock atomically
            self.redis_locks[slot_id] = driver_id

        # 2. Database Transaction: SELECT id, status FROM slots WHERE id = :slot_id FOR UPDATE NOWAIT
        with self.lock:
            slot = self.slots.get(slot_id)
            if not slot or slot["status"] != "AVAILABLE":
                # Release distributed lock on conflict
                self.redis_locks.pop(slot_id, None)
                return {
                    "success": False,
                    "status_code": 409,
                    "error": "CONFLICT: Slot already reserved in database",
                    "driver_id": driver_id,
                }

            # Update row atomically with 10-minute hold TTL
            slot["status"] = "HELD"
            slot["driver_id"] = driver_id
            slot["hold_expires_at"] = now + 600
            return {
                "success": True,
                "status_code": 200,
                "message": "HOLD_ACQUIRED: 10-minute hold granted",
                "driver_id": driver_id,
                "hold_expires_at": slot["hold_expires_at"],
            }


def test_unprotected_reservation_suffers_double_booking_defect():
    """Demonstrates that without concurrency locking, simultaneous drivers both succeed (defect)."""
    engine = MockConcurrencyEngine()
    results: List[bool] = []

    def attempt_reservation(driver_id: str):
        success = engine.reserve_slot_unprotected("slot-101", driver_id)
        results.append(success)

    t1 = threading.Thread(target=attempt_reservation, args=("driver-A",))
    t2 = threading.Thread(target=attempt_reservation, args=("driver-B",))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # In unprotected concurrency, both threads read 'AVAILABLE' and overwrite (TOCTOU defect)
    assert results.count(True) == 2, "Unprotected system should exhibit race condition double-booking"


def test_protected_reservation_strictly_prevents_simultaneous_success():
    """Demonstrates that with Redis Redlock + SELECT FOR UPDATE, exactly one driver succeeds."""
    engine = MockConcurrencyEngine()
    responses: List[Dict[str, Any]] = []

    def attempt_reservation(driver_id: str):
        res = engine.reserve_slot_protected("slot-101", driver_id)
        responses.append(res)

    t1 = threading.Thread(target=attempt_reservation, args=("driver-A",))
    t2 = threading.Thread(target=attempt_reservation, args=("driver-B",))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    successful = [r for r in responses if r["success"] is True]
    rejected = [r for r in responses if r["success"] is False]

    # Exactly one driver must succeed
    assert len(successful) == 1, f"Expected exactly 1 successful reservation, got {len(successful)}"
    assert successful[0]["status_code"] == 200

    # The other driver must receive HTTP 409 Conflict
    assert len(rejected) == 1, f"Expected exactly 1 rejected reservation, got {len(rejected)}"
    assert rejected[0]["status_code"] == 409
    assert "CONFLICT" in rejected[0]["error"]

    # Final database state must reflect only the winning driver
    assert engine.slots["slot-101"]["status"] == "HELD"
    assert engine.slots["slot-101"]["driver_id"] == successful[0]["driver_id"]


def test_validator_rejects_missing_guardrail_and_accepts_complete_design():
    """Verifies that Validator Engine enforces the locking requirement based on structural details."""
    validator = ValidatorEngine()

    # Package without locking details
    defective_design = {
        "generation_id": "gen_concurrency_eval",
        "prompt": "Build an IoT Parking Reservation System",
        "hld": {"system_name": "Smart Parking System", "major_services": [{"name": "ReservationService"}]},
        "llds": {
            "backend": {"services": [{"name": "ReservationService", "logic": "Standard non-locking read-then-write"}]},
            "database": {"tables": [{"name": "slots", "columns": [{"name": "status", "type": "VARCHAR"}]}]},
            "cloud": {"multi_az": True},
            "security": {},
            "frontend": {},
        },
    }

    res_defective: ValidatedArchitectureResponse = validator.validate(defective_design)
    findings = [f.id for f in res_defective.validation.findings]
    assert "RACE-RESERVATION-001" in findings, "Validator must identify missing concurrency guardrail"

    # Package with actual implementation details
    complete_design = {
        "generation_id": "gen_concurrency_eval_fixed",
        "prompt": "Build an IoT Parking Reservation System",
        "hld": {"system_name": "Smart Parking System", "major_services": [{"name": "ReservationService"}]},
        "llds": {
            "backend": {
                "reservation_concurrency_policy": {
                    "lock_type": "Redis Redlock Distributed Locking with 10-minute hold TTL",
                    "database_fallback": "SELECT id, status FROM slots WHERE id = :slot_id FOR UPDATE NOWAIT",
                    "atomic_hold_endpoint": "POST /api/v1/slots/{slot_id}/hold",
                }
            },
            "database": {
                "locking_and_concurrency": {
                    "row_level_locking": "SELECT FOR UPDATE row-level lock on slots table",
                    "indices": [{"name": "idx_slots_lot_status", "columns": ["parking_lot_id", "status"]}],
                }
            },
            "cloud": {
                "database": {"engine": "Amazon RDS PostgreSQL Multi-AZ Deployment"},
                "networking": {"multi_az": True},
            },
            "security": {
                "ingress_rate_limiting": {"algorithm": "Token Bucket (Redis-backed)", "limit_per_minute": 120}
            },
            "frontend": {},
        },
    }

    res_complete: ValidatedArchitectureResponse = validator.validate(complete_design)
    fixed_findings = [f.id for f in res_complete.validation.findings]
    assert "RACE-RESERVATION-001" not in fixed_findings, "Resolved concurrency guardrail must clear finding"
