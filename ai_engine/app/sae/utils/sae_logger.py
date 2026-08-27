"""SAE Structured Logging Framework.

Manages real-time structured logging per design_id in /sae/logs/{design_id}:
  - debug.log            : Complete verbose debug stream (LLM prompts, raw responses, RAG retrieval details, stack traces)
  - execution.log        : High-level execution lifecycle log
  - timeline.log         : Phase-by-phase timeline milestones with timestamp offsets
  - llm_calls.log        : Dedicated trace of all OpenRouter LLM requests, latencies, and responses
  - execution_summary.json: Structured JSON scorecard with all execution metrics, completeness scores, and gate checks
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_LOGS_ROOT = PROJECT_ROOT / "output" / "sae" / "logs"


class SAELogger:
    """Per-design_id Structured Logger for the Software Architecture Engine."""

    def __init__(
        self,
        design_id: str,
        logs_root: Optional[Path | str] = None,
        extra_log_dirs: Optional[List[Path | str]] = None,
        debug: bool = True,
        attach_logging_handler: bool = True,
    ) -> None:
        self.design_id = design_id
        self.debug = debug
        self.t_start = time.perf_counter()
        self._lock = threading.Lock()

        # Resolve primary logs directory
        if logs_root:
            r_path = Path(logs_root)
            if r_path.name.lower() == "logs":
                self.log_dir = r_path
            else:
                self.log_dir = r_path / "logs" if design_id in ("logs", None, "") else r_path / design_id
        else:
            self.log_dir = DEFAULT_LOGS_ROOT / (design_id or "default")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Collect all mirrored target directories
        self.target_dirs: List[Path] = [self.log_dir]
        standard_mirrors = [
            PROJECT_ROOT / "output" / "sae" / "logs" / (design_id or "default"),
            PROJECT_ROOT / "output" / "logs" / (design_id or "default"),
            PROJECT_ROOT / "logs" / (design_id or "default"),
        ]
        for sm in standard_mirrors:
            if sm not in self.target_dirs:
                self.target_dirs.append(sm)

        if extra_log_dirs:
            for ed in extra_log_dirs:
                p = Path(ed)
                if p not in self.target_dirs:
                    self.target_dirs.append(p)

        for td in self.target_dirs:
            td.mkdir(parents=True, exist_ok=True)

        # Primary file paths
        self.debug_log_path = self.log_dir / "debug.log"
        self.execution_log_path = self.log_dir / "execution.log"
        self.timeline_log_path = self.log_dir / "timeline.log"
        self.llm_calls_log_path = self.log_dir / "llm_calls.log"
        self.summary_json_path = self.log_dir / "execution_summary.json"

        # Timeline events registry
        self.timeline_events: List[Dict[str, Any]] = []

        # Initialize log files with headers across all target directories
        ts_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        mode_str = "DEBUG" if self.debug else "NORMAL"
        self._init_file("debug.log", f"=== SAE Debug Log Initialized at {ts_iso} [Design ID: {self.design_id}] Mode: {mode_str} ===\n\n")
        self._init_file("execution.log", f"=== SAE Execution Log Initialized at {ts_iso} [Design ID: {self.design_id}] ===\n\n")
        self._init_file("timeline.log", f"=== SAE Timeline Initialized at {ts_iso} [Design ID: {self.design_id}] ===\n\n")
        self._init_file("llm_calls.log", f"=== SAE LLM Calls Log Initialized at {ts_iso} [Design ID: {self.design_id}] ===\n\n")

        # Attach python logging FileHandler if requested
        self._file_handler: Optional[logging.FileHandler] = None
        if attach_logging_handler:
            self._setup_logging_handler()

    def add_target_dir(self, directory: Path | str) -> None:
        """Add an extra directory to mirror logs to."""
        p = Path(directory)
        p.mkdir(parents=True, exist_ok=True)
        if p not in self.target_dirs:
            self.target_dirs.append(p)

    def _init_file(self, filename: str, header: str) -> None:
        for td in self.target_dirs:
            p = td / filename
            if not p.exists():
                try:
                    with open(p, "w", encoding="utf-8") as f:
                        f.write(header)
                except Exception:
                    pass

    def _setup_logging_handler(self) -> None:
        """Attach a FileHandler to the 'app.sae' and root loggers pointing to debug.log."""
        try:
            self._file_handler = logging.FileHandler(self.debug_log_path, mode="a", encoding="utf-8")
            formatter = logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            self._file_handler.setFormatter(formatter)
            self._file_handler.setLevel(logging.DEBUG if self.debug else logging.INFO)

            # Attach to app logger and root
            logging.getLogger("app.sae").addHandler(self._file_handler)
            logging.getLogger().addHandler(self._file_handler)
        except Exception as err:
            sys.stderr.write(f"[SAELogger] Failed to attach FileHandler: {err}\n")

    def _append(self, filename_or_path: Path | str, text: str) -> None:
        """Thread-safe append text across all registered target directories."""
        fname = filename_or_path.name if isinstance(filename_or_path, Path) else filename_or_path
        with self._lock:
            for td in self.target_dirs:
                try:
                    td.mkdir(parents=True, exist_ok=True)
                    target_file = td / fname
                    with open(target_file, "a", encoding="utf-8") as f:
                        f.write(text if text.endswith("\n") else text + "\n")
                except Exception as e:
                    pass

    def get_offset_seconds(self) -> float:
        return round(time.perf_counter() - self.t_start, 3)

    # ── Logging Primitives ───────────────────────────────────────────────────

    def log_debug(self, message: str) -> None:
        """Write debug message to debug.log."""
        now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        line = f"[{now}] [DEBUG] {message}"
        self._append(self.debug_log_path, line)

    def log_info(self, message: str) -> None:
        """Write info message to debug.log and execution.log."""
        now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        line = f"[{now}] [INFO] {message}"
        self._append(self.debug_log_path, line)
        self._append(self.execution_log_path, line)

    def log_warning(self, message: str) -> None:
        """Write warning message to debug.log and execution.log."""
        now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        line = f"[{now}] [WARNING] {message}"
        self._append(self.debug_log_path, line)
        self._append(self.execution_log_path, line)

    def log_error(self, message: str) -> None:
        """Write error message to debug.log and execution.log."""
        now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        line = f"[{now}] [ERROR] {message}"
        self._append(self.debug_log_path, line)
        self._append(self.execution_log_path, line)

    # ── Timeline & Milestones ─────────────────────────────────────────────────

    def log_timeline_event(self, stage: str, details: str = "", agent: str = "") -> None:
        """Record timestamped milestone event in timeline.log."""
        offset = self.get_offset_seconds()
        iso_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        entry = {
            "timestamp_offset": offset,
            "stage": stage,
            "agent": agent,
            "details": details,
            "iso_time": iso_time,
        }
        self.timeline_events.append(entry)

        line = f"[{offset:07.3f}s] {stage:<30} | {agent:<20} | {details}"
        self._append(self.timeline_log_path, line)
        self._append(self.debug_log_path, f"[TIMELINE] {line}")

    def log_phase_start(self, phase_num: int, phase_name: str) -> None:
        """Record start of a major pipeline phase."""
        offset = self.get_offset_seconds()
        banner = f"\n{'='*78}\n▶ [Phase {phase_num}] {phase_name} (t={offset:.2f}s)\n{'='*78}"
        self._append(self.debug_log_path, banner)
        self._append(self.execution_log_path, f"[Phase {phase_num} Start] {phase_name}")
        self.log_timeline_event(stage=f"Phase {phase_num} Start: {phase_name}")

    def log_phase_end(self, phase_num: int, phase_name: str, duration_sec: float, details: str = "") -> None:
        """Record completion of a major pipeline phase."""
        msg = f"✓ Phase {phase_num} Completed in {duration_sec}s" + (f" — {details}" if details else "")
        self._append(self.debug_log_path, f"  {msg}\n")
        self._append(self.execution_log_path, f"[Phase {phase_num} End] {phase_name} ({duration_sec}s)")
        self.log_timeline_event(stage=f"Phase {phase_num} Completed", details=f"{duration_sec}s: {details}")

    # ── LLM & RAG Tracing ────────────────────────────────────────────────────

    def log_llm_request(
        self,
        agent_role: str,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        key_idx: int = 0,
        temperature: float = 0.2,
    ) -> None:
        """Log full LLM request prompt and parameters to debug.log and llm_calls.log."""
        now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        border = "━" * 78
        block = [
            f"\n{border}",
            f"🔍 [DEBUG: LLM REQUEST] [{now}] Role: {agent_role} | Model: {model} | Key: #{key_idx} | Temp: {temperature}",
        ]
        if system_prompt:
            sys_lines = system_prompt.strip().splitlines()
            block.append(f"┌─ [SYSTEM PROMPT] ({len(system_prompt)} chars):\n│ " + "\n│ ".join(sys_lines))
        usr_lines = prompt.strip().splitlines()
        block.append(f"┌─ [USER PROMPT] ({len(prompt)} chars):\n│ " + "\n│ ".join(usr_lines))
        block.append(f"{border}\n")

        full_text = "\n".join(block)
        self._append(self.debug_log_path, full_text)
        self._append(
            self.llm_calls_log_path,
            f"[{now}] [REQ] Role: {agent_role} | Model: {model} | PromptLen: {len(prompt)} | SysLen: {len(system_prompt or '')}",
        )

    def log_llm_response(
        self,
        agent_role: str,
        latency: float,
        content: str,
        parsed_fields: Optional[List[str]] = None,
        status: str = "SUCCESS",
    ) -> None:
        """Log raw LLM response payload and parsed model fields to debug.log and llm_calls.log."""
        now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        border = "━" * 78
        resp_lines = content.strip().splitlines()
        block = [
            f"\n{border}",
            f"📥 [DEBUG: LLM RAW RESPONSE] [{now}] Role: {agent_role} | Status: {status} | Latency: {latency}s | Length: {len(content)} chars",
            "│ " + "\n│ ".join(resp_lines),
        ]
        if parsed_fields is not None:
            block.append(f"📋 [DEBUG: PARSED MODEL FIELDS] {parsed_fields}")
        block.append(f"{border}\n")

        full_text = "\n".join(block)
        self._append(self.debug_log_path, full_text)
        self._append(
            self.llm_calls_log_path,
            f"[{now}] [RESP] Role: {agent_role} | Status: {status} | Latency: {latency}s | Chars: {len(content)} | Fields: {parsed_fields}",
        )

    def log_rag_retrieval(
        self,
        agent_role: str,
        query: str,
        chunks_count: int,
        avg_similarity: float,
        fallback: bool = False,
        top_sources: Optional[List[str]] = None,
    ) -> None:
        """Log agent-owned RAG retrieval details to debug.log."""
        now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        div = "─" * 78
        lines = [
            f"\n{div}",
            f"📚 [DEBUG: RAG RETRIEVAL] [{now}] Agent: {agent_role}",
            f"🔍 Query: {query}",
        ]
        if fallback:
            lines.append(f"⚠️ [RAG FALLBACK] Zero chunks met threshold or fallback triggered.")
        else:
            lines.append(f"✅ [RAG SUCCESS] Retrieved {chunks_count} chunks (avg_sim: {avg_similarity:.4f})")
            if top_sources:
                for idx, src in enumerate(top_sources, 1):
                    lines.append(f"   [{idx}] Source: {src}")
        lines.append(f"{div}\n")

        full_text = "\n".join(lines)
        self._append(self.debug_log_path, full_text)

    # ── Summary JSON ─────────────────────────────────────────────────────────

    def save_summary(self, summary_data: Dict[str, Any]) -> None:
        """Write execution_summary.json with complete metadata and timeline."""
        summary = {
            "design_id": self.design_id,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "total_execution_time_seconds": round(time.perf_counter() - self.t_start, 3),
            "log_directory": str(self.log_dir),
            "debug_log": str(self.debug_log_path),
            **summary_data,
            "timeline": self.timeline_events,
        }
        with open(self.summary_json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)
        self.log_info(f"Execution summary saved to {self.summary_json_path.name}")

    def close(self) -> None:
        """Detach logging handler."""
        if self._file_handler:
            try:
                logging.getLogger("app.sae").removeHandler(self._file_handler)
                logging.getLogger().removeHandler(self._file_handler)
                self._file_handler.close()
            except Exception:
                pass
            self._file_handler = None

    def __enter__(self) -> SAELogger:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
