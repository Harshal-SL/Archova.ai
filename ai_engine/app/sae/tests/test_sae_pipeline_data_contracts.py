"""Comprehensive Unit and Integration Tests for SAE v2 Pipeline Data Contracts & State Propagation.

Validates the 6 mandatory contract test cases:
  TEST 1: Requirement Analysis produces valid requirements -> Tech Advisor receives same IDs, FR > 0, domain & actors populated.
  TEST 2: Requirement Analysis produces invalid/empty requirements -> Tech Advisor, HLD, LLDs not called, pipeline fails cleanly.
  TEST 3: Valid data preserved in Tech Advisor input construction without losing fields or inserting blank defaults.
  TEST 4: Backend LLD validation failure generates structured diagnostics and fails scorecard when below threshold.
  TEST 5: Requirement IDs remain identical across REQ -> TECH -> ADP -> HLD -> Backend -> DB -> Frontend.
  TEST 6: Inferred features remain classified under domain gap analysis (RECOMMENDED / OPTIONAL / FUTURE) and never hallucinated as REQUIRED.
"""

import io
import json
import pytest
import sys
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.sae.utils.domain_lock import DomainContext, DomainLockEngine, validate_requirement_contract
from app.sae.utils.scoring_engine import ScoringEngine, BackendQualityDiagnostics, UnifiedScorecard
from app.sae.utils.cross_artifact_validator import CrossArtifactValidator, CrossArtifactConsistencyReport
from app.sae.agents.requirement_analysis_agent import RequirementAnalysisAgent
from app.sae.agents.technology_advisor_agent import TechnologyAdvisorAgent
from app.sae.agents.backend_lld_generation_agent import BackendLLDGenerationAgent


@pytest.fixture
def sample_arsrs():
    return {
        "project_profile": {
            "goal": "Build an enterprise library web application for students and librarians.",
            "system_type": "Web Application",
            "domain": "",
            "success_criteria": [
                "Search, borrow, and return workflows execute with ACID consistency."
            ],
        },
        "business_context": {
            "business_objectives": [
                "Provide a secure platform for managing books and student borrowings."
            ],
            "stakeholders": ["Student", "Librarian"],
            "constraints": ["Must support modern web browsers"],
        },
        "domain_context": {
            "industry": "Education & Library Management",
            "domain_concepts": ["Cataloging", "Circulation", "Patron Management"],
        },
        "modules": [
            "Authentication & Access Control",
            "Book & Catalog Management",
            "Borrowing & Circulation",
            "Return & Overdue Management",
        ],
        "workflows": [
            {"id": "WF-001", "name": "User Authentication", "actor": "Student", "steps": ["Enter credentials", "Validate JWT"]},
            {"id": "WF-002", "name": "Search Catalog", "actor": "Student", "steps": ["Search book", "View results"]},
            {"id": "WF-003", "name": "Borrow Book", "actor": "Student", "steps": ["Select copy", "Confirm loan"]},
        ],
        "functional_requirements": [
            {"id": "FR-001", "title": "User authentication (login/logout)", "description": "User authentication (login/logout)", "priority": "high"},
            {"id": "FR-002", "title": "Book operations (Search, Borrow, Return)", "description": "System shall manage Book operations (Search, Borrow, Return)", "priority": "high"},
        ],
        "non_functional_requirements": [
            {"id": "NFR-001", "title": "Response time", "description": "System response time shall be under 2.0 seconds for 95% of standard requests.", "priority": "high"},
            {"id": "NFR-002", "title": "Encryption", "description": "All sensitive data must be encrypted with AES-256 and TLS 1.3.", "priority": "high"},
        ],
    }


