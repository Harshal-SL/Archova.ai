"""Backend Unit Tests for Targeted AI Architecture Corrections (Part 2.2.2)."""

import asyncio
import copy
import pytest
from app.corrections.contracts import (
    AcceptCorrectionRequest,
    CorrectionApprovalRequest,
    TargetedCorrectionRequest,
)
from app.corrections.correction_service import CorrectionService, normalize_artifact_type


@pytest.fixture
def correction_svc():
    return CorrectionService()


@pytest.fixture
def sample_package():
    return {
        "version": "1.0",
        "version_tag": "v1.0",
        "hld": {
            "major_services": [
                {"name": "OrderService", "responsibility": "Process customer orders"},
                {"name": "InventoryService", "responsibility": "Track warehouse stock"},
            ],
            "nodes": [
                {"id": "order-service", "data": {"label": "OrderService"}},
                {"id": "inventory-service", "data": {"label": "InventoryService"}},
            ],
        },
        "llds": {
            "backend": {
                "service": "OrderService",
                "api_endpoints": [
                    {"path": "/api/v1/orders", "method": "POST", "summary": "Create order"},
                ],
                "telemetry": "OpenTelemetry tracing enabled",
            },
            "database": {
                "tables": [
                    {
                        "name": "orders",
                        "columns": ["id", "customer_id", "total_cents", "status"],
                    },
                ],
                "replication": "Multi-AZ synchronous replication",
            },
        },
    }


# ── TEST 1: Successful Targeted Correction ─────────────────────────────────────
@pytest.mark.asyncio
async def test_successful_targeted_correction(correction_svc, sample_package):
    # 1. Register approval
    app_res = correction_svc.register_approval(
        CorrectionApprovalRequest(
            generation_id="gen_test_001",
            finding_id="fnd_db_version_01",
            artifact_type="database",
            source_version="v1.0",
        )
    )
    assert app_res.approved is True

    # 2. Simulated correction to add optimistic locking version column
    simulated_db = {
        "tables": [
            {
                "name": "orders",
                "columns": ["id", "customer_id", "total_cents", "status", "version"],
            },
        ],
        "replication": "Multi-AZ synchronous replication",
    }

    req = TargetedCorrectionRequest(
        generation_id="gen_test_001",
        artifact_type="database",
        source_version="v1.0",
        finding_id="fnd_db_version_01",
        finding_description="Missing optimistic concurrency version column in orders table.",
        evidence="schema.tables[orders]",
        correction_instruction="Add version column to orders table.",
        baseline_package=sample_package,
        simulated_corrected_artifact=simulated_db,
    )

    res = await correction_svc.execute_targeted_correction(req)
    assert res.status == "CORRECTION_VERIFIED"
    assert res.verification_result.is_valid is True
    assert res.corrected_artifact["tables"][0]["columns"][-1] == "version"
    assert res.corrected_artifact["replication"] == "Multi-AZ synchronous replication"  # Unrelated preserved!


# ── TEST 2: Missing Artifact Handling ──────────────────────────────────────────
@pytest.mark.asyncio
async def test_missing_artifact_rejected(correction_svc):
    correction_svc.register_approval(
        CorrectionApprovalRequest(
            generation_id="gen_non_existent",
            finding_id="fnd_01",
            artifact_type="security",
            source_version="v1.0",
        )
    )
    req = TargetedCorrectionRequest(
        generation_id="gen_non_existent",
        artifact_type="security",
        source_version="v1.0",
        finding_id="fnd_01",
        finding_description="Missing WAF policy.",
        evidence="security.policies",
        correction_instruction="Add AWS WAF rate limiting rule.",
        baseline_package={"hld": {}},  # No security artifact
        simulated_corrected_artifact={"waf": True},
    )
    with pytest.raises(ValueError, match="could not be found"):
        await correction_svc.execute_targeted_correction(req)


