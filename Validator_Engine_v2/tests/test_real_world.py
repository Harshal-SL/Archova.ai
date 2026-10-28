"""Unit and integration tests for the Real-World Benchmark layer, L1 honesty, and mock safety."""

import copy
import json
from pathlib import Path
import pytest

from Validator_Engine_v2.config import config
from Validator_Engine_v2.decision.history import diff_iteration_corrections
from Validator_Engine_v2.decision.scoring import compute_artifact_score
from Validator_Engine_v2.l0_normalize.normalizer import PackageNormalizer
from Validator_Engine_v2.l1_evidence.dockerfile_check import check_dockerfile
from Validator_Engine_v2.l1_evidence.migration_check import check_migration
from Validator_Engine_v2.l1_evidence.openapi_check import check_openapi
from Validator_Engine_v2.l1_evidence.terraform_check import check_terraform
from Validator_Engine_v2.real_world.comparator import PatternComparator
from Validator_Engine_v2.real_world.corpus_loader import CorpusLoader, ReferenceDoc
from Validator_Engine_v2.real_world.profile_extractor import (
    ExtractedProfile,
    PatternApplicability,
    ProfileExtractor,
    RealWorldPattern,
)
from Validator_Engine_v2.real_world.scoring import score_real_world_assessments
from Validator_Engine_v2.real_world.selector import SystemSelector
from Validator_Engine_v2.review.llm_client import ReviewerLLMClient
from Validator_Engine_v2.schemas import (
    ArtifactResult,
    DimensionScore,
    Finding,
    Iteration,
    PatternAssessment,
    RealWorldResult,
    ReferenceSystemUsed,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
CORPUS_FIXTURE_DIR = FIXTURES_DIR / "corpus"
REAL_PACKAGE_PATH = FIXTURES_DIR / "real_package_unmodified.json"
SAMPLE_PACKAGE_PATH = FIXTURES_DIR / "sample_package.json"


# ── 1. Corpus Loader & Selector Tests ──────────────────────────────────────────

def test_corpus_loader_and_selector_sample_fixtures():
    loader = CorpusLoader(
        corpus_path=CORPUS_FIXTURE_DIR,
        folders=["category_10_real_world_systems", "domain_architectures"],
    )
    docs = loader.load_corpus()
    assert len(docs) == 3

    # Check sources and headings parsed
    parking_doc = next(d for d in docs if "parking" in d.system_name.lower())
    assert len(parking_doc.sources) > 0
    assert "https://example.com/parking-locking" in parking_doc.sources[0]
    assert any("concurrency" in h.lower() for h in [s["heading"] for s in parking_doc.sections])

    # Test Selection: Parking problem selects Parking Vault
    selector = SystemSelector(top_k=2)
    arsrs_parking = {
        "system_name": "Smart Parking Reservation System",
        "domain": "Smart Parking",
        "non_functional_requirements": [
            {"id": "NFR-1", "name": "Throughput", "metric": "50 requests/sec"},
        ],
    }
    selected = selector.select(docs, arsrs_parking)
    assert len(selected) > 0
    assert selected[0].doc.id == parking_doc.id
    assert any("domain" in r.lower() or "parking" in r.lower() for r in selected[0].match_reasons)
    # Target scale (50 rps) vs Doc scale (50,000 req/min) produces scale note
    assert selected[0].scale_note is not None


# ── 2. Profile Extractor Tests (Cache Hit/Miss & Extraction Failed) ───────────

@pytest.mark.asyncio
async def test_profile_extractor_cache_and_failure(tmp_path: Path):
    cache_dir = tmp_path / "rw_cache"
    client = ReviewerLLMClient(mock_mode="1")
    extractor = ProfileExtractor(llm_client=client, cache_dir=cache_dir)

    doc = ReferenceDoc(
        id="test_doc_01",
        system_name="Test FinTech Ledger",
        folder="category_10_real_world_systems",
        path="fake/path.md",
        sha256="abc12345def67890",
        sections=[{"heading": "Consistency", "content": "Append-only ledger."}],
        sources=["https://example.com/fintech"],
        tags=["fintech"],
    )

    # 1. First call: Cache miss -> generates and caches
    profile1 = await extractor.extract_profile(doc)
    assert not profile1.extraction_failed
    assert len(profile1.patterns) > 0
    cached_file = list(cache_dir.glob("*.json"))
    assert len(cached_file) == 1

    # 2. Second call: Cache hit
    profile2 = await extractor.extract_profile(doc)
    assert profile2.system == profile1.system
    assert len(profile2.patterns) == len(profile1.patterns)

    # 3. Extraction failed handling (no crash)
    failing_client = ReviewerLLMClient(mock_mode="unavailable")
    # New doc with uncached sha
    doc_fail = copy.deepcopy(doc)
    doc_fail.sha256 = "fail_sha_999999"
    extractor_fail = ProfileExtractor(llm_client=failing_client, cache_dir=cache_dir)
    profile_failed = await extractor_fail.extract_profile(doc_fail)
    assert profile_failed.extraction_failed is True
    assert profile_failed.patterns == []


# ── 3. Real-World Scoring Tests ───────────────────────────────────────────────

def test_real_world_scoring_all_aligned():
    artifact_data = {"reservation_policy": {"lock": "SELECT FOR UPDATE row-level lock"}}
    assessments = [
        PatternAssessment(
            pattern_id=f"RW-SYS-{i:02d}",
            system_name="Reference System",
            pattern_name=f"Pattern {i}",
            category="concurrency",
            priority=1,
            status="ALIGNED",
            evidence_path="/reservation_policy/lock",
            justification="Aligned.",
        )
        for i in range(1, 4)
    ]
    res, findings = score_real_world_assessments("backend", assessments, artifact_data, [])
    assert res.score == 100
    assert res.confidence == "normal"
    assert len(findings) == 0


def test_real_world_scoring_mixed_example():
    artifact_data = {
        "locking": "SELECT FOR UPDATE",
        "cache": "Redis replica",
        "api": "POST /reservations",
    }
    # 4 applicable: 1 ALIGNED (1.0), 1 PARTIAL (0.5), 1 JUSTIFIED_DIVERGENCE (0.8), 1 MISSING (0.0)
    # Expected: round(100 * (1.0 + 0.5 + 0.8 + 0.0) / 4) = round(100 * 2.3 / 4) = round(57.5) = 58
    assessments = [
        PatternAssessment(
            pattern_id="RW-01",
            system_name="SysA",
            pattern_name="Locking",
            category="concurrency",
            priority=1,
            status="ALIGNED",
            evidence_path="/locking",
            justification="Valid lock.",
        ),
        PatternAssessment(
            pattern_id="RW-02",
            system_name="SysA",
            pattern_name="Caching",
            category="caching",
            priority=2,
            status="PARTIAL",
            evidence_path="/cache",
            justification="Partial cache.",
        ),
        PatternAssessment(
            pattern_id="RW-03",
            system_name="SysA",
            pattern_name="Ingress",
            category="resilience",
            priority=2,
            status="JUSTIFIED_DIVERGENCE",
            evidence_path="/api",
            justification="Divergence justified.",
        ),
        PatternAssessment(
            pattern_id="RW-04",
            system_name="SysA",
            pattern_name="Telemetry",
            category="observability",
            priority=3,
            status="MISSING",
            justification="No telemetry found.",
        ),
    ]
    res, findings = score_real_world_assessments("backend", assessments, artifact_data, [])
    assert res.score == 58
    assert res.confidence == "normal"
    # PARTIAL and MISSING generate findings
    assert len(findings) == 2


def test_real_world_not_applicable_without_refs_downgraded():
    artifact_data = {"key": "val"}
    assessments = [
        PatternAssessment(
            pattern_id="RW-01",
            system_name="SysA",
            pattern_name="Sharding",
            category="scaling",
            priority=2,
            status="NOT_APPLICABLE",
            evidence_path=None,
            justification="Not needed.",
            requirement_refs=[],  # Missing requirement_refs => downgrade to MISSING!
        ),
        PatternAssessment(
            pattern_id="RW-02",
            system_name="SysA",
            pattern_name="Multi-Region",
            category="scaling",
            priority=2,
            status="NOT_APPLICABLE",
            evidence_path=None,
            justification="Small scale.",
            requirement_refs=["NFR-1"],  # Valid with requirement_refs
        ),
    ]
    res, findings = score_real_world_assessments("backend", assessments, artifact_data, [])
    assert res.counts["downgraded_unverified"] == 1
    assert res.counts["missing"] == 1
    assert res.counts["not_applicable"] == 1


def test_real_world_unverifiable_evidence_downgraded():
    artifact_data = {"actual_key": "actual_val"}
    assessments = [
        PatternAssessment(
            pattern_id="RW-01",
            system_name="SysA",
            pattern_name="Locking",
            category="concurrency",
            priority=1,
            status="ALIGNED",
            evidence_path="/non_existent_key/path",  # Unverifiable evidence => downgrade to MISSING!
            justification="Claims alignment with hallucinated pointer.",
        )
    ]
    res, findings = score_real_world_assessments("backend", assessments, artifact_data, [])
    assert res.counts["downgraded_unverified"] == 1
    assert res.counts["missing"] == 1
    assert res.counts["aligned"] == 0
    assert len(findings) == 1
    assert findings[0].severity == "high"


def test_real_world_low_confidence_and_unavailable():
    artifact_data = {"key": "val"}
    # Less than 3 applicable patterns => low confidence
    assessments_two = [
        PatternAssessment(
            pattern_id="RW-01",
            system_name="SysA",
            pattern_name="P1",
            category="caching",
            priority=1,
            status="ALIGNED",
            evidence_path="/key",
            justification="ok",
        ),
        PatternAssessment(
            pattern_id="RW-02",
            system_name="SysA",
            pattern_name="P2",
            category="caching",
            priority=2,
            status="ALIGNED",
            evidence_path="/key",
            justification="ok",
        ),
    ]
    res_low, _ = score_real_world_assessments("backend", assessments_two, artifact_data, [])
    assert res_low.confidence == "low"

    # Zero applicable => unavailable
    res_unavail, _ = score_real_world_assessments("backend", [], artifact_data, [])
    assert res_unavail.score is None
    assert res_unavail.confidence == "unavailable"


# ── 4. Decision Scoring & Safety Gate Tests ───────────────────────────────────

def test_decision_scoring_rw_below_min_rejected():
    reviewer_res = ArtifactResult(
        artifact="backend",
        score=90,
        verdict="ACCEPTED",
        dimensions=[
            DimensionScore(id="D1", label="Quality", score=5, weight=1.0, evidence_path="/k", missing=[], rationale="Good"),
        ],
        findings=[],
        reviewer_status="ok",
    )
    rw_low = RealWorldResult(
        artifact="backend",
        score=50,  # Below RW_MIN (60)!
        confidence="normal",
        counts={"aligned": 1, "partial": 0, "missing": 1, "justified_divergence": 0, "not_applicable": 0, "downgraded_unverified": 0},
        assessments=[],
        references_used=[],
    )
    final_res = compute_artifact_score(
        artifact_name="backend",
        reviewer_result=reviewer_res,
        l0_findings=[],
        l1_findings=[],
        real_world_result=rw_low,
        real_world_findings=[],
        reviewer_mode="live",
    )
    assert final_res.verdict == "REJECTED"


def test_decision_scoring_rw_unavailable_provisional():
    reviewer_res = ArtifactResult(
        artifact="backend",
        score=95,
        verdict="ACCEPTED",
        dimensions=[
            DimensionScore(id="D1", label="Quality", score=5, weight=1.0, evidence_path="/k", missing=[], rationale="Good"),
        ],
        findings=[],
        reviewer_status="ok",
    )
    rw_unavail = RealWorldResult(
        artifact="backend",
        score=None,  # Real-world score unavailable
        confidence="unavailable",
        counts={},
        assessments=[],
        references_used=[],
    )
    final_res = compute_artifact_score(
        artifact_name="backend",
        reviewer_result=reviewer_res,
        l0_findings=[],
        l1_findings=[],
        real_world_result=rw_unavail,
        real_world_findings=[],
        reviewer_mode="live",
    )
    assert final_res.verdict == "PROVISIONAL"


def test_decision_weight_switches_on_low_confidence():
    reviewer_res = ArtifactResult(
        artifact="backend",
        score=100,
        verdict="ACCEPTED",
        dimensions=[
            DimensionScore(id="D1", label="Quality", score=5, weight=1.0, evidence_path="/k", missing=[], rationale="Good"),
        ],
        findings=[],
        reviewer_status="ok",
    )
    rw_normal = RealWorldResult(
        artifact="backend",
        score=60,
        confidence="normal",
        counts={},
        assessments=[],
        references_used=[],
    )
    res_normal = compute_artifact_score(
        artifact_name="backend",
        reviewer_result=reviewer_res,
        l0_findings=[],
        l1_findings=[],
        real_world_result=rw_normal,
        real_world_findings=[],
        reviewer_mode="live",
    )
    # (1 - 0.35)*100 + 0.35*60 = 65 + 21 = 86
    assert res_normal.final_score == 86

    rw_low = RealWorldResult(
        artifact="backend",
        score=60,
        confidence="low",
        counts={},
        assessments=[],
        references_used=[],
    )
    res_low = compute_artifact_score(
        artifact_name="backend",
        reviewer_result=reviewer_res,
        l0_findings=[],
        l1_findings=[],
        real_world_result=rw_low,
        real_world_findings=[],
        reviewer_mode="live",
    )
    # (1 - 0.15)*100 + 0.15*60 = 85 + 9 = 94
    assert res_low.final_score == 94


def test_mock_mode_cannot_accept_unless_allowed(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(config, "ALLOW_MOCK_ACCEPT", 0)
    reviewer_res = ArtifactResult(
        artifact="backend",
        score=95,
        verdict="ACCEPTED",
        dimensions=[
            DimensionScore(id="D1", label="Quality", score=5, weight=1.0, evidence_path="/k", missing=[], rationale="Good"),
        ],
        findings=[],
        reviewer_status="ok",
    )
    rw_good = RealWorldResult(
        artifact="backend",
        score=90,
        confidence="normal",
        counts={},
        assessments=[],
        references_used=[],
    )
    # Without ALLOW_MOCK_ACCEPT, mock reviewer caps at PROVISIONAL
    res_mock = compute_artifact_score(
        artifact_name="backend",
        reviewer_result=reviewer_res,
        l0_findings=[],
        l1_findings=[],
        real_world_result=rw_good,
        real_world_findings=[],
        reviewer_mode="mock",
    )
    assert res_mock.verdict == "PROVISIONAL"

    # With ALLOW_MOCK_ACCEPT=1, it can be ACCEPTED
    monkeypatch.setattr(config, "ALLOW_MOCK_ACCEPT", 1)
    res_mock_allowed = compute_artifact_score(
        artifact_name="backend",
        reviewer_result=reviewer_res,
        l0_findings=[],
        l1_findings=[],
        real_world_result=rw_good,
        real_world_findings=[],
        reviewer_mode="mock",
    )
    assert res_mock_allowed.verdict == "ACCEPTED"


# ── 5. Layer 1 Honesty on Unmodified Real Package ─────────────────────────────

def test_l1_honesty_on_real_unmodified_package():
    assert REAL_PACKAGE_PATH.exists()
    real_pkg = json.loads(REAL_PACKAGE_PATH.read_text(encoding="utf-8"))

    normalizer = PackageNormalizer()
    normalized = normalizer.normalize(real_pkg)

    # In real unmodified output, scaffolds are absent
    scaffolds = normalized.scaffold_files

    op_findings, op_meta = check_openapi(scaffolds.get("openapi.yaml"), normalized.endpoints)
    assert op_meta["status"] == "not_evaluated"
    assert "no scaffold provided" in op_meta["message"]
    assert len(op_findings) == 0

    df_findings, df_meta = check_dockerfile(scaffolds.get("Dockerfile"))
    assert df_meta["status"] == "not_evaluated"
    assert "no scaffold provided" in df_meta["message"]
    assert len(df_findings) == 0

    tf_findings, tf_meta = check_terraform(scaffolds.get("terraform/main.tf"), {})
    assert tf_meta["status"] == "not_evaluated"
    assert "no scaffold provided" in tf_meta["message"]
    assert len(tf_findings) == 0

    mg_findings, mg_meta = check_migration(scaffolds.get("alembic_migration.py"), normalized.tables)
    assert mg_meta["status"] == "not_evaluated"
    assert "no scaffold provided" in mg_meta["message"]
    assert len(mg_findings) == 0


# ── 6. History Pattern Status Diffing Across Iterations ───────────────────────

def test_history_pattern_diff_across_iterations():
    # Iteration 1: RW-01 and RW-02 MISSING
    it1_results = {
        "backend": ArtifactResult(
            artifact="backend",
            score=70,
            rubric_score=75,
            real_world=RealWorldResult(
                artifact="backend",
                score=40,
                confidence="normal",
                counts={},
                assessments=[
                    PatternAssessment(pattern_id="RW-01", system_name="SysA", pattern_name="Locking", category="concurrency", priority=1, status="MISSING", justification="Missing lock."),
                    PatternAssessment(pattern_id="RW-02", system_name="SysA", pattern_name="Audit", category="data", priority=2, status="MISSING", justification="Missing audit."),
                ],
                references_used=[],
            ),
            verdict="REJECTED",
            dimensions=[],
            findings=[],
        )
    }
    it1 = Iteration(n=1, results=it1_results, started_at="2026-10-25T00:00:00Z", finished_at="2026-10-25T00:00:10Z")

    # Iteration 2: RW-01 ALIGNED, RW-02 still MISSING
    it2_results = {
        "backend": ArtifactResult(
            artifact="backend",
            score=85,
            rubric_score=85,
            real_world=RealWorldResult(
                artifact="backend",
                score=80,
                confidence="normal",
                counts={},
                assessments=[
                    PatternAssessment(pattern_id="RW-01", system_name="SysA", pattern_name="Locking", category="concurrency", priority=1, status="ALIGNED", justification="Aligned lock."),
                    PatternAssessment(pattern_id="RW-02", system_name="SysA", pattern_name="Audit", category="data", priority=2, status="MISSING", justification="Missing audit."),
                ],
                references_used=[],
            ),
            verdict="ACCEPTED",
            dimensions=[],
            findings=[],
        )
    }

    corrections = diff_iteration_corrections(
        prev_iteration=it1,
        curr_results=it2_results,
        regenerated_artifacts=["backend"],
        regenerated_with_feedback=True,
    )

    assert len(corrections) == 1
    backend_corr = corrections[0]
    assert "RW-01" in backend_corr.patterns_resolved
    assert "RW-02" in backend_corr.patterns_still_missing
