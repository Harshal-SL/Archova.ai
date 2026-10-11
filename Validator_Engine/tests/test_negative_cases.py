"""Controlled Negative and Defect Injection Tests for Validator Engine."""

import copy
import json
from pathlib import Path
import pytest

from Validator_Engine.engine import ValidatorEngine
from Validator_Engine.models.finding_models import FindingCategory, FindingSeverity
from Validator_Engine.models.input_models import ArchitecturePackageInput
from Validator_Engine.validators.cross_artifact_validator import CrossArtifactValidator
from Validator_Engine.validators.nfr_quality_validator import NFRQualityValidator
from Validator_Engine.validators.red_team_reviewer import RedTeamReviewer
from Validator_Engine.validators.requirement_aligner import RequirementAligner
from Validator_Engine.validators.structural_validator import StructuralValidator

FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "ai_engine"
    / "output"
    / "run_20261004_205308_gen_1fc86766b1a5"
    / "10_architecture_package.json"
)


@pytest.fixture
def real_package() -> dict:
    assert FIXTURE_PATH.exists(), f"Fixture not found at {FIXTURE_PATH}"
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_negative_structural_missing_backend(real_package: dict):
    """Defect: Remove backend LLD entirely."""
    defective = copy.deepcopy(real_package)
    del defective["llds"]["backend"]

    pkg = ArchitecturePackageInput(data=defective)
    validator = StructuralValidator()
    report = validator.validate(pkg)

    assert not report.is_valid
    assert any("llds.backend" in s for s in report.missing_sections)
    assert any(f.id == "STRUCT-MISSING-LLD-BACKEND" for f in report.findings)


def test_negative_requirement_untraced(real_package: dict):
    """Defect: Introduce a phantom requirement with zero matching services, endpoints, or tables."""
    defective = copy.deepcopy(real_package)
    defective["arsrs"]["functional_requirements"].append({
        "id": "FR-999",
        "title": "Quantum Teleportation of physical cargo pods",
        "description": "System shall beam solid physical cargo across sub-atomic wormholes",
    })

    pkg = ArchitecturePackageInput(data=defective)
    aligner = RequirementAligner()
    report = aligner.validate(pkg)

    assert "FR-999" in report.uncovered_requirement_ids
    assert not report.is_aligned
    assert any(f.requirement_id == "FR-999" for f in report.findings)


def test_negative_cross_artifact_missing_table(real_package: dict):
    """Defect: Model bound to non-existent database table."""
    defective = copy.deepcopy(real_package)
    # Backend domain model bound to missing table
    be_data = defective["llds"]["backend"]["data"]
    be_data["domain_models"] = [{
        "name": "PhantomAuditLog",
        "database_table": "tbl_phantom_audit_logs_v99",
    }]

    pkg = ArchitecturePackageInput(data=defective)
    validator = CrossArtifactValidator()
    report = validator.validate(pkg)

    assert len(report.missing_entity_mappings) > 0
    assert any("PhantomAuditLog" in s for s in report.missing_entity_mappings)
    assert any(f.id.startswith("CONSIST-DB-TABLE-MISSING") for f in report.findings)


def test_negative_cross_artifact_domain_drift(real_package: dict):
    """Defect: Table from completely unrelated domain (classroom attendance)."""
    defective = copy.deepcopy(real_package)
    defective["llds"]["database"]["data"]["tables"].append({
        "name": "classroom_attendance_records",
        "description": "Student daily roll call attendance tracking",
    })

    pkg = ArchitecturePackageInput(data=defective)
    validator = CrossArtifactValidator()
    report = validator.validate(pkg)

    assert any(f.id.startswith("CONSIST-DOMAIN-DRIFT") for f in report.findings)


def test_negative_nfr_missing_ha(real_package: dict):
    """Defect: Cloud LLD lacks Multi-AZ deployment."""
    defective = copy.deepcopy(real_package)
    defective["llds"]["cloud"]["data"]["compute"]["service"] = "Single EC2 t2.micro instance"
    defective["llds"]["cloud"]["data"]["compute"]["high_availability"] = "None (Single Zone)"
    defective["llds"]["cloud"]["data"]["networking"]["vpc"] = "Single public subnet in us-east-1a"

    pkg = ArchitecturePackageInput(data=defective)
    validator = NFRQualityValidator()
    report = validator.validate(pkg)

    assert any(f.id == "NFR-PILLAR-001" for f in report.findings)


def test_negative_red_team_spof_detection(real_package: dict):
    """Defect: Single standalone database without standby failover."""
    defective = copy.deepcopy(real_package)
    defective["llds"]["database"]["data"]["backup_and_replication"] = {
        "strategy": "Single SQLite file on local disk without replication",
    }
    defective["llds"]["cloud"]["data"]["database"] = {
        "service": "Standalone SQLite Database",
    }

    pkg = ArchitecturePackageInput(data=defective)
    reviewer = RedTeamReviewer()
    report = reviewer.review(pkg)

    assert any(f.category == FindingCategory.SPOF for f in report.findings)
    assert any("Single Database" in spof.get("title", "") for spof in report.single_points_of_failure)