# ── TEST 3: Unsupported Artifact Type ──────────────────────────────────────────
@pytest.mark.asyncio
async def test_unsupported_artifact_type_rejected(correction_svc, sample_package):
    req = TargetedCorrectionRequest(
        generation_id="gen_test_001",
        artifact_type="unsupported_quantum_mesh",
        source_version="v1.0",
        finding_id="fnd_01",
        finding_description="Unknown artifact",
        evidence="unknown",
        correction_instruction="Fix it",
        baseline_package=sample_package,
    )
    with pytest.raises(ValueError, match="Unsupported artifact type"):
        await correction_svc.execute_targeted_correction(req)


# ── TEST 4: Missing Evidence Rejected ──────────────────────────────────────────
@pytest.mark.asyncio
async def test_missing_evidence_rejected(correction_svc, sample_package):
    correction_svc.register_approval(
        CorrectionApprovalRequest(
            generation_id="gen_test_001",
            finding_id="fnd_01",
            artifact_type="backend",
            source_version="v1.0",
        )
    )
    req = TargetedCorrectionRequest(
        generation_id="gen_test_001",
        artifact_type="backend",
        source_version="v1.0",
        finding_id="fnd_01",
        finding_description="Missing health check.",
        evidence="",  # Empty evidence!
        correction_instruction="Add /healthz",
        baseline_package=sample_package,
    )
    with pytest.raises(ValueError, match="Required evidence cannot be empty"):
        await correction_svc.execute_targeted_correction(req)


# ── TEST 5: Missing Correction Instruction Rejected ────────────────────────────
@pytest.mark.asyncio
async def test_missing_correction_instruction_rejected(correction_svc, sample_package):
    correction_svc.register_approval(
        CorrectionApprovalRequest(
            generation_id="gen_test_001",
            finding_id="fnd_01",
            artifact_type="backend",
            source_version="v1.0",
        )
    )
    req = TargetedCorrectionRequest(
        generation_id="gen_test_001",
        artifact_type="backend",
        source_version="v1.0",
        finding_id="fnd_01",
        finding_description="Missing health check.",
        evidence="endpoints",
        correction_instruction="   ",  # Blank instruction!
        baseline_package=sample_package,
    )
    with pytest.raises(ValueError, match="Correction instruction cannot be empty"):
        await correction_svc.execute_targeted_correction(req)


# ── TEST 6: Unapproved Finding Rejected ────────────────────────────────────────
@pytest.mark.asyncio
async def test_unapproved_finding_rejected(correction_svc, sample_package):
    # Notice: No prior approval registered for fnd_unapproved_01!
    req = TargetedCorrectionRequest(
        generation_id="gen_test_001",
        artifact_type="database",
        source_version="v1.0",
        finding_id="fnd_unapproved_01",
        finding_description="Missing index.",
        evidence="schema.tables[orders]",
        correction_instruction="Add index.",
        baseline_package=sample_package,
    )
    with pytest.raises(PermissionError, match="has not been approved for correction"):
        await correction_svc.execute_targeted_correction(req)


# ── TEST 7: Stale Artifact Version Rejected ────────────────────────────────────
@pytest.mark.asyncio
async def test_stale_artifact_version_rejected(correction_svc, sample_package):
    correction_svc.register_approval(
        CorrectionApprovalRequest(
            generation_id="gen_test_001",
            finding_id="fnd_db_01",
            artifact_type="database",
            source_version="v1.0",
        )
    )
    # Baseline is v1.2, but request specifies old v1.0
    stale_pkg = copy.deepcopy(sample_package)
    stale_pkg["version_tag"] = "v1.2"
    stale_pkg["version"] = "1.2"

    req = TargetedCorrectionRequest(
        generation_id="gen_test_001",
        artifact_type="database",
        source_version="v1.0",
        finding_id="fnd_db_01",
        finding_description="Missing index.",
        evidence="schema.tables[orders]",
        correction_instruction="Add index.",
        baseline_package=stale_pkg,
        simulated_corrected_artifact={"tables": []},
    )
    with pytest.raises(ValueError, match="Stale artifact version"):
        await correction_svc.execute_targeted_correction(req)


