"""Tests for schemas and Layer 0 Normalizer."""

import json
from pathlib import Path
import pytest

from Validator_Engine_v2.l0_normalize.normalizer import PackageNormalizer
from Validator_Engine_v2.schemas import (
    Finding,
    compute_finding_id,
    DimensionScore,
    ArtifactResult,
    Correction,
    Iteration,
    Report,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_package.json"


@pytest.fixture
def sample_package() -> dict:
    assert FIXTURE_PATH.exists(), f"Fixture missing at {FIXTURE_PATH}"
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_compute_finding_id_stability():
    id1 = compute_finding_id("L0.ORPHAN_REF", "backend", "/api/v1/test", "Test message")
    id2 = compute_finding_id("L0.ORPHAN_REF", "backend", "/api/v1/test", "Test message")
    assert id1 == id2
    assert id1.startswith("fnd_")

    # Whitespace variance should still hash identically
    id3 = compute_finding_id("L0.ORPHAN_REF", "backend", "  /api/v1/test  ", "Test   message")
    assert id1 == id3


def test_schemas_instantiation():
    f = Finding.create(
        layer="L0",
        rule_id="L0.ORPHAN_REF",
        artifact="backend",
        severity="low",
        message="Orphan endpoint found",
    )
    assert f.id.startswith("fnd_")
    assert f.layer == "L0"
    assert f.severity == "low"

    dim = DimensionScore(
        id="dim1",
        label="Requirement Coverage",
        weight=0.2,
        score=4,
        rationale="Strong alignment across all key functional requirements.",
    )
    assert dim.score == 4

    res = ArtifactResult(
        artifact="backend",
        score=85,
        verdict="ACCEPTED",
        dimensions=[dim],
        findings=[f],
        best_dimension="dim1",
    )
    assert res.verdict == "ACCEPTED"


def test_normalizer_on_sample_package(sample_package: dict):
    normalizer = PackageNormalizer()
    normalized = normalizer.normalize(sample_package)

    assert normalized.generation_id == "gen_415ece685f85"
    assert len(normalized.requirements) > 0
    assert any(r.type == "FR" for r in normalized.requirements)
    assert any(r.type == "NFR" for r in normalized.requirements)

    assert len(normalized.components) > 0
    assert len(normalized.endpoints) > 0
    assert len(normalized.tables) > 0
    assert len(normalized.scaffold_files) > 0
    assert "openapi.yaml" in normalized.scaffold_files
    assert "Dockerfile" in normalized.scaffold_files


def test_normalizer_orphan_ref_detection():
    normalizer = PackageNormalizer()
    pkg = {
        "generation_id": "test_orphan",
        "system_name": "Test System",
        "domain": "Test Domain",
        "arsrs": {
            "functional_requirements": [{"id": "FR-1", "title": "Test FR"}],
        },
        "hld": {
            "major_services": [{"name": "AuthService", "responsibility": "Auth"}],
        },
        "llds": {
            "backend": {
                "api_endpoints": [
                    {
                        "path": "/api/v1/unknown",
                        "method": "POST",
                        "service": "NonExistentService",
                    }
                ],
                "services": [{"name": "AuthService"}],
            },
            "database": {
                "tables": [
                    {
                        "name": "orders",
                        "columns": [
                            {"name": "id", "primary_key": True},
                            {"name": "user_id", "foreign_key": "users.id"},
                        ],
                    }
                ]
            },
            "frontend": {
                "api_integration": {
                    "endpoints_consumed": ["/api/v1/missing_endpoint"]
                }
            },
        },
    }

    normalized = normalizer.normalize(pkg)
    orphan_findings = [f for f in normalized.l0_findings if f.rule_id == "L0.ORPHAN_REF"]
    assert len(orphan_findings) >= 3

    artifacts_flagged = {f.artifact for f in orphan_findings}
    assert "backend" in artifacts_flagged
    assert "database" in artifacts_flagged
    assert "frontend" in artifacts_flagged
