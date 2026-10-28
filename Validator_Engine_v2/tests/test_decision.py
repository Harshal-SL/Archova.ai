"""Unit tests for Scoring, Caps, Feedback, and History Diffing."""

import pytest

from Validator_Engine_v2.decision.feedback import build_artifact_feedback
from Validator_Engine_v2.decision.history import diff_iteration_corrections
from Validator_Engine_v2.decision.scoring import compute_artifact_score
from Validator_Engine_v2.schemas import (
    ArtifactResult,
    DimensionScore,
    Finding,
    Iteration,
    compute_finding_id,
)


def test_scoring_weights_and_deductions():
    # 2 dimensions with weights 0.6 (score 4) and 0.4 (score 5)
    # base = 100 * (0.6*4/5 + 0.4*5/5) = 100 * (0.48 + 0.40) = 88
    dims = [
        DimensionScore(id="d1", label="D1", weight=0.6, score=4, rationale="Good"),
        DimensionScore(id="d2", label="D2", weight=0.4, score=5, rationale="Great"),
    ]
    reviewer_res = ArtifactResult(
        artifact="backend",
        score=88,
        verdict="ACCEPTED",
        dimensions=dims,
        findings=[],
        reviewer_status="ok",
    )

    # L1 high deduction: -8
    l1_findings = [
        Finding.create(
            layer="L1",
            rule_id="L1.OPENAPI_MISSING_ENDPOINT",
            artifact="backend",
            severity="high",
            message="Missing endpoint",
        )
    ]

    from Validator_Engine_v2.schemas import RealWorldResult
    rw_res = RealWorldResult(
        artifact="backend",
        score=80,
        confidence="normal",
        counts={},
        assessments=[],
        references_used=[],
    )

    final_res = compute_artifact_score(
        "backend",
        reviewer_res,
        l0_findings=[],
        l1_findings=l1_findings,
        real_world_result=rw_res,
    )
    # C = 100 - 8 (high) = 92
    # R = 88
    # W = 80
    # S = round(0.20*92 + 0.45*88 + 0.35*80) = round(18.4 + 39.6 + 28.0) = 86
    assert final_res.c_score == 92
    assert final_res.r_score == 88
    assert final_res.w_score == 80
    assert final_res.penalty_d == 0
    assert final_res.score == 86
    # Because there is a high-severity finding unresolved, verdict must be REJECTED
    assert final_res.verdict == "REJECTED"


def test_critical_cap_forces_rejected_at_60():
    # Reviewer gave score 95
    reviewer_res = ArtifactResult(
        artifact="database",
        score=95,
        verdict="ACCEPTED",
        dimensions=[DimensionScore(id="d1", label="D1", weight=1.0, score=5, rationale="Perfect")],
        findings=[],
        reviewer_status="ok",
    )

    # But L1 has a critical syntax error finding
    critical_fnd = [
        Finding.create(
            layer="L1",
            rule_id="L1.MIGRATION_SYNTAX_ERROR",
            artifact="database",
            severity="critical",
            message="Syntax error in migration",
        )
    ]

    final_res = compute_artifact_score("database", reviewer_res, l0_findings=[], l1_findings=critical_fnd)
    # Cap at 60 and forced REJECTED
    assert final_res.score <= 60
    assert final_res.verdict == "REJECTED"


def test_reviewer_unavailable_provisional():
    reviewer_res = ArtifactResult(
        artifact="cloud",
        score=50,
        verdict="PROVISIONAL",
        dimensions=[],
        findings=[],
        reviewer_status="unavailable",
    )

    # 1 medium finding (-3)
    l1_findings = [
        Finding.create(
            layer="L1",
            rule_id="L1.DOCKERFILE_MISSING_HEALTHCHECK",
            artifact="cloud",
            severity="medium",
            message="No healthcheck",
        )
    ]

    final_res = compute_artifact_score("cloud", reviewer_res, l0_findings=[], l1_findings=l1_findings)
    assert final_res.reviewer_status == "unavailable"
    # Incomplete reviewer returns PROVISIONAL with formula score: 0.20*97 + 0.80*50 = 59
    assert final_res.c_score == 97
    assert final_res.r_score == 50
    assert final_res.score == 59


def test_feedback_builder():
    dims = [
        DimensionScore(
            id="concurrency",
            label="Concurrency",
            weight=0.5,
            score=1,
            missing=["Row locking", "Redis hold"],
            rationale="Defective",
        )
    ]
    finding = Finding.create(
        layer="REVIEW",
        rule_id="REVIEW.CONCURRENCY",
        artifact="backend",
        severity="high",
        message="Race condition detected",
        evidence_path="/api_endpoints",
        suggested_fix="Use SELECT FOR UPDATE",
    )
    res = ArtifactResult(
        artifact="backend",
        score=40,
        verdict="REJECTED",
        dimensions=dims,
        findings=[finding],
    )

    feedback = build_artifact_feedback(res)
    assert feedback["artifact"] == "backend"
    assert feedback["score"] == 40
    assert "concurrency" in feedback["failed_dimensions"]
    assert "Row locking" in feedback["missing"]
    assert len(feedback["findings"]) == 1
    assert "SELECT FOR UPDATE" in feedback["findings"][0]["fix"]


def test_history_diffing():
    # Iteration 1 has defects F1 and F2
    f1 = Finding.create("REVIEW", "RULE.1", "backend", "high", "Defect 1", evidence_path="/path/1")
    f2 = Finding.create("REVIEW", "RULE.2", "backend", "medium", "Defect 2", evidence_path="/path/2")

    iter1 = Iteration(
        n=1,
        results={
            "backend": ArtifactResult(
                artifact="backend",
                score=62,
                verdict="REJECTED",
                findings=[f1, f2],
            )
        },
        corrections=[],
        started_at="2026-10-25T10:00:00Z",
        finished_at="2026-10-25T10:01:00Z",
    )

    # Iteration 2 resolved F1, still has F2, and introduced F3
    f3 = Finding.create("REVIEW", "RULE.3", "backend", "low", "Defect 3", evidence_path="/path/3")
    iter2_results = {
        "backend": ArtifactResult(
            artifact="backend",
            score=82,
            verdict="ACCEPTED",
            findings=[f2, f3],
        )
    }

    corrections = diff_iteration_corrections(
        prev_iteration=iter1,
        curr_results=iter2_results,
        regenerated_artifacts=["backend"],
        regenerated_with_feedback=True,
    )

    assert len(corrections) == 1
    c = corrections[0]
    assert c.artifact == "backend"
    assert c.score_before == 62
    assert c.score_after == 82
    assert f1.id in c.resolved
    assert f2.id in c.unresolved
    assert f3.id in c.new_findings
    assert c.regenerated_with_feedback is True
