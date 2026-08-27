"""Comprehensive Unit and Integration Tests for SAE Quality Gates & Architectural Fixes.

Validates:
  1. Domain Lock & Canonical Requirements immutability
  2. HLD Quality Gate & Self-Healing Repair
  3. Cross-Artifact Consistency Engine
  4. Adversarial Remediation Loop
  5. 3-Tier Scoring & Hard Quality Gate Enforcement (eliminates contradictory metrics)
"""

import io
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.sae.utils.domain_lock import DomainContext, DomainLockEngine
from app.sae.utils.hld_quality_gate import HLDQualityGate, HLDQualityReport
from app.sae.utils.cross_artifact_validator import CrossArtifactValidator, CrossArtifactConsistencyReport
from app.sae.utils.remediation_engine import RemediationEngine, RemediationPlan
from app.sae.utils.scoring_engine import ScoringEngine, UnifiedScorecard


def test_domain_lock_and_canonical_requirements():
    """Test domain identification and canonical requirement normalization."""
    raw_arsrs = {
        "project_profile": {
            "goal": "Build an online college library management system for students and librarians",
            "domain": "Education",
        },
        "domain_context": {
            "industry": "Higher Education & Library Services",
        },
        "functional_requirements": [
            {"id": "FR-1", "title": "Book Search", "description": "Students shall search book catalog by ISBN, author, title."},
            {"id": "FR-2", "title": "Borrow Book", "description": "Students shall borrow available books with due date tracking."},
        ],
        "non_functional_requirements": [
            {"id": "NFR-1", "title": "Latency", "description": "API response time under 200ms."},
        ],
    }

    ctx = DomainLockEngine.lock_domain_and_requirements(raw_arsrs)
    assert "Library" in ctx.domain_name, f"Expected Library domain, got {ctx.domain_name}"
    assert ctx.domain_key == "library"
    assert ctx.canonical_requirements[0].id.startswith("FR-") or ctx.canonical_requirements[0].id.startswith("REQ-"), "Expected stable FR-XXX prefix"

    quality = DomainLockEngine.validate_requirement_quality(ctx)
    assert quality["is_healthy"] is True
    assert quality["quality_score"] >= 0.75
    print("[PASS] Domain Lock & Canonical Requirements Verified")


def test_hld_quality_gate_and_repair():
    """Test HLD quality evaluation and self-healing repair loop."""
    domain_ctx = DomainLockEngine.lock_domain_and_requirements({
        "domain_context": {"industry": "Library Management"},
        "project_profile": {"goal": "Library System"},
    })

    tech_rec = {"backend": {"selected": "FastAPI"}, "database": {"selected": "PostgreSQL"}}
    adp = {"architecture_style": "Modular Monolith"}

    # 1. Defective / Sparse HLD (Simulating LLM output where only 1 field was populated)
    sparse_hld = {
        "architecture_style": "Modular Monolith",
        "rag_metadata": {"sources": ["test.md"]},
    }

    initial_report = HLDQualityGate.evaluate_hld(sparse_hld, domain_ctx)
    assert initial_report.is_valid is False, "Sparse HLD should fail quality gate"
    assert initial_report.score < 0.50, f"Sparse HLD score ({initial_report.score}) should be low"

    # 2. Self-Healing Repair
    repaired_hld, repaired_report = HLDQualityGate.synthesize_domain_archetype_hld(domain_ctx, tech_rec, adp), None
    repaired_report = HLDQualityGate.evaluate_hld(repaired_hld, domain_ctx)

    assert repaired_report.is_valid is True, "Repaired HLD must pass quality gate"
    assert repaired_report.score >= 0.80, f"Repaired HLD score ({repaired_report.score}) must be >= 0.80"
    assert repaired_report.service_count >= 4, "Repaired HLD must decompose into at least 4 services"
    print(f"[PASS] HLD Quality Gate & Self-Repair Verified (Score: {initial_report.score:.2f} -> {repaired_report.score:.2f})")


