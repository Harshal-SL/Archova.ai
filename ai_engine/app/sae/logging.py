"""SAE Logging Facade and Enterprise Logger Manager.

Provides backward-compatible and modern structured loggers:
  - SAELogger: Per-design_id logger writing to /sae/logs/{design_id}/
  - EnterpriseLoggerManager: Session logger for console wizards and pipeline runners
  - StreamNoiseSuppressor: Context manager suppressing noisy third-party stream output
"""

from __future__ import annotations

import contextlib
import io
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.sae.utils.sae_logger import SAELogger, DEFAULT_LOGS_ROOT

logger = logging.getLogger(__name__)


class StreamNoiseSuppressor:
    """Context manager to suppress stdout noise from verbose third-party libraries."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._stdout_backup = None
        self._stderr_backup = None

    def __enter__(self) -> StreamNoiseSuppressor:
        if self.enabled:
            self._stdout_backup = sys.stdout
            self._stderr_backup = sys.stderr
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.enabled and self._stdout_backup:
            sys.stdout = self._stdout_backup
            sys.stderr = self._stderr_backup


class EnterpriseLoggerManager:
    """Session-level logger manager writing to session.log and metadata.json."""

    def __init__(
        self,
        project_name: str = "default_project",
        request_id: Optional[str] = None,
        debug_mode: bool = False,
        logs_root: Optional[Path | str] = None,
    ) -> None:
        self.raw_project_name = project_name
        self.project_slug = re.sub(r"[^a-zA-Z0-9_\-]", "_", project_name[:40]).strip("_") or "sae_project"
        self.request_id = request_id or f"req_{int(time.time())}"
        self.debug_mode = debug_mode
        self.t_start = time.perf_counter()

        # Initialize underlying SAELogger targeted at request_id / project_slug
        self.sae_logger = SAELogger(
            design_id=self.request_id,
            logs_root=logs_root or DEFAULT_LOGS_ROOT,
            debug=self.debug_mode,
        )
        self.log_dir = self.sae_logger.log_dir
        self.session_log_path = self.log_dir / "session.log"
        self.metadata_json_path = self.log_dir / "metadata.json"

    def log_info(self, msg: str) -> None:
        self.sae_logger.log_info(msg)
        self._append_session("INFO", msg)

    def log_debug(self, msg: str) -> None:
        self.sae_logger.log_debug(msg)
        if self.debug_mode:
            self._append_session("DEBUG", msg)

    def log_warn(self, msg: str) -> None:
        self.sae_logger.log_warning(msg)
        self._append_session("WARN", msg)

    def log_error(self, msg: str) -> None:
        self.sae_logger.log_error(msg)
        self._append_session("ERROR", msg)

    def log_agent_execution(self, agent_name: str, stage: str, duration_sec: float) -> None:
        self.sae_logger.log_timeline_event(stage=stage, agent=agent_name, details=f"duration: {duration_sec}s")

    def log_llm_status(
        self,
        capability: str,
        provider: str,
        model: str,
        status: str,
        reason: str = "",
        prompt: str = "",
        response: str = "",
        latency_sec: float = 0.0,
    ) -> None:
        self.sae_logger.log_llm_response(
            agent_role=capability,
            latency=latency_sec,
            content=f"[{status}] Model: {model} | {response}",
            status=status,
        )

    def log_exception(self, exc: Exception, agent: str = "", stage: str = "") -> None:
        import traceback
        tb = traceback.format_exc()
        self.sae_logger.log_error(f"Exception in [{stage}/{agent}]: {exc}\n{tb}")

    def save_metadata(self, meta: Dict[str, Any]) -> None:
        with open(self.metadata_json_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, default=str)
        self.sae_logger.save_summary(meta)

    def _append_session(self, level: str, msg: str) -> None:
        try:
            with open(self.session_log_path, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {msg}\n")
        except Exception:
            pass


__all__ = [
    "SAELogger",
    "EnterpriseLoggerManager",
    "StreamNoiseSuppressor",
    "DEFAULT_LOGS_ROOT",
]
