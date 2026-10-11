"""Command-line interface for the Validator Engine.

Usage:
    python -m Validator_Engine.cli <input_architecture.json> [-o <output_validated.json>] [--pretty]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from Validator_Engine.engine import ValidatorEngine


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validator Engine: Standalone Architecture Verification & Evidence Assessor",
    )
    parser.add_argument(
        "input_path",
        type=str,
        help="Path to the input architecture package JSON file (e.g. 10_architecture_package.json)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Path to save the validated_architecture.json output. If omitted, prints summary to stdout.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Format JSON output with 2-space indentation.",
    )

    args = parser.parse_args()
    input_file = Path(args.input_path)

    if not input_file.exists():
        print(f"Error: Input file does not exist: {input_file}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading and validating architecture package from {input_file}...")
    engine = ValidatorEngine()
    response = engine.validate(input_file)

    # Output result
    output_dict = response.model_dump(mode="json")
    indent = 2 if args.pretty else None
    json_str = json.dumps(output_dict, indent=indent, default=str)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json_str, encoding="utf-8")
        print(f"Validated architecture successfully saved to: {out_path}")
    else:
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        print(f"System: {response.system_name} ({response.domain})")
        print(f"Status: {response.status}")
        print(f"Overall Composite Score: {response.scorecard.overall_composite_score * 100:.1f}%")
        print(f"Production Readiness: {response.scorecard.production_readiness_score * 100:.1f}%")
        print(f"Consistency Score: {response.scorecard.consistency_score * 100:.1f}%")
        print(f"Traceability Score: {response.scorecard.traceability_score * 100:.1f}%")
        print(f"Total Remediation Actions: {len(response.remediation_plan.actions)}")
        print(f"Hard Gate Violations: {len(response.scorecard.hard_gate_violations)}")
        if response.scorecard.hard_gate_violations:
            for v in response.scorecard.hard_gate_violations:
                print(f"  - [FAIL] {v}")
        print("=" * 60)


if __name__ == "__main__":
    main()