# ── TEST 8: Malformed LLM Output Handled Safely ───────────────────────────────
@pytest.mark.asyncio
async def test_malformed_llm_output_handled(correction_svc, sample_package, monkeypatch):
    correction_svc.register_approval(
        CorrectionApprovalRequest(
            generation_id="gen_test_001",
            finding_id="fnd_be_01",
            artifact_type="backend",
            source_version="v1.0",
        )
    )

    # Mock LLM provider to return malformed non-JSON
    async def fake_acall(*args, **kwargs):
        return "I am an AI and I suggest you rewrite everything in Rust."

    monkeypatch.setattr(correction_svc._llm_provider, "acall", fake_acall)

    req = TargetedCorrectionRequest(
        generation_id="gen_test_001",
        artifact_type="backend",
        source_version="v1.0",
        finding_id="fnd_be_01",
        finding_description="Add endpoint",
        evidence="endpoints",
        correction_instruction="Add GET /readyz",
        baseline_package=sample_package,
    )
    with pytest.raises(ValueError, match="Malformed model response"):
        await correction_svc.execute_targeted_correction(req)


# ── TEST 9: LLM Provider Failure Handled Safely ────────────────────────────────
@pytest.mark.asyncio
async def test_llm_provider_failure_handled(correction_svc, sample_package, monkeypatch):
    correction_svc.register_approval(
        CorrectionApprovalRequest(
            generation_id="gen_test_001",
            finding_id="fnd_be_01",
            artifact_type="backend",
            source_version="v1.0",
        )
    )

    async def fail_acall(*args, **kwargs):
        raise ConnectionError("OpenRouter 503 Service Unavailable")

    monkeypatch.setattr(correction_svc._llm_provider, "acall", fail_acall)

    req = TargetedCorrectionRequest(
        generation_id="gen_test_001",
        artifact_type="backend",
        source_version="v1.0",
        finding_id="fnd_be_01",
        finding_description="Add endpoint",
        evidence="endpoints",
        correction_instruction="Add GET /readyz",
        baseline_package=sample_package,
    )
    with pytest.raises(RuntimeError, match="Model provider request failed"):
        await correction_svc.execute_targeted_correction(req)


# ── TEST 10: Empty or Truncated Output Detected ────────────────────────────────
@pytest.mark.asyncio
async def test_empty_or_truncated_output_detected(correction_svc, sample_package):
    correction_svc.register_approval(
        CorrectionApprovalRequest(
            generation_id="gen_test_001",
            finding_id="fnd_be_01",
            artifact_type="backend",
            source_version="v1.0",
        )
    )
    req = TargetedCorrectionRequest(
        generation_id="gen_test_001",
        artifact_type="backend",
        source_version="v1.0",
        finding_id="fnd_be_01",
        finding_description="Add endpoint",
        evidence="endpoints",
        correction_instruction="Add GET /readyz",
        baseline_package=sample_package,
        simulated_corrected_artifact={},  # Empty dict!
    )
    res = await correction_svc.execute_targeted_correction(req)
    assert res.status == "CORRECTION_FAILED"
    assert res.verification_result.is_valid is False
    assert any("empty" in f.lower() for f in res.verification_result.checks_failed)


# ── TEST 11: Verification Failure on Dropped Content ──────────────────────────
@pytest.mark.asyncio
async def test_verification_failure_when_unrelated_content_dropped(correction_svc, sample_package):
    correction_svc.register_approval(
        CorrectionApprovalRequest(
            generation_id="gen_test_001",
            finding_id="fnd_db_01",
            artifact_type="database",
            source_version="v1.0",
        )
    )
    # The original has "tables" and "replication".
    # Simulated drops "replication" and replaces with only an empty table
    mutilated_db = {"new_unrelated_key": 123}

    req = TargetedCorrectionRequest(
        generation_id="gen_test_001",
        artifact_type="database",
        source_version="v1.0",
        finding_id="fnd_db_01",
        finding_description="Fix table",
        evidence="schema",
        correction_instruction="Fix table",
        baseline_package=sample_package,
        simulated_corrected_artifact=mutilated_db,
    )
    res = await correction_svc.execute_targeted_correction(req)
    assert res.status == "CORRECTION_FAILED"
    assert res.verification_result.is_valid is False
    assert res.verification_result.unrelated_keys_preserved is False


