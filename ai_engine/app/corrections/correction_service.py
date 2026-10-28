"""Correction Service: Implementation of Targeted AI Architecture Correction (Part 2.2.2)."""

from __future__ import annotations

import asyncio
import copy
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx
from pathlib import Path

from app.corrections.contracts import (
    AcceptCorrectionRequest,
    AcceptCorrectionResponse,
    CorrectionApprovalRequest,
    CorrectionApprovalResponse,
    RejectCorrectionResponse,
    TargetedCorrectionRequest,
    TargetedCorrectionResponse,
    VerificationResult,
)
from app.sae.providers.llm_provider import OpenRouterProvider


logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CORRECTIONS_DIR = PROJECT_ROOT / "outputs" / "corrections"
CORRECTIONS_MIRROR_DIR = PROJECT_ROOT / "output" / "corrections"

SUPPORTED_ARTIFACT_TYPES = {
    "hld",
    "backend",
    "database",
    "frontend",
    "security",
    "cloud",
    "arsrs",
}

ARTIFACT_ALIASES = {
    "hld": "hld",
    "backend": "backend",
    "backend-lld": "backend",
    "backend_lld": "backend",
    "backend lld": "backend",
    "database": "database",
    "database-lld": "database",
    "database_lld": "database",
    "database lld": "database",
    "frontend": "frontend",
    "frontend-lld": "frontend",
    "frontend_lld": "frontend",
    "frontend lld": "frontend",
    "security": "security",
    "security-lld": "security",
    "security_lld": "security",
    "security lld": "security",
    "cloud": "cloud",
    "cloud-lld": "cloud",
    "cloud_lld": "cloud",
    "cloud lld": "cloud",
    "arsrs": "arsrs",
}


def normalize_artifact_type(raw_type: str) -> str:
    """Map arbitrary artifact names or aliases to canonical lowercase identifier."""
    cleaned = (raw_type or "").strip().lower()
    return ARTIFACT_ALIASES.get(cleaned, cleaned)


def bump_version_string(version_str: str, bump_type: str = "minor") -> str:
    """Calculates next semantic version string (e.g. 1.0 -> 1.1)."""
    clean_v = str(version_str).lstrip("v").strip()
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
    else:  # minor
        return f"{major}.{minor + 1}"


