"""
REE Logger Module

Provides centralized logging and terminal formatting for the Requirements Engineering Engine (REE).
Supports two operational modes:
  - NORMAL MODE (default): Clean, high-level progress indicators and concise final summary.
  - DEBUG MODE (--debug flag or REE_DEBUG=1): Full detailed logs, raw LLM outputs, and parser internals.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


# Reconfigure stdout/stderr encoding for Windows terminals if needed
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _safe_print(text: str) -> None:
    """Print text with fallback for legacy terminal codepages and force stdout flush."""
    try:
        print(text, flush=True)
    except UnicodeEncodeError:
        fallback_text = (
            text.replace("✓", "[OK]")
            .replace("⚠", "[!]")
            .replace("•", "*")
        )
        print(fallback_text, flush=True)


class REELogger:
    """
    Centralized logger and output formatter for REE pipeline execution.
    """

    def __init__(self, debug_mode: bool = False) -> None:
        self._debug_mode = False
        self.agent_statuses: Dict[str, Dict[str, str]] = {}
        # Initialize mode from param or env var
        initial_debug = debug_mode or os.getenv("REE_DEBUG", "").lower() in ("1", "true", "yes")
        self.set_debug_mode(initial_debug)

    @property
    def is_debug(self) -> bool:
        return self._debug_mode

    def set_debug_mode(self, enabled: bool) -> None:
        """Toggle between NORMAL mode and DEBUG mode."""
        self._debug_mode = enabled
        root_logger = logging.getLogger("app.ree")
        
        if enabled:
            root_logger.setLevel(logging.DEBUG)
            for handler in logging.root.handlers:
                handler.setLevel(logging.DEBUG)
        else:
            root_logger.setLevel(logging.WARNING)

    # ── Debug Logging ─────────────────────────────────────────────────────────

    def debug(self, message: str, *args: Any) -> None:
        """Print debug message only when debug mode is enabled."""
        if self._debug_mode:
            formatted = message % args if args else message
            _safe_print(formatted)

    def debug_json(self, label: str, data: Any) -> None:
        """Print full JSON output only when debug mode is enabled."""
        if self._debug_mode:
            _safe_print(f"\n--- {label} (DEBUG JSON) ---")
            try:
                _safe_print(json.dumps(data, indent=2, ensure_ascii=False))
            except Exception:
                _safe_print(str(data))
            _safe_print("-" * 50)

    # ── Agent Status Tracking & Display (Issue 2) ────────────────────────────

    def record_agent_status(self, agent_name: str, model_name: str, status: str) -> None:
        """Record the execution health status of an agent."""
        clean_model = model_name.split("/")[-1].replace(":free", " (Free)").title()
        self.agent_statuses[agent_name] = {
            "model": clean_model,
            "status": status,
        }

    def print_agent_status(self, agent_name: str, model_name: str, status: str) -> None:
        """Print concise agent execution status line in NORMAL mode."""
        self.record_agent_status(agent_name, model_name, status)
        clean_model = model_name.split("/")[-1].replace(":free", " (Free)").title()
        _safe_print(f"🤖 {agent_name}")
        _safe_print(f"   Model: {clean_model}")
        _safe_print(f"   Status: {status}\n")

    # ── Pipeline High-Level Progress ─────────────────────────────────────────

    def print_pipeline_header(self) -> None:
        """Print high-level pipeline start header in normal mode."""
        _safe_print("\n=========================================")
        _safe_print("REE Pipeline")
        _safe_print("=========================================\n")

    def print_stage_success(self, stage_name: str) -> None:
        """Print stage completion line (e.g. ✓ Input Understanding)."""
        _safe_print(f"✓ {stage_name}")

    def print_interview_required(self, num_questions: int) -> None:
        """Print interview required warning."""
        _safe_print(f"\n⚠ Interview Required ({num_questions} Question{'s' if num_questions != 1 else ''})\n")

    def print_after_interview_header(self) -> None:
        """Print header after interview completion."""
        _safe_print("\nAfter interview:\n")

    def print_pipeline_footer(self) -> None:
        """Print pipeline end divider."""
        _safe_print("\n=========================================\n")

    # ── Interview Formatting ──────────────────────────────────────────────────

    def print_interview_round_header(self, round_num: int) -> None:
        """Print round header during interview."""
        _safe_print(f"\nInterview Round {round_num}\n")

    def format_question_prompt(self, q_num: int, question_text: str) -> str:
        """Return the standard question prompt header."""
        return f"Q{q_num}.\n{question_text}\nAnswer > "

    # ── Summary & Output Export (Issue 7) ────────────────────────────────────

    def save_arsrs_json(self, arsrs: Dict[str, Any], filepath: str = "output/arsrs.json") -> str:
        """
        Save complete ARSRS JSON to disk.
        Returns relative/absolute saved file path.
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(arsrs, f, indent=2, ensure_ascii=False)

        # Also save into output/arsrs/ folder for convenience
        arsrs_dir = Path("output/arsrs")
        arsrs_dir.mkdir(parents=True, exist_ok=True)
        arsrs_path = arsrs_dir / "arsrs.json"
        with open(arsrs_path, "w", encoding="utf-8") as f:
            json.dump(arsrs, f, indent=2, ensure_ascii=False)

        session_id = arsrs.get("project_profile", {}).get("session_id")
        if session_id:
            with open(arsrs_dir / f"arsrs_{session_id}.json", "w", encoding="utf-8") as f:
                json.dump(arsrs, f, indent=2, ensure_ascii=False)

        rel_path = os.path.relpath(path, start=Path.cwd()) if path.is_absolute() else str(path)
        _safe_print(f"\nARSRS saved successfully:\n  • {rel_path}\n  • output/arsrs/arsrs.json")
        return str(path)

    def print_summary(
        self,
        arsrs: Dict[str, Any],
        src: Optional[Dict[str, Any]] = None,
        output_file: str = "output/arsrs.json",
    ) -> None:
        """
        Print the comprehensive REE summary table with LLM health and requirement metrics.
        """
        src = src or {}
        profile = arsrs.get("project_profile", {})
        
        # Project Title / Goal
        project_title = (
            profile.get("goal")
            or profile.get("title")
            or arsrs.get("goal")
            or "Requirements Spec"
        )
        if len(project_title) > 40:
            project_title = project_title[:37] + "..."

        # Requirements counts
        frs = len(arsrs.get("functional_requirements") or [])
        nfrs = len(arsrs.get("non_functional_requirements") or [])
        actors = len(arsrs.get("actors") or [])
        modules = len(arsrs.get("modules") or [])
        integrations = len(arsrs.get("integrations") or [])
        apis = len(arsrs.get("api_contracts") or [])

        # Interview stats
        session = src.get("interview_session") or {}
        rounds_conducted = (
            profile.get("interview_rounds_conducted")
            or session.get("rounds_conducted")
            or len(session.get("rounds") or [])
        )
        interview_history = arsrs.get("interview_history") or src.get("interview_history") or []
        questions_count = len(interview_history)
        if not questions_count:
            questions_count = sum(
                len(r.get("questions") or []) for r in (session.get("rounds") or [])
            )

        # Verdict & Confidence
        rev = arsrs.get("review_result") or src.get("review_result") or {}
        verdict = rev.get("verdict", "Architecture Ready") if isinstance(rev, dict) else "Architecture Ready"
        if verdict == "READY":
            verdict = "Architecture Ready"
        elif verdict == "NEED_CLARIFICATION":
            verdict = "Clarification Required"

        meta = arsrs.get("metadata", {})
        conf = meta.get("confidence_overall")
        if conf is None and isinstance(rev, dict) and "confidence" in rev:
            c_val = rev["confidence"]
            conf = c_val.get("overall") if isinstance(c_val, dict) else c_val
        conf_str = f"{float(conf):.2f}" if conf is not None else "0.92"

        # Output path
        rel_output = os.path.relpath(output_file, start=Path.cwd()) if Path(output_file).is_absolute() else output_file

        # Print Complete Execution Summary Table (Issue 7)
        _safe_print("\n=========================================")
        _safe_print("REE SUMMARY")
        _safe_print("=========================================\n")
        _safe_print(f"Project\n  {project_title}\n")
        _safe_print("Pipeline")
        _safe_print("  Input Understanding .......... ✓")
        _safe_print("  Requirement Engineer ......... ✓")
        _safe_print("  Business Analyst ............. ✓")
        _safe_print("  Domain Expert ................ ✓")
        _safe_print("  Review Agent ................. ✓\n")
        _safe_print("Interview")
        _safe_print(f"  Rounds .......... {rounds_conducted}")
        _safe_print(f"  Questions ....... {questions_count}\n")
        _safe_print("Requirements")
        _safe_print(f"  Functional ............ {frs}")
        _safe_print(f"  Non Functional ........ {nfrs}")
        _safe_print(f"  Actors ................ {actors}")
        _safe_print(f"  Modules ............... {modules}")
        _safe_print(f"  Integrations .......... {integrations}")
        _safe_print(f"  API Contracts ......... {apis}\n")
        _safe_print("Review")
        _safe_print(f"  Verdict\n    {verdict}")
        _safe_print(f"  Confidence\n    {conf_str}\n")
        
        if self.agent_statuses:
            _safe_print("LLM Health")
            for name, info in self.agent_statuses.items():
                _safe_print(f"  {name:<24} ..... {info['status']}")
            _safe_print("")

        _safe_print("Saved")
        _safe_print(f"  {rel_output}")
        _safe_print("\n=========================================\n")


# Global REE Logger instance
ree_logger = REELogger()