# ── TEST 12: Manual Review Required When Unresolved Issues Exist ───────────────
@pytest.mark.asyncio
async def test_manual_review_required_on_uncertainty(correction_svc, sample_package, monkeypatch):
    correction_svc.register_approval(
        CorrectionApprovalRequest(
            generation_id="gen_test_001",
            finding_id="fnd_sec_01",
            artifact_type="database",
            source_version="v1.0",
        )
    )

    async def uncertain_acall(*args, **kwargs):
        return """```json
{
  "corrected_artifact": {
    "tables": [{"name": "orders", "columns": ["id"]}],
    "replication": "Multi-AZ synchronous replication"
  },
  "change_summary": "Added partial encryption",
  "explanation": "KMS key ARN was not provided",
  "unresolved_issues": ["Stakeholder must specify KMS Multi-Region key ARN"]
}
```"""

    monkeypatch.setattr(correction_svc._llm_provider, "acall", uncertain_acall)

    req = TargetedCorrectionRequest(
        generation_id="gen_test_001",
        artifact_type="database",
        source_version="v1.0",
        finding_id="fnd_sec_01",
        finding_description="Add column encryption",
        evidence="schema",
        correction_instruction="Add KMS encryption",
        baseline_package=sample_package,
    )
    res = await correction_svc.execute_targeted_correction(req)
    assert res.status == "MANUAL_REVIEW_REQUIRED"
    assert "Stakeholder must specify KMS Multi-Region key ARN" in res.unresolved_issues


# ── TEST 13: Rejected Correction Preserves Original ────────────────────────────
@pytest.mark.asyncio
async def test_rejected_correction_preserves_original(correction_svc, sample_package):
    correction_svc.register_approval(
        CorrectionApprovalRequest(
            generation_id="gen_test_001",
            finding_id="fnd_01",
            artifact_type="database",
            source_version="v1.0",
        )
    )
    req = TargetedCorrectionRequest(
        generation_id="gen_test_001",
        artifact_type="database",
        source_version="v1.0",
        finding_id="fnd_01",
        finding_description="Add index",
        evidence="schema",
        correction_instruction="Add index",
        baseline_package=sample_package,
        simulated_corrected_artifact={
            "tables": [{"name": "orders", "columns": ["id"]}],
            "replication": "Multi-AZ synchronous replication",
        },
    )
    res = await correction_svc.execute_targeted_correction(req)
    op_id = res.operation_id

    rej_res = correction_svc.reject_correction(op_id)
    assert rej_res.status == "REJECTED"

    # Operation status is recorded as REJECTED
    op_details = correction_svc.get_operation(op_id)
    assert op_details["status"] == "REJECTED"


# ── TEST 14: Accepted Correction Creates New Version ──────────────────────────
@pytest.mark.asyncio
async def test_accepted_correction_creates_new_version(correction_svc, sample_package):
    correction_svc.register_approval(
        CorrectionApprovalRequest(
            generation_id="gen_test_001",
            finding_id="fnd_01",
            artifact_type="database",
            source_version="v1.0",
        )
    )
    simulated_db = {
        "tables": [{"name": "orders", "columns": ["id", "version"]}],
        "replication": "Multi-AZ synchronous replication",
    }
    req = TargetedCorrectionRequest(
        generation_id="gen_test_001",
        artifact_type="database",
        source_version="v1.0",
        finding_id="fnd_01",
        finding_description="Add version column",
        evidence="schema",
        correction_instruction="Add version column",
        baseline_package=sample_package,
        simulated_corrected_artifact=simulated_db,
    )
    res = await correction_svc.execute_targeted_correction(req)
    op_id = res.operation_id

    acc_res = await correction_svc.accept_correction(op_id)
    assert acc_res.status == "ACCEPTED"
    assert acc_res.previous_version == "v1.0"
    assert acc_res.new_version == "v1.1"
    assert acc_res.updated_artifact["tables"][0]["columns"] == ["id", "version"]