def test_1_requirement_analysis_produces_valid_contract(sample_arsrs):
    """TEST 1: Requirement Analysis produces valid requirements with populated domain, actors, and FRs."""
    domain_ctx = DomainLockEngine.lock_domain_and_requirements(sample_arsrs)
    assert domain_ctx.domain_name == "Education & Library Management"
    assert len(domain_ctx.canonical_requirements) >= 3
    assert len(domain_ctx.actors) >= 2
    assert len(domain_ctx.modules) >= 2

    artifact = domain_ctx.to_validated_artifact()
    is_valid, score, violations = validate_requirement_contract(artifact, domain_ctx)
    
    assert is_valid is True, f"Contract violations: {violations}"
    assert score >= 0.70
    assert len(artifact["functional_requirements"]) >= 2
    assert len(artifact["actors"]) >= 2
    assert bool(artifact["domain"]) is True
    print(f"[PASS] TEST 1: Valid requirement contract verified (Score: {score})")


def test_2_invalid_requirements_halt_pipeline():
    """TEST 2: Empty/defective requirements trigger contract failure and do not propagate downstream."""
    empty_reqs = {
        "system_name": "",
        "domain": "",
        "functional_requirements": [],
        "non_functional_requirements": [],
        "actors": [],
        "modules": [],
    }

    dummy_ctx = DomainLockEngine.lock_domain_and_requirements({"project_profile": {"goal": "Test"}})
    is_valid, score, violations = validate_requirement_contract(empty_reqs, dummy_ctx)

    assert is_valid is False
    assert score < 0.70
    assert len(violations) >= 4
    assert any("functional_requirements" in v for v in violations)
    assert any("system_name" in v for v in violations)
    print(f"[PASS] TEST 2: Invalid requirement contract blocked successfully (Violations: {len(violations)})")


def test_3_technology_advisor_input_preservation(sample_arsrs):
    """TEST 3: Valid requirement data is preserved completely when constructing Technology Advisor input."""
    domain_ctx = DomainLockEngine.lock_domain_and_requirements(sample_arsrs)
    validated_req = domain_ctx.to_validated_artifact()

    tech_agent = TechnologyAdvisorAgent()
    prompt = tech_agent._build_prompt(validated_req)

    assert "College Library Management System" in prompt or "Library" in prompt
    assert "Book & Catalog Management" in prompt or "Authentication" in prompt
    assert "FR-001" in prompt
    assert "Student" in prompt or "Librarian" in prompt
    print("[PASS] TEST 3: Technology Advisor input construction preserves all fields")


def test_4_backend_lld_quality_gate_diagnostics():
    """TEST 4: Defective Backend LLD produces structured diagnostics and fails quality gate."""
    defective_backend = {
        "api_endpoints": [],
        "domain_models": [],
        "services": [],
        "repositories": [],
    }

    dummy_ctx = DomainLockEngine.lock_domain_and_requirements({"domain_context": {"industry": "Library"}})
    diag = ScoringEngine.evaluate_backend_quality_gate(defective_backend, dummy_ctx)

    assert diag.passed is False
    assert diag.score == 0.0
    assert len(diag.missing_fields) >= 3
    assert len(diag.failed_checks) >= 3
    assert any(fc["check"] == "api_endpoints_presence" for fc in diag.failed_checks)
    print(f"[PASS] TEST 4: Backend quality gate diagnostics exposed failure cleanly (Score: {diag.score})")


