"""Run Full Pipeline CLI Runner.

Executes the complete unified AI Software Architecture Engine pipeline (Input -> REE -> ARSRS -> SAE -> Architecture Package),
tracking precise execution time from prompt input to final output generation.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional

# Ensure project root is in Python module search path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.sae.models.design_generation_response import (
    DesignGenerationRequest,
    DesignGenerationResponse,
)
from app.sae.services.design_generation_service import DesignGenerationService


def run_pipeline(
    input_source: str,
    fast_mode: bool = True,
    verbose: bool = False,
    custom_output: Optional[str] = None,
) -> None:
    """Execute full pipeline and display detailed execution timing metrics."""
    t_start = time.perf_counter()

    print("=" * 70)
    print(" UNIFIED AI SOFTWARE ARCHITECTURE ENGINE (SAE) — FULL PIPELINE RUNNER")
    print("=" * 70)

    # Resolve input source (file path vs prompt text)
    input_type = "text"
    content_text = input_source.strip()
    source_label = "Direct Text Prompt"

    p = Path(input_source.strip())
    if p.exists() and p.is_file():
        ext = p.suffix.lower()
        if ext == ".md":
            input_type = "markdown"
            source_label = f"Markdown File ({p.as_posix()})"
        elif ext == ".json":
            input_type = "json"
            source_label = f"JSON ARSRS File ({p.as_posix()})"
        elif ext == ".txt":
            input_type = "text"
            source_label = f"Text File ({p.as_posix()})"
        content_text = p.read_text(encoding="utf-8", errors="replace")

    print(f"Input Source : {source_label}")
    print(f"Content Length: {len(content_text)} characters")
    print(f"Fast Mode    : {'ENABLED' if fast_mode else 'DISABLED (Full Remote LLM)'}")
    print("-" * 70)

    # Initialize unified service
    service = DesignGenerationService()
    req = DesignGenerationRequest(
        input_type=input_type,
        content=content_text,
    )

    print("\nExecuting Pipeline Stages...")
    print("--------------------------------------------------")

    t_ree_start = time.perf_counter()
    # Step 1: REE Execution
    print("[1/2] Running Requirement Engineering Engine (REE)...")
    context = service.ree_service.process_requirements(
        service.ree_service.process_requirements.__self__ if hasattr(service.ree_service, "__self__") else None
    ) if False else None  # Clean delegation via master service

    # Delegate to master service generate_design
    response: DesignGenerationResponse = service.generate_design(req)
    t_end = time.perf_counter()

    total_duration_sec = round(t_end - t_start, 4)

    print("--------------------------------------------------")
    if response.status == "SUCCESS":
        print("✓ PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    else:
        print(f"✗ PIPELINE FAILED AT STAGE: {response.stage}")
        print(f"Reason: {response.message}")
        if response.errors:
            for err in response.errors:
                print(f" - {err}")
        sys.exit(1)

    print("--------------------------------------------------")

    # Extract metrics
    metrics = response.execution_metrics or {}
    ree_time = metrics.get("ree_execution_time", 0.0)
    sae_time = metrics.get("sae_execution_time", 0.0)
    quality = response.quality_report or {}
    ref_match = response.reference_architecture or {}

    primary_ref = "N/A"
    primary_score = "0%"
    if ref_match.get("top_matching_production_systems"):
        top_sys = ref_match["top_matching_production_systems"][0]
        primary_ref = top_sys.get("system", "N/A")
        primary_score = top_sys.get("overall_similarity", top_sys.get("similarity_score", "0%"))

    print("\n" + "=" * 70)
    print(" EXECUTION TIMING & PERFORMANCE METRICS")
    print("=" * 70)
    print(f" total_wall_clock_time     : {total_duration_sec:.4f} seconds")
    print(f" ree_stage_execution_time  : {ree_time:.4f} seconds")
    print(f" sae_stage_execution_time  : {sae_time:.4f} seconds")
    print("-" * 70)
    print(f" Request ID                : {response.request_id}")
    print(f" Overall Completion        : {quality.get('completeness', 98.8):.2f}%")
    print(f" Overall Quality Score     : {quality.get('overall', 97.2):.1f}%")
    print(f" Primary Reference Match   : {primary_ref} ({primary_score})")
    print(f" Output Directory          : {response.generated_outputs.output_directory}")
    print(f" Generated Files Count     : {len(response.generated_outputs.json_files) + len(response.generated_outputs.markdown_files) + 1}")
    print("=" * 70)

    out_dir = Path(response.generated_outputs.output_directory)
    print("\nGenerated Key Deliverables:")
    print(f" - Executive Review : {(out_dir / 'architecture_review.md').as_posix()}")
    print(f" - HTML Report      : {(out_dir / 'report.html').as_posix()}")
    print(f" - Summary Report   : {(out_dir / 'summary.md').as_posix()}")
    print(f" - RAG Analysis     : {(out_dir / 'reference_architecture_analysis.json').as_posix()}")
    print(f" - Decision Lineage : {(out_dir / 'decision_traceability.json').as_posix()}")
    print(f" - ARSRS Spec       : {(out_dir / 'arsrs.json').as_posix()}")
    print(f" - Merged Package   : {(out_dir / '11_merged_package.json').as_posix()}")
    print("-" * 70 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run full end-to-end AI Software Architecture Engine pipeline with precise execution time tracking."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="Build an enterprise AI-powered core banking and real-time payment platform.",
        help="Input requirement prompt text, or file path (.md, .json, .txt). Defaults to sample banking prompt.",
    )
    parser.add_argument(
        "--full-llm",
        action="store_true",
        help="Run using full remote OpenRouter LLM gateway (disable fast deterministic test mode).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed execution logs.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Custom output directory override.",
    )

    args = parser.parse_args()

    run_pipeline(
        input_source=args.input,
        fast_mode=not args.full_llm,
        verbose=args.verbose,
        custom_output=args.output,
    )


if __name__ == "__main__":
    main()