# ── TEST 15: Duplicate Acceptance Blocked ──────────────────────────────────────
@pytest.mark.asyncio
async def test_duplicate_acceptance_blocked(correction_svc, sample_package):
    correction_svc.register_approval(
        CorrectionApprovalRequest(
            generation_id="gen_test_001",
            finding_id="fnd_01",
            artifact_type="database",
            source_version="v1.0",
        )
    )
    req = TargetedCorrectionRequest(
        generation_id="gen_test_001",
        artifact_type="database",
        source_version="v1.0",
        finding_id="fnd_01",
        finding_description="Add version",
        evidence="schema",
        correction_instruction="Add version",
        baseline_package=sample_package,
        simulated_corrected_artifact={"tables": [], "replication": "yes"},
    )
    res = await correction_svc.execute_targeted_correction(req)
    op_id = res.operation_id

    # First accept
    await correction_svc.accept_correction(op_id)

    # Second accept attempt must fail
    with pytest.raises(ValueError, match="already been accepted"):
        await correction_svc.accept_correction(op_id)


# ── TEST 16: Concurrent Acceptance Protection ──────────────────────────────────
@pytest.mark.asyncio
async def test_concurrent_acceptance_protection(correction_svc, sample_package):
    correction_svc.register_approval(
        CorrectionApprovalRequest(
            generation_id="gen_test_001",
            finding_id="fnd_01",
            artifact_type="database",
            source_version="v1.0",
        )
    )
    req = TargetedCorrectionRequest(
        generation_id="gen_test_001",
        artifact_type="database",
        source_version="v1.0",
        finding_id="fnd_01",
        finding_description="Add version",
        evidence="schema",
        correction_instruction="Add version",
        baseline_package=sample_package,
        simulated_corrected_artifact={"tables": [], "replication": "yes"},
    )
    res = await correction_svc.execute_targeted_correction(req)
    op_id = res.operation_id

    # Launch two concurrent accepts
    results = await asyncio.gather(
        correction_svc.accept_correction(op_id),
        correction_svc.accept_correction(op_id),
        return_exceptions=True,
    )
    # Exactly one succeeded and one raised ValueError
    successes = [r for r in results if not isinstance(r, Exception)]
    errors = [r for r in results if isinstance(r, Exception)]
    assert len(successes) == 1
    assert len(errors) == 1
    assert "already been accepted" in str(errors[0])


# ── TEST 17: Stale Operation Acceptance Rejected ──────────────────────────────
@pytest.mark.asyncio
async def test_stale_operation_acceptance_rejected(correction_svc, sample_package):
    correction_svc.register_approval(
        CorrectionApprovalRequest(
            generation_id="gen_test_001",
            finding_id="fnd_01",
            artifact_type="database",
            source_version="v1.0",
        )
    )
    req = TargetedCorrectionRequest(
        generation_id="gen_test_001",
        artifact_type="database",
        source_version="v1.0",
        finding_id="fnd_01",
        finding_description="Add version",
        evidence="schema",
        correction_instruction="Add version",
        baseline_package=sample_package,
        simulated_corrected_artifact={"tables": [], "replication": "yes"},
    )
    res = await correction_svc.execute_targeted_correction(req)
    op_id = res.operation_id

    # Expected source version has moved to v1.1
    with pytest.raises(ValueError, match="Stale correction operation"):
        await correction_svc.accept_correction(
            op_id,
            AcceptCorrectionRequest(expected_source_version="v1.1"),
        )


