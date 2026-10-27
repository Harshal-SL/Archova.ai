"""Unit & Regression Tests for Architecture Version Manager."""

import copy
import sys
from pathlib import Path

_AI_ENGINE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_AI_ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(_AI_ENGINE_ROOT))

try:
    import pytest
except ImportError:
    class _MockPytest:
        def fixture(self, f):
            return f
        class mark:
            @staticmethod
            def asyncio(f):
                return f
    pytest = _MockPytest()

from app.versioning.contracts import (
    ArchitecturePatch,
    ColumnAddition,
    ExistingServiceEndpointAddition,
)
from app.versioning.differ import ArchitectureDiffer
from app.versioning.patcher import ArchitecturePatcher
from app.versioning.prompt_builder import DeltaPromptBuilder
from app.versioning.verifier import ArchitectureVerifier
from app.versioning.version_manager import VersionManager


# ── Sample Fixtures ──

@pytest.fixture
def sample_v1_baseline():
    """A realistic v1.0 architecture package."""
    return {
        "version": "1.0",
        "prompt": "Build an Online Event Management System",
        "hld": {
            "system_name": "Online Event Management Platform",
            "architecture_style": "Event-Driven Microservices",
            "nodes": [
                {
                    "id": "api-gateway",
                    "type": "gateway",
                    "data": {"label": "API Gateway", "category": "gateway"},
                },
                {
                    "id": "event-service",
                    "type": "service",
                    "data": {"label": "Event Service", "category": "service"},
                },
                {
                    "id": "event-db",
                    "type": "database",
                    "data": {"label": "Event PostgreSQL", "category": "database"},
                },
            ],
            "edges": [
                {
                    "id": "e-gw-event",
                    "source": "api-gateway",
                    "target": "event-service",
                    "label": "HTTPS",
                },
                {
                    "id": "e-event-db",
                    "source": "event-service",
                    "target": "event-db",
                    "label": "SQL",
                },
            ],
        },
        "llds": {
            "database": {
                "tables": [
                    {
                        "name": "events",
                        "columns": [
                            {"name": "id", "type": "UUID", "is_primary_key": True},
                            {"name": "title", "type": "VARCHAR(255)", "nullable": False},
                            {"name": "capacity", "type": "INTEGER", "nullable": False},
                        ],
                    }
                ]
            },
            "backend": {
                "api_endpoints": [
                    {
                        "id": "ep-events-get",
                        "path": "/api/v1/events",
                        "method": "GET",
                        "service": "event-service",
                    }
                ],
                "services": [{"name": "EventService", "description": "Core event logic"}],
            },
        },
    }


@pytest.fixture
def valid_v1_1_patch():
    """A valid, additive patch adding real-time notifications to the event system."""
    return ArchitecturePatch(
        version_bump="minor",
        feature_summary="Added real-time notification service and WebSocket broadcast gateway",
        added_nodes=[
            {
                "id": "notification-service",
                "type": "service",
                "data": {"label": "Notification Service", "category": "service"},
            },
            {
                "id": "notification-db",
                "type": "database",
                "data": {"label": "Notification Redis Cache", "category": "database"},
            },
        ],
        added_edges=[
            {
                "id": "e-event-notification",
                "source": "event-service",
                "target": "notification-service",
                "label": "AMQP / Event",
            },
            {
                "id": "e-notification-db",
                "source": "notification-service",
                "target": "notification-db",
                "label": "TCP",
            },
        ],
        added_tables=[
            {
                "name": "notifications",
                "description": "User notification records",
                "columns": [
                    {"name": "id", "type": "UUID", "is_primary_key": True},
                    {"name": "message", "type": "TEXT", "nullable": False},
                ],
            }
        ],
        added_columns=[
            ColumnAddition(
                table_name="events",
                column_name="enable_live_notifications",
                column_type="BOOLEAN",
                nullable=True,
                default="TRUE",
            )
        ],
        added_endpoints=[
            {
                "path": "/api/v1/notifications",
                "method": "GET",
                "service": "notification-service",
                "description": "List user notifications",
            }
        ],
    )