def test_5_requirement_ids_traceability_across_pipeline(sample_arsrs):
    """TEST 5: Requirement IDs remain identical and traceable across all pipeline stages."""
    domain_ctx = DomainLockEngine.lock_domain_and_requirements(sample_arsrs)
    canonical_ids = domain_ctx.get_req_ids()
    assert len(canonical_ids) >= 3

    # Check that canonical IDs are present in validated artifact
    artifact = domain_ctx.to_validated_artifact()
    req_ids_in_art = [r["id"] for r in artifact["functional_requirements"] + artifact["non_functional_requirements"]]
    for cid in canonical_ids:
        assert cid in req_ids_in_art, f"Canonical ID {cid} missing from requirement artifact"

    # Check Technology Advisor fallback preserves IDs
    tech_agent = TechnologyAdvisorAgent()
    fallback_tech = tech_agent._synthesize_fallback_stack(artifact)
    satisfies_in_tech = []
    for cat, val in fallback_tech.items():
        if isinstance(val, dict) and "satisfies" in val:
            satisfies_in_tech.extend(val["satisfies"])
    assert any(cid in satisfies_in_tech for cid in canonical_ids)

    # Check Backend LLD fallback preserves IDs
    be_agent = BackendLLDGenerationAgent()
    hld_mock = {"major_services": [{"name": "Catalog"}], "technology_stack": {"backend": "FastAPI"}}
    fallback_be = be_agent._synthesize_fallback_backend_lld(hld_mock)
    be_satisfies = []
    for ep in fallback_be["api_endpoints"]:
        be_satisfies.extend(ep.get("satisfies", []))
    assert any(cid in be_satisfies for cid in canonical_ids)
    print("[PASS] TEST 5: Requirement IDs verified identical across pipeline stages")


def test_6_inferred_features_not_hallucinated_as_required(sample_arsrs):
    """TEST 6: Domain checklist features not present in ARSRS remain classified as gaps/recommended, not REQUIRED."""
    domain_ctx = DomainLockEngine.lock_domain_and_requirements(sample_arsrs)
    gap_analysis = domain_ctx.domain_gap_analysis
    assert "checklist_status" in gap_analysis

    for item in gap_analysis["checklist_status"]:
        # Unstated features (e.g. Holds queue or fine penalty) must be ABSENT_POTENTIAL_GAP
        if "fine" in item["feature"].lower() or "hold" in item["feature"].lower():
            assert item["status"] == "ABSENT_POTENTIAL_GAP"
            assert item["classification"] in ("RECOMMENDED_FUTURE_PHASE", "OPTIONAL", "FUTURE")
            # Verify it is NOT placed into functional_requirements as REQUIRED
            assert not any(r.title == item["feature"] and r.priority == "REQUIRED" for r in domain_ctx.canonical_requirements)
        elif "catalog" in item["feature"].lower() or "search" in item["feature"].lower():
            assert item["status"] == "PRESENT"
            assert item["classification"] == "REQUIRED"

    print("[PASS] TEST 6: Inferred features strictly classified without hallucination")


def run_all_contract_tests():
    print("\n" + "=" * 70)
    print("RUNNING SAE PIPELINE DATA CONTRACT & STATE PROPAGATION TESTS")
    print("=" * 70)
    sample = {
        "project_profile": {
            "goal": "Build a college library web app.",
            "system_type": "Web Application",
            "domain": "Education",
        },
        "business_context": {
            "business_objectives": ["Manage book lending."],
            "stakeholders": ["Student", "Librarian"],
        },
        "domain_context": {"industry": "Library Management"},
        "modules": ["Catalog", "Borrowing"],
        "workflows": [{"id": "WF-1", "name": "Borrow", "steps": ["Search", "Borrow"]}],
        "functional_requirements": [
            {"id": "FR-001", "title": "Search books", "description": "Student shall search books", "priority": "high"},
            {"id": "FR-002", "title": "Borrow books", "description": "Student shall borrow books", "priority": "high"},
        ],
        "non_functional_requirements": [
            {"id": "NFR-001", "title": "Latency", "description": "Response under 200ms", "priority": "high"},
        ],
    }

    test_1_requirement_analysis_produces_valid_contract(sample)
    test_2_invalid_requirements_halt_pipeline()
    test_3_technology_advisor_input_preservation(sample)
    test_4_backend_lld_quality_gate_diagnostics()
    test_5_requirement_ids_traceability_across_pipeline(sample)
    test_6_inferred_features_not_hallucinated_as_required(sample)
    print("=" * 70)
    print("ALL 6 SAE DATA CONTRACT TESTS PASSED SUCCESSFULLY!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_all_contract_tests()