# ── TEST 18: Historical Version Preservation ──────────────────────────────────
@pytest.mark.asyncio
async def test_historical_version_preservation(correction_svc, sample_package):
    original_hld = copy.deepcopy(sample_package["hld"])
    correction_svc.register_approval(
        CorrectionApprovalRequest(
            generation_id="gen_test_001",
            finding_id="fnd_hld_01",
            artifact_type="hld",
            source_version="v1.0",
        )
    )
    req = TargetedCorrectionRequest(
        generation_id="gen_test_001",
        artifact_type="hld",
        source_version="v1.0",
        finding_id="fnd_hld_01",
        finding_description="Add Gateway",
        evidence="major_services",
        correction_instruction="Add GatewayService",
        baseline_package=sample_package,
        simulated_corrected_artifact={
            "major_services": original_hld["major_services"] + [{"name": "GatewayService"}],
            "nodes": original_hld["nodes"],
        },
    )
    res = await correction_svc.execute_targeted_correction(req)
    # The response carries the original artifact intact for comparison
    assert res.original_artifact == original_hld
    assert len(res.original_artifact["major_services"]) == 2
    assert len(res.corrected_artifact["major_services"]) == 3


# ── TEST 19: Unrelated Artifacts Remain Untouched ──────────────────────────────
@pytest.mark.asyncio
async def test_unrelated_artifacts_remain_untouched(correction_svc, sample_package):
    correction_svc.register_approval(
        CorrectionApprovalRequest(
            generation_id="gen_test_001",
            finding_id="fnd_db_01",
            artifact_type="database",
            source_version="v1.0",
        )
    )
    req = TargetedCorrectionRequest(
        generation_id="gen_test_001",
        artifact_type="database",
        source_version="v1.0",
        finding_id="fnd_db_01",
        finding_description="Add column",
        evidence="schema",
        correction_instruction="Add column",
        baseline_package=sample_package,
        simulated_corrected_artifact={"tables": [], "replication": "yes"},
    )
    res = await correction_svc.execute_targeted_correction(req)
    acc = await correction_svc.accept_correction(res.operation_id)

    # In sample_package, the backend LLD and HLD were not modified
    assert sample_package["hld"]["major_services"][0]["name"] == "OrderService"
    assert sample_package["llds"]["backend"]["service"] == "OrderService"


# ── TEST 20: No Automatic Revalidation ────────────────────────────────────────
@pytest.mark.asyncio
async def test_no_automatic_revalidation_triggered(correction_svc, sample_package):
    correction_svc.register_approval(
        CorrectionApprovalRequest(
            generation_id="gen_test_001",
            finding_id="fnd_db_01",
            artifact_type="database",
            source_version="v1.0",
        )
    )
    req = TargetedCorrectionRequest(
        generation_id="gen_test_001",
        artifact_type="database",
        source_version="v1.0",
        finding_id="fnd_db_01",
        finding_description="Add column",
        evidence="schema",
        correction_instruction="Add column",
        baseline_package=sample_package,
        simulated_corrected_artifact={"tables": [], "replication": "yes"},
    )
    res = await correction_svc.execute_targeted_correction(req)
    acc = await correction_svc.accept_correction(res.operation_id)

    # Confirm acceptance response has status "ACCEPTED" and does NOT contain any validation verdict
    assert acc.status == "ACCEPTED"
    assert not hasattr(acc, "validation_verdict")
    assert not hasattr(acc, "revalidation_scores")


# ── TEST 21: Artifact Type Aliases Normalization ──────────────────────────────
def test_artifact_type_normalization():
    assert normalize_artifact_type("Backend LLD") == "backend"
    assert normalize_artifact_type("backend-lld") == "backend"
    assert normalize_artifact_type("database_lld") == "database"
    assert normalize_artifact_type("HLD") == "hld"
    assert normalize_artifact_type("cloud-lld") == "cloud"
    assert normalize_artifact_type("security") == "security"
    assert normalize_artifact_type("ARSRS") == "arsrs"