class CorrectionLLMClient:
    """Isolated LLM client for targeted architecture corrections using OpenRouter free tier with multi-key rotation and model fallback."""

    def __init__(self, provider: Optional[OpenRouterProvider] = None) -> None:
        self.provider = provider or OpenRouterProvider(debug=False)
        self.fallback_models = [
            "nvidia/nemotron-3.5-lightning:free",
            "cohere/north-mini-code:free",
            "openrouter/free",
            self.provider.default_model,
        ]

    def get_candidate_keys(self, agent_role: str = "general") -> List[str]:
        """Collect all available OpenRouter API keys in priority order for key rotation."""
        keys: List[str] = []
        preferred = self.provider.get_api_key_for_role(agent_role)
        if preferred and preferred.strip():
            keys.append(preferred.strip())

        for env_var in (
            "OPENROUTER_API_KEY_1",
            "OPENROUTER_API_KEY_3",
            "OPENROUTER_API_KEY",
            "OPENROUTER_API_KEY_2",
            "OPENROUTER_API_KEY_4",
            "VALIDATOR_API_KEY",
        ):
            v = os.getenv(env_var, "").strip()
            if v and v not in keys:
                keys.append(v)

        if not keys and getattr(self.provider, "api_key", None):
            keys.append(self.provider.api_key)

        return keys

    async def acall(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.1,
        agent_role: str = "general",
    ) -> str:
        """Call OpenRouter chat completion asynchronously with key rotation and free model fallback."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        # Deduplicate candidate models
        candidate_models: List[str] = []
        for m in self.fallback_models:
            if m and m not in candidate_models:
                candidate_models.append(m)

        candidate_keys = self.get_candidate_keys(agent_role)
        if not candidate_keys:
            raise RuntimeError("No OpenRouter API key configured for architecture corrections.")

        last_err: Optional[Exception] = None

        for active_key in candidate_keys:
            headers = self.provider._get_headers(active_key)
            key_exhausted = False

            for model in candidate_models:
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": self.provider.max_tokens,
                    "response_format": {"type": "json_object"},
                }

                try:
                    async with httpx.AsyncClient(timeout=float(self.provider.timeout or 35.0)) as client:
                        resp = await client.post(
                            f"{self.provider.base_url}/chat/completions",
                            json=payload,
                            headers=headers,
                        )

                        # Check for key-level daily limit or auth errors (rotate key)
                        if resp.status_code in (401, 403) or (resp.status_code == 429 and "free-models-per-day" in resp.text):
                            logger.warning(
                                "OpenRouter key [%s...] daily limit reached or auth rejected (HTTP %d). Rotating to next key...",
                                active_key[:12],
                                resp.status_code,
                            )
                            key_exhausted = True
                            last_err = httpx.HTTPStatusError(
                                f"HTTP {resp.status_code}: {resp.text[:120]}",
                                request=resp.request,
                                response=resp,
                            )
                            break

                        # Model-level temporary rate limit or 5xx server error (fallback model)
                        if resp.status_code in (404, 429, 500, 502, 503, 504, 520):
                            logger.warning(
                                "OpenRouter model [%s] returned HTTP %d. Trying fallback model...",
                                model,
                                resp.status_code,
                            )
                            last_err = httpx.HTTPStatusError(
                                f"HTTP {resp.status_code}", request=resp.request, response=resp
                            )
                            continue

                        resp.raise_for_status()
                        data = resp.json()
                        choices = data.get("choices", [])
                        if not choices:
                            raise ValueError(f"Empty choices in response from OpenRouter model [{model}].")
                        content = self.provider._extract_choice_content(choices[0])
                        if not content:
                            raise ValueError(f"Empty content returned from OpenRouter model [{model}].")
                        return content
                except httpx.TimeoutException as exc:
                    logger.warning("OpenRouter free model [%s] timed out. Trying fallback model...", model)
                    last_err = exc
                    continue
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code in (429, 502, 503, 504, 520):
                        logger.warning("OpenRouter free model [%s] returned status %s. Trying fallback...", model, exc)
                        last_err = exc
                        continue
                    raise

            if key_exhausted:
                continue

        if last_err:
            raise last_err
        raise RuntimeError("No candidate free OpenRouter models/keys available.")


class CorrectionService:
    """Manages targeted architecture correction lifecycle, approval verification, and delta patching."""

    def __init__(self, llm_provider: Optional[Any] = None) -> None:
        self._llm_provider = llm_provider or CorrectionLLMClient()
        self._approval_store: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self._operations_store: Dict[str, Dict[str, Any]] = {}
        self._historical_versions: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()
        self._ensure_storage()
        self._load_persisted_state()

    def _ensure_storage(self) -> None:
        """Create durable directories for corrections, approvals, operations, and versions."""
        for p in (CORRECTIONS_DIR, CORRECTIONS_MIRROR_DIR):
            for sub in ("approvals", "operations", "versions"):
                (p / sub).mkdir(parents=True, exist_ok=True)

    def _persist_file(self, subdir: str, filename: str, data: Any) -> None:
        """Atomically persist JSON data to both outputs/corrections and output/corrections."""
        try:
            for parent_dir in (CORRECTIONS_DIR, CORRECTIONS_MIRROR_DIR):
                target_dir = parent_dir / subdir
                target_dir.mkdir(parents=True, exist_ok=True)
                target_file = target_dir / filename
                tmp_file = target_file.with_suffix(".tmp")
                tmp_file.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
                tmp_file.replace(target_file)
        except Exception as e:
            logger.warning("Failed to persist correction record [%s/%s]: %s", subdir, filename, e)

    def _load_persisted_state(self) -> None:
        """Pre-populate in-memory stores with existing records from disk across restarts."""
        try:
            for parent_dir in (CORRECTIONS_DIR, CORRECTIONS_MIRROR_DIR):
                if not parent_dir.exists():
                    continue

                # Approvals
                app_dir = parent_dir / "approvals"
                if app_dir.exists():
                    for f in app_dir.glob("*.json"):
                        try:
                            rec = json.loads(f.read_text(encoding="utf-8"))
                            key = (rec.get("generation_id", "").strip(), rec.get("finding_id", "").strip())
                            if key[0] and key[1]:
                                self._approval_store[key] = rec
                        except Exception:
                            pass

                # Operations
                op_dir = parent_dir / "operations"
                if op_dir.exists():
                    for f in op_dir.glob("*.json"):
                        try:
                            op = json.loads(f.read_text(encoding="utf-8"))
                            op_id = op.get("operation_id")
                            if op_id:
                                self._operations_store[op_id] = op
                        except Exception:
                            pass

                # Versions
                ver_dir = parent_dir / "versions"
                if ver_dir.exists():
                    for f in ver_dir.glob("*.json"):
                        try:
                            v_recs = json.loads(f.read_text(encoding="utf-8"))
                            gen_id = f.stem
                            if isinstance(v_recs, list):
                                self._historical_versions[gen_id] = v_recs
                        except Exception:
                            pass
        except Exception as e:
            logger.warning("Error loading persisted corrections state: %s", e)

    # ── 1. Server-Side Approval Management ─────────────────────────────────────

    def register_approval(self, payload: CorrectionApprovalRequest) -> CorrectionApprovalResponse:
        """Record an explicit user approval for a finding on the server with durable persistence."""
        norm_art = normalize_artifact_type(payload.artifact_type)
        key = (payload.generation_id.strip(), payload.finding_id.strip())
        now = datetime.now(timezone.utc).isoformat()

        record = {
            "generation_id": payload.generation_id.strip(),
            "finding_id": payload.finding_id.strip(),
            "artifact_type": norm_art,
            "source_version": payload.source_version.strip(),
            "approved_by": payload.approved_by or "user",
            "notes": payload.notes,
            "approved_at": now,
        }
        self._approval_store[key] = record

        # Persist approval to disk
        safe_gen = re.sub(r"[^\w\-]", "_", payload.generation_id.strip())
        safe_fnd = re.sub(r"[^\w\-]", "_", payload.finding_id.strip())
        self._persist_file("approvals", f"{safe_gen}_{safe_fnd}.json", record)

        logger.info(
            "Registered approval for finding [%s] on artifact [%s] (gen: %s, ver: %s)",
            payload.finding_id, norm_art, payload.generation_id, payload.source_version
        )
        return CorrectionApprovalResponse(
            generation_id=payload.generation_id,
            finding_id=payload.finding_id,
            artifact_type=norm_art,
            source_version=payload.source_version,
            approved=True,
            approved_at=now,
            message=f"Finding '{payload.finding_id}' approved for correction on artifact '{norm_art}'.",
        )

    def is_approved(self, generation_id: str, finding_id: str, source_version: Optional[str] = None) -> bool:
        """Verify whether the specified finding has an active approval record with disk fallback."""
        key = (generation_id.strip(), finding_id.strip())
        record = self._approval_store.get(key)
        if not record:
            # Check disk for persisted approval
            safe_gen = re.sub(r"[^\w\-]", "_", generation_id.strip())
            safe_fnd = re.sub(r"[^\w\-]", "_", finding_id.strip())
            for parent_dir in (CORRECTIONS_DIR, CORRECTIONS_MIRROR_DIR):
                f = parent_dir / "approvals" / f"{safe_gen}_{safe_fnd}.json"
                if f.exists():
                    try:
                        record = json.loads(f.read_text(encoding="utf-8"))
                        self._approval_store[key] = record
                        break
                    except Exception:
                        pass

        if not record:
            return False
        if source_version:
            v_stored = record.get("source_version", "").lstrip("v").strip()
            v_check = source_version.lstrip("v").strip()
            if v_stored and v_check and v_stored != v_check:
                logger.warning("Approval version mismatch for finding [%s]: %s != %s", finding_id, v_stored, v_check)
                return False
        return True

    def get_approvals_for_generation(self, generation_id: str) -> List[Dict[str, Any]]:
        """List all approvals recorded for a given generation."""
        gen_clean = generation_id.strip()
        approvals = [rec for (g_id, _), rec in self._approval_store.items() if g_id == gen_clean]
        return approvals

    # ── 2. Artifact Resolution ────────────────────────────────────────────────

    def resolve_artifact(
        self,
        generation_id: str,
        artifact_type: str,
        baseline_package: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Locate the original artifact payload from the baseline package or active generation."""
        norm_type = normalize_artifact_type(artifact_type)
        if norm_type not in SUPPORTED_ARTIFACT_TYPES:
            raise ValueError(f"Unsupported artifact type '{artifact_type}'. Must be one of: {sorted(SUPPORTED_ARTIFACT_TYPES)}")

        # 1. Check explicit baseline package if provided
        if baseline_package and isinstance(baseline_package, dict):
            if norm_type == "hld" and "hld" in baseline_package:
                return copy.deepcopy(baseline_package["hld"])
            if norm_type == "arsrs" and "arsrs" in baseline_package:
                return copy.deepcopy(baseline_package["arsrs"])
            llds = baseline_package.get("llds", {})
            if isinstance(llds, dict) and norm_type in llds:
                entry = llds[norm_type]
                data = entry.get("data", entry) if isinstance(entry, dict) else entry
                return copy.deepcopy(data)
            if norm_type in baseline_package:
                return copy.deepcopy(baseline_package[norm_type])

        # 2. Check active in-memory or persisted generation context
        try:
            from app.services.generation_service import generation_service
            context = generation_service.get_context(generation_id)
            if context:
                if norm_type == "hld" and context.hld:
                    return copy.deepcopy(context.hld)
                if norm_type == "arsrs" and context.arsrs:
                    return copy.deepcopy(context.arsrs)
                if norm_type in context.llds:
                    entry = context.llds[norm_type]
                    if entry and entry.data:
                        return copy.deepcopy(entry.data)

            # 3. Check full package from generation_service
            pkg = generation_service.get_package(generation_id)
            if norm_type == "hld" and "hld" in pkg:
                return copy.deepcopy(pkg["hld"])
            if norm_type == "arsrs" and "arsrs" in pkg:
                return copy.deepcopy(pkg["arsrs"])
            llds = pkg.get("llds", {})
            if isinstance(llds, dict) and norm_type in llds:
                entry = llds[norm_type]
                data = entry.get("data", entry) if isinstance(entry, dict) else entry
                return copy.deepcopy(data)
        except Exception:
            pass

        raise ValueError(f"Artifact '{norm_type}' could not be found for generation ID '{generation_id}'.")

    # ── 3. Targeted AI Correction Execution ────────────────────────────────────

    async def execute_targeted_correction(
        self,
        payload: TargetedCorrectionRequest,
    ) -> TargetedCorrectionResponse:
        """Execute surgical, evidence-based correction of an approved defect."""
        norm_type = normalize_artifact_type(payload.artifact_type)
        if norm_type not in SUPPORTED_ARTIFACT_TYPES:
            raise ValueError(f"Unsupported artifact type '{payload.artifact_type}'.")

        if not payload.evidence or not payload.evidence.strip():
            raise ValueError("Required evidence cannot be empty for targeted correction.")

        if not payload.correction_instruction or not payload.correction_instruction.strip():
            raise ValueError("Correction instruction cannot be empty for targeted correction.")

        # Backend independent approval check
        if not self.is_approved(payload.generation_id, payload.finding_id, payload.source_version):
            raise PermissionError(
                f"Finding '{payload.finding_id}' on artifact '{norm_type}' has not been approved for correction on version '{payload.source_version}'."
            )

        # Resolve original artifact
        original_artifact = self.resolve_artifact(
            generation_id=payload.generation_id,
            artifact_type=norm_type,
            baseline_package=payload.baseline_package,
        )

        # Check source version matching
        if payload.baseline_package:
            base_ver = str(payload.baseline_package.get("version_tag", payload.baseline_package.get("version", "v1.0"))).strip()
            req_ver = payload.source_version.strip()
            if base_ver and req_ver and base_ver.lstrip("v") != req_ver.lstrip("v"):
                raise ValueError(
                    f"Stale artifact version: source version '{req_ver}' does not match active baseline version '{base_ver}'."
                )

        operation_id = f"corr_op_{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()

        # Branch 1: Simulated corrected artifact for testing / deterministic simulation
        if payload.simulated_corrected_artifact is not None:
            corrected_artifact = copy.deepcopy(payload.simulated_corrected_artifact)
            change_summary = f"Applied targeted update to resolve [{payload.finding_id}]: {payload.correction_instruction}"
            explanation = payload.reason or "Simulated targeted refinement applied."
            unresolved = []
        else:
            # Branch 2: Real LLM Inference via OpenRouterProvider
            corrected_artifact, change_summary, explanation, unresolved = await self._run_llm_correction(
                artifact_type=norm_type,
                original_artifact=original_artifact,
                payload=payload,
            )

        # Verify the correction result
        verification, status = self.verify_correction(
            original=original_artifact,
            corrected=corrected_artifact,
            payload=payload,
            unresolved=unresolved,
        )

        response = TargetedCorrectionResponse(
            operation_id=operation_id,
            status=status,
            generation_id=payload.generation_id,
            source_version=payload.source_version,
            artifact_type=norm_type,
            finding_id=payload.finding_id,
            change_summary=change_summary,
            explanation=explanation,
            original_artifact=original_artifact,
            corrected_artifact=corrected_artifact,
            verification_result=verification,
            unresolved_issues=unresolved,
            created_at=now,
        )

        # Record operation in store
        self._operations_store[operation_id] = {
            "operation_id": operation_id,
            "status": status,
            "generation_id": payload.generation_id,
            "source_version": payload.source_version,
            "artifact_type": norm_type,
            "finding_id": payload.finding_id,
            "original_artifact": original_artifact,
            "corrected_artifact": corrected_artifact,
            "change_summary": change_summary,
            "explanation": explanation,
            "verification_result": verification.model_dump(),
            "unresolved_issues": unresolved,
            "created_at": now,
            "accepted_at": None,
            "rejected_at": None,
            "baseline_package": payload.baseline_package,
        }

        # Persist operation record to disk
        safe_op = re.sub(r"[^\w\-]", "_", operation_id)
        self._persist_file("operations", f"{safe_op}.json", self._operations_store[operation_id])

        return response

    # ── 4. Prompt Engineering and OpenRouter LLM Call ─────────────────────────

    async def _run_llm_correction(
        self,
        artifact_type: str,
        original_artifact: Dict[str, Any],
        payload: TargetedCorrectionRequest,
    ) -> Tuple[Dict[str, Any], str, str, List[str]]:
        """Query free OpenRouter model for isolated, structured artifact refinement."""
        system_prompt = (
            "You are a Principal Software Architect performing a targeted, surgical correction on an architecture artifact.\n"
            "Your objective is to resolve an approved validator finding while strictly preserving all unrelated content.\n\n"
            "STRICT GUIDELINES:\n"
            "1. Modify ONLY the component or section directly affected by the finding.\n"
            "2. PRESERVE 100% of all existing interfaces, endpoints, schemas, service boundaries, and configurations that are unrelated.\n"
            "3. Do not invent unrelated features, tools, or dependencies.\n"
            "4. Output MUST be valid JSON only, enclosed in ```json ``` codeblock with the exact schema:\n"
            "{\n"
            '  "corrected_artifact": <the complete corrected artifact JSON object>,\n'
            '  "change_summary": "<concise 1-2 sentence description of what was changed>",\n'
            '  "explanation": "<architectural rationale for the change>",\n'
            '  "unresolved_issues": []\n'
            "}"
        )

        user_prompt = (
            f"TARGET ARTIFACT TYPE: {artifact_type.upper()}\n"
            f"APPROVED FINDING ID: {payload.finding_id}\n"
            f"DEFECT DESCRIPTION: {payload.finding_description}\n"
            f"VALIDATOR EVIDENCE: {payload.evidence}\n"
            f"TARGET COMPONENT: {payload.affected_target or 'Primary domain artifact'}\n"
            f"CORRECTION INSTRUCTION: {payload.correction_instruction}\n"
            f"RATIONALE: {payload.reason or 'Resolve architectural violation identified by Validator Engine v2'}\n\n"
            f"SOURCE ARTIFACT JSON TO CORRECT:\n{json.dumps(original_artifact, indent=2)}\n\n"
            "Produce the corrected artifact JSON resolving the finding while preserving unrelated fields verbatim."
        )

        try:
            # Uses OpenRouterProvider configured with free tier OpenRouter model
            raw_response = await self._llm_provider.acall(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                agent_role=f"correction_{artifact_type}",
            )
        except Exception as exc:
            logger.error("LLM call failed for targeted correction [%s]: %s", payload.finding_id, exc)
            raise RuntimeError(f"Model provider request failed: {str(exc)}") from exc

        # Extract structured JSON
        cleaned_json = self._extract_json_block(raw_response)
        if not cleaned_json:
            raise ValueError("Malformed model response: LLM failed to return valid JSON.")

        try:
            parsed = json.loads(cleaned_json)
        except Exception as p_err:
            raise ValueError(f"Malformed model response: JSON decode error: {str(p_err)}") from p_err

        corrected_art = parsed.get("corrected_artifact")
        if not isinstance(corrected_art, dict) or not corrected_art:
            raise ValueError("Malformed model response: 'corrected_artifact' field is missing or empty.")

        summary = parsed.get("change_summary") or f"Updated {artifact_type} to resolve {payload.finding_id}."
        explanation = parsed.get("explanation") or payload.reason or "Applied targeted architectural refinement."
        unresolved = parsed.get("unresolved_issues") or []
        if not isinstance(unresolved, list):
            unresolved = [str(unresolved)]

        return corrected_art, summary, explanation, unresolved

    def _extract_json_block(self, text: str) -> Optional[str]:
        """Extract outermost JSON object from Markdown code fence or raw string."""
        if not text or not isinstance(text, str):
            return None
        # Try ```json ... ```
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            return m.group(1).strip()
        # Fallback to matching outer braces
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            return text[first_brace : last_brace + 1].strip()
        return None

    # ── 5. Correction Result Verification ──────────────────────────────────────

    def verify_correction(
        self,
        original: Dict[str, Any],
        corrected: Dict[str, Any],
        payload: TargetedCorrectionRequest,
        unresolved: Optional[List[str]] = None,
    ) -> Tuple[VerificationResult, Literal["CORRECTION_PROPOSED", "CORRECTION_VERIFIED", "MANUAL_REVIEW_REQUIRED", "CORRECTION_FAILED"]]:
        """Verify structure, completeness, and baseline preservation of the corrected artifact."""
        passed: List[str] = []
        failed: List[str] = []
        warnings: List[str] = []

        # Check 1: Output is non-empty dictionary
        if not isinstance(corrected, dict) or len(corrected) == 0:
            failed.append("Corrected artifact is empty or invalid data type.")
            return (
                VerificationResult(
                    is_valid=False,
                    checks_passed=passed,
                    checks_failed=failed,
                    warnings=warnings,
                    baseline_preservation_score=0.0,
                    unrelated_keys_preserved=False,
                ),
                "CORRECTION_FAILED",
            )
        passed.append("Corrected artifact structure is parseable dictionary.")

        # Check 2: Unrelated top-level keys preservation
        orig_keys: Set[str] = set(original.keys())
        corr_keys: Set[str] = set(corrected.keys())
        preserved_keys = orig_keys.intersection(corr_keys)
        dropped_keys = orig_keys - corr_keys

        preservation_score = len(preserved_keys) / len(orig_keys) if orig_keys else 1.0

        if dropped_keys:
            warnings.append(f"Some top-level keys were removed: {sorted(dropped_keys)}")
            if preservation_score < 0.7:
                failed.append(f"Significant content dropped: baseline preservation score is {preservation_score:.2f} (< 0.70).")
        else:
            passed.append("100% of original top-level architecture sections preserved.")

        # Check 3: Check artifact-specific invariants
        norm_type = normalize_artifact_type(payload.artifact_type)
        if norm_type == "database":
            if "tables" in original and not isinstance(corrected.get("tables"), list):
                failed.append("Database tables array missing in corrected artifact.")
            else:
                passed.append("Database schema structure valid.")
        elif norm_type == "backend":
            if "api_endpoints" in original and not isinstance(corrected.get("api_endpoints"), list):
                failed.append("Backend api_endpoints array missing in corrected artifact.")
            else:
                passed.append("Backend service structure valid.")
        elif norm_type == "hld":
            if "major_services" in original and not isinstance(corrected.get("major_services"), list):
                failed.append("HLD major_services missing in corrected artifact.")
            else:
                passed.append("HLD service topology structure valid.")

        # Check 4: Unresolved issues flag
        if unresolved and len(unresolved) > 0:
            warnings.append(f"Model identified unresolved questions: {'; '.join(unresolved)}")

        is_valid = len(failed) == 0

        # Determine status
        if not is_valid:
            status = "CORRECTION_FAILED"
        elif unresolved and len(unresolved) > 0:
            status = "MANUAL_REVIEW_REQUIRED"
        elif len(warnings) > 0:
            status = "CORRECTION_PROPOSED"
        else:
            status = "CORRECTION_VERIFIED"

        return (
            VerificationResult(
                is_valid=is_valid,
                checks_passed=passed,
                checks_failed=failed,
                warnings=warnings,
                baseline_preservation_score=preservation_score,
                unrelated_keys_preserved=len(dropped_keys) == 0,
            ),
            status,
        )

    # ── 6. Safe Acceptance & Versioning ────────────────────────────────────────

    async def accept_correction(
        self,
        operation_id: str,
        payload: Optional[AcceptCorrectionRequest] = None,
    ) -> AcceptCorrectionResponse:
        """Commit an approved and verified correction draft into a new architecture version."""
        async with self._lock:
            op = self.get_operation(operation_id)
            if not op:
                raise KeyError(f"Correction operation '{operation_id}' not found.")

            if op.get("status") == "ACCEPTED":
                raise ValueError(f"Correction operation '{operation_id}' has already been accepted.")

            if op.get("status") == "REJECTED":
                raise ValueError(f"Cannot accept a previously rejected correction operation '{operation_id}'.")

            # Validate generation ID isolation
            if payload and payload.generation_id:
                req_gen = payload.generation_id.strip()
                op_gen = str(op.get("generation_id", "")).strip()
                if req_gen and op_gen and req_gen != op_gen:
                    raise ValueError(
                        f"Cross-generation acceptance forbidden: operation was created for generation '{op_gen}' but requested for '{req_gen}'."
                    )

            # Check expected source version hasn't changed (stale detection)
            if payload and payload.expected_source_version:
                curr_source = str(op.get("source_version", "")).lstrip("v").strip()
                exp_source = payload.expected_source_version.lstrip("v").strip()
                if curr_source != exp_source:
                    raise ValueError(
                        f"Stale correction operation: expected source version '{exp_source}' but operation was generated on '{curr_source}'."
                    )

            # Determine next version tag (e.g. v1.0 -> v1.1)
            prev_ver = op.get("source_version", "v1.0")
            clean_prev = prev_ver.lstrip("v")
            if payload and payload.target_version:
                new_ver = payload.target_version
            else:
                new_ver = f"v{bump_version_string(clean_prev, 'minor')}"

            norm_art = op["artifact_type"]
            corrected_art = op["corrected_artifact"]
            gen_id = op["generation_id"]
            now = datetime.now(timezone.utc).isoformat()

            # Update generation_service context in-memory and on-disk if active
            updated_pkg: Optional[Dict[str, Any]] = None
            try:
                from app.services.generation_service import generation_service
                context = generation_service.get_context(gen_id)
                if context:
                    if norm_art == "hld":
                        context.hld = corrected_art
                        generation_service._save_artifact(gen_id, "03_hld.json", corrected_art)
                    elif norm_art == "arsrs":
                        context.arsrs = corrected_art
                        generation_service._save_artifact(gen_id, "02_arsrs.json", corrected_art)
                    elif norm_art in context.llds:
                        context.llds[norm_art].data = corrected_art
                        context.llds[norm_art].status = "READY"
                        generation_service._save_artifact(gen_id, f"09_{norm_art}_lld.json", corrected_art)

                    context.updated_at = now
                    try:
                        updated_pkg = generation_service.get_package(gen_id)
                        updated_pkg["version"] = new_ver.lstrip("v")
                        updated_pkg["version_tag"] = new_ver
                        updated_pkg["updated_at"] = now
                        generation_service._save_artifact(gen_id, "10_architecture_package.json", updated_pkg)
                    except Exception:
                        pass
            except Exception:
                pass

            # Mark operation accepted
            op["status"] = "ACCEPTED"
            op["accepted_at"] = now
            op["committed_version"] = new_ver

            # Record version history
            if gen_id not in self._historical_versions:
                self._historical_versions[gen_id] = []
            self._historical_versions[gen_id].append({
                "operation_id": operation_id,
                "artifact_type": norm_art,
                "from_version": prev_ver,
                "to_version": new_ver,
                "finding_id": op.get("finding_id"),
                "change_summary": op.get("change_summary"),
                "previous_artifact": op.get("original_artifact"),
                "committed_artifact": corrected_art,
                "timestamp": now,
            })

            # Persist operation and version history to disk
            safe_op = re.sub(r"[^\w\-]", "_", operation_id)
            self._persist_file("operations", f"{safe_op}.json", op)
            safe_gen = re.sub(r"[^\w\-]", "_", gen_id)
            self._persist_file("versions", f"{safe_gen}.json", self._historical_versions[gen_id])

            logger.info(
                "Correction operation [%s] ACCEPTED. Bumped version %s -> %s for artifact [%s].",
                operation_id, prev_ver, new_ver, norm_art
            )

            return AcceptCorrectionResponse(
                operation_id=operation_id,
                status="ACCEPTED",
                new_version=new_ver,
                previous_version=prev_ver,
                artifact_type=norm_art,
                updated_artifact=corrected_art,
                updated_package=updated_pkg,
                accepted_at=now,
                message=f"Correction operation '{operation_id}' committed as version {new_ver}. Original artifact preserved in prior version.",
            )

    # ── 7. Rejection (Preserve Original Artifact) ──────────────────────────────

    def reject_correction(self, operation_id: str) -> RejectCorrectionResponse:
        """Reject a proposed correction draft. Leaves original architecture 100% untouched."""
        op = self.get_operation(operation_id)
        if not op:
            raise KeyError(f"Correction operation '{operation_id}' not found.")

        if op.get("status") == "ACCEPTED":
            raise ValueError(f"Cannot reject an already accepted correction operation '{operation_id}'.")

        now = datetime.now(timezone.utc).isoformat()
        op["status"] = "REJECTED"
        op["rejected_at"] = now

        # Persist rejected state to disk
        safe_op = re.sub(r"[^\w\-]", "_", operation_id)
        self._persist_file("operations", f"{safe_op}.json", op)

        logger.info("Correction operation [%s] REJECTED by user. Original artifact preserved.", operation_id)

        return RejectCorrectionResponse(
            operation_id=operation_id,
            status="REJECTED",
            message="Correction draft rejected. Original artifact remains completely unchanged.",
            rejected_at=now,
        )

    def get_operation(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Fetch details of a specific correction operation with disk recovery."""
        op = self._operations_store.get(operation_id)
        if not op:
            safe_op = re.sub(r"[^\w\-]", "_", operation_id)
            for parent_dir in (CORRECTIONS_DIR, CORRECTIONS_MIRROR_DIR):
                f = parent_dir / "operations" / f"{safe_op}.json"
                if f.exists():
                    try:
                        op = json.loads(f.read_text(encoding="utf-8"))
                        if op and isinstance(op, dict):
                            self._operations_store[operation_id] = op
                            return op
                    except Exception:
                        pass
        return op

    def get_historical_versions(self, generation_id: str) -> List[Dict[str, Any]]:
        """Fetch historical committed version audit trail for a generation."""
        gen_clean = generation_id.strip()
        if gen_clean in self._historical_versions:
            return self._historical_versions[gen_clean]
        safe_gen = re.sub(r"[^\w\-]", "_", gen_clean)
        for parent_dir in (CORRECTIONS_DIR, CORRECTIONS_MIRROR_DIR):
            f = parent_dir / "versions" / f"{safe_gen}.json"
            if f.exists():
                try:
                    records = json.loads(f.read_text(encoding="utf-8"))
                    if isinstance(records, list):
                        self._historical_versions[gen_clean] = records
                        return records
                except Exception:
                    pass
        return []


# Global singleton instance of CorrectionService
correction_service = CorrectionService()

