"""Unit tests for Reviewer, Evidence Verification, and Reference Loader."""

import json
from pathlib import Path
import pytest

from Validator_Engine_v2.l0_normalize.normalizer import PackageNormalizer
from Validator_Engine_v2.reference.loader import reference_loader
from Validator_Engine_v2.review.evidence import (
    is_evidence_verified,
    verify_and_filter_evidence,
)
from Validator_Engine_v2.review.llm_client import ReviewerLLMClient
from Validator_Engine_v2.review.reviewer import Reviewer
from Validator_Engine_v2.schemas import DimensionScore, Finding

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_package.json"


@pytest.fixture
def sample_package() -> dict:
    assert FIXTURE_PATH.exists()
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_reference_loader_selection():
    # Tag match for concurrency
    excerpts = reference_loader.select_excerpts(["concurrency", "locking"])
    assert "Concurrency Control" in excerpts
    assert len(excerpts) > 0

    # Tag match for multi-az
    ha_excerpts = reference_loader.select_excerpts(["multi-az", "ha"])
    assert "High Availability" in ha_excerpts or "Multi-AZ" in ha_excerpts


def test_evidence_verification():
    artifact_data = {
        "services": [
            {"name": "OrderService", "description": "Handles retail orders."}
        ],
        "api_endpoints": [
            {"path": "/api/v1/orders", "method": "POST"}
        ],
        "notes": "Uses Redis Redlock for concurrency locking.",
    }

    # 1. Valid JSON pointer
    assert is_evidence_verified("/services/0/name", artifact_data) is True
    assert is_evidence_verified("/api_endpoints/0/path", artifact_data) is True

    # 2. Invalid JSON pointer
    assert is_evidence_verified("/services/99/name", artifact_data) is False
    assert is_evidence_verified("/non_existent_key", artifact_data) is False

    # 3. Valid Quoted snippet
    assert is_evidence_verified("Redis Redlock for concurrency locking", artifact_data) is True

    # 4. Fabricated Quoted snippet
    assert is_evidence_verified("Cassandra distributed counter", artifact_data) is False


def test_verify_and_filter_evidence_dimension_and_finding_caps():
    artifact_data = {
        "services": [{"name": "AuthService"}],
    }

    dimensions = [
        # Verified evidence -> keeps score 5
        DimensionScore(
            id="dim_verified",
            label="Verified Dim",
            weight=0.5,
            score=5,
            evidence_path="/services/0/name",
            rationale="Validly proven in architecture",
        ),
        # Fabricated evidence on score >= 3 -> must be capped at 2
        DimensionScore(
            id="dim_fabricated",
            label="Fabricated Dim",
            weight=0.5,
            score=4,
            evidence_path="/services/fabricated/path",
            rationale="Claimed mechanism not in artifact",
        ),
    ]

    findings = [
        # Verified finding -> kept
        Finding.create(
            layer="REVIEW",
            rule_id="REVIEW.VALID",
            artifact="backend",
            severity="medium",
            message="Valid finding",
            evidence_path="/services/0/name",
        ),
        # Fabricated finding -> dropped
        Finding.create(
            layer="REVIEW",
            rule_id="REVIEW.FABRICATED",
            artifact="backend",
            severity="high",
            message="Fabricated finding without evidence",
            evidence_path="/totally/made/up",
        ),
    ]

    verified_dims, verified_findings, dropped = verify_and_filter_evidence(
        dimensions=dimensions,
        findings=findings,
        artifact_data=artifact_data,
    )

    # Check dimension capping
    assert verified_dims[0].score == 5
    assert verified_dims[1].score == 2
    assert "[Evidence unverified]" in verified_dims[1].rationale

    # Check finding dropping
    assert len(verified_findings) == 1
    assert verified_findings[0].rule_id == "REVIEW.VALID"
    assert dropped == 1


@pytest.mark.asyncio
async def test_reviewer_parallel_with_mock(sample_package: dict):
    normalizer = PackageNormalizer()
    normalized = normalizer.normalize(sample_package)

    client = ReviewerLLMClient(mock_mode="1")
    reviewer = Reviewer(llm_client=client)

    results = await reviewer.review_all_parallel(normalized)

    assert len(results) == 6
    for art in ("hld", "backend", "database", "frontend", "security", "cloud"):
        assert art in results
        res = results[art]
        assert res.reviewer_status == "ok"
        assert res.score >= 0
        assert res.verdict in ("ACCEPTED", "REJECTED")
        assert len(res.dimensions) > 0


@pytest.mark.asyncio
async def test_reviewer_unavailable_mode(sample_package: dict):
    normalizer = PackageNormalizer()
    normalized = normalizer.normalize(sample_package)

    client = ReviewerLLMClient(mock_mode="unavailable")
    reviewer = Reviewer(llm_client=client)

    results = await reviewer.review_all_parallel(normalized)
    for art, res in results.items():
        assert res.reviewer_status == "unavailable"
        assert res.verdict == "PROVISIONAL"