# ── Tests ──

def test_detect_version_context_initial():
    """New chats must bypass version manager and start at v1.0."""
    ctx = VersionManager.detect_version_context(session_id="chat-1", previous_package=None)
    assert ctx.mode == "INITIAL"
    assert ctx.target_version == "1.0"
    assert ctx.parent_package is None


def test_detect_version_context_evolution(sample_v1_baseline):
    """Existing chats with a v1.0 package must enter EVOLUTION mode targeting v1.1."""
    ctx = VersionManager.detect_version_context(
        session_id="chat-1",
        previous_package=sample_v1_baseline,
    )
    assert ctx.mode == "EVOLUTION"
    assert ctx.base_version == "1.0"
    assert ctx.target_version == "1.1"


def test_bump_version_string():
    """Semantic version increment logic."""
    assert VersionManager.bump_version_string("1.0", "minor") == "1.1"
    assert VersionManager.bump_version_string("1.1", "minor") == "1.2"
    assert VersionManager.bump_version_string("v1.2", "minor") == "1.3"
    assert VersionManager.bump_version_string("1.0", "patch") == "1.0.1"
    assert VersionManager.bump_version_string("1.5", "major") == "2.0"


def test_patcher_preserves_all_baseline_and_adds_new(sample_v1_baseline, valid_v1_1_patch):
    """Patcher must preserve 100% of baseline while cleanly tagging new items."""
    patcher = ArchitecturePatcher(target_version="1.1")
    patched = patcher.apply_patch(sample_v1_baseline, valid_v1_1_patch)

    assert patched["version"] == "1.1"
    assert patched["version_tag"] == "v1.1"

    # Baseline nodes survived
    b_node_ids = {n["id"] for n in sample_v1_baseline["hld"]["nodes"]}
    p_node_ids = {n["id"] for n in patched["hld"]["nodes"]}
    assert b_node_ids.issubset(p_node_ids)

    # Added nodes exist with flags
    new_node = next(n for n in patched["hld"]["nodes"] if n["id"] == "notification-service")
    assert new_node["is_new"] is True
    assert new_node["version_added"] == "1.1"

    # Baseline table survived and new column was added safely
    event_tbl = next(t for t in patched["llds"]["database"]["tables"] if t["name"] == "events")
    col_names = [c["name"] for c in event_tbl["columns"]]
    assert "id" in col_names
    assert "title" in col_names
    assert "enable_live_notifications" in col_names

    # New table added
    tbl_names = [t["name"] for t in patched["llds"]["database"]["tables"]]
    assert "notifications" in tbl_names


def test_verifier_passes_on_valid_evolution(sample_v1_baseline, valid_v1_1_patch):
    """Clean additive patch must yield is_valid=True with 0 violations."""
    patcher = ArchitecturePatcher(target_version="1.1")
    patched = patcher.apply_patch(sample_v1_baseline, valid_v1_1_patch)

    verifier = ArchitectureVerifier()
    res = verifier.verify(sample_v1_baseline, patched, valid_v1_1_patch)
    assert res.is_valid is True
    assert len(res.violations) == 0


def test_verifier_rejects_node_deletion(sample_v1_baseline, valid_v1_1_patch):
    """Adversarial: Removing a baseline node must trigger IMMUTABLE_NODE_SURVIVAL."""
    patcher = ArchitecturePatcher(target_version="1.1")
    patched = patcher.apply_patch(sample_v1_baseline, valid_v1_1_patch)

    # Maliciously delete baseline node 'event-db'
    patched["hld"]["nodes"] = [n for n in patched["hld"]["nodes"] if n["id"] != "event-db"]

    verifier = ArchitectureVerifier()
    res = verifier.verify(sample_v1_baseline, patched, valid_v1_1_patch)
    assert res.is_valid is False
    assert any(v.rule == "IMMUTABLE_NODE_SURVIVAL" for v in res.violations)


