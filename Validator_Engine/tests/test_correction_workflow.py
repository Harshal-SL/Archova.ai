"""End-to-End Tests for the Closed-Loop Validator-AI Correction Workflow.

Verifies:
1. Defect detection (parking slot double-booking concurrency risk).
2. Structured feedback generation (missing locking, affected artifacts, RAG evidence).
3. AI Engine correction application (targeting affected/dependent artifacts while preserving others).
4. Revalidation pass (confirming defect resolution, approval verdict, and audit history).
5. Clean package handling (ensuring no unnecessary regeneration cycles).
6. Retry limit boundary enforcement (no infinite loops, correct unvalidated status if unresolved).
"""

import copy
import json
from pathlib import Path
import pytest

from Validator_Engine.engine import ValidatorEngine
from Validator_Engine.models.input_models import ArchitecturePackageInput
from Validator_Engine.models.output_models import ValidatedArchitectureResponse
from Validator_Engine.models.report_models import ArchitectureCorrectionFeedback
from ai_engine.app.services.generation_service import generation_service

FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "ai_engine"
    / "output"
    / "run_20261004_200235_gen_415ece685f85"
    / "10_architecture_package.json"
)


@pytest.fixture
def clean_architecture_package() -> dict:
    """Fixture providing a clean, verified architecture package from actual generation output."""
    assert FIXTURE_PATH.exists(), f"Fixture missing at {FIXTURE_PATH}"
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def defective_parking_package(clean_architecture_package: dict) -> dict:
    """Fixture introducing the representative defect: Smart Parking System lacking double-booking protection."""
    pkg = copy.deepcopy(clean_architecture_package)

    # 1. Re-target domain & prompt to a Smart Parking Reservation System
    pkg["generation_id"] = "gen_test_parking_defect"
    pkg["prompt"] = "Build a Smart Parking Reservation System"
    if "arsrs" in pkg and isinstance(pkg["arsrs"], dict):
        pkg["arsrs"]["system_name"] = "Smart Parking Reservation System"
        pkg["arsrs"]["domain"] = "IoT & Smart Transportation / Parking"

    # 2. Strip all pre-existing locking and concurrency guarantees to introduce the representative defect
    pkg_str = (
        json.dumps(pkg)
        .replace("SELECT FOR UPDATE", "standard SELECT query")
        .replace("select for update", "standard SELECT query")
        .replace("optimistic locking", "standard database updates")
        .replace("concurrency locking", "standard data persistence")
        .replace("distributed lock", "in-memory session state")
        .replace("Redlock", "standard cache")
    )
    defective_pkg = json.loads(pkg_str)
    return defective_pkg


def test_validator_identifies_parking_concurrency_defect(defective_parking_package: dict):
    """Verify Validator identifies double-booking race condition and builds structured feedback."""
    validator = ValidatorEngine()
    response: ValidatedArchitectureResponse = validator.validate(defective_parking_package, attempt=1, max_retries=2)

    # 1. Defect must be detected
    finding_ids = [f.id for f in response.validation.findings]
    assert "RACE-RESERVATION-001" in finding_ids, f"Expected RACE-RESERVATION-001 finding, got: {finding_ids}"

    # 2. Package must not be marked fully validated
    assert response.is_fully_validated is False
    assert response.attempt == 1
    assert response.max_retries == 2

    # 3. Build structured correction feedback
    feedback = validator.build_correction_feedback(response, attempt=1)
    assert isinstance(feedback, ArchitectureCorrectionFeedback)
    assert len(feedback.items) > 0

    # 4. Check feedback details
    concurrency_items = [it for it in feedback.items if it.issue_id == "RACE-RESERVATION-001"]
    assert len(concurrency_items) == 1
    item = concurrency_items[0]
    assert any(k in item.issue_identified.lower() for k in ["parking slot", "simultaneous", "race condition", "concurrency", "double-booking", "toctou"])
    assert item.severity == "HIGH"
    assert "SELECT FOR UPDATE" in item.recommended_correction or "Redlock" in item.recommended_correction or "Redis" in item.recommended_correction
    assert item.affected_artifact in ("backend_lld", "database_lld")
    assert item.missing_or_incorrect_detail != ""


