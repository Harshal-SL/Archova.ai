"""
Interactive REE Testing Playground

Standalone developer testing utility for manually testing the Requirements
Engineering Engine (REE) with real or simulated stakeholder input.

Usage:
    py scripts/test_ree_playground.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import reload_settings, print_startup_env_diagnostics
from app.ree.llm.model_registry import reload_registry
from app.ree.llm.gateway import reload_gateway, llm_gateway
from app.ree.logger import ree_logger

# Parse --debug flag from sys.argv
IS_DEBUG = "--debug" in sys.argv
if IS_DEBUG:
    os.environ["REE_DEBUG"] = "1"

ree_logger.set_debug_mode(IS_DEBUG)

# Ensure .env is loaded before any module uses cached settings
reload_settings()
reload_registry()
reload_gateway()

if IS_DEBUG:
    print_startup_env_diagnostics()

from app.ree import REEOrchestrator, REERequest, REEStatus


def load_file_content(file_path: str, expected_ext: Optional[str] = None) -> str:
    """Load text content from a given file path (PDF, DOCX, TXT, MD)."""
    clean_path = file_path.strip().strip('"\'')
    path = Path(clean_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()
    if expected_ext and ext != expected_ext and not (expected_ext == ".md" and ext in (".md", ".markdown")):
        print(f"[Warning] Expected {expected_ext} extension, but got {ext}. Attempting to parse anyway.")

    if ext in (".txt", ".md", ".markdown"):
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    elif ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            pages = [page.extract_text() for page in reader.pages if page.extract_text()]
            if not pages:
                raise ValueError("PDF file contains no extractable text.")
            return "\n\n".join(pages)
        except Exception as exc:
            raise RuntimeError(f"Failed to read PDF file '{path}': {exc}") from exc

    elif ext == ".docx":
        try:
            import docx
            doc = docx.Document(str(path))
            full_text = [p.text for p in doc.paragraphs if p.text.strip()]
            if not full_text:
                raise ValueError("DOCX file contains no text.")
            return "\n\n".join(full_text)
        except Exception as exc:
            raise RuntimeError(f"Failed to read DOCX file '{path}': {exc}") from exc

    else:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()


def prompt_multiline_text(initial_line: Optional[str] = None) -> str:
    """Prompt the user for multi-line text input until 'END' or blank line."""
    print("\n--- Paste Project Description ---")
    print("Paste your text below. When finished, enter 'END' on a new line (or press Enter twice).")
    print("-" * 50)

    lines = []
    if initial_line:
        lines.append(initial_line)
        print(initial_line)

    consecutive_empty = 0
    while True:
        try:
            line = input()
        except EOFError:
            break

        if line.strip().upper() == "END":
            break

        if not line.strip():
            consecutive_empty += 1
            if consecutive_empty >= 2:
                break
        else:
            consecutive_empty = 0

        lines.append(line)

    return "\n".join(lines).strip()


def run_interview_loop(
    orchestrator: REEOrchestrator,
    initial_response: REEResponse,
) -> REEResponse:
    """Handle interactive interview rounds when status is INTERVIEWING."""
    response = initial_response

    while response.status == REEStatus.INTERVIEWING:
        src = response.src or {}
        session = src.get("interview_session") or {}
        rounds = session.get("rounds") or []

        if not rounds:
            # Fall back to interview_result
            interview_res = response.interview_result or {}
            questions = interview_res.get("questions") or []
            round_num = interview_res.get("round", 1)
            if not questions:
                if ree_logger.is_debug:
                    print("\n[Error] Status is INTERVIEWING but no questions found.")
                break
        else:
            latest_round = rounds[-1]
            questions = latest_round.get("questions") or []
            round_num = latest_round.get("round_number", len(rounds))

        if not questions:
            if ree_logger.is_debug:
                print("[Warning] Status is INTERVIEWING but no questions were generated. Stopping loop.")
            break

        ree_logger.print_interview_round_header(round_num)

        answers: List[Dict[str, Any]] = []
        for i, q in enumerate(questions, 1):
            q_id = q.get("question_id", f"q{i}")
            target_field = q.get("target_field") or q.get("target_section") or "general"
            q_text = q.get("question", "")

            prompt_str = ree_logger.format_question_prompt(i, q_text)
            try:
                ans_text = input(prompt_str).strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[Interview interrupted]")
                return response

            answers.append({
                "question_id": q_id,
                "parameter": target_field,
                "answer_text": ans_text,
                "answer": ans_text,
            })

        prompt_text = src.get("raw_input") or src.get("project_context", {}).get("normalized_text", "")
        resume_request = REERequest(
            combined_prompt=prompt_text,
            prior_src=src,
            interview_answers=answers,
        )
        response = orchestrator.run(resume_request)

    return response


def print_formatted_summary(arsrs: Dict[str, Any], src: Dict[str, Any]):
    """Print clean summary sections of the final requirements engineering output."""
    print("\n" + "=" * 70)
    print("                      REQUIREMENTS SUMMARY")
    print("=" * 70)

    # Project Summary
    profile = arsrs.get("project_profile", {})
    print("\n--- Project Summary ---")
    print(f"  Goal:        {profile.get('goal') or arsrs.get('goal', 'N/A')}")
    print(f"  System Type: {profile.get('system_type') or arsrs.get('system_type', 'N/A')}")
    print(f"  Domain:      {profile.get('domain', 'N/A')}")
    print(f"  Session ID:  {profile.get('session_id', 'N/A')}")
    print(f"  Rounds:      {profile.get('interview_rounds_conducted', 0)}")

    # Business Context
    biz = arsrs.get("business_context", {})
    print("\n--- Business Context ---")
    print(f"  Objectives:   {', '.join(biz.get('business_objectives', [])) or 'None'}")
    print(f"  Stakeholders: {', '.join(biz.get('stakeholders', [])) or 'None'}")
    print(f"  Constraints:  {', '.join(biz.get('constraints', [])) or 'None'}")
    print(f"  KPIs:         {', '.join(biz.get('kpis', [])) or 'None'}")
    print(f"  Pain Points:  {', '.join(biz.get('pain_points', [])) or 'None'}")

    # Domain Context
    dom = arsrs.get("domain_context", {})
    print("\n--- Domain Context ---")
    print(f"  Similar Systems: {', '.join(dom.get('similar_systems', [])) or 'None'}")
    print(f"  Patterns:        {', '.join(dom.get('architecture_patterns', [])) or 'None'}")
    print(f"  Tech Signals:    {', '.join(dom.get('technology_signals', [])) or 'None'}")
    print(f"  Compliance:      {', '.join(dom.get('compliance', [])) or 'None'}")

    # Actors
    actors = arsrs.get("actors", [])
    print("\n--- Actors ---")
    if actors:
        for a in actors:
            title = a.get("title", "") if isinstance(a, dict) else str(a)
            desc = a.get("description", "") if isinstance(a, dict) else ""
            print(f"  • {title}" + (f": {desc}" if desc else ""))
    else:
        print("  None specified")

    # Functional Requirements
    frs = arsrs.get("functional_requirements", [])
    print("\n--- Functional Requirements ---")
    if frs:
        for fr in frs:
            req_id = fr.get("req_id", "FR") if isinstance(fr, dict) else "FR"
            title = fr.get("title", "") if isinstance(fr, dict) else str(fr)
            desc = fr.get("description", "") if isinstance(fr, dict) else ""
            print(f"  [{req_id}] {title}" + (f" - {desc}" if desc else ""))
    else:
        print("  None specified")

    # Non-Functional Requirements
    nfrs = arsrs.get("non_functional_requirements", [])
    print("\n--- Non-Functional Requirements ---")
    if nfrs:
        for nfr in nfrs:
            req_id = nfr.get("req_id", "NFR") if isinstance(nfr, dict) else "NFR"
            title = nfr.get("title", "") if isinstance(nfr, dict) else str(nfr)
            category = nfr.get("category", "") if isinstance(nfr, dict) else ""
            print(f"  [{req_id}] {title}" + (f" ({category})" if category else ""))
    else:
        print("  None specified")

    # Constraints
    constraints = arsrs.get("constraints", [])
    print("\n--- Constraints ---")
    if constraints:
        for c in constraints:
            desc = c.get("description", "") or c.get("title", "") if isinstance(c, dict) else str(c)
            print(f"  • {desc}")
    else:
        print("  None specified")

    # Integrations
    integrations = arsrs.get("integrations", [])
    print("\n--- Integrations ---")
    if integrations:
        for i in integrations:
            title = i.get("title", "") if isinstance(i, dict) else str(i)
            print(f"  • {title}")
    else:
        print("  None specified")

    # Assumptions
    assumptions = arsrs.get("assumptions", [])
    print("\n--- Assumptions ---")
    if assumptions:
        for asm in assumptions:
            desc = asm.get("description", "") or asm.get("title", "") if isinstance(asm, dict) else str(asm)
            print(f"  • {desc}")
    else:
        print("  None specified")

    # Review Result
    rev = arsrs.get("review_result") or src.get("review_result") or {}
    print("\n--- Review Result ---")
    if isinstance(rev, dict):
        print(f"  Verdict: {rev.get('verdict', 'N/A')}")
        print(f"  Summary: {rev.get('review_summary', 'N/A')}")
        amb = rev.get("ambiguities", [])
        if amb:
            print(f"  Ambiguities ({len(amb)}):")
            for a in amb:
                print(f"    - [{a.get('severity', 'med')}] {a.get('field')}: {a.get('description')}")
    else:
        print(f"  {rev}")

    # Interview History
    history = arsrs.get("interview_history", []) or src.get("interview_history", [])
    print("\n--- Interview History ---")
    if history:
        for item in history:
            print(f"  • {item}")
    else:
        print("  No interview history")

    # Confidence
    meta = arsrs.get("metadata", {})
    conf = meta.get("confidence_overall")
    if conf is None and isinstance(rev, dict) and "confidence" in rev:
        conf = rev["confidence"].get("overall") if isinstance(rev["confidence"], dict) else rev["confidence"]
    print("\n--- Confidence ---")
    print(f"  Overall Score: {conf if conf is not None else 'N/A'}")

    # Metadata
    print("\n--- Metadata ---")
    print(f"  Generated At:       {meta.get('generated_at', 'N/A')}")
    print(f"  Pipeline Version:   {meta.get('pipeline_version', 'N/A')}")
    print(f"  Total Requirements: {meta.get('total_requirements', 0)}")
    print(f"  Warnings:           {len(meta.get('warnings', []))}")

    print("\n" + "=" * 70)


def print_architecture_output(design_output: Dict[str, Any]):
    """Display the generated architecture design sections cleanly."""
    print("\n" + "=" * 70)
    print("                     ARCHITECTURE GENERATION")
    print("=" * 70)

    hld = design_output.get("hld", {})
    lld = design_output.get("lld", {})

    # Architecture Plan
    print("\n--- Architecture Plan ---")
    print(f"  Overview: {hld.get('overview', 'N/A')}")

    # RAG Summary
    print("\n--- RAG Summary ---")
    context_snippet = hld.get("context", "")
    if context_snippet:
        print(f"  Retrieved Knowledge Snippet:\n  {context_snippet[:300]}...")
    else:
        print("  RAG retrieval complete.")

    # High-Level Design (HLD)
    print("\n--- High-Level Design (HLD) ---")
    sections = hld.get("sections", [])
    if isinstance(sections, list) and sections:
        for sec in sections:
            if isinstance(sec, dict):
                print(f"\n  [{sec.get('title', 'Section')}]")
                print(f"  {sec.get('content', '')}")
    else:
        print(json.dumps(hld, indent=2))

    # Low-Level Design (LLD)
    print("\n--- Low-Level Design (LLD) ---")
    if isinstance(lld, dict):
        for sec_name, sec_content in lld.items():
            print(f"\n  >> Component: {sec_name.upper()}")
            if isinstance(sec_content, dict):
                code = sec_content.get("code") or sec_content.get("content") or ""
                notes = sec_content.get("notes", "")
                if code:
                    print(f"  Code/Structure:\n{code[:400]}")
                if notes:
                    print(f"  Notes: {notes}")
            else:
                print(f"  {sec_content}")
    else:
        print(json.dumps(lld, indent=2))

    print("\n" + "=" * 70)


def main_menu():
    """Main interactive playground loop."""
    ree_logger.debug("\nValidating configured OpenRouter models before starting...")
    try:
        llm_gateway.validate_configured_models()
    except Exception as exc:
        print(f"\n[CRITICAL ERROR] OpenRouter Model Validation Failed:\n{exc}\nExiting...")
        sys.exit(1)

    orchestrator = REEOrchestrator()

    while True:
        print("\n" + "=" * 45)
        print("        REE Testing Playground")
        print("=" * 45)
        print("1. Paste text")
        print("2. Load PDF")
        print("3. Load DOCX")
        print("4. Load TXT")
        print("5. Load Markdown")
        print("6. Exit")
        print("=" * 45)

        choice = input("Select option (1-6) > ").strip()

        if choice == "6":
            print("\nExiting REE Playground. Goodbye!")
            sys.exit(0)

        text_input = ""
        source_label = "interactive"

        if choice == "1":
            text_input = prompt_multiline_text()
            source_label = "pasted_text"

        elif choice in ("2", "3", "4", "5"):
            ext_map = {"2": ".pdf", "3": ".docx", "4": ".txt", "5": ".md"}
            expected_ext = ext_map[choice]
            file_path = input(f"Enter path to {expected_ext} file > ").strip()

            if not file_path:
                print("[Error] No file path provided.")
                continue

            try:
                text_input = load_file_content(file_path, expected_ext=expected_ext)
                source_label = Path(file_path.strip('"\'')).name
                print(f"[Success] Loaded {len(text_input)} characters from '{source_label}'.")
            except Exception as exc:
                print(f"[Error] Could not load file: {exc}")
                continue

        elif len(choice) > 3 and not choice.isdigit():
            # Developer pasted text directly into the menu prompt instead of selecting 1 first
            print("\n[Auto-detected direct text paste]")
            text_input = prompt_multiline_text(initial_line=choice)
            source_label = "pasted_text"

        else:
            print("[Error] Invalid option. Please enter a number between 1 and 6.")
            continue

        if not text_input.strip():
            print("[Error] Input text is empty. Cannot run REE pipeline.")
            continue

        ree_logger.debug("\nStarting REE Workflow...")
        request = REERequest(
            combined_prompt=text_input,
            input_sources=[source_label],
        )

        try:
            response = orchestrator.run(request)
        except Exception as exc:
            print(f"[Error] REE Orchestrator run failed: {exc}")
            continue

        # Handle interview loop if needed
        if response.status == REEStatus.INTERVIEWING:
            response = run_interview_loop(orchestrator, response)

        if response.status == REEStatus.FAILED:
            print(f"\n[Error] REE Workflow failed: {response.message}")
            if response.src and response.src.get("errors"):
                print(f"Errors: {response.src.get('errors')}")
            continue

        arsrs = response.arsrs or {}
        src = response.src or {}

        # Save ARSRS JSON to disk and display notification
        output_file = ree_logger.save_arsrs_json(arsrs, "output/arsrs.json")

        # Display concise summary fitting within one terminal screen
        ree_logger.print_summary(arsrs, src, output_file=output_file)

        # Print full JSON output only in debug mode
        if ree_logger.is_debug:
            ree_logger.debug_json("Complete ARSRS Formatted JSON", arsrs)

        # 5. Optional Architecture Generation
        print("\n" + "-" * 50)
        gen_arch = input("Generate Architecture? (Y/N) > ").strip().lower()
        if gen_arch in ("y", "yes"):
            print("\nInvoking Architecture Generation Pipeline (SAEGenerationService)...")
            try:
                from app.sae.services.sae_service import SAEGenerationService
                from app.sae.context.design_generation_context import DesignGenerationContext
                sae_service = SAEGenerationService()
                ctx = DesignGenerationContext(arsrs=arsrs)
                res_ctx = sae_service.process_architecture(ctx)
                print(f"[Success] Architecture generated in: {res_ctx.output_directory}")
            except Exception as exc:
                print(f"[Error] Architecture generation failed: {exc}")

        print("\nRun complete! Returning to main menu...\n")


if __name__ == "__main__":
    main_menu()