def test_verifier_rejects_node_type_change(sample_v1_baseline, valid_v1_1_patch):
    """Adversarial: Mutating a baseline node's type must trigger NODE_TYPE_IMMUTABILITY."""
    patcher = ArchitecturePatcher(target_version="1.1")
    patched = patcher.apply_patch(sample_v1_baseline, valid_v1_1_patch)

    # Maliciously change node type of 'event-service' from service to queue
    for n in patched["hld"]["nodes"]:
        if n["id"] == "event-service":
            n["type"] = "queue"

    verifier = ArchitectureVerifier()
    res = verifier.verify(sample_v1_baseline, patched, valid_v1_1_patch)
    assert res.is_valid is False
    assert any(v.rule == "NODE_TYPE_IMMUTABILITY" for v in res.violations)


def test_verifier_rejects_dangling_edge(sample_v1_baseline):
    """Adversarial: Edge pointing to non-existent target node must trigger DANGLING_EDGE_TARGET."""
    broken_patch = ArchitecturePatch(
        feature_summary="Broken edge test",
        added_edges=[
            {
                "id": "e-bad",
                "source": "api-gateway",
                "target": "non_existent_ghost_service",
                "label": "HTTPS",
            }
        ],
    )
    patcher = ArchitecturePatcher(target_version="1.1")
    patched = patcher.apply_patch(sample_v1_baseline, broken_patch)

    verifier = ArchitectureVerifier()
    res = verifier.verify(sample_v1_baseline, patched, broken_patch)
    assert res.is_valid is False
    assert any(v.rule == "DANGLING_EDGE_TARGET" for v in res.violations)


def test_verifier_rejects_breaking_column_addition(sample_v1_baseline):
    """Adversarial: Adding non-nullable column without default must trigger BREAKING_COLUMN_ADDITION."""
    breaking_patch = ArchitecturePatch(
        feature_summary="Breaking column addition",
        added_columns=[
            ColumnAddition(
                table_name="events",
                column_name="breaking_col",
                column_type="INTEGER",
                nullable=False,
                default=None,  # Forbidden: non-nullable without default breaks existing data!
            )
        ],
    )
    patcher = ArchitecturePatcher(target_version="1.1")
    patched = patcher.apply_patch(sample_v1_baseline, breaking_patch)

    verifier = ArchitectureVerifier()
    res = verifier.verify(sample_v1_baseline, patched, breaking_patch)
    assert res.is_valid is False
    assert any(v.rule == "BREAKING_COLUMN_ADDITION" for v in res.violations)


def test_differ_computes_accurate_diff(sample_v1_baseline, valid_v1_1_patch):
    """Differ must generate accurate summary stats and added lists."""
    patcher = ArchitecturePatcher(target_version="1.1")
    patched = patcher.apply_patch(sample_v1_baseline, valid_v1_1_patch)

    diff = ArchitectureDiffer.compute_diff(
        baseline=sample_v1_baseline,
        patched=patched,
        patch=valid_v1_1_patch,
        from_version="1.0",
        to_version="1.1",
        feature_prompt="Add live notifications",
    )

    assert diff.from_version == "1.0"
    assert diff.to_version == "1.1"
    assert len(diff.added_nodes) == 2
    assert len(diff.added_edges) == 2
    assert "notifications" in diff.added_tables
    assert any("enable_live_notifications" in c for c in diff.added_columns)
    assert diff.baseline_stats["nodes"] == 3
    assert diff.new_stats["nodes"] == 5


def test_prompt_builder_compactness(sample_v1_baseline):
    """Compact summary must be concise and include existing IDs and names."""
    summary = DeltaPromptBuilder.build_compact_baseline_summary(sample_v1_baseline)
    assert "EXISTING NODES" in summary
    assert "api-gateway" in summary
    assert "event-service" in summary
    assert "events" in summary
    assert len(summary) < 2500  # Token efficient (< 600 tokens)


