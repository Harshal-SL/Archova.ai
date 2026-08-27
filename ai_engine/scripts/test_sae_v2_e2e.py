"""End-to-End Test for SAE v2 Lean Multi-Agent Pipeline.

Runs the complete 4-phase pipeline against real ARSRS:
  Phase 1: Planning (Req Analysis + Tech Advisor + ADP)
  Phase 2: HLD Generation
  Phase 3: 5-way Parallel LLD Generation (Backend, DB, Frontend, Security, Cloud)
  Phase 4: Unified Architecture Package Assembly & Completeness Report

Usage:
    python scripts/test_sae_v2_e2e.py
"""

from __future__ import annotations

import io
import json
import os
import sys
import time
from pathlib import Path

# Unbuffered output for Windows consoles
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=True)

from app.sae.pipeline import SAEPipeline


def main():
    print("=" * 60, flush=True)
    print(" SAE v2 LEAN MULTI-AGENT PIPELINE END-TO-END TEST", flush=True)
    print("=" * 60, flush=True)

    arsrs_path = PROJECT_ROOT / "output" / "arsrs.json"
    if not arsrs_path.exists():
        print(f"[ERROR] ARSRS file not found at {arsrs_path}", flush=True)
        sys.exit(1)

    with open(arsrs_path, "r", encoding="utf-8") as f:
        arsrs = json.load(f)

    out_dir = PROJECT_ROOT / "outputs" / f"test_sae_v2_{int(time.time())}"
    pipeline = SAEPipeline(output_dir=str(out_dir), debug=True)

    print(f" Output Directory : {pipeline.output_dir}", flush=True)
    print(f" LLM Model        : {pipeline.llm_provider.default_model}", flush=True)
    print(f" API Keys Count   : {len(pipeline.llm_provider.api_keys)}", flush=True)
    print("-" * 60, flush=True)

    t0 = time.perf_counter()
    package = pipeline.run(arsrs)
    total_time = round(time.perf_counter() - t0, 2)

    print("\n" + "=" * 60, flush=True)
    print(" PIPELINE EXECUTION SUMMARY", flush=True)
    print("=" * 60, flush=True)
    print(f" Status             : SUCCESS", flush=True)
    print(f" Total Elapsed Time : {total_time}s ({total_time/60:.1f} minutes)", flush=True)
    print(f" Target Duration    : <= 300s (5 minutes)", flush=True)
    print(f" Time Budget Check  : {'[PASS] UNDER 5 MIN' if total_time <= 300 else '[WARN] OVER 5 MIN'}", flush=True)
    print("-" * 60, flush=True)

    timings = package.metadata.get("phase_timings", {})
    print(f" Phase 1 (Planning) : {timings.get('phase1_planning_seconds', '?')}s", flush=True)
    print(f" Phase 2 (HLD)      : {timings.get('phase2_hld_seconds', '?')}s", flush=True)
    print(f" Phase 3 (5-way LLD): {timings.get('phase3_lld_parallel_seconds', '?')}s", flush=True)
    print(f" Phase 4 (Assembly) : {timings.get('phase4_assembly_seconds', '?')}s", flush=True)
    print("-" * 60, flush=True)

    completeness = package.completeness
    print(f" Overall Quality    : {completeness.get('overall_completeness', 0.0)*100:.0f}%", flush=True)
    print(f" Status             : {completeness.get('status', 'UNKNOWN')}", flush=True)
    print(" Section Fill Rates :", flush=True)
    for sec, score in completeness.get("section_scores", {}).items():
        print(f"   • {sec:<28}: {score*100:.0f}%", flush=True)

    # Check generated files
    files = list(pipeline.output_dir.glob("*.json"))
    print(f"\n Generated Artifacts ({len(files)} JSON files):", flush=True)
    for f in sorted(files):
        size_kb = round(f.stat().st_size / 1024, 1)
        print(f"   • {f.name} ({size_kb} KB)", flush=True)

    print("=" * 60, flush=True)


if __name__ == "__main__":
    main()