# ── TEST 22: Cannot Reject Accepted Operation ──────────────────────────────────
@pytest.mark.asyncio
async def test_cannot_reject_accepted_operation(correction_svc, sample_package):
    correction_svc.register_approval(
        CorrectionApprovalRequest(
            generation_id="gen_test_001",
            finding_id="fnd_01",
            artifact_type="database",
            source_version="v1.0",
        )
    )
    req = TargetedCorrectionRequest(
        generation_id="gen_test_001",
        artifact_type="database",
        source_version="v1.0",
        finding_id="fnd_01",
        finding_description="Add version",
        evidence="schema",
        correction_instruction="Add version",
        baseline_package=sample_package,
        simulated_corrected_artifact={"tables": [], "replication": "yes"},
    )
    res = await correction_svc.execute_targeted_correction(req)
    op_id = res.operation_id
    await correction_svc.accept_correction(op_id)

    with pytest.raises(ValueError, match="already accepted"):
        correction_svc.reject_correction(op_id)


# ── TEST 23: Cross-Generation Acceptance Forbidden ───────────────────────────
@pytest.mark.asyncio
async def test_cross_generation_acceptance_forbidden(correction_svc, sample_package):
    correction_svc.register_approval(
        CorrectionApprovalRequest(
            generation_id="gen_session_A",
            finding_id="fnd_iso_01",
            artifact_type="database",
            source_version="v1.0",
        )
    )
    req = TargetedCorrectionRequest(
        generation_id="gen_session_A",
        artifact_type="database",
        source_version="v1.0",
        finding_id="fnd_iso_01",
        finding_description="Fix table",
        evidence="schema",
        correction_instruction="Add index",
        baseline_package=sample_package,
        simulated_corrected_artifact={"tables": [], "replication": "yes"},
    )
    res = await correction_svc.execute_targeted_correction(req)
    op_id = res.operation_id

    # Attempt to accept with mismatched generation_id
    with pytest.raises(ValueError, match="Cross-generation acceptance forbidden"):
        await correction_svc.accept_correction(
            op_id,
            AcceptCorrectionRequest(generation_id="gen_session_B"),
        )


# ── TEST 24: Durable Persistence Survives Service Restart ────────────────────
@pytest.mark.asyncio
async def test_durable_persistence_survives_restart(correction_svc, sample_package):
    test_gen = "gen_persist_test_99"
    test_fnd = "fnd_persist_01"

    # 1. Register approval
    correction_svc.register_approval(
        CorrectionApprovalRequest(
            generation_id=test_gen,
            finding_id=test_fnd,
            artifact_type="backend",
            source_version="v1.0",
        )
    )

    # 2. Execute correction
    req = TargetedCorrectionRequest(
        generation_id=test_gen,
        artifact_type="backend",
        source_version="v1.0",
        finding_id=test_fnd,
        finding_description="Add rate limiting",
        evidence="api_endpoints",
        correction_instruction="Add rate limit middleware",
        baseline_package=sample_package,
        simulated_corrected_artifact={"service": "OrderService", "api_endpoints": []},
    )
    res = await correction_svc.execute_targeted_correction(req)
    op_id = res.operation_id

    # 3. Simulate backend restart by creating a completely new CorrectionService instance
    restarted_svc = CorrectionService()

    # Verify approval survived
    assert restarted_svc.is_approved(test_gen, test_fnd) is True

    # Verify operation survived
    recovered_op = restarted_svc.get_operation(op_id)
    assert recovered_op is not None
    assert recovered_op["operation_id"] == op_id
    assert recovered_op["artifact_type"] == "backend"

    # 4. Accept on restarted service
    accept_res = await restarted_svc.accept_correction(op_id)
    assert accept_res.status == "ACCEPTED"
    assert accept_res.new_version == "v1.1"

    # 5. Simulate second restart and verify accepted status & versions survived
    second_restart_svc = CorrectionService()
    final_op = second_restart_svc.get_operation(op_id)
    assert final_op["status"] == "ACCEPTED"

    history = second_restart_svc.get_historical_versions(test_gen)
    assert len(history) >= 1
    assert history[-1]["operation_id"] == op_id
    assert history[-1]["from_version"] == "v1.0"
    assert history[-1]["to_version"] == "v1.1"

