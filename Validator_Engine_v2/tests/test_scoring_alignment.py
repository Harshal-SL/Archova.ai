"""Authoritative tests verifying exact scoring formulas, weights, verdicts, and fallbacks.

Authoritative Specification:
C = Structural and Technical Correctness (0-100)
R = Architecture Quality Review (0-100)
W = Real-World Architecture Suitability (0-100)
D = Additional verified defect penalties

NORMAL FORMULA:
S = 0.20*C + 0.45*R + 0.35*W - D

LOW-CONFIDENCE BENCHMARK FORMULA:
S = 0.20*C + 0.65*R + 0.15*W - D

VERDICTS:
ACCEPTED: S >= 80, W >= 60, no unresolved critical/high findings
ACCEPTED_WITH_WARNINGS: Acceptance thresholds met, non-critical issues remain
REJECTED: Critical defect or fails acceptance criteria
PROVISIONAL: Mandatory validation incomplete, benchmark/review unavailable
UNRESOLVED: Max rounds exhausted without satisfying acceptance criteria
CRITICAL DEFECT: Force REJECTED and cap final score at 60
"""

import pytest
from unittest.mock import patch

from Validator_Engine_v2.decision.scoring import compute_artifact_score
from Validator_Engine_v2.real_world.scoring import score_real_world_assessments
from Validator_Engine_v2.review.evidence import verify_and_filter_evidence
from Validator_Engine_v2.review.llm_client import ReviewerLLMClient
from Validator_Engine_v2.schemas import (
    ArtifactResult,
    DimensionScore,
    Finding,
    PatternAssessment,
    RealWorldResult,
)


# ── 1. Authoritative Normal Scoring Formula Test ─────────────────────────────

def test_exact_normal_scoring_formula():
    """Verify S = round(0.20*C + 0.45*R + 0.35*W - D)."""
    # C = 93, R = 80, W = 70, D = 5
    # S = 0.20*93 (18.6) + 0.45*80 (36.0) + 0.35*70 (24.5) - 5 = 74.1 -> 74
    dims = [
        DimensionScore(id="d1", label="Scalability", weight=1.0, score=4, rationale="Good"),  # 4/5 * 100 = 80
    ]
    reviewer_res = ArtifactResult(
        artifact="backend",
        score=80,
        verdict="ACCEPTED",
        dimensions=dims,
        findings=[],
        reviewer_status="ok",
    )
    rw_res = RealWorldResult(
        artifact="backend",
        score=70,
        confidence="normal",
        counts={},
        assessments=[],
        references_used=[],
    )
    # deductions: 3 + 3 + 1 = 7 -> C = 93
    l1_fnds = [
        Finding.create(layer="L1", rule_id="L1.1", artifact="backend", severity="medium", message="Med 1"),
        Finding.create(layer="L1", rule_id="L1.2", artifact="backend", severity="medium", message="Med 2"),
        Finding.create(layer="L1", rule_id="L1.3", artifact="backend", severity="low", message="Low 1"),
    ]
    res = compute_artifact_score(
        artifact_name="backend",
        reviewer_result=reviewer_res,
        l0_findings=[],
        l1_findings=l1_fnds,
        real_world_result=rw_res,
        additional_penalty_d=5,
    )
    assert res.c_score == 93
    assert res.r_score == 80
    assert res.w_score == 70
    assert res.penalty_d == 5
    assert res.score == 74


# ── 2. Authoritative Low-Confidence Benchmark Scoring Formula Test ────────────

def test_exact_low_confidence_scoring_formula():
    """Verify S = round(0.20*C + 0.65*R + 0.15*W - D)."""
    # C = 100, R = 85, W = 60, D = 2
    # Low-confidence: 0.20*100 (20) + 0.65*85 (55.25) + 0.15*60 (9.0) - 2 = 82.25 -> 82
    reviewer_res = ArtifactResult(
        artifact="database",
        score=85,
        verdict="ACCEPTED",
        dimensions=[],  # empty dims will use reviewer_res.score = 85
        findings=[],
        reviewer_status="ok",
    )
    rw_res = RealWorldResult(
        artifact="database",
        score=60,
        confidence="low",
        counts={},
        assessments=[],
        references_used=[],
    )
    res = compute_artifact_score(
        artifact_name="database",
        reviewer_result=reviewer_res,
        l0_findings=[],
        l1_findings=[],
        real_world_result=rw_res,
        additional_penalty_d=2,
    )
    assert res.c_score == 100
    assert res.r_score == 85
    assert res.w_score == 60
    assert res.penalty_d == 2
    assert res.score == 82


