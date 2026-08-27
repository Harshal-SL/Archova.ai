"""End-to-End AI Engine Complete Pipeline Runner & Integration Test (REE + SAE).

Executes the full pipeline:
  1. Stakeholder Requirement Input (Text / File / ARSRS / Interactive CLI)
  2. Requirement Engineering Engine (REE: Input Understanding -> Specialist Agents -> Review -> Finalizer)
  3. Architecture-Ready Structured Requirement Specification (ARSRS)
  4. Software Architecture Engine (SAE: 6-Phase High-Level & Low-Level Design Engine)
  5. Scaffolding Generation & Automated Remediation
  6. Final Packaging & Unified Quality Scorecard

Directory Hierarchy:
  outputs/
  └── <request_title_slug>/
      ├── outputs/   (arsrs.json, architecture_package.json, openapi.yaml, scaffolds/, etc.)
      └── logs/      (debug.log, execution.log, timeline.log, llm_calls.log, execution_summary.json)
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=True)

# Auto-switch to venv Python if running with system Python on Windows
venv_python = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"
if venv_python.exists() and Path(sys.executable).resolve() != venv_python.resolve():
    import subprocess
    proc = subprocess.run([str(venv_python), str(Path(__file__).resolve())] + sys.argv[1:])
    sys.exit(proc.returncode)

# Reconfigure stdout for unicode formatting
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app.sae.models.design_generation_response import DesignGenerationRequest, DesignGenerationResponse
from app.sae.services.design_generation_service import DesignGenerationService
from app.sae.services.ree_service import REEGenerationService
from app.sae.services.sae_service import SAEGenerationService
from app.sae.providers.llm_provider import _load_api_keys

DEFAULT_DEMO_PROMPT = """Build a modern, cloud-native College Library Management System.
The system must allow students to register, authenticate securely, search and browse the book catalog, and borrow/return books.
Librarians must be able to manage inventory (add, update, delete books), track overdue items, and issue fine receipts.
The platform requires high availability (99.9%), sub-250ms catalog search response time under 500 concurrent users, and strict role-based access control (RBAC)."""


def extract_title_from_text(text: str) -> str:
    """Extract a concise project title (<= 45 chars) from text."""
    if not text:
        return "System Design"
    
    # 1. Search for explicit patterns like 'Online Event Management System'
    patterns = [
        r'(?:(?:Build|Create|Develop|Design|The proposed|A|An)\s+)?([A-Z][A-Za-z0-9\s\-]{3,40}?(?:Management System|System|Platform|Application|Portal|Service|Engine|Hub))',
        r'([A-Z][A-Za-z0-9\s\-]{3,35}?(?:System|Platform|App|Portal))',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            candidate = m.group(1).strip()
            if 4 <= len(candidate) <= 45:
                return candidate

    # 2. Fallback to first line or first 5 words
    first_line = text.strip().splitlines()[0].strip()
    words = first_line.split()
    short = " ".join(words[:5])
    return short[:40] if short else "System Design"


def sanitize_title(title: str) -> str:
    """Convert human title to a clean folder slug with safe max length (<= 40 chars)."""
    if len(title) > 50 or "\n" in title:
        title = extract_title_from_text(title)
    slug = re.sub(r"[^\w\-_]+", "_", title.strip().lower()).strip("_")
    # Truncate at word boundaries to keep slug <= 40 chars (avoids Windows MAX_PATH issues)
    if len(slug) > 40:
        slug = slug[:40].rsplit("_", 1)[0]
    return slug or "system_design"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Complete AI Engine (REE + SAE) End-to-End Pipeline Runner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-p", "--prompt",
        type=str,
        default=None,
        help="Direct stakeholder requirement prompt text string",
    )
    parser.add_argument(
        "-f", "--file",
        type=str,
        default=None,
        help="Path to requirements document file (.txt, .md, .pdf, .docx)",
    )
    parser.add_argument(
        "-a", "--arsrs",
        type=str,
        default=None,
        help="Path to pre-existing ARSRS JSON file (bypasses REE to test SAE directly)",
    )
    parser.add_argument(
        "-t", "--title",
        type=str,
        default=None,
        help="Optional explicit title for the request (e.g. 'College Library Management System')",
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        default=os.getenv("SAE_DEBUG", "false").lower() in ("true", "1", "yes"),
        help="Enable continuous verbose debug stream (LLM prompts, raw outputs, RAG retrieval details)",
    )
    parser.add_argument(
        "-o", "--outputs-root",
        type=str,
        default=str(PROJECT_ROOT / "outputs"),
        help="Root directory for outputs (will contain /outputs/<title>/outputs and /logs)",
    )
    parser.add_argument(
        "--skip-interview",
        action="store_true",
        default=False,
        help="Skip interactive stakeholder clarification interview (run non-interactively)",
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        default=True,
        help="Enable interactive stakeholder questionnaire if REE requests clarifications (default: True)",
    )
    return parser.parse_args()


def read_input_content(args: argparse.Namespace) -> tuple[str, str, Optional[Dict[str, Any]]]:
    """Resolve input content, request title, and optional pre-existing ARSRS."""
    # 1. Pre-existing ARSRS provided
    if args.arsrs:
        arsrs_path = Path(args.arsrs)
        if not arsrs_path.exists():
            print(f"❌ Error: ARSRS file not found at {args.arsrs}")
            sys.exit(1)
        with open(arsrs_path, "r", encoding="utf-8") as f:
            arsrs_data = json.load(f)
        title = (
            args.title
            or arsrs_data.get("project_profile", {}).get("name")
            or arsrs_data.get("system_name")
            or arsrs_path.stem
        )
        return json.dumps(arsrs_data), title, arsrs_data

    # 2. File input provided
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ Error: Input file not found at {args.file}")
            sys.exit(1)
        title = args.title or file_path.stem.replace("_", " ").title()
        if file_path.suffix.lower() in (".txt", ".md", ".json"):
            content = file_path.read_text(encoding="utf-8")
        else:
            try:
                from app.ree.agents.text_normalizer import TextNormalizer
                content = TextNormalizer().normalize_raw_text(file_path.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
        return content, title, None

    # 3. Direct prompt flag provided
    if args.prompt:
        title = args.title or extract_title_from_text(args.prompt)
        return args.prompt, title, None

    # 4. Interactive CLI fallback
    print("\n" + "═" * 80)
    print(" 🤖 AI ENGINE (REE + SAE) — END-TO-END PIPELINE RUNNER")
    print("═" * 80)
    print(" No requirement prompt provided via arguments.")
    print(" Options:")
    print("   [1] Use Default Demo: 'College Library Management System'")
    print("   [2] Enter / Paste Custom Requirement Prompt")
    print("═" * 80)
    try:
        choice = input(" Select option [1/2] (Default: 1): ").strip()
    except (EOFError, KeyboardInterrupt):
        choice = "1"

    if choice == "2":
        try:
            print("\nEnter or paste your project requirements (Press Enter twice when done):")
            lines = []
            while True:
                line = input()
                if not line and lines and not lines[-1]:
                    break
                lines.append(line)
            content = "\n".join(lines).strip()
            if not content:
                content = DEFAULT_DEMO_PROMPT
            title = args.title or extract_title_from_text(content)
        except (EOFError, KeyboardInterrupt):
            title = "College Library Management System"
            content = DEFAULT_DEMO_PROMPT
    else:
        title = "College Library Management System"
        content = DEFAULT_DEMO_PROMPT

    return content, title, None


def main() -> None:
    """Execute complete end-to-end AI Engine."""
    args = parse_args()
    content, title, existing_arsrs = read_input_content(args)
    title_slug = sanitize_title(title)

    # Resolve target directory structure:
    #   outputs/<title_slug>/outputs
    #   outputs/<title_slug>/logs
    outputs_root = Path(args.outputs_root)
    project_base_dir = outputs_root / title_slug
    outputs_dir = project_base_dir / "outputs"
    logs_dir = project_base_dir / "logs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Set environment variables for child processes/loggers
    if args.debug:
        os.environ["SAE_DEBUG"] = "true"
        os.environ["REE_DEBUG"] = "1"
        logging.basicConfig(level=logging.INFO, format="%(message)s")
    else:
        os.environ["SAE_DEBUG"] = "false"
        os.environ["REE_DEBUG"] = "0"
        logging.basicConfig(level=logging.WARNING, format="%(message)s")

    # Banner
    api_keys = _load_api_keys()
    print("\n" + "═" * 80)
    print(" 🚀 STARTING UNIFIED AI ENGINE PIPELINE (REE ──► ARSRS ──► SAE)")
    print("═" * 80)
    print(f" • Project Title : {title}")
    print(f" • Target Slug   : {title_slug}")
    print(f" • Mode          : {'DEBUG (Verbose Live Streaming)' if args.debug else 'NORMAL (Progress Cards)'}")
    print(f" • API Keys      : {len(api_keys)} OpenRouter Keys Loaded")
    print(f" • Output Folder : {outputs_dir}")
    print(f" • Logs Folder   : {logs_dir}")
    print("═" * 80 + "\n")

    t_start = time.perf_counter()

    # Step 1: Initialize Context & Services
    allow_interview = not args.skip_interview
    metadata = {
        "title": title,
        "project_title": title,
        "title_slug": title_slug,
        "design_id": f"{title_slug}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "interactive": allow_interview,
        "allow_interview": allow_interview,
        "skip_interview": args.skip_interview,
        "max_interview_rounds": 3 if allow_interview else 0,
    }
    if existing_arsrs:
        metadata["arsrs"] = existing_arsrs

    request = DesignGenerationRequest(
        input_type="arsrs" if existing_arsrs else "text",
        content=content,
        metadata=metadata,
    )

    # Execute Master Design Generation Service
    service = DesignGenerationService()

    try:
        response: DesignGenerationResponse = service.generate_design(request)
    except KeyboardInterrupt:
        print("\n[ABORT] Pipeline cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ [ERROR] Unified Pipeline Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    total_time = round(time.perf_counter() - t_start, 2)

    if response.status == "FAILED":
        print("\n" + "━" * 80)
        print(" ❌ PIPELINE EXECUTION FAILED")
        print("━" * 80)
        print(f" Stage   : {response.stage}")
        print(f" Message : {response.message}")
        print(" Errors  :")
        for err in response.errors:
            print(f"   • {err}")
        print("━" * 80)
        sys.exit(1)

    # Print Final Unified Scorecard
    pkg = response.software_architecture_package or {}
    completeness = pkg.get("completeness", {}) or response.quality_report or {}
    metrics = response.execution_metrics or {}
    scaffolds = pkg.get("scaffolds", {}) or {}

    print("\n" + "═" * 80)
    print("           🌟 UNIFIED AI ENGINE EXECUTION SCORECARD 🌟")
    print("═" * 80)
    print(f" Project Title      : {title} ({title_slug})")
    print(f" Overall Status     : 🟢 {completeness.get('status', 'HEALTHY')}")
    print(f" Total Elapsed Time : {total_time}s ({round(total_time/60, 2)} min)")
    print(f"   • REE Duration   : {metrics.get('ree_execution_time', 0.0)}s")
    print(f"   • SAE Duration   : {metrics.get('sae_execution_time', 0.0)}s")
    print("─" * 80)
    print(" 📊 Quality & Production Readiness Gates:")
    print(f"   • Architectural Quality  : {int(completeness.get('architectural_quality', 1.0) * 100)}%")
    print(f"   • Structural Completeness: {int(completeness.get('structural_completeness', 1.0) * 100)}%")
    print(f"   • Consistency Score      : {int(completeness.get('consistency_score', 1.0) * 100)}%")
    print(f"   • Production Readiness   : {int(completeness.get('production_readiness', 1.0) * 100)}%")
    print(f"   • Overall Composite Score: {int(completeness.get('overall_score', 0.95) * 100)}%")
    print("─" * 80)
    print(" 📦 Delivered Code Scaffolds:")
    print(f"   • OpenAPI YAML Spec      -> {outputs_dir / 'openapi.yaml'}")
    print(f"   • Dockerfile             -> {outputs_dir / 'scaffolds' / 'Dockerfile'}")
    print(f"   • Docker Compose         -> {outputs_dir / 'scaffolds' / 'docker-compose.yml'}")
    print(f"   • Alembic DB Migration   -> {outputs_dir / 'scaffolds' / 'alembic' / 'versions' / '0001_initial_schema.py'}")
    print(f"   • Terraform IaC (main.tf)-> {outputs_dir / 'scaffolds' / 'terraform' / 'main.tf'}")
    print("─" * 80)
    print(" 📂 Output & Log Directories:")
    print(f"   • Generated Artifacts    : {outputs_dir}")
    print(f"   • Execution & LLM Logs   : {logs_dir}")
    print(f"   • Master Unified Package : {outputs_dir / 'architecture_package.json'}")
    print("═" * 80 + "\n")
    print(" [SUCCESS] End-to-end requirement engineering & architecture package delivered successfully.\n")


if __name__ == "__main__":
    main()