def test_cross_artifact_consistency():
    """Test deterministic multi-way consistency validation between HLD, Backend, DB, Frontend, Security, Cloud."""
    domain_ctx = DomainLockEngine.lock_domain_and_requirements({
        "domain_context": {"industry": "Library Management"},
        "project_profile": {"goal": "College Library System"},
    })

    req_ids = domain_ctx.get_req_ids()
    fr1 = req_ids[0] if req_ids else "FR-001"

    hld = {
        "major_services": [
            {"name": "Catalog & Search Service", "satisfies": [fr1]},
            {"name": "Circulation & Borrowing Service", "satisfies": [fr1]},
            {"name": "Authentication Service", "satisfies": [fr1]},
        ],
        "communication_patterns": [{"pattern": "REST / JSON"}],
        "data_strategy": {"database": "PostgreSQL"},
    }

    backend_lld = {
        "api_endpoints": [
            {"path": "/api/v1/catalog/books", "method": "GET", "satisfies": [fr1]},
            {"path": "/api/v1/circulation/borrow", "method": "POST", "satisfies": [fr1]},
            {"path": "/api/v1/auth/login", "method": "POST", "satisfies": [fr1]},
        ],
        "domain_models": [
            {"name": "Book", "fields": ["id", "isbn", "title"]},
            {"name": "BorrowTransaction", "fields": ["id", "book_id", "user_id"]},
        ],
        "security_config": {"auth": "JWT Token validation middleware"},
    }

    database_lld = {
        "tables": [
            {"name": "books", "columns": ["id", "isbn", "title"]},
            {"name": "borrow_transactions", "columns": ["id", "book_id", "user_id"]},
        ],
    }

    frontend_lld = {
        "pages": [{"name": "CatalogSearch", "route": "/catalog"}],
        "api_integration": {"canonical_operations": ["POST /api/v1/circulation/borrow", "GET /api/v1/catalog/books", "POST /api/v1/auth/login"]},
    }

    security_lld = {
        "authentication": {"type": "JWT", "rbac": True},
    }

    cloud_lld = {
        "compute": {"type": "Kubernetes", "cluster": "EKS"},
        "database": {"type": "RDS PostgreSQL Multi-AZ"},
        "networking": {"vpc": "Multi-AZ VPC with public and private subnets, TLS Ingress"},
    }

    report = CrossArtifactValidator.validate_cross_artifacts(
        domain_ctx=domain_ctx,
        hld=hld,
        backend_lld=backend_lld,
        database_lld=database_lld,
        frontend_lld=frontend_lld,
        security_lld=security_lld,
        cloud_lld=cloud_lld,
    )

    print(f"DEBUG consistency report: score={report.score}, hld_backend={report.hld_to_backend_alignment}, be_db={report.backend_to_database_alignment}, fe_be={report.frontend_to_backend_alignment}, sec={report.security_to_backend_alignment}, cloud={report.cloud_to_architecture_alignment}, trace={report.traceability_coverage}")
    assert report.is_valid is True, f"Expected consistency report to pass, score: {report.score}"
    print(f"[PASS] Cross-Artifact Consistency Engine Verified (Score: {report.score:.2f})")


def test_adversarial_remediation_loop():
    """Test adversarial finding extraction and automated remediation loop."""
    domain_ctx = DomainLockEngine.lock_domain_and_requirements({
        "domain_context": {"industry": "Library Management"},
    })

    adversarial_review = {
        "production_readiness_verdict": "REJECTED",
        "single_points_of_failure": [
            "Single instance database without replication or automated failover is a critical SPOF",
            "Single ingress load balancer node without multi-AZ clustering",
        ],
        "unresolved_risks": [
            "Missing circuit breakers could cause cascading service exhaustion",
        ],
    }

    interim_pkg = {
        "cloud_lld": {"compute": {"type": "Single VM"}, "storage": {"database": "Local SQLite"}},
        "backend_lld": {"security_config": {}},
    }

    plan = RemediationEngine.create_remediation_plan(adversarial_review)
    assert plan.total_findings == 3
    assert "cloud_lld" in plan.affected_artifacts
    assert "backend_lld" in plan.affected_artifacts

    remediated_pkg, remediated_review = RemediationEngine.apply_remediation(
        plan=plan,
        interim_package=interim_pkg,
        domain_ctx=domain_ctx,
    )

    assert remediated_review["production_readiness_verdict"] == "APPROVED_AFTER_REMEDIATION"
    assert len(remediated_review["remediations_applied"]) >= 2
    assert "Multi-AZ" in str(remediated_pkg["cloud_lld"])
    assert "Circuit Breaker" in str(remediated_pkg["backend_lld"])
    print("[PASS] Adversarial Review Remediation Loop Verified")


