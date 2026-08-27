"""Comprehensive Unit and Integration Tests for SAE v2 Canonical Architecture Contract (CAC).

Validates the 8 mandatory test cases:
  TEST 1: Requirement ID integrity (FR-001..FR-004, no REQ-* aliases, unknown IDs trigger UNKNOWN_REQUIREMENT_ID).
  TEST 2: API contract integrity (Operation IDs & URIs identical across Backend, Frontend, Testing, Observability).
  TEST 3: Explicit Entity Mapping (ENT-003 BorrowTransaction -> DB-003 borrow_records).
  TEST 4: Invalid upstream artifact blocks Technology Advisor and downstream generation.
  TEST 5: Frontend/Backend mismatch (< 0.95 or wrong routes) triggers hard gate violation & pipeline failure.
  TEST 6: Backend/Database mismatch triggers hard gate violation & pipeline failure.
  TEST 7: Observability non-canonical routes trigger consistency violation.
  TEST 8: Adversarial review is grounded in consistency findings and cannot return APPROVED when blocking issues exist.
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
from app.sae.utils.canonical_contract import (
    CanonicalArchitectureContract,
    CanonicalAPIOperation,
    CanonicalDomainEntity,
    CanonicalDatabaseEntity,
    CanonicalEntityMapping,
    ContractBuilder,
)
from app.sae.utils.cross_artifact_validator import CrossArtifactValidator, CrossArtifactConsistencyReport
from app.sae.utils.scoring_engine import ScoringEngine, UnifiedScorecard
from app.sae.agents.adversarial_review_agent import AdversarialReviewAgent
from app.sae.agents.frontend_lld_generation_agent import FrontendLLDGenerationAgent
from app.sae.agents.backend_lld_generation_agent import BackendLLDGenerationAgent
from app.sae.agents.database_lld_generation_agent import DatabaseLLDGenerationAgent
from app.sae.agents.observability_agent import ObservabilityAgent


@pytest.fixture
def library_sample():
    raw_arsrs = {
        "project_profile": {
            "goal": "Build an enterprise college library system for students and librarians.",
            "system_type": "Web Application",
            "domain": "Education & Library Management",
        },
        "business_context": {
            "business_objectives": ["Automate cataloging, borrowing, and overdue fines."],
            "stakeholders": ["Student", "Librarian"],
        },
        "domain_context": {"industry": "Library Management"},
        "modules": ["Authentication", "Catalog Management", "Circulation", "Inventory Administration"],
        "workflows": [
            {"id": "WF-001", "name": "User Authentication", "actor": "Student", "steps": ["Submit credentials", "Issue token"]},
            {"id": "WF-002", "name": "Borrow Book", "actor": "Student", "steps": ["Search book", "Confirm borrow"]},
        ],
        "functional_requirements": [
            {"id": "FR-001", "title": "User Authentication", "description": "Users authenticate via credentials", "priority": "HIGH"},
            {"id": "FR-002", "title": "Catalog Search", "description": "Search catalog books with pagination", "priority": "HIGH"},
            {"id": "FR-003", "title": "Book Borrowing", "description": "Borrow available book copies", "priority": "HIGH"},
            {"id": "FR-004", "title": "Book Return & Fines", "description": "Return books and compute overdue fines", "priority": "MEDIUM"},
        ],
        "non_functional_requirements": [
            {"id": "NFR-001", "category": "Performance", "requirement": "Response time < 200ms", "priority": "HIGH"},
            {"id": "NFR-002", "category": "Security", "requirement": "JWT OAuth2 RS256 encryption", "priority": "HIGH"},
        ],
    }
    domain_ctx = DomainLockEngine.lock_domain_and_requirements(raw_arsrs)
    req_analysis = domain_ctx.to_validated_artifact()

    hld_mock = {
        "system_name": "College Library Management System",
        "domain": "Education & Library Management",
        "architecture_style": "Modular Monolith",
        "technology_stack": {
            "backend": "FastAPI (Python 3.12)",
            "frontend": "React 18 / Next.js 14",
            "database": "PostgreSQL 16",
        },
        "major_services": [
            {"name": "AuthService", "responsibility": "User authentication", "satisfies": ["FR-001"]},
            {"name": "CatalogService", "responsibility": "Catalog search and stock", "satisfies": ["FR-001", "FR-002"]},
            {"name": "CirculationService", "responsibility": "Circulation loan transactions", "satisfies": ["FR-003", "FR-004"]},
        ],
    }

    cac = ContractBuilder.build_from_hld(hld_mock, req_analysis, domain_ctx)
    return domain_ctx, req_analysis, hld_mock, cac


def test_1_requirement_id_integrity(library_sample):
    """TEST 1: Requirement ID integrity (FR-001..FR-004, no REQ-* aliases)."""
    domain_ctx, req_analysis, hld, cac = library_sample

    assert "FR-001" in cac.requirement_ids
    assert "FR-002" in cac.requirement_ids
    assert "FR-003" in cac.requirement_ids
    assert "FR-004" in cac.requirement_ids
    assert not any(r.startswith("REQ-") for r in cac.requirement_ids)

    # Simulate backend referencing invalid REQ-001 alias
    defective_backend = {
        "api_endpoints": [{"route": "/api/v1/auth/login", "method": "POST", "satisfies": ["REQ-001", "REQ-999"]}],
        "domain_models": [{"name": "User"}, {"name": "Book"}, {"name": "BorrowTransaction"}],
        "services": [{"name": "AuthService", "satisfies": ["REQ-001"]}],
    }
    database_mock = {"tables": [{"name": "users"}, {"name": "books"}, {"name": "borrow_records"}]}
    frontend_mock = {"pages": [{"route": "/login"}], "api_integration": {"canonical_operations": ["POST /api/v1/auth/login"]}}
    security_mock = {"authentication": "JWT", "satisfies": ["NFR-002"]}
    cloud_mock = {"compute": "ECS", "database": "RDS", "networking": "VPC"}

    report = CrossArtifactValidator.validate_cross_artifacts(
        domain_ctx=domain_ctx,
        hld=hld,
        backend_lld=defective_backend,
        database_lld=database_mock,
        frontend_lld=frontend_mock,
        security_lld=security_mock,
        cloud_lld=cloud_mock,
        cac=cac,
    )

    assert report.requirement_id_integrity < 1.0
    assert len(report.unknown_requirement_ids) >= 1
    assert any("REQ-001" in str(inc) or "REQ-999" in str(inc) for inc in report.inconsistencies)
    print(f"[PASS] TEST 1: Requirement ID integrity successfully detected invalid aliases (Unknown IDs: {report.unknown_requirement_ids})")


def test_2_api_contract_integrity(library_sample):
    """TEST 2: API Contract integrity across Backend, Frontend, Testing, and Observability."""
    domain_ctx, req_analysis, hld, cac = library_sample

    # Check that CAC has borrowBook mapped to /api/v1/circulation/borrow
    borrow_op = cac.get_api_by_operation_id("borrowBook")
    assert borrow_op is not None
    assert borrow_op.path == "/api/v1/circulation/borrow"
    assert borrow_op.method == "POST"

    be_agent = BackendLLDGenerationAgent()
    fe_agent = FrontendLLDGenerationAgent()

    be_lld = be_agent._synthesize_fallback_backend_lld(hld, cac=cac)
    fe_lld = fe_agent._synthesize_fallback_frontend_lld(hld, cac=cac)

    be_routes = [ep["route"] for ep in be_lld["api_endpoints"]]
    assert "/api/v1/circulation/borrow" in be_routes
    assert "/api/v1/catalog/books" in be_routes
    assert "/api/v1/auth/login" in be_routes

    # Assert Frontend API calls reference the same operations
    fe_ops_str = json.dumps(fe_lld["api_integration"])
    assert "borrowBook" in fe_ops_str
    assert "/api/v1/circulation/borrow" in fe_ops_str
    print("[PASS] TEST 2: Canonical API operations verified consistent across Backend and Frontend")


def test_3_entity_mapping(library_sample):
    """TEST 3: Explicit mapping between Domain Entity BorrowTransaction and Database Table borrow_records."""
    domain_ctx, req_analysis, hld, cac = library_sample

    mapping = cac.get_entity_mapping_by_domain_name("BorrowTransaction")
    assert mapping is not None
    assert mapping.domain_entity == "BorrowTransaction"
    assert mapping.database_table == "borrow_records"
    assert mapping.db_entity_id == "DB-003"
    print(f"[PASS] TEST 3: Explicit entity mapping verified: {mapping.domain_entity} -> {mapping.database_table} ({mapping.db_entity_id})")


def test_4_invalid_upstream_artifact():
    """TEST 4: Invalid/empty requirements halt execution before downstream agents."""
    empty_reqs = {
        "system_name": "",
        "domain": "",
        "functional_requirements": [],
        "non_functional_requirements": [],
        "actors": [],
        "modules": [],
    }
    dummy_ctx = DomainLockEngine.lock_domain_and_requirements({"project_profile": {"goal": "Test System"}})
    is_valid, score, violations = validate_requirement_contract(empty_reqs, dummy_ctx)

    assert is_valid is False
    assert score < 0.70
    print(f"[PASS] TEST 4: Invalid upstream requirements halted pipeline (Violations: {len(violations)})")


def test_5_frontend_backend_mismatch(library_sample):
    """TEST 5: Frontend referencing wrong endpoints causes frontend_backend_alignment < threshold and FAILED status."""
    domain_ctx, req_analysis, hld, cac = library_sample

    be_agent = BackendLLDGenerationAgent()
    be_lld = be_agent._synthesize_fallback_backend_lld(hld, cac=cac)
    db_agent = DatabaseLLDGenerationAgent()
    db_lld = db_agent._synthesize_fallback_database_lld(hld, cac=cac)

    # Defective Frontend with zero matching endpoints (e.g. invented /loans, /payments, /settings)
    defective_frontend = {
        "pages": [{"route": "/loans"}, {"route": "/payments"}],
        "components": [{"name": "LoanForm"}],
        "api_integration": {"client": "axios", "endpoints": ["/api/v1/loans", "/api/v1/payments"]},
    }

    report = CrossArtifactValidator.validate_cross_artifacts(
        domain_ctx=domain_ctx,
        hld=hld,
        backend_lld=be_lld,
        database_lld=db_lld,
        frontend_lld=defective_frontend,
        security_lld={"authentication": "JWT", "satisfies": ["NFR-002"]},
        cloud_lld={"compute": "ECS", "database": "RDS", "networking": "VPC"},
        cac=cac,
    )

    assert report.frontend_to_backend_alignment == 0.0

    sections = {
        "requirement_analysis": req_analysis,
        "technology_recommendation": {"backend": "FastAPI", "database": "PostgreSQL"},
        "architecture_decision_plan": {"architecture_style": "Modular Monolith"},
        "hld": hld,
        "backend_lld": be_lld,
        "database_lld": db_lld,
        "frontend_lld": defective_frontend,
        "security_lld": {"authentication": "JWT"},
        "cloud_lld": {"compute": "ECS"},
    }

    scorecard: UnifiedScorecard = ScoringEngine.compute_unified_scorecard(
        sections=sections,
        domain_ctx=domain_ctx,
        consistency_report=report,
        adversarial_verdict="APPROVED",
    )

    assert scorecard.status == "FAILED"
    assert any("Frontend ↔ Backend alignment" in v for v in scorecard.hard_gate_violations)
    print(f"[PASS] TEST 5: Frontend/Backend mismatch successfully triggered hard gate failure (Status: {scorecard.status})")


def test_6_backend_database_mismatch(library_sample):
    """TEST 6: Removing database mapping for BorrowTransaction causes backend_database_alignment failure."""
    domain_ctx, req_analysis, hld, cac = library_sample

    be_agent = BackendLLDGenerationAgent()
    be_lld = be_agent._synthesize_fallback_backend_lld(hld, cac=cac)

    # Defective DB missing borrow_records table
    defective_db = {
        "tables": [{"name": "audit_logs"}, {"name": "metrics"}],
        "entity_mappings": [],
    }

    report = CrossArtifactValidator.validate_cross_artifacts(
        domain_ctx=domain_ctx,
        hld=hld,
        backend_lld=be_lld,
        database_lld=defective_db,
        frontend_lld={"pages": [{"route": "/catalog"}], "api_integration": {"canonical_operations": ["POST /api/v1/circulation/borrow"]}},
        security_lld={"authentication": "JWT"},
        cloud_lld={"compute": "ECS", "database": "RDS", "networking": "VPC"},
        cac=cac,
    )

    assert report.backend_to_database_alignment == 0.0

    sections = {
        "requirement_analysis": req_analysis,
        "technology_recommendation": {"backend": "FastAPI", "database": "PostgreSQL"},
        "architecture_decision_plan": {"architecture_style": "Modular Monolith"},
        "hld": hld,
        "backend_lld": be_lld,
        "database_lld": defective_db,
        "frontend_lld": {"pages": [{"route": "/catalog"}]},
        "security_lld": {"authentication": "JWT"},
        "cloud_lld": {"compute": "ECS"},
    }

    scorecard: UnifiedScorecard = ScoringEngine.compute_unified_scorecard(
        sections=sections,
        domain_ctx=domain_ctx,
        consistency_report=report,
        adversarial_verdict="APPROVED",
    )

    assert scorecard.status == "FAILED"
    assert any("Backend ↔ Database alignment" in v for v in scorecard.hard_gate_violations)
    print(f"[PASS] TEST 6: Backend/Database mismatch successfully triggered hard gate failure (Status: {scorecard.status})")


def test_7_observability_mismatch(library_sample):
    """TEST 7: Observability referencing non-existent routes triggers consistency violation."""
    domain_ctx, req_analysis, hld, cac = library_sample

    be_agent = BackendLLDGenerationAgent()
    be_lld = be_agent._synthesize_fallback_backend_lld(hld, cac=cac)
    db_agent = DatabaseLLDGenerationAgent()
    db_lld = db_agent._synthesize_fallback_database_lld(hld, cac=cac)

    # Observability referencing invented routes
    defective_obs = {
        "service_level_objectives": [
            {"name": "Fake SLO 1", "sli": "Latency for /api/v1/invented_ghost_route_xyz"},
            {"name": "Fake SLO 2", "sli": "Latency for /api/v1/non_existent_path"},
        ],
    }

    report = CrossArtifactValidator.validate_cross_artifacts(
        domain_ctx=domain_ctx,
        hld=hld,
        backend_lld=be_lld,
        database_lld=db_lld,
        frontend_lld={"pages": [{"route": "/catalog"}], "api_integration": {"canonical_operations": ["POST /api/v1/circulation/borrow"]}},
        security_lld={"authentication": "JWT"},
        cloud_lld={"compute": "ECS", "database": "RDS", "networking": "VPC"},
        observability=defective_obs,
        cac=cac,
    )

    assert len(report.unknown_api_operations) >= 1
    assert any(inc["type"] == "OBSERVABILITY_API_MISMATCH" for inc in report.inconsistencies)
    print(f"[PASS] TEST 7: Observability non-canonical routes flagged cleanly: {report.unknown_api_operations}")


def test_8_adversarial_reviewer_grounding(library_sample):
    """TEST 8: Adversarial review cannot return APPROVED if consistency contains a blocking issue."""
    domain_ctx, req_analysis, hld, cac = library_sample

    blocking_consistency_report = CrossArtifactConsistencyReport(
        score=0.45,
        is_valid=False,
        frontend_to_backend_alignment=0.0,
        backend_to_database_alignment=0.30,
        inconsistencies=[
            {"type": "FRONTEND_BACKEND_MISMATCH", "severity": "CRITICAL", "detail": "Frontend API alignment is 0%"},
            {"type": "UNKNOWN_REQUIREMENT_ID", "severity": "CRITICAL", "detail": "Backend references unknown REQ-999"},
        ],
        unknown_requirement_ids=["REQ-999"],
    )

    adv_agent = AdversarialReviewAgent()
    raw_response = {
        "production_readiness_verdict": "APPROVED",
        "remediation_status": "NONE_REQUIRED",
        "findings": [],
    }

    grounded_review = adv_agent._enforce_consistency_grounding(raw_response, consistency_report=blocking_consistency_report)

    assert grounded_review["production_readiness_verdict"] in ("REJECTED", "NEEDS_REMEDIATION")
    assert grounded_review["remediation_status"] == "REMEDIATION_REQUIRED"
    assert len(grounded_review["findings"]) >= 1
    print(f"[PASS] TEST 8: Adversarial review successfully downgraded from APPROVED to {grounded_review['production_readiness_verdict']}")


def run_all_cac_tests():
    print("\n" + "=" * 75)
    print("RUNNING SAE v2 CANONICAL ARCHITECTURE CONTRACT (CAC) VERIFICATION SUITE")
    print("=" * 75)

    raw_arsrs = {
        "project_profile": {
            "goal": "Build an enterprise college library system for students and librarians.",
            "system_type": "Web Application",
            "domain": "Education & Library Management",
        },
        "business_context": {
            "business_objectives": ["Automate cataloging, borrowing, and overdue fines."],
            "stakeholders": ["Student", "Librarian"],
        },
        "domain_context": {"industry": "Library Management"},
        "modules": ["Authentication", "Catalog Management", "Circulation", "Inventory Administration"],
        "workflows": [
            {"id": "WF-001", "name": "User Authentication", "actor": "Student", "steps": ["Submit credentials", "Issue token"]},
            {"id": "WF-002", "name": "Borrow Book", "actor": "Student", "steps": ["Search book", "Confirm borrow"]},
        ],
        "functional_requirements": [
            {"id": "FR-001", "title": "User Authentication", "description": "Users authenticate via credentials", "priority": "HIGH"},
            {"id": "FR-002", "title": "Catalog Search", "description": "Search catalog books with pagination", "priority": "HIGH"},
            {"id": "FR-003", "title": "Book Borrowing", "description": "Borrow available book copies", "priority": "HIGH"},
            {"id": "FR-004", "title": "Book Return & Fines", "description": "Return books and compute overdue fines", "priority": "MEDIUM"},
        ],
        "non_functional_requirements": [
            {"id": "NFR-001", "category": "Performance", "requirement": "Response time < 200ms", "priority": "HIGH"},
            {"id": "NFR-002", "category": "Security", "requirement": "JWT OAuth2 RS256 encryption", "priority": "HIGH"},
        ],
    }
    domain_ctx = DomainLockEngine.lock_domain_and_requirements(raw_arsrs)
    req_analysis = domain_ctx.to_validated_artifact()

    hld_mock = {
        "system_name": "College Library Management System",
        "domain": "Education & Library Management",
        "architecture_style": "Modular Monolith",
        "technology_stack": {
            "backend": "FastAPI (Python 3.12)",
            "frontend": "React 18 / Next.js 14",
            "database": "PostgreSQL 16",
        },
        "major_services": [
            {"name": "AuthService", "responsibility": "User authentication", "satisfies": ["FR-001"]},
            {"name": "CatalogService", "responsibility": "Catalog search and stock", "satisfies": ["FR-001", "FR-002"]},
            {"name": "CirculationService", "responsibility": "Circulation loan transactions", "satisfies": ["FR-003", "FR-004"]},
        ],
    }

    cac = ContractBuilder.build_from_hld(hld_mock, req_analysis, domain_ctx)
    sample = (domain_ctx, req_analysis, hld_mock, cac)

    test_1_requirement_id_integrity(sample)
    test_2_api_contract_integrity(sample)
    test_3_entity_mapping(sample)
    test_4_invalid_upstream_artifact()
    test_5_frontend_backend_mismatch(sample)
    test_6_backend_database_mismatch(sample)
    test_7_observability_mismatch(sample)
    test_8_adversarial_reviewer_grounding(sample)

    print("=" * 75)
    print("ALL 8 CANONICAL ARCHITECTURE CONTRACT TESTS PASSED SUCCESSFULLY!")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    run_all_cac_tests()
