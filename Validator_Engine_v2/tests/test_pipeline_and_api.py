"""Integration tests for ValidationPipeline, fake AI Engine client, persistence, and FastAPI endpoints."""

import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import pytest
from fastapi.testclient import TestClient

from Validator_Engine_v2.ai_engine_client import (
    AIEngineClient,
    RegenerationAdapter,
    SimulationRegenerationAdapter,
)
from Validator_Engine_v2.config import config
from Validator_Engine_v2.main import app
from Validator_Engine_v2.pipeline import ValidationPipeline
from Validator_Engine_v2.review.llm_client import ReviewerLLMClient
from Validator_Engine_v2.review.reviewer import Reviewer
from Validator_Engine_v2.schemas import ArtifactResult, DimensionScore, Finding
from Validator_Engine_v2.storage.report_store import ReportStore

# Fixture: synthetic_clean_fixture (hand-augmented clean architecture package for golden-path pipeline verification)
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_package.json"


@pytest.fixture
def clean_package() -> dict:
    """Fixture role: synthetic_clean_fixture.
    Provides hand-augmented clean architecture package with complete schema tables, locking semantics, and scaffolds."""
    assert FIXTURE_PATH.exists()
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def defective_package(clean_package: dict) -> dict:
    pkg = copy.deepcopy(clean_package)
    pkg["generation_id"] = "gen_test_defect"
    pkg["prompt"] = "Build a Smart Parking Reservation System with double-booking defect"
    if "arsrs" in pkg and isinstance(pkg["arsrs"], dict):
        pkg["arsrs"]["system_name"] = "Smart Parking Reservation System"
        pkg["arsrs"]["domain"] = "Smart Parking"
    # Strip row-level locking & Redlock
    s = (
        json.dumps(pkg)
        .replace("SELECT FOR UPDATE", "standard SELECT")
        .replace("select for update", "standard SELECT")
        .replace("Redis Redlock", "in-memory session state")
        .replace("Redlock", "standard cache")
    )
    return json.loads(s)


class FakeAIEngineClient(AIEngineClient):
    """Fake AI Engine Client providing canned packages in-memory."""

    def __init__(self, package: dict, adapter: Optional[RegenerationAdapter] = None) -> None:
        super().__init__(base_url="http://fake-ai-engine:8000", regeneration_adapter=adapter or SimulationRegenerationAdapter())
        self.stored_package = copy.deepcopy(package)

    async def fetch_package(self, generation_id: str) -> Optional[dict]:
        return copy.deepcopy(self.stored_package)


# ── Scenario A: All Accepted on Round 1 ───────────────────────────────────────

