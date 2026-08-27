"""Requirement diff engine helper for comparing ARSRS payloads."""

from __future__ import annotations

import json
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class RequirementDiffResult(BaseModel):
    """Result of comparing two ARSRS payloads."""
    has_changes: bool = Field(default=False)
    added_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    removed_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    modified_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    diff_summary: str = Field(default="No changes detected.")


class RequirementDiffEngine:
    """Helper for computing differences between ARSRS payloads."""

    def compute_diff(
        self,
        old_arsrs: Dict[str, Any],
        new_arsrs: Dict[str, Any],
    ) -> RequirementDiffResult:
        if not old_arsrs:
            return RequirementDiffResult(has_changes=True, diff_summary="Initial generation.")

        old_reqs = {r.get("id"): r for r in old_arsrs.get("functional_requirements", []) if isinstance(r, dict)}
        new_reqs = {r.get("id"): r for r in new_arsrs.get("functional_requirements", []) if isinstance(r, dict)}

        added = [new_reqs[k] for k in new_reqs if k not in old_reqs]
        removed = [old_reqs[k] for k in old_reqs if k not in new_reqs]
        modified = [new_reqs[k] for k in new_reqs if k in old_reqs and new_reqs[k] != old_reqs[k]]

        has_changes = bool(added or removed or modified)
        summary = f"Added: {len(added)}, Removed: {len(removed)}, Modified: {len(modified)}"

        return RequirementDiffResult(
            has_changes=has_changes,
            added_requirements=added,
            removed_requirements=removed,
            modified_requirements=modified,
            diff_summary=summary,
        )
