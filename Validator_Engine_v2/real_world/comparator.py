"""Pattern Comparator for Real-World Benchmark Engine.

Compares target architectural artifacts against transferable real-world patterns
via ReviewerLLMClient with deterministic offline mock mode.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from Validator_Engine_v2.real_world.profile_extractor import RealWorldPattern
from Validator_Engine_v2.review.llm_client import ReviewerLLMClient, _extract_first_json
from Validator_Engine_v2.schemas import PatternAssessment

SYSTEM_PROMPT_COMPARATOR = """You are an independent architecture reviewer evaluating alignment against real-world production engineering practices.
Evaluate whether the target artifact addresses the transferable capabilities defined in the reference patterns.

CRITICAL RULES:
1. A missing pattern is NOT a defect if it does not apply at the target system's stated scale.
2. Do not reward unnecessary complexity or over-engineering.
3. Do not invent content absent from the artifact.
4. For status 'ALIGNED', 'PARTIAL', or 'JUSTIFIED_DIVERGENCE', 'evidence_path' is REQUIRED (JSON pointer like '/api_endpoints/0' or exact quoted snippet <= 200 chars).
5. For status 'NOT_APPLICABLE', 'requirement_refs' is REQUIRED (list of FR/NFR IDs or concrete numbers justifying why it is not needed).
6. 'justification' must be <= 200 characters.

