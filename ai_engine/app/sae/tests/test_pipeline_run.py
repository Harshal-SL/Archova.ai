"""End-to-End Pipeline Runner & Integration Test for SAE v2.

Supports 2 modes:
  1. Normal Mode (Default):
     Clean, concise phase progress bars, status indicators, and final executive scorecard.
  2. Debug Mode (--debug / -d):
     Continuous verbose real-time streaming of all details:
       - Pipeline & agent lifecycle events
       - Agent-owned RAG retrieval (domain queries, chunk scores, source files, previews, fallbacks)
       - LLM status & prompts (model, key index, system prompt, user prompt)
       - Raw LLM responses & parsed Pydantic field models
       - Code scaffolding outputs
       - Production readiness score breakdown & quality gates

Usage:
  Normal mode:
    python app/sae/tests/test_pipeline_run.py
  Debug mode:
    python app/sae/tests/test_pipeline_run.py --debug
  Custom ARSRS input:
    python app/sae/tests/test_pipeline_run.py --arsrs path/to/arsrs.json --debug
"""

from __future__ import annotations

import argparse
import datetime
import io
import json
import logging
import os
import sys
import time
from pathlib import Path

# Setup unbuffered UTF-8 console output and project root path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Automatically re-exec with project venv Python if running under global python
venv_python = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"
if venv_python.exists() and Path(sys.executable).resolve() != venv_python.resolve():
    import subprocess
    proc = subprocess.run([str(venv_python), str(Path(__file__).resolve())] + sys.argv[1:])
    sys.exit(proc.returncode)

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=True)

from app.sae.pipeline import SAEPipeline
from app.sae.utils.sae_logger import DEFAULT_LOGS_ROOT


def setup_logging(
    debug: bool,
    design_id: Optional[str] = None,
    logs_dir: Optional[str | Path] = None,
) -> Optional[Path]:
    """Configure system logging format, level, and FileHandler based on design_id and debug mode."""
    handlers: List[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    debug_log_path: Optional[Path] = None

    if design_id:
        root_logs = Path(logs_dir) if logs_dir else DEFAULT_LOGS_ROOT
        target_dir = root_logs / design_id
        target_dir.mkdir(parents=True, exist_ok=True)
        debug_log_path = target_dir / "debug.log"
        file_handler = logging.FileHandler(debug_log_path, mode="a", encoding="utf-8")
        handlers.append(file_handler)

    if debug:
        os.environ["SAE_DEBUG"] = "true"
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%H:%M:%S",
            handlers=handlers,
            force=True,
        )
        # Keep noisy third-party libraries at INFO/WARNING to avoid overwhelming the log
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
        logging.getLogger("transformers").setLevel(logging.ERROR)
    else:
        os.environ["SAE_DEBUG"] = "false"
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            handlers=handlers,
            force=True,
        )
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

    return debug_log_path


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="SAE v2 Production Architecture Pipeline Runner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        default=os.getenv("SAE_DEBUG", "false").lower() in ("true", "1", "yes"),
        help="Enable continuous verbose debug logging (LLM prompts, RAG data, raw responses, agent status)",
    )
    parser.add_argument(
        "-i", "--design-id",
        type=str,
        default=None,
        help="Design ID for partitioning logs in /sae/logs/{design_id} (defaults to ARSRS session_id/design_id)",
    )
    parser.add_argument(
        "-l", "--logs-dir",
        type=str,
        default=str(DEFAULT_LOGS_ROOT),
        help="Base directory for SAE logs (e.g. output/sae/logs)",
    )
    parser.add_argument(
        "-a", "--arsrs",
        type=str,
        default=str(PROJECT_ROOT / "output" / "arsrs.json"),
        help="Path to input ARSRS JSON file",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=str(PROJECT_ROOT / "output" / "sae"),
        help="Target output directory for architecture artifacts",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=None,
        help="Optional OpenRouter model override (e.g. nvidia/nemotron-3.5-lightning:free)",
    )
    return parser.parse_args()


