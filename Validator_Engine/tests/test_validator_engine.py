"""Comprehensive Integration and Unit Tests for the Validator Engine."""

import json
from pathlib import Path
import pytest

from Validator_Engine.engine import ValidatorEngine
from Validator_Engine.models.input_models import ArchitecturePackageInput
from Validator_Engine.models.output_models import ValidatedArchitectureResponse
from Validator_Engine.validators.cross_artifact_validator import CrossArtifactValidator
from Validator_Engine.validators.nfr_quality_validator import NFRQualityValidator
from Validator_Engine.validators.red_team_reviewer import RedTeamReviewer
from Validator_Engine.validators.requirement_aligner import RequirementAligner
from Validator_Engine.validators.structural_validator import StructuralValidator

FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "ai_engine"
    / "output"
    / "run_20261004_200235_gen_415ece685f85"
    / "10_architecture_package.json"
)


@pytest.fixture
def real_package_data() -> dict:
    assert FIXTURE_PATH.exists(), f"Fixture not found at {FIXTURE_PATH}"
    raw = FIXTURE_PATH.read_text(encoding="utf-8")
    return json.loads(raw)


@pytest.fixture
def package_input(real_package_data: dict) -> ArchitecturePackageInput:
    return ArchitecturePackageInput(
        package_id=real_package_data.get("generation_id", "test_pkg"),
        data=real_package_data,
    )


def test_structural_validator(package_input: ArchitecturePackageInput):
    validator = StructuralValidator()
    report = validator.validate(package_input)
    assert report is not None
    assert 0.0 <= report.score <= 1.0
    assert isinstance(report.missing_sections, list)
    assert isinstance(report.placeholder_items, list)


def test_requirement_aligner(package_input: ArchitecturePackageInput):
    aligner = RequirementAligner()
    report = aligner.validate(package_input)
    assert report is not None
    assert report.total_requirements > 0
    assert 0.0 <= report.traceability_ratio <= 1.0
    assert isinstance(report.traceability_matrix, list)


def test_cross_artifact_validator(package_input: ArchitecturePackageInput):
    validator = CrossArtifactValidator()
    report = validator.validate(package_input)
    assert report is not None
    assert 0.0 <= report.score <= 1.0
    assert 0.0 <= report.frontend_to_backend_alignment <= 1.0
    assert 0.0 <= report.backend_to_database_alignment <= 1.0


def test_nfr_quality_validator(package_input: ArchitecturePackageInput):
    validator = NFRQualityValidator()
    report = validator.validate(package_input)
    assert report is not None
    assert 0.0 <= report.score <= 1.0
    assert report.total_nfrs > 0


def test_red_team_reviewer(package_input: ArchitecturePackageInput):
    reviewer = RedTeamReviewer()
    report = reviewer.review(package_input)
    assert report is not None
    assert report.verdict in ("APPROVED", "APPROVED_WITH_CONDITIONS", "NEEDS_REMEDIATION", "REJECTED")
    assert isinstance(report.single_points_of_failure, list)


def test_end_to_end_validator_engine(real_package_data: dict):
    engine = ValidatorEngine()
    response: ValidatedArchitectureResponse = engine.validate(real_package_data)

    assert response is not None
    assert response.system_name != ""
    assert response.status in ("HEALTHY", "DEGRADED", "NEEDS_REMEDIATION", "FAILED")

    # Verify all nested reports are populated via accessors
    assert response.scorecard is not None
    assert 0.0 <= response.scorecard.overall_composite_score <= 1.0
    assert 0.0 <= response.scorecard.production_readiness_score <= 1.0

    assert response.structural_validation is not None
    assert response.requirement_alignment is not None
    assert response.cross_artifact_consistency is not None
    assert response.nfr_validation is not None
    assert response.real_world_evidence is not None
    assert response.red_team_review is not None

    # Verify Decision Provenance
    assert len(response.decision_provenance) > 0
    assert all(item.decision_id != "" for item in response.decision_provenance)

    # Verify Remediation Plan
    assert response.remediation_plan is not None
    assert isinstance(response.remediation_plan.actions, list)

    # Verify Canonical JSON Contract Schema
    json_output = response.model_dump(mode="json")
    assert isinstance(json_output, dict)
    assert "architecture" in json_output
    assert "validation" in json_output
    assert "evidence" in json_output
    assert "explainability" in json_output
    assert "remediation" in json_output
    assert "metadata" in json_output

    assert "scorecard" in json_output["validation"]
    assert "decisions_provenance" in json_output["explainability"]
    assert "actions" in json_output["remediation"]
