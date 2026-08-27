"""Unit Test for SAELogger and debug logging in /sae/logs/{design_id}."""

import io
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.sae.utils.sae_logger import SAELogger, DEFAULT_LOGS_ROOT


def test_sae_logger_creates_all_files():
    design_id = "test_verification_design_123"
    logger = SAELogger(design_id=design_id, debug=True)

    # 1. Verify directory creation
    log_dir = logger.log_dir
    assert log_dir.exists(), f"Log directory {log_dir} does not exist"
    assert log_dir.name == design_id

    # 2. Test Phase logging
    logger.log_phase_start(1, "Test Planning Phase")
    logger.log_debug("This is a debug test message.")
    logger.log_info("This is an info test message.")

    # 3. Test LLM request/response logging
    logger.log_llm_request(
        agent_role="backend_lld",
        model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        prompt="Sample user prompt for backend architecture",
        system_prompt="Sample system prompt",
        key_idx=1,
        temperature=0.2,
    )
    logger.log_llm_response(
        agent_role="backend_lld",
        latency=1.85,
        content='{"api_endpoints": [{"path": "/api/v1/test", "method": "GET"}]}',
        parsed_fields=["api_endpoints"],
        status="SUCCESS",
    )

    # 4. Test RAG retrieval logging
    logger.log_rag_retrieval(
        agent_role="backend_lld",
        query="Repository and DAO pattern in Python",
        chunks_count=3,
        avg_similarity=0.824,
        fallback=False,
        top_sources=["patterns/repo.md (0.89)", "patterns/clean_arch.md (0.80)"],
    )

    logger.log_phase_end(1, "Test Planning Phase", 2.34, "Completed successfully")

    # 5. Save summary
    logger.save_summary({
        "status": "HEALTHY",
        "completeness": {"structural_completeness": 1.0},
    })

    logger.close()

    # 6. Verify all files exist and are populated
    debug_log = log_dir / "debug.log"
    execution_log = log_dir / "execution.log"
    timeline_log = log_dir / "timeline.log"
    llm_calls_log = log_dir / "llm_calls.log"
    summary_json = log_dir / "execution_summary.json"

    assert debug_log.exists(), "debug.log missing"
    assert execution_log.exists(), "execution.log missing"
    assert timeline_log.exists(), "timeline.log missing"
    assert llm_calls_log.exists(), "llm_calls.log missing"
    assert summary_json.exists(), "execution_summary.json missing"

    # Verify debug.log content
    debug_text = debug_log.read_text(encoding="utf-8")
    assert "Test Planning Phase" in debug_text
    assert "This is a debug test message." in debug_text
    assert "Sample user prompt for backend architecture" in debug_text
    assert "Repository and DAO pattern in Python" in debug_text
    assert "api_endpoints" in debug_text

    # Verify summary JSON
    summary_data = json.loads(summary_json.read_text(encoding="utf-8"))
    assert summary_data["design_id"] == design_id
    assert summary_data["status"] == "HEALTHY"
    assert len(summary_data["timeline"]) > 0

    print(f"✓ All SAELogger tests passed! Verified directory: {log_dir}")


if __name__ == "__main__":
    test_sae_logger_creates_all_files()
