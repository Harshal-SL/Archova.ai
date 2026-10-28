"""Opt-in live smoke verification script for Validator Engine v2.

Runs selection, extraction, pattern comparison, and rubric review for ONE chosen artifact
using real LLM calls (opt-in only).

Requirements:
- Set VALIDATOR_API_KEY to a valid key.
- Set VALIDATOR_MOCK=0 (must be explicit live mode).

Usage:
    python -m Validator_Engine_v2.scripts.live_smoke --package path/to/package.json --artifact backend
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Validator_Engine_v2.config import config
from Validator_Engine_v2.decision.scoring import compute_artifact_score
from Validator_Engine_v2.l0_normalize.normalizer import PackageNormalizer
from Validator_Engine_v2.l1_evidence.dockerfile_check import check_dockerfile
from Validator_Engine_v2.l1_evidence.migration_check import check_migration
from Validator_Engine_v2.l1_evidence.openapi_check import check_openapi
from Validator_Engine_v2.l1_evidence.terraform_check import check_terraform
from Validator_Engine_v2.real_world.comparator import PatternComparator
from Validator_Engine_v2.real_world.corpus_loader import CorpusLoader
from Validator_Engine_v2.real_world.profile_extractor import ProfileExtractor
from Validator_Engine_v2.real_world.scoring import score_real_world_assessments
from Validator_Engine_v2.real_world.selector import SystemSelector
from Validator_Engine_v2.review.llm_client import ReviewerLLMClient
from Validator_Engine_v2.review.reviewer import Reviewer
from Validator_Engine_v2.schemas import ReferenceSystemUsed


async def run_live_smoke(package_path: Path, artifact_name: str) -> None:
    api_key = os.getenv("VALIDATOR_API_KEY", "").strip()
    mock_mode = os.getenv("VALIDATOR_MOCK", "1").strip().lower()

    if not api_key or mock_mode != "0":
        print("=" * 80)
        print("OPT-IN LIVE SMOKE SKIPPED:")
        print("Live smoke execution requires VALIDATOR_API_KEY and VALIDATOR_MOCK=0.")
        print(f"Current state: VALIDATOR_API_KEY={'set' if api_key else 'EMPTY'}, VALIDATOR_MOCK={mock_mode}")
        print("=" * 80)
        sys.exit(0)

    print(f"Loading architecture package from: {package_path}")
    raw_package = json.loads(package_path.read_text(encoding="utf-8"))

    # 1. Normalize and run static analysis
    normalizer = PackageNormalizer()
    normalized = normalizer.normalize(raw_package)
    l0_findings = normalizer.validate_schema(normalized)

    scaffolds = normalized.scaffold_files
    l1_findings = []
    op_f, _ = check_openapi(scaffolds.get("openapi.yaml") or scaffolds.get("scaffolds/openapi.yaml"), normalized.endpoints)
    l1_findings.extend(op_f)
    df_f, _ = check_dockerfile(scaffolds.get("Dockerfile") or scaffolds.get("scaffolds/Dockerfile"))
    l1_findings.extend(df_f)
    cloud_data = normalized.raw_package.get("llds", {}).get("cloud", {})
    if isinstance(cloud_data, dict) and "data" in cloud_data:
        cloud_data = cloud_data["data"]
    tf_f, _ = check_terraform(scaffolds.get("terraform/main.tf") or scaffolds.get("scaffolds/terraform/main.tf"), cloud_data if isinstance(cloud_data, dict) else {})
    l1_findings.extend(tf_f)
    mg_f, _ = check_migration(scaffolds.get("alembic/versions/0001_initial_schema.py") or scaffolds.get("scaffolds/alembic/versions/0001_initial_schema.py"), normalized.tables)
    l1_findings.extend(mg_f)

    # 2. Extract artifact payload
    art_lower = artifact_name.lower()
    if art_lower == "hld":
        artifact_data = raw_package.get("hld", {})
    else:
        llds = raw_package.get("llds", {})
        raw_art = llds.get(art_lower, {})
        artifact_data = raw_art.get("data", raw_art) if isinstance(raw_art, dict) else {}

    if not artifact_data:
        print(f"Error: Target artifact '{artifact_name}' has no data in package.")
        sys.exit(1)

    # 3. Real-World Benchmark Corpus Selection
    print("Loading Real-World Corpus...")
    loader = CorpusLoader(corpus_path=config.REAL_WORLD_CORPUS_PATH)
    docs = loader.load_corpus()
    selector = SystemSelector(top_k=config.REAL_WORLD_TOP_K)
    selected_systems = selector.select(docs, normalized.raw_package.get("arsrs", {}))

    print(f"Selected {len(selected_systems)} Reference Systems:")
    references_used = []
    for s in selected_systems:
        print(f"  - {s.doc.system_name} (Score: {s.score:.1f}, Reasons: {', '.join(s.match_reasons)})")
        if s.scale_note:
            print(f"    Scale Note: {s.scale_note}")
        references_used.append(
            ReferenceSystemUsed(
                id=s.doc.id,
                system_name=s.doc.system_name,
                match_reasons=s.match_reasons,
                scale_note=s.scale_note,
                sources=s.doc.sources,
            )
        )

    # 4. Profile Extraction
    llm_client = ReviewerLLMClient(
        api_base=config.VALIDATOR_API_BASE,
        api_key=api_key,
        model=config.VALIDATOR_MODEL,
        mock_mode="0",
    )
    extractor = ProfileExtractor(llm_client=llm_client)

    all_patterns = []
    system_names_by_pattern = {}
    for s in selected_systems:
        prof = await extractor.extract_profile(s.doc)
        for p in prof.patterns:
            all_patterns.append(p)
            system_names_by_pattern[p.id] = s.doc.system_name

    # 5. Rubric Review & Comparator Execution
    print(f"\nExecuting Live LLM Rubric Review for '{artifact_name}'...")
    reviewer = Reviewer(llm_client=llm_client)
    rubric_res = await reviewer.review_artifact(art_lower, artifact_data, normalized)

    print(f"Executing Live LLM Real-World Pattern Comparison for '{artifact_name}'...")
    comparator = PatternComparator(llm_client=llm_client)
    assessments = await comparator.compare_artifact(
        artifact_name=art_lower,
        artifact_data=artifact_data,
        patterns=all_patterns,
        system_names_by_pattern=system_names_by_pattern,
        arsrs=normalized.raw_package.get("arsrs", {}),
    )

    rw_result, rw_findings = score_real_world_assessments(
        artifact_name=art_lower,
        assessments=assessments,
        artifact_data=artifact_data,
        references_used=references_used,
    )

    # 6. Scoring & Deductions
    final_result = compute_artifact_score(
        artifact_name=art_lower,
        reviewer_result=rubric_res,
        l0_findings=l0_findings,
        l1_findings=l1_findings,
        real_world_result=rw_result,
        real_world_findings=rw_findings,
        reviewer_mode="live",
    )

    # 7. Print Diagnostic Summary
    print("\n" + "=" * 80)
    print(f"LIVE SMOKE RESULTS FOR ARTIFACT: {artifact_name.upper()}")
    print("=" * 80)
    print(f"Verdict:           {final_result.verdict}")
    print(f"Final Score:       {final_result.final_score} / 100")
    print(f"Rubric Score:      {final_result.rubric_score} / 100")
    print(f"Real-World Score:  {rw_result.score if rw_result else 'None'} (Confidence: {rw_result.confidence if rw_result else 'N/A'})")
    print(f"Dropped Unverified Findings:    {final_result.dropped_unverified}")
    print(f"Downgraded Unverified Patterns: {rw_result.counts.get('downgraded_unverified', 0) if rw_result else 0}")
    print(f"Total Findings Flagged:         {len(final_result.findings)}")

    print("\n--- Dimension Scores ---")
    for d in final_result.dimensions:
        print(f"  [{d.id}] Score: {d.score}/5 | Weight: {d.weight} | Evidence: {d.evidence_path}")
        if d.missing:
            print(f"      Missing: {', '.join(d.missing)}")

    print("\n--- Real-World Pattern Statuses ---")
    if rw_result:
        for a in rw_result.assessments:
            print(f"  [{a.status:20s}] {a.pattern_id}: {a.pattern_name} ({a.system_name})")
            print(f"      Justification: {a.justification}")
            if a.evidence_path:
                print(f"      Evidence:      {a.evidence_path}")
            if a.requirement_refs:
                print(f"      Refs:          {', '.join(a.requirement_refs)}")

    print("\n--- Findings Flagged ---")
    for f in final_result.findings:
        print(f"  [{f.severity.upper():8s}] {f.rule_id} ({f.layer}): {f.message}")
        if f.evidence_path:
            print(f"      Evidence: {f.evidence_path}")
        if f.suggested_fix:
            print(f"      Fix:      {f.suggested_fix}")

    print("\n--- Composite Breakdown ---")
    print(
        f"Composite: (1 - w)*{final_result.rubric_score} + w*{rw_result.score if rw_result else 0} "
        f"- deductions -> Final Score: {final_result.final_score} -> Verdict: {final_result.verdict}"
    )
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description="Live smoke verification of Validator Engine v2.")
    parser.add_argument("--package", type=str, default="Validator_Engine_v2/tests/fixtures/sample_package.json")
    parser.add_argument("--artifact", type=str, default="backend")
    args = parser.parse_args()

    asyncio.run(run_live_smoke(Path(args.package), args.artifact))


if __name__ == "__main__":
    main()