# ── 3. Unavailable Benchmark Handling ─────────────────────────────────────────

def test_unavailable_benchmark_yields_provisional():
    """Verify unavailable benchmark does not assign W=0 and yields PROVISIONAL."""
    reviewer_res = ArtifactResult(
        artifact="frontend",
        score=90,
        verdict="ACCEPTED",
        dimensions=[],
        findings=[],
        reviewer_status="ok",
    )
    res = compute_artifact_score(
        artifact_name="frontend",
        reviewer_result=reviewer_res,
        l0_findings=[],
        l1_findings=[],
        real_world_result=None,
    )
    assert res.w_score is None
    assert res.verdict == "PROVISIONAL"
    # Does not treat missing W as zero (which would drop score to 0.20*100 + 0.45*90 = 60.5)
    assert res.score > 65


# ── 4. Critical Defect Cap and Rejection ──────────────────────────────────────

def test_critical_defect_caps_at_60_and_forces_rejected():
    """Verify any critical defect caps the score at 60 and forces REJECTED."""
    reviewer_res = ArtifactResult(
        artifact="security",
        score=98,
        verdict="ACCEPTED",
        dimensions=[],
        findings=[],
        reviewer_status="ok",
    )
    rw_res = RealWorldResult(
        artifact="security",
        score=95,
        confidence="normal",
        counts={},
        assessments=[],
        references_used=[],
    )
    critical_fnd = [
        Finding.create(
            layer="L0",
            rule_id="L0.ORPHAN_CRITICAL",
            artifact="security",
            severity="critical",
            message="Critical unauthenticated service binding",
        )
    ]
    res = compute_artifact_score(
        artifact_name="security",
        reviewer_result=reviewer_res,
        l0_findings=critical_fnd,
        l1_findings=[],
        real_world_result=rw_res,
    )
    assert res.score <= 60
    assert res.verdict == "REJECTED"


# ── 5. Real-World Pattern Values and Denominator ──────────────────────────────

def test_real_world_pattern_values_and_scoring():
    """Verify fixed pattern values: ALIGNED=1.0, JUSTIFIED_DIVERGENCE=0.8, PARTIAL=0.5, MISSING=0.0."""
    artifact_data = {
        "caching": {"redis": True},
        "resilience": {"retry_policy": "exponential"},
        "scaling": {"hpa": True},
    }
    assessments = [
        PatternAssessment(
            pattern_id="RW-1", system_name="S1", pattern_name="P1", category="caching", priority=1,
            status="ALIGNED", evidence_path="/caching/redis",
        ),  # 1.0
        PatternAssessment(
            pattern_id="RW-2", system_name="S1", pattern_name="P2", category="resilience", priority=1,
            status="JUSTIFIED_DIVERGENCE", evidence_path="/resilience/retry_policy",
        ),  # 0.8
        PatternAssessment(
            pattern_id="RW-3", system_name="S1", pattern_name="P3", category="scaling", priority=2,
            status="PARTIAL", evidence_path="/scaling/hpa",
        ),  # 0.5
        PatternAssessment(
            pattern_id="RW-4", system_name="S1", pattern_name="P4", category="data", priority=2,
            status="MISSING",
        ),  # 0.0
        PatternAssessment(
            pattern_id="RW-5", system_name="S1", pattern_name="P5", category="security", priority=3,
            status="NOT_APPLICABLE",
            requirement_refs=["REQ-1"],  # Evidence-supported NOT_APPLICABLE excluded from denominator
        ),
    ]
    # Applicable count = 4 (NOT_APPLICABLE excluded)
    # Sum of points = 1.0 + 0.8 + 0.5 + 0.0 = 2.3
    # W = 100 * (2.3 / 4) = 57.5 -> 58
    rw_res, findings = score_real_world_assessments(
        artifact_name="backend",
        assessments=assessments,
        artifact_data=artifact_data,
        references_used=[],
    )
    assert rw_res.score == 58
    assert rw_res.counts["aligned"] == 1
    assert rw_res.counts["justified_divergence"] == 1
    assert rw_res.counts["partial"] == 1
    assert rw_res.counts["missing"] == 1
    assert rw_res.counts["not_applicable"] == 1


