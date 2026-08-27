"""Unit and integration tests for SAE v2 Lean Architecture Engine."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import pytest
from app.sae.models.response_models import (
    BackendLLDResponse,
    DatabaseLLDResponse,
    FrontendLLDResponse,
    HLDResponse,
    RequirementAnalysisResponse,
    SecurityLLDResponse,
    CloudLLDResponse,
    SoftwareArchitecturePackageResponse,
    TechAdvisorResponse,
)
from app.sae.pipeline import SAEPipeline
from app.sae.providers.llm_provider import OpenRouterProvider


def test_response_models_instantiation():
    """Verify all flat response models instantiate cleanly with valid defaults."""
    req = RequirementAnalysisResponse(system_name="Library App")
    assert req.system_name == "Library App"

    tech = TechAdvisorResponse()
    assert isinstance(tech.backend, dict)

    hld = HLDResponse(architecture_style="Modular Microservices")
    assert hld.architecture_style == "Modular Microservices"

    backend = BackendLLDResponse(api_endpoints=[{"route": "/api/books", "method": "GET"}])
    assert len(backend.api_endpoints) == 1

    db = DatabaseLLDResponse(tables=[{"table_name": "books"}])
    assert len(db.tables) == 1

    fe = FrontendLLDResponse(framework="React")
    assert fe.framework == "React"

    sec = SecurityLLDResponse(compliance=["OWASP"])
    assert len(sec.compliance) == 1

    cld = CloudLLDResponse(cloud_provider="AWS")
    assert cld.cloud_provider == "AWS"

    pkg = SoftwareArchitecturePackageResponse(system_name="Library App")
    assert pkg.system_name == "Library App"


def test_multi_key_role_resolution():
    """Verify per-role API key resolution."""
    keys = ["key_1", "key_2", "key_3", "key_4"]
    provider = OpenRouterProvider(api_keys=keys)

    assert provider.get_api_key_for_role("hld") == "key_1"
    assert provider.get_api_key_for_role("backend") == "key_1"
    assert provider.get_api_key_for_role("database") == "key_2"
    assert provider.get_api_key_for_role("frontend") == "key_3"
    assert provider.get_api_key_for_role("security") == "key_4"
    assert provider.get_api_key_for_role("cloud") == "key_1"


def test_clean_parsing_auto_unwrap():
    """Verify parse_and_validate correctly unwraps nested container dicts without repair corruption."""
    provider = OpenRouterProvider()

    raw_json = '{"backend_lld": {"api_endpoints": [{"route": "/test", "method": "GET"}], "services": [{"name": "TestService"}]}}'
    parsed: BackendLLDResponse = provider.parse_and_validate(raw_json, BackendLLDResponse, agent_name="test")

    assert len(parsed.api_endpoints) == 1
    assert parsed.api_endpoints[0]["route"] == "/test"
    assert len(parsed.services) == 1
    assert parsed.services[0]["name"] == "TestService"


def test_adp_formulation():
    """Verify deterministic ADP formulation."""
    pipeline = SAEPipeline()
    req = {"system_name": "Test System", "domain": "Finance"}
    tech = {"backend": {"selected_option": "FastAPI"}, "database": {"selected_option": "PostgreSQL"}}
    arsrs = {}

    adp = pipeline._formulate_adp(req, tech, arsrs)
    assert adp["system_name"] == "Test System"
    assert adp["technology_stack"]["backend"] == "FastAPI"
    assert adp["technology_stack"]["database"] == "PostgreSQL"
    assert len(adp["major_components"]) >= 3


def test_completeness_calculation():
    """Verify completeness quality computation."""
    from app.sae.utils.domain_lock import DomainLockEngine
    from app.sae.utils.cross_artifact_validator import CrossArtifactConsistencyReport

    pipeline = SAEPipeline()
    sections = {
        "requirement_analysis": {"system_name": "App", "functional_requirements": [1, 2]},
        "hld": {"architecture_style": "Microservices", "major_services": [1]},
        "backend_lld": {"api_endpoints": [1], "services": [1]},
        "database_lld": {},
    }
    dom_ctx = DomainLockEngine.lock_domain({"domain_context": {"industry": "Library"}})
    consistency = CrossArtifactConsistencyReport(score=0.85, is_valid=True)

    rep = pipeline._compute_completeness(sections, domain_ctx=dom_ctx, consistency_report=consistency)
    assert "overall_completeness" in rep
    assert "structural_completeness" in rep