def print_debug_banner(
    args: argparse.Namespace,
    api_keys_count: int,
    arsrs_summary: dict,
    design_id: str,
    debug_log_path: Optional[Path],
) -> None:
    """Print debug initialization header."""
    print("━" * 80)
    print(" 🛠️  SAE v2 PIPELINE — CONTINUOUS DEBUG MODE ENABLED")
    print("━" * 80)
    print(f" • Design ID   : {design_id}")
    print(f" • Debug Log   : {debug_log_path or 'N/A'}")
    print(f" • ARSRS Path  : {args.arsrs}")
    print(f" • Output Dir  : {args.output}")
    print(f" • API Keys    : {api_keys_count} available")
    print(f" • Default Model: {args.model or os.getenv('LLM_MODEL', 'nvidia/nemotron-3.5-lightning:free')}")
    print(f" • System Goal : {arsrs_summary.get('goal', 'N/A')}")
    print(f" • System Type : {arsrs_summary.get('system_type', 'N/A')}")
    print(f" • Domain      : {arsrs_summary.get('domain', 'N/A')}")
    print("━" * 80 + "\n")


def print_normal_banner(
    args: argparse.Namespace,
    api_keys_count: int,
    design_id: str,
    debug_log_path: Optional[Path],
) -> None:
    """Print standard execution header."""
    print("=" * 70)
    print(f" Running SAE v2 Pipeline (Design ID: {design_id}, Output: {args.output})")
    if debug_log_path:
        print(f" Log File: {debug_log_path}")
    print("=" * 70)