# ── 6. Anti-Hallucination Evidence Filtering ──────────────────────────────────

def test_anti_hallucination_evidence_resolution():
    """Verify valid JSON pointers match and fabricated pointers are dropped/capped."""
    artifact_data = {
        "services": [
            {"name": "AuthService", "port": 8080},
        ],
        "database": {
            "type": "PostgreSQL",
        },
    }
    dims = [
        DimensionScore(
            id="d1", label="Security", weight=1.0, score=4,
            evidence_path="/services/0/name", rationale="AuthService present",
        ),
        DimensionScore(
            id="d2", label="Scalability", weight=1.0, score=4,
            evidence_path="/nonexistent/fabrication/pointer", rationale="Fabricated evidence",
        ),
    ]
    findings = [
        Finding.create(
            layer="REVIEW", rule_id="REV.1", artifact="backend", severity="medium",
            message="Valid finding", evidence_path="/database/type",
        ),
        Finding.create(
            layer="REVIEW", rule_id="REV.2", artifact="backend", severity="medium",
            message="Invalid finding", evidence_path="/fake/endpoint",
        ),
    ]
    verified_dims, verified_fnds, dropped = verify_and_filter_evidence(
        dimensions=dims,
        findings=findings,
        artifact_data=artifact_data,
    )
    # Valid pointer verified -> score stays 4
    assert verified_dims[0].score == 4
    # Unverified pointer -> score capped from 4 to 2
    assert verified_dims[1].score == 2
    assert "[Evidence unverified]" in verified_dims[1].rationale
    # Fabricated finding is dropped
    assert len(verified_fnds) == 1
    assert verified_fnds[0].rule_id == "REV.1"
    assert dropped == 1


# ── 7. Free Model Fallback Sequence ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_free_model_fallback_on_retryable_error():
    """Verify LLM client iterates through free fallback models upon 429/503/timeout."""
    client = ReviewerLLMClient(
        model="google/gemini-2.0-flash-exp:free",
        fallback_models=["meta-llama/llama-3.3-70b-instruct:free"],
        api_key="test-key",
        mock_mode="0",
    )
    call_records = []

    async def fake_post(self, url, headers=None, json=None, **kwargs):
        model = json.get("model")
        call_records.append(model)
        from unittest.mock import MagicMock
        mock_resp = MagicMock()
        if model == "google/gemini-2.0-flash-exp:free":
            mock_resp.status_code = 429
            return mock_resp
        elif model == "meta-llama/llama-3.3-70b-instruct:free":
            mock_resp.status_code = 200
            mock_resp.raise_for_status = lambda: None
            mock_resp.json = lambda: {
                "choices": [{
                    "message": {
                        "content": '{"dimensions": [{"id": "scalability", "score": 4, "rationale": "Good"}], "findings": [], "assessments": []}'
                    }
                }]
            }
            return mock_resp
        mock_resp.status_code = 500
        return mock_resp

    with patch("httpx.AsyncClient.post", new=fake_post):
        data, status = await client.call_review(
            artifact_name="backend",
            artifact_data={"services": []},
            rubric={"dimensions": []},
            user_prompt="Evaluate backend",
        )
        assert status == "ok"
        assert data is not None
        assert client.last_model_used == "meta-llama/llama-3.3-70b-instruct:free"
        assert len(call_records) == 2
        assert call_records[0] == "google/gemini-2.0-flash-exp:free"
        assert call_records[1] == "meta-llama/llama-3.3-70b-instruct:free"