def test_unified_scoring_and_hard_gates():
    """Test that scoring strictly enforces hard gates and eliminates metric contradictions."""
    domain_ctx = DomainLockEngine.lock_domain_and_requirements({
        "domain_context": {"industry": "Library Management"},
    })

    consistency_report = CrossArtifactConsistencyReport(
        score=0.85,
        is_valid=True,
        traceability_coverage=0.90,
    )

    # Scenario A: Broken HLD (0.08) - MUST CAP production readiness and set DEGRADED
    broken_sections = {
        "requirement_analysis": {"functional_requirements": [{"id": "REQ-1"} for _ in range(5)], "non_functional_requirements": [{"id": "REQ-6"}]},
        "technology_recommendation": {"backend": {"selected": "FastAPI"}, "database": {"selected": "PostgreSQL"}, "frontend": {"selected": "React"}, "authentication": {"selected": "JWT"}},
        "hld": {"rag_metadata": {"sources": ["test.md"]}},  # Broken HLD!
        "backend_lld": {"api_endpoints": [{"path": "/api"}]},
        "database_lld": {"tables": [{"table_name": "books"}]},
    }

    broken_scorecard = ScoringEngine.compute_unified_scorecard(
        sections=broken_sections,
        domain_ctx=domain_ctx,
        consistency_report=consistency_report,
        adversarial_verdict="APPROVED",
    )

    assert broken_scorecard.hard_gates["hld_quality_gate_passed"] is False
    assert broken_scorecard.production_readiness_score <= 0.30, f"Production readiness ({broken_scorecard.production_readiness_score}) should be capped <= 0.30 when HLD is broken"
    assert broken_scorecard.status in ("DEGRADED", "FAILED"), f"Status should be DEGRADED or FAILED, got {broken_scorecard.status}"
    assert len(broken_scorecard.hard_gate_violations) > 0

    # Scenario B: High Quality Complete Architecture - MUST PASS HEALTHY
    healthy_sections = {
        "requirement_analysis": {"functional_requirements": [{"id": f"REQ-{i}"} for i in range(1, 6)], "non_functional_requirements": [{"id": "REQ-6"}]},
        "technology_recommendation": {"backend": {"s": 1}, "frontend": {"s": 1}, "database": {"s": 1}, "authentication": {"s": 1}},
        "architecture_decision_plan": {"architecture_style": "Modular Monolith"},
        "hld": {
            "major_services": [{"name": f"Service {i}"} for i in range(1, 5)],
            "communication_patterns": [{"p": "REST"}],
            "data_strategy": {"db": "Postgres"},
            "security_overview": {"auth": "JWT"},
        },
        "backend_lld": {"api_endpoints": [{"path": "/api/v1/test"} for _ in range(4)], "domain_models": [{"name": "M1"}, {"name": "M2"}, {"name": "M3"}]},
        "database_lld": {"tables": [{"table_name": "t1"}, {"table_name": "t2"}, {"table_name": "t3"}]},
        "frontend_lld": {"components": [{"name": "C1"}, {"name": "C2"}, {"name": "C3"}]},
        "security_lld": {"threat_model": [{"t": "T1"}]},
        "cloud_lld": {"compute": {"k8s": True}, "cost_estimation": {"total": 500}},
        "testing_strategy": {"load_testing": {"traffic_model": {"concurrent_users": 500}}},
        "observability": {"service_level_objectives": [{"slo": "99.9% uptime"}, {"slo": "p95 < 200ms"}]},
        "runbooks": {"disaster_recovery": {"steps": ["restore"]}},
    }

    healthy_scorecard = ScoringEngine.compute_unified_scorecard(
        sections=healthy_sections,
        domain_ctx=domain_ctx,
        consistency_report=consistency_report,
        adversarial_verdict="APPROVED",
    )

    assert healthy_scorecard.status == "HEALTHY", f"Expected HEALTHY, got {healthy_scorecard.status}"
    assert healthy_scorecard.production_readiness_score >= 0.75
    assert healthy_scorecard.artifact_quality_score >= 0.80
    assert healthy_scorecard.overall_composite_score >= 0.80
    print("[PASS] Unified 3-Tier Scoring & Hard Quality Gates Verified")


def run_all_tests():
    print("\n" + "=" * 70)
    print("RUNNING SAE ARCHITECTURAL QUALITY GATE & REMEDIATION TESTS")
    print("=" * 70)
    test_domain_lock_and_canonical_requirements()
    test_hld_quality_gate_and_repair()
    test_cross_artifact_consistency()
    test_adversarial_remediation_loop()
    test_unified_scoring_and_hard_gates()
    print("=" * 70)
    print("ALL SAE ARCHITECTURAL TESTS PASSED SUCCESSFULLY!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_all_tests()
