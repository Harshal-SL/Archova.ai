"""Version manager helper for semantic versioning and SHA256 fingerprints."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, Optional


class VersionManager:
    """Manager for versioning ARSRS and output packages."""

    def version_arsrs(
        self,
        arsrs_data: Dict[str, Any],
        parent_version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Version incoming ARSRS payload with SHA256 fingerprint."""
        arsrs_str = json.dumps(arsrs_data, sort_keys=True, default=str)
        fingerprint = hashlib.sha256(arsrs_str.encode("utf-8")).hexdigest()
        timestamp = datetime.now(timezone.utc).isoformat()

        version_str = "1.0.0"
        if parent_version:
            v_parts = parent_version.split(".")
            if len(v_parts) == 3:
                version_str = f"{v_parts[0]}.{v_parts[1]}.{int(v_parts[2]) + 1}"

        return {
            "version": version_str,
            "fingerprint": fingerprint,
            "timestamp": timestamp,
            "parent_version": parent_version,
            "project_name": arsrs_data.get("system_name") or arsrs_data.get("title") or "arsrs_design",
            "requirement_count": len(arsrs_data.get("functional_requirements", [])) + len(arsrs_data.get("non_functional_requirements", [])),
        }
