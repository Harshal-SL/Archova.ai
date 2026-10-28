"""Report storage layer.

Persists full validation report and package snapshot to runs/{generation_id}.json
after EVERY iteration so progress is immediately visible to the UI and resilient to crashes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional
from Validator_Engine_v2.schemas import Report

RUNS_DIR = Path(__file__).resolve().parent.parent / "runs"


class ReportStore:
    def __init__(self, runs_dir: Optional[Path] = None) -> None:
        self.runs_dir = runs_dir or RUNS_DIR
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, generation_id: str) -> Path:
        clean_id = str(generation_id).strip().replace("/", "_").replace("\\", "_")
        return self.runs_dir / f"{clean_id}.json"

    def save_report(self, report: Report, final_package: Optional[Dict[str, Any]] = None) -> Path:
        """Persist report and final package snapshot atomically."""
        path = self._get_path(report.generation_id)
        report_dict = report.model_dump(mode="json")
        if final_package is not None:
            report_dict["final_package"] = final_package

        # Write to temp file then atomic replace
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(report_dict, indent=2), encoding="utf-8")
        tmp_path.replace(path)
        return path

    def load_report(self, generation_id: str) -> Optional[Dict[str, Any]]:
        """Load report dictionary from disk if exists."""
        path = self._get_path(generation_id)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None


# Global singleton
report_store = ReportStore()