@pytest.mark.asyncio
async def test_version_evolution_chain(sample_v1_baseline, valid_v1_1_patch):
    """Chain test: v1.0 -> v1.1 -> v1.2 maintains all entities across the entire chain."""
    vm = VersionManager()

    # Step 1: Evolve v1.0 -> v1.1
    patched_v1_1, diff_v1_1 = await vm.evolve_architecture(
        baseline=sample_v1_baseline,
        feature_prompt="Add notifications",
        custom_llm_caller=lambda prompt: valid_v1_1_patch.model_dump(),
        target_version="1.1",
    )
    assert patched_v1_1["version"] == "1.1"
    assert len(patched_v1_1["hld"]["nodes"]) == 5

    # Step 2: Evolve v1.1 -> v1.2 with another feature (e.g. Analytics Engine)
    v1_2_patch = ArchitecturePatch(
        feature_summary="Added Analytics Service",
        added_nodes=[
            {
                "id": "analytics-service",
                "type": "service",
                "data": {"label": "Analytics Service", "category": "service"},
            }
        ],
        added_edges=[
            {
                "id": "e-event-analytics",
                "source": "event-service",
                "target": "analytics-service",
                "label": "Kafka",
            }
        ],
    )

    patched_v1_2, diff_v1_2 = await vm.evolve_architecture(
        baseline=patched_v1_1,
        feature_prompt="Add analytics engine",
        custom_llm_caller=lambda prompt: v1_2_patch.model_dump(),
        target_version="1.2",
    )

    assert patched_v1_2["version"] == "1.2"
    # All 3 original v1.0 nodes + 2 v1.1 nodes + 1 v1.2 node = 6 total nodes!
    assert len(patched_v1_2["hld"]["nodes"]) == 6

    # Assert 100% baseline survival across all versions
    final_node_ids = {n["id"] for n in patched_v1_2["hld"]["nodes"]}
    assert "api-gateway" in final_node_ids
    assert "event-service" in final_node_ids
    assert "event-db" in final_node_ids
    assert "notification-service" in final_node_ids
    assert "notification-db" in final_node_ids
    assert "analytics-service" in final_node_ids


if __name__ == "__main__":
    import asyncio
    print("Running Versioning Test Suite...")
    b = sample_v1_baseline()
    p = valid_v1_1_patch()

    test_detect_version_context_initial()
    print("[PASS] test_detect_version_context_initial")

    test_detect_version_context_evolution(b)
    print("[PASS] test_detect_version_context_evolution")

    test_bump_version_string()
    print("[PASS] test_bump_version_string")

    test_patcher_preserves_all_baseline_and_adds_new(b, p)
    print("[PASS] test_patcher_preserves_all_baseline_and_adds_new")

    test_verifier_passes_on_valid_evolution(b, p)
    print("[PASS] test_verifier_passes_on_valid_evolution")

    test_verifier_rejects_node_deletion(b, p)
    print("[PASS] test_verifier_rejects_node_deletion")

    test_verifier_rejects_node_type_change(b, p)
    print("[PASS] test_verifier_rejects_node_type_change")

    test_verifier_rejects_dangling_edge(b)
    print("[PASS] test_verifier_rejects_dangling_edge")

    test_verifier_rejects_breaking_column_addition(b)
    print("[PASS] test_verifier_rejects_breaking_column_addition")

    test_differ_computes_accurate_diff(b, p)
    print("[PASS] test_differ_computes_accurate_diff")

    test_prompt_builder_compactness(b)
    print("[PASS] test_prompt_builder_compactness")

    asyncio.run(test_version_evolution_chain(b, p))
    print("[PASS] test_version_evolution_chain")

    print("\n>>> ALL 12 VERSIONING SUITE TESTS PASSED 100%! <<<")