def main() -> None:
    args = parse_args()

    # 1. Load ARSRS input
    arsrs_file = Path(args.arsrs)
    if not arsrs_file.exists():
        print(
            f"[FATAL] ARSRS input file not found at: {arsrs_file}\n"
            f"Please generate or place the ARSRS file there first before running.",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(arsrs_file, "r", encoding="utf-8") as f:
        arsrs = json.load(f)

    # 2. Resolve design_id and Setup logging
    arsrs_profile = arsrs.get("project_profile", {}) if isinstance(arsrs.get("project_profile"), dict) else {}
    arsrs_meta = arsrs.get("metadata", {}) if isinstance(arsrs.get("metadata"), dict) else {}
    design_id = (
        args.design_id
        or arsrs.get("design_id")
        or arsrs.get("session_id")
        or arsrs_profile.get("session_id")
        or arsrs_meta.get("design_id")
        or f"design_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )

    debug_log_path = setup_logging(args.debug, design_id=design_id, logs_dir=args.logs_dir)

    # 3. Load API keys
    api_keys = [os.getenv(f"OPENROUTER_API_KEY_{i}", "").strip() for i in range(1, 10)]
    api_keys = [k for k in api_keys if k] or (
        [os.getenv("OPENROUTER_API_KEY", "").strip()] if os.getenv("OPENROUTER_API_KEY") else []
    )
    if not api_keys or not any(api_keys):
        print(
            "[FATAL] No OpenRouter API keys found in environment. "
            "Set OPENROUTER_API_KEY_1..4 or OPENROUTER_API_KEY in .env.",
            file=sys.stderr,
        )
        sys.exit(1)

    # 4. Model override if specified
    if args.model:
        os.environ["LLM_MODEL"] = args.model

    # 5. Display Banner
    arsrs_summary = {
        "goal": arsrs_profile.get("goal") or arsrs.get("goal"),
        "system_type": arsrs_profile.get("system_type") or arsrs.get("system_type"),
        "domain": arsrs.get("domain_context", {}).get("industry") or arsrs.get("domain"),
    }

    if args.debug:
        print_debug_banner(args, len(api_keys), arsrs_summary, design_id, debug_log_path)
    else:
        print_normal_banner(args, len(api_keys), design_id, debug_log_path)

    # 6. Instantiate and Run Pipeline
    pipeline = SAEPipeline(
        api_keys=api_keys,
        output_dir=args.output,
        design_id=design_id,
        logs_root=args.logs_dir,
        debug=args.debug,
    )

    t0 = time.perf_counter()
    try:
        package = pipeline.run(arsrs, design_id=design_id)
    except KeyboardInterrupt:
        print("\n[ABORT] Pipeline run cancelled by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as exc:
        print(f"\n[FATAL] Uncaught error during pipeline run: {exc}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

    elapsed = round(time.perf_counter() - t0, 2)

    # 6. Timing Budget Evaluation
    if elapsed > 300:
        print(f"\n[WARNING] Execution time exceeded 5-minute budget: {elapsed}s > 300s", file=sys.stderr)
    elif elapsed >= 240:
        print(f"\n[WARNING] Execution time close to 5-minute budget: {elapsed}s (240s-300s window)")

    # 7. Summary & Scorecard Output
    pkg_dict = package.model_dump(mode="json")
    core_sections = [
        "requirement_analysis",
        "technology_recommendation",
        "architecture_decision_plan",
        "hld",
        "backend_lld",
        "database_lld",
        "frontend_lld",
        "security_lld",
        "cloud_lld",
        "testing_strategy",
        "observability",
        "runbooks",
        "adversarial_review",
    ]
    successful_sections = [s for s in core_sections if pkg_dict.get(s)]
    missing_sections = [s for s in core_sections if not pkg_dict.get(s)]

    print("\n" + "=" * 70)
    print("             SAE v2 PIPELINE EXECUTION SCORECARD")
    print("=" * 70)
    print(f"Elapsed Time       : {elapsed}s ({elapsed/60:.2f} min)")
    print(f"Generated Sections : {len(successful_sections)}/{len(core_sections)}")
    if missing_sections:
        print(f"Partial/Fallback   : {', '.join(missing_sections)}")

    # RAG Metadata Summary
    rag_sections = []
    for s in core_sections:
        sec_data = pkg_dict.get(s, {})
        if isinstance(sec_data, dict) and "rag_metadata" in sec_data:
            meta = sec_data["rag_metadata"]
            if meta.get("used_rag"):
                rag_sections.append(f"{s} (chunks: {meta.get('chunk_count')}, sim: {meta.get('avg_similarity'):.2f})")
            else:
                rag_sections.append(f"{s} (fallback: static)")

    if rag_sections:
        print(f"\n--- RAG Retrieval Inventory ---")
        for rs in rag_sections:
            print(f"  • {rs}")

    # Production Readiness & Quality Report
    completeness_info = pkg_dict.get("completeness", {})
    status = completeness_info.get("status", "UNKNOWN")
    status_icon = "🟢" if status == "HEALTHY" else "🟡"

    print(f"\n--- Production Readiness & Quality Gates ---")
    print(f"  • System Status          : {status_icon} {status}")
    print(f"  • Structural Completeness: {completeness_info.get('structural_completeness', 0)*100:.0f}%")
    print(f"  • Production Readiness   : {completeness_info.get('production_readiness_score', 0)*100:.0f}%")
    print(f"  • Architectural Quality  : {completeness_info.get('architectural_quality_score', 0)*100:.0f}%")
    print(f"  • Overall Composite Score: {completeness_info.get('overall_completeness', 0)*100:.0f}%")

    gates = completeness_info.get("production_readiness_gates", {})
    if gates:
        print(f"\n--- Production Gate Checks ({gates.get('gates_passed_count')}/{gates.get('gates_total')}) ---")
        for gname, gval in gates.items():
            if gname not in ("gates_passed_count", "gates_total"):
                icon = "✓" if gval else "✗"
                print(f"  [{icon}] {gname.replace('_', ' ').title()}")

    # Code Scaffolds
    artifacts = pkg_dict.get("generated_artifacts", {})
    if artifacts:
        print(f"\n--- Generated Code Scaffolds ---")
        for k, v in artifacts.items():
            if k.endswith("_path"):
                print(f"  • {k:<25} -> {v}")

    final_pkg_path = Path(args.output) / "architecture_package.json"
    print(f"\nFinal Unified Package : {final_pkg_path}")
    if debug_log_path:
        print(f"Debug Log Stream      : {debug_log_path}")
        print(f"Logs Directory        : {debug_log_path.parent}")
    print("=" * 70 + "\n")

    # 8. Exit Code Check
    if not successful_sections:
        print("[FATAL] All sections failed to generate.", file=sys.stderr)
        sys.exit(1)

    print("[SUCCESS] Pipeline run finished successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
