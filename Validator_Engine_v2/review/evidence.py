"""Deterministic anti-hallucination evidence verification.

Verifies evidence_path supplied by the LLM reviewer against the actual artifact:
1. JSON pointer resolution (e.g. /api_endpoints/0/route)
2. Whitespace-normalized substring match for quoted snippets (<=200 chars)

Rules:
- Findings with unverifiable evidence are DROPPED.
- Dimensions with score >= 3 must have verified evidence; otherwise capped at score 2.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from Validator_Engine_v2.schemas import DimensionScore, Finding


def _resolve_json_pointer(doc: Any, pointer: str) -> Tuple[bool, Any]:
    """Resolve RFC 6901 JSON pointer against a Python dict/list structure."""
    if not pointer or not pointer.startswith("/"):
        return False, None

    tokens = pointer.strip("/").split("/")
    curr = doc
    for t in tokens:
        # Unescape RFC 6901 ~1 -> / and ~0 -> ~
        key = t.replace("~1", "/").replace("~0", "~")
        if isinstance(curr, dict):
            if key in curr:
                curr = curr[key]
            else:
                return False, None
        elif isinstance(curr, list):
            try:
                idx = int(key)
                if 0 <= idx < len(curr):
                    curr = curr[idx]
                else:
                    return False, None
            except ValueError:
                return False, None
        else:
            return False, None

    return True, curr


def _normalize_ws(s: str) -> str:
    """Normalize internal whitespace."""
    return re.sub(r"\s+", " ", str(s or "")).strip().lower()


def is_evidence_verified(evidence_path: Optional[str], artifact_data: Dict[str, Any]) -> bool:
    """Returns True if evidence_path is either a resolving JSON pointer or a substring in the artifact."""
    if not evidence_path or not str(evidence_path).strip():
        return False

    raw_ep = str(evidence_path).strip()

    # 1. Try JSON Pointer
    if raw_ep.startswith("/"):
        resolved, _ = _resolve_json_pointer(artifact_data, raw_ep)
        if resolved:
            return True

    # 2. Try Substring Match in whitespace-normalized serialized artifact
    clean_snippet = _normalize_ws(raw_ep.strip("\"'`"))
    if len(clean_snippet) >= 4:
        serialized = _normalize_ws(json.dumps(artifact_data, ensure_ascii=False))
        if clean_snippet in serialized:
            return True

    return False


def verify_and_filter_evidence(
    dimensions: List[DimensionScore],
    findings: List[Finding],
    artifact_data: Dict[str, Any],
) -> Tuple[List[DimensionScore], List[Finding], int]:
    """Verify evidence for dimensions and findings.

    Returns:
        verified_dimensions: capped at 2 if evidence is unverifiable and score >= 3
        verified_findings: dropped if evidence is unverifiable
        dropped_count: number of dropped unverified findings
    """
    verified_dims: List[DimensionScore] = []
    for dim in dimensions:
        # Every score >= 3 requires verifiable evidence
        if dim.score >= 3:
            if not is_evidence_verified(dim.evidence_path, artifact_data):
                # Cap at score 2
                updated_dim = dim.model_copy(
                    update={
                        "score": 2,
                        "rationale": f"[Evidence unverified] {dim.rationale}"[:197] + "...",
                    }
                )
                verified_dims.append(updated_dim)
                continue
        verified_dims.append(dim)

    verified_findings: List[Finding] = []
    dropped_count = 0

    for f in findings:
        # If finding has no evidence or unverified evidence -> drop it
        if is_evidence_verified(f.evidence_path, artifact_data):
            verified_findings.append(f)
        else:
            dropped_count += 1

    return verified_dims, verified_findings, dropped_count