Return ONLY JSON:
{
  "assessments": [
    {
      "pattern_id": "<Pattern ID>",
      "status": "ALIGNED" | "PARTIAL" | "MISSING" | "JUSTIFIED_DIVERGENCE" | "NOT_APPLICABLE",
      "evidence_path": "<JSON pointer or quoted snippet from artifact>",
      "justification": "<Reasoning, max 200 chars>",
      "requirement_refs": ["<Requirement ID>", ...]
    }
  ]
}
"""


class PatternComparator:
    """Evaluates artifact content against applicable real-world patterns."""

    def __init__(self, llm_client: Optional[ReviewerLLMClient] = None) -> None:
        self.llm_client = llm_client or ReviewerLLMClient()

    async def compare_artifact(
        self,
        artifact_name: str,
        artifact_data: Dict[str, Any],
        patterns: List[RealWorldPattern],
        system_names_by_pattern: Dict[str, str],
        arsrs: Dict[str, Any],
    ) -> List[PatternAssessment]:
        """Run comparison for a single artifact against applicable patterns."""
        # Filter patterns that apply to this artifact
        applicable_patterns = [
            p for p in patterns if artifact_name.lower() in [a.lower() for a in p.applies_to_artifacts]
        ]
        # Sort by priority and cap at 12
        applicable_patterns.sort(key=lambda x: x.priority)
        applicable_patterns = applicable_patterns[:12]

        if not applicable_patterns:
            return []

        # 1. Mock Mode
        if self.llm_client.mock_mode in ("1", "true", "mock"):
            return self._generate_mock_assessments(
                artifact_name=artifact_name,
                artifact_data=artifact_data,
                patterns=applicable_patterns,
                system_names=system_names_by_pattern,
                arsrs=arsrs,
            )

        # 2. Live LLM Comparison
        patterns_payload = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "category": p.category,
                "priority": p.priority,
                "applicability": p.applicability.model_dump(),
            }
            for p in applicable_patterns
        ]

        target_nfrs = arsrs.get("non_functional_requirements", [])
        req_ids = [r.get("id") for r in arsrs.get("functional_requirements", []) if isinstance(r, dict)]
        req_ids += [r.get("id") for r in target_nfrs if isinstance(r, dict)]

        user_prompt = (
            f"Evaluate the following {artifact_name.upper()} artifact against {len(applicable_patterns)} real-world patterns.\n\n"
            f"Target System Requirements & NFR Scale Profile:\n"
            f"{json.dumps(target_nfrs, indent=2)[:1500]}\n\n"
            f"Applicable Reference Patterns:\n"
            f"{json.dumps(patterns_payload, indent=2)}\n\n"
            f"Artifact JSON to evaluate:\n"
            f"{json.dumps(artifact_data, indent=2)[:8000]}\n"
        )

        # Handle mock mode or unavailable mode deterministically
        if self.llm_client.mock_mode in ("1", "true", "mock"):
            return self._generate_mock_assessments(
                artifact_name=artifact_name,
                artifact_data=artifact_data,
                patterns=applicable_patterns,
                system_names=system_names_by_pattern,
                arsrs=arsrs,
            )
        elif self.llm_client.mock_mode in ("unavailable", "fail"):
            return []

        parsed_json, status = await self.llm_client.call_review(
            artifact_name=artifact_name,
            artifact_data=artifact_data,
            rubric={"dimensions": []},
            user_prompt=user_prompt,
        )

        if not parsed_json or "assessments" not in parsed_json:
            # Fallback when LLM comparison unavailable
            return []

        assessments: List[PatternAssessment] = []
        raw_items = parsed_json.get("assessments", [])
        raw_by_id = {item.get("pattern_id"): item for item in raw_items if isinstance(item, dict)}

        for pat in applicable_patterns:
            sys_name = system_names_by_pattern.get(pat.id, "Real-World System")
            raw = raw_by_id.get(pat.id)
            if raw:
                st = raw.get("status", "MISSING")
                if st not in ("ALIGNED", "PARTIAL", "MISSING", "JUSTIFIED_DIVERGENCE", "NOT_APPLICABLE"):
                    st = "MISSING"

                ev = raw.get("evidence_path")
                just = str(raw.get("justification") or "")[:200]
                refs = raw.get("requirement_refs") or []
                if not isinstance(refs, list):
                    refs = [str(refs)]

                assessments.append(
                    PatternAssessment(
                        pattern_id=pat.id,
                        system_name=sys_name,
                        pattern_name=pat.name,
                        category=pat.category,
                        priority=pat.priority,
                        status=st,
                        evidence_path=ev,
                        justification=just,
                        requirement_refs=[str(r) for r in refs],
                    )
                )
            else:
                assessments.append(
                    PatternAssessment(
                        pattern_id=pat.id,
                        system_name=sys_name,
                        pattern_name=pat.name,
                        category=pat.category,
                        priority=pat.priority,
                        status="MISSING",
                        justification="Pattern not addressed in artifact specification.",
                    )
                )

        return assessments

    def _generate_mock_assessments(
        self,
        artifact_name: str,
        artifact_data: Dict[str, Any],
        patterns: List[RealWorldPattern],
        system_names: Dict[str, str],
        arsrs: Dict[str, Any],
    ) -> List[PatternAssessment]:
        """Produce deterministic mock assessments based on artifact content."""
        serialized = json.dumps(artifact_data).lower()
        has_concurrency = (
            "select for update" in serialized
            or "redlock" in serialized
            or "concurrency_lock" in serialized
            or "reservation_concurrency_policy" in serialized
            or "locking_and_concurrency" in serialized
        )
        has_caching = "cache" in serialized or "redis" in serialized or "cdn" in serialized or "tanstack" in serialized or "state" in serialized
        has_security = "security_controls" in serialized or "jwt" in serialized or "auth" in serialized

        assessments: List[PatternAssessment] = []
        for p in patterns:
            sys_name = system_names.get(p.id, "Real-World Reference")
            status = "ALIGNED"
            ev: Optional[str] = None
            just = f"Aligned with {p.name} specification."
            refs: List[str] = []

            # Check valid key in artifact for evidence path
            valid_key = next((k for k in artifact_data.keys() if isinstance(artifact_data[k], (dict, list))), None)
            default_ev = f"/{valid_key}" if valid_key else f"/{list(artifact_data.keys())[0]}" if artifact_data else None

            if p.category == "concurrency":
                if has_concurrency:
                    status = "ALIGNED"
                    ev = "/reservation_concurrency_policy" if "reservation_concurrency_policy" in artifact_data else (
                        "/locking_and_concurrency" if "locking_and_concurrency" in artifact_data else default_ev
                    )
                    just = "Concurrency policy enforces distributed locks preventing race conditions."
                elif artifact_name not in ("backend", "database"):
                    status = "NOT_APPLICABLE"
                    ev = None
                    refs = ["NFR-1", "NFR-2"]
                    just = "Low-level concurrency locking delegates to backend and database implementation layers."
                else:
                    status = "MISSING"
                    ev = None
                    just = "No distributed locking or row-level locking found for shared state."
            elif p.category in ("caching", "scaling"):
                if has_caching:
                    status = "ALIGNED"
                    ev = default_ev
                    just = f"Caching topology aligned with {p.name}."
                else:
                    # Check if scale is small
                    status = "NOT_APPLICABLE"
                    ev = None
                    refs = ["NFR-1", "NFR-2"]
                    just = "High-tier planetary caching not required at target system traffic scale."
            elif p.category == "security":
                if has_security:
                    status = "ALIGNED"
                    ev = "/security_controls" if "security_controls" in artifact_data else default_ev
                    just = "Security controls enforce token authentication and authorization."
                else:
                    status = "PARTIAL"
                    ev = default_ev
                    just = "Basic security controls defined without fine-grained resource RBAC."
            else:
                status = "ALIGNED"
                ev = default_ev
                just = f"Verified architectural alignment with {p.name}."

            assessments.append(
                PatternAssessment(
                    pattern_id=p.id,
                    system_name=sys_name,
                    pattern_name=p.name,
                    category=p.category,
                    priority=p.priority,
                    status=status,
                    evidence_path=ev,
                    justification=just,
                    requirement_refs=refs,
                )
            )

        return assessments

    def _build_unavailable_assessments(
        self, patterns: List[RealWorldPattern], system_names: Dict[str, str]
    ) -> List[PatternAssessment]:
        return [
            PatternAssessment(
                pattern_id=p.id,
                system_name=system_names.get(p.id, "Reference System"),
                pattern_name=p.name,
                category=p.category,
                priority=p.priority,
                status="MISSING",
                justification="Reviewer LLM unavailable to assess pattern alignment.",
            )
            for p in patterns
        ]