def test_ai_engine_applies_feedback_and_resolves_defect(defective_parking_package: dict):
    """Test full closed-loop: Defect detected -> Feedback created -> AI Engine corrects -> Revalidation passes."""
    initial_pkg = copy.deepcopy(defective_parking_package)

    # Run closed-loop validation and correction workflow
    result = generation_service.validate_and_correct_package(initial_pkg, max_retries=2)

    assert result is not None
    # 1. Output reflects resolution
    assert result.get("is_fully_validated") is True, f"Expected package to be fully validated. Status: {result.get('validation', {}).get('status')}"
    assert result.get("validation", {}).get("summary", {}).get("verdict") in ("APPROVED", "APPROVED_WITH_CONDITIONS")
    assert result.get("validation", {}).get("summary", {}).get("high_findings_count") == 0

    # 2. Correction history audit trail is populated
    history = result.get("correction_history", [])
    assert len(history) == 1, f"Expected 1 correction iteration, got {len(history)}"
    attempt_record = history[0]
    assert attempt_record["attempt"] == 1
    assert "backend_lld" in attempt_record["regenerated_artifacts"]
    assert "database_lld" in attempt_record["regenerated_artifacts"]
    assert "RACE-RESERVATION-001" in attempt_record["resolved_issue_ids"]

    # 3. Verify actual architecture package was enriched with locking
    updated_pkg = result.get("architecture", {})
    llds = updated_pkg.get("llds", {})
    backend_data = llds.get("backend", {}).get("data", llds.get("backend", {}))
    db_data = llds.get("database", {}).get("data", llds.get("database", {}))

    assert "reservation_concurrency_policy" in backend_data
    assert "Redis Redlock" in backend_data["reservation_concurrency_policy"]["lock_type"]
    assert "locking_and_concurrency" in db_data
    assert "SELECT FOR UPDATE" in db_data["locking_and_concurrency"]["row_level_locking"]

    # 4. Untouched artifacts preserved (e.g. HLD, Frontend)
    assert "hld" in updated_pkg
    assert updated_pkg["hld"] == initial_pkg.get("hld")


def test_clean_package_does_not_trigger_unnecessary_regeneration(clean_architecture_package: dict):
    """Verify that an architecture that already satisfies checks does NOT trigger unnecessary regeneration."""
    result = generation_service.validate_and_correct_package(clean_architecture_package, max_retries=2)

    # 1. Must be marked fully validated on the initial attempt
    assert result.get("is_fully_validated") is True
    assert result.get("attempt") == 1
    assert result.get("validation", {}).get("summary", {}).get("verdict") in ("APPROVED", "APPROVED_WITH_CONDITIONS")

    # 2. Zero correction iterations should have been triggered
    history = result.get("correction_history", [])
    assert len(history) == 0, f"Clean package should not trigger any correction cycles, but got {len(history)}"


def test_retry_limit_boundary_enforced_without_infinite_loop():
    """Verify that retry limit is strictly respected and incomplete packages are marked unvalidated."""
    # Create an artificially defective package that cannot be automatically fixed
    malformed_pkg = {
        "generation_id": "gen_stub_unfixable",
        "prompt": "Build an unresolvable test system",
        "hld": {},  # Completely empty HLD causing permanent structural violations
        "llds": {
            "backend": {"data": {}},
            "frontend": {"data": {}},
            "database": {"data": {}},
            "security": {"data": {}},
            "cloud": {"data": {}},
        },
    }

    # Run with max_retries=2
    result = generation_service.validate_and_correct_package(malformed_pkg, max_retries=2)

    # 1. Must terminate within retry budget without looping
    assert result is not None
    assert result.get("attempt") == 2
    assert result.get("max_retries") == 2

    # 2. Must NOT be marked fully validated merely because retry limit was reached
    assert result.get("is_fully_validated") is False
    assert result.get("validation", {}).get("summary", {}).get("is_valid") is False

    # 3. Unresolved findings must be returned in the final output
    findings = result.get("validation", {}).get("findings", [])
    assert len(findings) > 0