@pytest.mark.asyncio
async def test_pipeline_all_accepted_round_1(clean_package: dict, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(config, "ALLOW_MOCK_ACCEPT", 1)
    fake_client = FakeAIEngineClient(clean_package)
    client_llm = ReviewerLLMClient(mock_mode="1")
    reviewer = Reviewer(llm_client=client_llm)

    pipeline = ValidationPipeline(ai_engine_client=fake_client, reviewer=reviewer)
    report = await pipeline.execute_pipeline(clean_package["generation_id"])

    assert report.final_status == "ACCEPTED"
    assert len(report.iterations) == 1
    assert all(r.verdict == "ACCEPTED" for r in report.iterations[0].results.values())


# ── Scenario B: LLD Rejected then Accepted on Round 2 ─────────────────────────

@pytest.mark.asyncio
async def test_pipeline_lld_rejected_then_accepted(defective_package: dict, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(config, "ALLOW_MOCK_ACCEPT", 1)
    # SimulationRegenerationAdapter fixes the defect on round 2
    adapter = SimulationRegenerationAdapter()
    fake_client = FakeAIEngineClient(defective_package, adapter=adapter)

    client_llm = ReviewerLLMClient(mock_mode="1")
    reviewer = Reviewer(llm_client=client_llm)

    pipeline = ValidationPipeline(ai_engine_client=fake_client, reviewer=reviewer)
    report = await pipeline.execute_pipeline(defective_package["generation_id"])

    assert len(report.iterations) == 2
    # Iteration 1 had corrections triggered
    assert len(report.iterations[1].corrections) > 0
    # Artifacts accepted on second round
    assert report.final_status == "ACCEPTED"


# ── Scenario C: Never Accepted -> UNRESOLVED after MAX_ROUNDS ─────────────────

class BrokenRegenerationAdapter(RegenerationAdapter):
    """Stubborn adapter that never fixes the defect."""

    async def regenerate(self, generation_id: str, rejected_artifacts: list, feedback: dict, current_package: dict):
        return current_package, False


@pytest.mark.asyncio
async def test_pipeline_never_accepted_unresolved(defective_package: dict):
    stubborn_adapter = BrokenRegenerationAdapter()
    fake_client = FakeAIEngineClient(defective_package, adapter=stubborn_adapter)

    client_llm = ReviewerLLMClient(mock_mode="1")
    reviewer = Reviewer(llm_client=client_llm)

    pipeline = ValidationPipeline(ai_engine_client=fake_client, reviewer=reviewer)
    report = await pipeline.execute_pipeline(defective_package["generation_id"])

    assert len(report.iterations) == config.MAX_ROUNDS
    assert report.final_status == "UNRESOLVED"


# ── Scenario D: Reviewer Unavailable -> PROVISIONAL ───────────────────────────

@pytest.mark.asyncio
async def test_pipeline_reviewer_unavailable_provisional(clean_package: dict):
    fake_client = FakeAIEngineClient(clean_package)
    client_llm = ReviewerLLMClient(mock_mode="unavailable")
    reviewer = Reviewer(llm_client=client_llm)

    pipeline = ValidationPipeline(ai_engine_client=fake_client, reviewer=reviewer)
    report = await pipeline.execute_pipeline(clean_package["generation_id"])

    assert report.final_status == "PROVISIONAL"
    assert report.iterations[0].results["backend"].reviewer_status == "unavailable"


# ── Scenario E: Persistence After Every Iteration ─────────────────────────────

@pytest.mark.asyncio
async def test_persistence_after_iteration(defective_package: dict, tmp_path: Path):
    store = ReportStore(runs_dir=tmp_path)
    from Validator_Engine_v2.storage import report_store
    report_store.runs_dir = tmp_path

    adapter = SimulationRegenerationAdapter()
    fake_client = FakeAIEngineClient(defective_package, adapter=adapter)
    client_llm = ReviewerLLMClient(mock_mode="1")
    reviewer = Reviewer(llm_client=client_llm)
    pipeline = ValidationPipeline(ai_engine_client=fake_client, reviewer=reviewer)

    gen_id = defective_package["generation_id"]
    await pipeline.execute_pipeline(gen_id)

    persisted = store.load_report(gen_id)
    assert persisted is not None
    assert persisted["generation_id"] == gen_id
    assert "iterations" in persisted
    assert "final_package" in persisted


# ── 2. FastAPI Endpoints Tests ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_api_health_endpoint():
    import httpx
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Validator Engine v2"


@pytest.mark.asyncio
async def test_api_direct_validate(clean_package: dict, monkeypatch: pytest.MonkeyPatch):
    import httpx
    monkeypatch.setattr(config, "VALIDATOR_MOCK", "1")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        res = await client.post("/v1/validate", json=clean_package)
        assert res.status_code == 200
        data = res.json()
        assert "generation_id" in data
        assert "final_scores" in data
        assert "iterations" in data


@pytest.mark.asyncio
async def test_api_pipeline_run_and_status(clean_package: dict, monkeypatch: pytest.MonkeyPatch):
    import httpx
    monkeypatch.setattr(config, "VALIDATOR_MOCK", "1")
    gen_id = clean_package["generation_id"]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        res = await client.post(
            "/v1/pipeline/run",
            json={"generation_id": gen_id, "package": clean_package},
        )
        assert res.status_code == 202
        run_data = res.json()
        assert "generation_id" in run_data

        # Poll status
        status_res = await client.get(f"/v1/pipeline/{gen_id}/status")
        assert status_res.status_code == 200
        st_data = status_res.json()
        assert st_data["state"] in ("running", "completed")
