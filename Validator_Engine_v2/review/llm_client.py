"""OpenAI-compatible LLM Client for architectural review with free model fallback.

Handles:
- OpenAI-compatible chat completions over HTTP via httpx
- Deterministic mock mode (VALIDATOR_MOCK=1) for offline testing
- Free-only fallback model sequence (no paid inference, no paid fallback)
- Error handling for 401, 403, 429, 502, 503, 504, timeouts, and JSON decode errors with 1 retry
- Status tracking: ok | unavailable | partial
- Model tracking: records model_used per execution
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple
import httpx

from Validator_Engine_v2.config import config
from Validator_Engine_v2.review.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def _extract_first_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract and parse first valid JSON object from LLM response text."""
    if not text or not str(text).strip():
        return None

    clean = text.strip()

    # 1. Direct JSON parse
    try:
        data = json.loads(clean)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # 2. Check for markdown code fences ```json ... ```
    fence_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if fence_match:
        try:
            data = json.loads(fence_match.group(1).strip())
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    # 3. Regex search for outermost curly braces
    m = re.search(r"(\{[\s\S]*\})", text)
    if m:
        try:
            data = json.loads(m.group(1).strip())
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    return None


class ReviewerLLMClient:
    """Async client for architectural evaluation using OpenAI-compatible API with free fallback."""

    def __init__(
        self,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        mock_mode: Optional[str] = None,
        timeout: Optional[float] = None,
        fallback_models: Optional[List[str]] = None,
    ) -> None:
        self.api_base = (api_base or config.VALIDATOR_API_BASE).rstrip("/")
        self.api_key = api_key or config.VALIDATOR_API_KEY
        self.model = model or config.VALIDATOR_MODEL
        self.mock_mode = mock_mode
        self.timeout = timeout or config.LLM_TIMEOUT_SECONDS
        self.fallback_models = fallback_models or config.get_fallback_models()
        self.last_model_used: Optional[str] = None
        self.call_count: int = 0

    def get_api_keys(self) -> List[str]:
        """Ordered sequence of candidate API keys to try across environments."""
        keys: List[str] = []
        if self.api_key and self.api_key.strip():
            keys.append(self.api_key.strip())
        for env_var in (
            "VALIDATOR_API_KEY",
            "OPENROUTER_API_KEY",
            "OPENROUTER_API_KEY_1",
            "OPENROUTER_API_KEY_2",
            "OPENROUTER_API_KEY_3",
            "OPENROUTER_API_KEY_4",
        ):
            val = os.getenv(env_var, "").strip()
            if val and val not in keys:
                keys.append(val)
        return keys

    def get_model_sequence(self) -> List[str]:
        """Ordered sequence of free models to try."""
        seq = [self.model]
        for m in self.fallback_models:
            if m and m not in seq:
                seq.append(m)
        return seq

    def _generate_mock_response(
        self,
        artifact_name: str,
        artifact_data: Dict[str, Any],
        rubric: Dict[str, Any],
        user_prompt: str = "",
    ) -> Dict[str, Any]:
        """Produce deterministic mock review responses based on artifact content."""
        dimensions = []
        findings = []

        serialized = json.dumps(artifact_data).lower()
        context_str = (serialized + " " + user_prompt.lower())
        has_concurrency_defect = (
            ("parking" in context_str or "defect" in context_str or "double-booking" in context_str)
            and "select for update" not in serialized
            and "redlock" not in serialized
        )

        for d in rubric.get("dimensions", []):
            d_id = d["id"]
            score = 4
            missing = []
            rationale = f"Thorough {d['label']} aligned with architecture standards."
            evidence_path = None

            # Find a real key in artifact to serve as valid evidence
            if artifact_data:
                for k in artifact_data.keys():
                    if k in ("api_endpoints", "services", "tables", "major_services", "pages", "security_controls"):
                        evidence_path = f"/{k}"
                        break
                if not evidence_path:
                    evidence_path = f"/{list(artifact_data.keys())[0]}"

            # Detect concurrency defect in backend / database
            if has_concurrency_defect and ("concurrency" in d_id or "isolation" in d_id):
                score = 2
                missing = ["Missing row-level locking (SELECT FOR UPDATE) or distributed hold lock."]
                rationale = "High concurrency contention detected with no locking mechanism specified."
                if evidence_path:
                    findings.append({
                        "rule_id": "REVIEW.CONCURRENCY_RISK",
                        "severity": "high",
                        "message": "Double-booking race condition: no atomic locking on reservation resource.",
                        "evidence_path": evidence_path,
                        "fix": "Implement SELECT FOR UPDATE or Redis Redlock with finite hold TTL.",
                    })

            dimensions.append({
                "id": d_id,
                "score": score,
                "evidence_path": evidence_path,
                "missing": missing,
                "rationale": rationale,
            })

        response: Dict[str, Any] = {
            "dimensions": dimensions,
            "findings": findings,
        }

        # If user prompt asked for assessments, generate mock assessments
        if "assessments" in user_prompt.lower() or "real-world reference patterns" in user_prompt.lower():
            # Extract pattern IDs if mentioned
            pattern_ids = re.findall(r'"id":\s*"([^"]+)"', user_prompt)
            assessments = []
            for pid in pattern_ids:
                status = "ALIGNED"
                ev = f"/{list(artifact_data.keys())[0]}" if artifact_data else None
                just = "Aligned with reference architecture capability."
                refs: List[str] = []

                if "concurrency" in pid.lower() or "region" in pid.lower() or "outage" in pid.lower():
                    if has_concurrency_defect and artifact_name in ("backend", "database"):
                        status = "MISSING"
                        ev = None
                        just = "No distributed locking or row-level locking found for shared state."
                    elif artifact_name not in ("backend", "database"):
                        status = "NOT_APPLICABLE"
                        ev = None
                        refs = ["NFR-001", "NFR-002"]
                        just = "Concurrency locking delegates to persistence and backend layers."

                assessments.append({
                    "pattern_id": pid,
                    "status": status,
                    "evidence_path": ev,
                    "justification": just,
                    "requirement_refs": refs,
                })
            response["assessments"] = assessments

        return response

    async def call_review(
        self,
        artifact_name: str,
        artifact_data: Dict[str, Any],
        rubric: Dict[str, Any],
        user_prompt: str,
        mock_mode: Optional[str] = None,
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """Execute LLM review call with fallback model sequence.

        Returns:
            parsed_json: Dict with dimensions and findings or None
            reviewer_status: 'ok' | 'unavailable' | 'partial'
        """
        self.call_count += 1
        effective_mock = mock_mode if mock_mode is not None else (self.mock_mode if self.mock_mode is not None else config.VALIDATOR_MOCK)

        # 1. Mock Mode
        if str(effective_mock) in ("1", "true", "mock"):
            self.last_model_used = "mock"
            mock_res = self._generate_mock_response(artifact_name, artifact_data, rubric, user_prompt=user_prompt)
            return mock_res, "ok"
        elif str(effective_mock) in ("unavailable", "fail"):
            self.last_model_used = None
            return None, "unavailable"

        # 2. Real HTTP Call with Free Fallback Model Sequence
        keys_to_try = self.get_api_keys()
        if not keys_to_try:
            logger.error(
                "Real LLM review requested (VALIDATOR_MOCK=0) but no API key was provided. "
                "Set VALIDATOR_API_KEY or OPENROUTER_API_KEY in Validator_Engine_v2/.env"
            )
            self.last_model_used = None
            return None, "unavailable"

        url = f"{self.api_base}/chat/completions"
        models_to_try = self.get_model_sequence()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for active_key in keys_to_try:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {active_key}",
                    "HTTP-Referer": "https://archova.ai",
                    "X-Title": "Archova Validator Engine v2",
                }

                for current_model in models_to_try:
                    payload = {
                        "model": current_model,
                        "temperature": 0.0,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                    }

                    # Up to 2 attempts per model (initial + 1 JSON repair retry)
                    key_rejected = False
                    for attempt in range(2):
                        try:
                            resp = await asyncio.wait_for(
                                client.post(url, headers=headers, json=payload),
                                timeout=self.timeout,
                            )

                            # If unauthorized or forbidden (401, 403) or daily free-tier rate limit (429), key is blocked/exhausted -> rotate key
                            is_key_exhausted = resp.status_code in (401, 403) or (resp.status_code == 429 and "free-models-per-day" in resp.text)
                            if is_key_exhausted:
                                masked_key = active_key[:12] + "..." + active_key[-4:] if len(active_key) > 16 else "***"
                                logger.warning(
                                    "LLM reviewer key [%s] daily quota limit or authentication failure (HTTP %d). Rotating to next candidate key...",
                                    masked_key,
                                    resp.status_code,
                                )
                                key_rejected = True
                                break

                            # If model not found (404), temporary rate limit (429), or server error (500, 502, 503, 504) -> fallback model
                            if resp.status_code in (404, 429, 500, 502, 503, 504):
                                logger.warning(
                                    "Model %s returned status %d. Attempting fallback to next free model in sequence...",
                                    current_model,
                                    resp.status_code,
                                )
                                break

                            resp.raise_for_status()
                            data = resp.json()
                            choices = data.get("choices", [])
                            if not choices:
                                break

                            content = choices[0].get("message", {}).get("content", "")
                            parsed = _extract_first_json(content)
                            if parsed and ("dimensions" in parsed or "assessments" in parsed):
                                self.last_model_used = current_model
                                self.api_key = active_key
                                return parsed, "ok"

                            # If first attempt returned invalid JSON, retry once on this model with repair prompt
                            if attempt == 0:
                                payload["messages"].append({"role": "assistant", "content": content})
                                payload["messages"].append({
                                    "role": "user",
                                    "content": "Your previous response was not valid JSON. Return ONLY the JSON object with 'dimensions', 'findings', and 'assessments'.",
                                })
                        except (httpx.TimeoutException, httpx.NetworkError, asyncio.TimeoutError) as net_err:
                            logger.warning(
                                "Network/timeout error for model %s: %s. Attempting fallback...",
                                current_model,
                                net_err,
                            )
                            break
                        except Exception as exc:
                            logger.warning("Error calling model %s: %s", current_model, exc)
                            break

                    if key_rejected:
                        break

        # All configured free models and keys exhausted or failed
        logger.error("All configured free OpenRouter models/keys failed. Marking reviewer stage unavailable.")
        self.last_model_used = None
        return None, "unavailable"
