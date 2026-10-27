"""Version Manager: Orchestrator for architecture lifecycle, delta evolution, and version bumping."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.versioning.contracts import (
    ArchitectureDiff,
    ArchitecturePatch,
    PatchVerificationResult,
    VerificationViolation,
    VersionContext,
)
from app.versioning.differ import ArchitectureDiffer
from app.versioning.patcher import ArchitecturePatcher
from app.versioning.prompt_builder import DeltaPromptBuilder
from app.versioning.verifier import ArchitectureVerifier

logger = logging.getLogger(__name__)


class VersionManager:
    """Orchestrates non-destructive architecture evolution, verification, and diff generation."""

    def __init__(self, llm_provider: Optional[Any] = None) -> None:
        if llm_provider is None:
            try:
                from app.sae.providers.llm_provider import OpenRouterProvider
                llm_provider = OpenRouterProvider()
            except Exception as exc:
                logger.warning("VersionManager: Could not initialize default OpenRouterProvider: %s", exc)
        self.llm_provider = llm_provider
        self.verifier = ArchitectureVerifier()

    @staticmethod
    def detect_version_context(
        session_id: Optional[str] = None,
        previous_package: Optional[Dict[str, Any]] = None,
    ) -> VersionContext:
        """Determines whether to bypass (INITIAL v1.0) or evolve (EVOLUTION v1.x)."""
        if not previous_package or not previous_package.get("hld"):
            return VersionContext(
                mode="INITIAL",
                session_id=session_id,
                base_version=None,
                target_version="1.0",
                parent_package=None,
            )

        current_ver = str(previous_package.get("version", "1.0")).strip()
        next_ver = VersionManager.bump_version_string(current_ver, bump_type="minor")

        return VersionContext(
            mode="EVOLUTION",
            session_id=session_id,
            base_version=current_ver,
            target_version=next_ver,
            parent_package=previous_package,
        )

    @staticmethod
    def bump_version_string(version_str: str, bump_type: str = "minor") -> str:
        """Calculates next semantic version string (e.g. 1.0 -> 1.1)."""
        clean_v = version_str.lstrip("v").strip()
        parts = clean_v.split(".")
        try:
            major = int(parts[0]) if len(parts) > 0 else 1
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
        except ValueError:
            major, minor, patch = 1, 0, 0

        if bump_type == "major":
            return f"{major + 1}.0"
        elif bump_type == "patch":
            return f"{major}.{minor}.{patch + 1}"
        else:  # minor (default for features)
            return f"{major}.{minor + 1}"

    async def evolve_architecture(
        self,
        baseline: Dict[str, Any],
        feature_prompt: str,
        custom_llm_caller: Optional[Callable[[str], Any]] = None,
        target_version: Optional[str] = None,
        max_retries: int = 2,
    ) -> Tuple[Dict[str, Any], ArchitectureDiff]:
        """Runs the verified evolution pipeline:
        1. Formulates delta prompt
        2. Queries LLM for ArchitecturePatch
        3. Applies patch additively
        4. Verifies 100% baseline preservation
        5. Retries with violation feedback if invariant fails (max 2 attempts)
        6. Produces diff & returns (patched_architecture, diff)
        """
        base_version = str(baseline.get("version", "1.0")).strip()
        target_ver = target_version or self.bump_version_string(base_version, "minor")
        patcher = ArchitecturePatcher(target_version=target_ver)

        violations: Optional[List[VerificationViolation]] = None
        last_patch: Optional[ArchitecturePatch] = None
        last_patched_pkg: Optional[Dict[str, Any]] = None

        for attempt in range(1, max_retries + 2):
            prompt = DeltaPromptBuilder.build_evolution_prompt(
                baseline=baseline,
                feature_prompt=feature_prompt,
                violations=violations,
            )

            # Query LLM (or custom caller)
            patch_dict = await self._call_llm_for_patch(prompt, custom_llm_caller)
            patch = ArchitecturePatch.model_validate(patch_dict)
            last_patch = patch

            # Apply patch additively
            candidate_pkg = patcher.apply_patch(baseline, patch)
            last_patched_pkg = candidate_pkg

            # Verify invariants
            ver_result: PatchVerificationResult = self.verifier.verify(baseline, candidate_pkg, patch)

            if ver_result.is_valid:
                logger.info(
                    "Architecture evolution verified on attempt %d for version %s",
                    attempt,
                    target_ver,
                )
                diff = ArchitectureDiffer.compute_diff(
                    baseline=baseline,
                    patched=candidate_pkg,
                    patch=patch,
                    from_version=base_version,
                    to_version=target_ver,
                    feature_prompt=feature_prompt,
                )
                return candidate_pkg, diff

            # If invalid, collect violations for the next retry
            violations = ver_result.violations
            logger.warning(
                "Evolution attempt %d failed verification: %s. Retrying...",
                attempt,
                ver_result.summary(),
            )

        # If retries exhausted, raise structured error with violation list
        raise ValueError(
            f"Architecture evolution failed verification after {max_retries + 1} attempts. "
            f"Violations: {[v.model_dump() for v in (violations or [])]}"
        )

    async def _call_llm_for_patch(
        self,
        prompt: str,
        custom_caller: Optional[Callable[[str], Any]],
    ) -> Dict[str, Any]:
        """Dispatches prompt to LLM provider or fallback caller."""
        if custom_caller:
            result = custom_caller(prompt)
            if hasattr(result, "__await__"):
                result = await result
            if isinstance(result, str):
                return json.loads(result)
            elif isinstance(result, dict):
                return result

        if self.llm_provider and hasattr(self.llm_provider, "generate_structured_async"):
            result = await self.llm_provider.generate_structured_async(
                prompt=prompt,
                response_model=ArchitecturePatch,
                agent_role="evolution",
                temperature=0.2,
            )
            return result.model_dump(mode="json")

        raise RuntimeError("No LLM provider or custom caller configured for VersionManager.")
