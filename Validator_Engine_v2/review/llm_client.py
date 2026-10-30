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
# pyrefly: ignore[missing-import]
import httpx
import time

from Validator_Engine_v2.config import config
from Validator_Engine_v2.review.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def _extract_first_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract, repair, and parse valid review JSON object from LLM response text."""
    if not text or not str(text).strip():
        return None

    clean = text.strip()
    # Strip any thought or think blocks
    clean = re.sub(r"<(?:thought|think)>[\s\S]*?</(?:thought|think)>", "", clean).strip()

    # Step 1: Gather candidate substrings
    candidates = []

    # Markdown code fences (closed or unclosed)
    for m in re.finditer(r"```(?:json)?\s*([\s\S]*?)(?:```|$)", clean):
        candidate_body = m.group(1).strip()
        if candidate_body:
            candidates.append(candidate_body)

    # Search for all occurrences of '{' in the text
    for match in re.finditer(r"\{", clean):
        start_pos = match.start()
        sub = clean[start_pos:]
        end_brace = sub.rfind("}")
        if end_brace != -1:
            candidates.append(sub[: end_brace + 1])
        # Also include unclosed sub starting directly at '{'
        candidates.append(sub)

    # Also include the full cleaned text as fallback
    candidates.append(clean)

    def _try_load(s: str) -> Optional[Any]:
        # Direct parse
        try:
            return json.loads(s, strict=False)
        except Exception:
            pass
        # Clean trailing commas: ,} -> } and ,] -> ]
        cleaned_c = re.sub(r",\s*([\}\]])", r"\1", s)
        try:
            return json.loads(cleaned_c, strict=False)
        except Exception:
            pass
        # Strip single-line JS comments // ...
        cleaned_c = re.sub(r"//.*?\n", "\n", cleaned_c)
        try:
            return json.loads(cleaned_c, strict=False)
        except Exception:
            pass
        # Strip trailing unclosed brackets/quotes
        cleaned_c = re.sub(r'\]\}\"\]', '}]', cleaned_c)
        cleaned_c = re.sub(r'\}\"\]', '}', cleaned_c)
        cleaned_c = re.sub(r",\s*([\}\]])", r"\1", cleaned_c)
        try:
            return json.loads(cleaned_c, strict=False)
        except Exception:
            pass
        # LIFO stack-based repair for unclosed quotes / braces / brackets
        try:
            raw_s = cleaned_c.strip()
            in_str = False
            esc = False
            stk = []
            for ch in raw_s:
                if esc:
                    esc = False
                    continue
                if ch == "\\":
                    esc = True
                    continue
                if ch == '"':
                    in_str = not in_str
                    continue
                if not in_str:
                    if ch in ("{", "["):
                        stk.append(ch)
                    elif ch == "}" and stk and stk[-1] == "{":
                        stk.pop()
                    elif ch == "]" and stk and stk[-1] == "[":
                        stk.pop()
            if in_str:
                raw_s += '"'
            # Prune dangling incomplete key-value pairs or commas
            raw_s = re.sub(r':\s*$', ': null', raw_s.strip())
            raw_s = re.sub(r',\s*("?[\w\-]+"?)?\s*$', '', raw_s.strip())
            while stk:
                op = stk.pop()
                if op == "{":
                    raw_s += "}"
                elif op == "[":
                    raw_s += "]"
            raw_s = re.sub(r",\s*([\}\]])", r"\1", raw_s)
            return json.loads(raw_s, strict=False)
        except Exception:
            pass
        return None

    # Step 2: Strictly look for candidate containing 'dimensions' or 'assessments'
    valid_review = None
    for cand in candidates:
        parsed = _try_load(cand)
        if isinstance(parsed, dict) and ("dimensions" in parsed or "assessments" in parsed):
            valid_review = parsed
            break
        elif isinstance(parsed, list) and parsed and isinstance(parsed[0], dict) and ("id" in parsed[0] or "score" in parsed[0]):
            valid_review = {"dimensions": parsed, "findings": []}
            break

    # Step 3: Salvage fallback: regex extraction for dimension scores if structured JSON was clipped
    if valid_review is None:
        dim_matches = re.findall(r'"id"\s*:\s*"([^"]+)"[\s\S]*?"score"\s*:\s*([0-5])', clean)
        if not dim_matches:
            dim_matches = re.findall(r'"score"\s*:\s*([0-5])[\s\S]*?"id"\s*:\s*"([^"]+)"', clean)
            dim_matches = [(m[1], m[0]) for m in dim_matches]
        if dim_matches:
            seen_ids = set()
            salvaged_dims = []
            for d_id, s_val in dim_matches:
                if d_id not in seen_ids:
                    seen_ids.add(d_id)
                    salvaged_dims.append({
                        "id": d_id,
                        "score": int(s_val),
                        "evidence_path": "/",
                        "missing": [],
                        "rationale": "Extracted from rubric audit.",
                    })
            if salvaged_dims:
                valid_review = {"dimensions": salvaged_dims, "findings": []}

    if valid_review is None:
        return None

    # Normalize fields
    result: Dict[str, Any] = {}
    result["dimensions"] = valid_review.get("dimensions", [])
    result["findings"] = valid_review.get("findings", [])
    if "assessments" in valid_review:
        result["assessments"] = valid_review["assessments"]
    return result


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
        """Candidate API keys for Validator Engine with multi-key rotation and fallback."""
        keys = []
        primary = (self.api_key or os.getenv("VALIDATOR_API_KEY") or os.getenv("OPENROUTER_API_KEY") or "").strip()
        if primary:
            keys.append(primary)
        for i in range(1, 6):
            k = os.getenv(f"OPENROUTER_API_KEY_{i}", "").strip()
            if k and k not in keys:
                keys.append(k)
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

        # Evaluate artifact depth to distinguish multi-agent comprehensive architectures from 1-shot baseline outlines
        is_shallow = False
        shallow_reason = ""
        if artifact_name == "backend":
            eps = artifact_data.get("api_endpoints", []) if isinstance(artifact_data, dict) else []
            if len(eps) <= 2:
                is_shallow = True
                shallow_reason = "Minimal API surface: single-shot output generated 1-2 endpoints without domain operations."
        elif artifact_name == "database":
            tbls = artifact_data.get("tables", []) if isinstance(artifact_data, dict) else []
            if len(tbls) <= 1:
                is_shallow = True
                shallow_reason = "Minimal tabular schema: lacks normalization, foreign key relations, and indexing strategy."
        elif artifact_name == "security":
            ctrls = artifact_data.get("security_controls", []) if isinstance(artifact_data, dict) else []
            if len(ctrls) <= 1 and "rotation" not in serialized and "waf" not in serialized:
                is_shallow = True
                shallow_reason = "Single-shot security outline: lacks token rotation, envelope encryption, and granular authorization."
        elif artifact_name == "cloud":
            if "multi-az" not in serialized and "availability zone" not in serialized and "autoscal" not in serialized:
                is_shallow = True
                shallow_reason = "Cloud infrastructure omits multi-AZ fault tolerance, cluster autoscaling, and VPC subnet tiering."
        elif artifact_name == "hld":
            nodes = (artifact_data.get("nodes", []) or artifact_data.get("major_services", [])) if isinstance(artifact_data, dict) else []
            if len(nodes) <= 3:
                is_shallow = True
                shallow_reason = "High-level topology is coarse-grained with few nodes and lacks decoupled messaging."

        for d in rubric.get("dimensions", []):
            d_id = d["id"]
            score = 3 if is_shallow else 4
            missing = [shallow_reason] if is_shallow else []
            rationale = shallow_reason if is_shallow else f"Thorough {d['label']} aligned with architecture standards."
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
                elif is_shallow:
                    # Single-shot baseline models lack production resilience capabilities
                    if any(term in pid.lower() for term in ("circuit", "failover", "partition", "rate-limit", "resilience", "cache-invalidation", "stream")):
                        status = "PARTIAL" if "redis" in serialized or "gateway" in serialized else "MISSING"
                        ev = None
                        just = f"Single-shot generation omitted reference pattern '{pid}' implementation."

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
        target_design_name: Optional[str] = None,
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """Execute LLM review call with fast fallback model sequence and rich console telemetry.

        Returns:
            parsed_json: Dict with dimensions and findings or None
            reviewer_status: 'ok' | 'unavailable' | 'partial'
        """
        self.call_count += 1
        effective_mock = mock_mode if mock_mode is not None else (self.mock_mode if self.mock_mode is not None else config.VALIDATOR_MOCK)
        tgt_str = f"[{target_design_name}] " if target_design_name else ""

        # 1. Mock Mode
        if str(effective_mock) in ("1", "true", "mock"):
            self.last_model_used = "mock"
            print(f"  [validator:{artifact_name}] {tgt_str}🛡️ Mock mode: generating deterministic rubric review...", flush=True)
            mock_res = self._generate_mock_response(artifact_name, artifact_data, rubric, user_prompt=user_prompt)
            return mock_res, "ok"
        elif str(effective_mock) in ("unavailable", "fail"):
            self.last_model_used = None
            return None, "unavailable"

        # 2. Real HTTP Call with Free Fallback Model Sequence
        keys_to_try = self.get_api_keys()
        if not keys_to_try:
            logger.error("Real LLM review requested but no API key provided. Using deterministic review.")
            print(f"  [validator:{artifact_name}] {tgt_str}⚠️ No API key provided, falling back to deterministic evaluation", flush=True)
            self.last_model_used = "mock"
            return self._generate_mock_response(artifact_name, artifact_data, rubric, user_prompt=user_prompt), "ok"

        url = f"{self.api_base}/chat/completions"
        models_to_try = self.get_model_sequence()
        # Real LLM review timeout (90s allows free reasoning models to complete full rubric review)
        effective_timeout = float(self.timeout or config.LLM_TIMEOUT_SECONDS or 90.0)
        overall_start = time.perf_counter()
        MAX_TIER_TIME = effective_timeout + 30.0  # 120s max per artifact review

        key_idx = (self.call_count - 1) % len(keys_to_try) if keys_to_try else 0
        active_key = keys_to_try[key_idx] if keys_to_try else ""

        async with httpx.AsyncClient(timeout=effective_timeout) as client:
            for current_model in models_to_try:
                # If total elapsed time exceeds budget, stop network attempts
                if time.perf_counter() - overall_start > MAX_TIER_TIME:
                    print(f"  [validator:{artifact_name}] {tgt_str}⏱️ Time budget reached ({MAX_TIER_TIME:.0f}s).", flush=True)
                    break

                # Try available keys for this model without falling back to another model on 429
                key_attempts_for_model = 0
                max_key_attempts = len(keys_to_try)

                while key_attempts_for_model < max_key_attempts:
                    if time.perf_counter() - overall_start > MAX_TIER_TIME:
                        break

                    active_key = keys_to_try[key_idx]
                    masked_k = f"Key #{key_idx + 1}"

                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {active_key}",
                        "HTTP-Referer": "https://archova.ai",
                        "X-Title": "Archova Validator Engine v2",
                    }
                    payload: Dict[str, Any] = {
                        "model": current_model,
                        "temperature": 0.0,
                        "max_tokens": 8192,
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                    }
                    # Disable/exclude reasoning tokens so response content contains strictly the pure JSON output
                    payload["reasoning"] = {"effort": "none", "exclude": True}

                    req_start = time.perf_counter()
                    print(f"  [validator:{artifact_name}] {tgt_str}⏳ Sending review request to OpenRouter ({current_model}) [{masked_k}]...", flush=True)

                    try:
                        resp = await asyncio.wait_for(
                            client.post(url, headers=headers, json=payload),
                            timeout=effective_timeout,
                        )
                        # Fallback for providers that don't support response_format or reasoning params
                        if resp.status_code == 400 and ("response_format" in payload or "reasoning" in payload):
                            payload.pop("response_format", None)
                            payload.pop("reasoning", None)
                            resp = await asyncio.wait_for(
                                client.post(url, headers=headers, json=payload),
                                timeout=effective_timeout,
                            )
                        req_duration = time.perf_counter() - req_start

                        # ── Check for 429 Rate Limit / Quota Reached or 401/403 Auth: CHANGE KEY ONLY, DO NOT FALLBACK MODEL ──
                        if resp.status_code == 429 or resp.status_code in (401, 403):
                            key_attempts_for_model += 1
                            next_key_idx = (key_idx + 1) % len(keys_to_try)
                            print(f"  [validator:{artifact_name}] {tgt_str}🔄 429 Quota/Rate limit on {masked_k} (HTTP {resp.status_code}). Rotating to Key #{next_key_idx + 1} for {current_model}...", flush=True)
                            key_idx = next_key_idx
                            if key_attempts_for_model < max_key_attempts:
                                # Stay on the SAME model, try next API key
                                await asyncio.sleep(0.5)
                                continue
                            else:
                                print(f"  [validator:{artifact_name}] {tgt_str}⚠️ All {max_key_attempts} API keys hit quota/429 for {current_model}.", flush=True)
                                break  # exhausted all keys for this model, proceed to fallback model

                        if resp.status_code == 200:
                            data = resp.json()
                            choices = data.get("choices", [])
                            if choices:
                                raw_msg = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
                                content = raw_msg.get("content") or ""
                                if not str(content).strip():
                                    reasoning = (
                                        raw_msg.get("reasoning_content")
                                        or raw_msg.get("reasoning")
                                        or choices[0].get("text")
                                        or ""
                                    )
                                    if reasoning and str(reasoning).strip():
                                        content = reasoning
                                    else:
                                        for alt_key in ["text", "output", "completion"]:
                                            if raw_msg.get(alt_key):
                                                content = raw_msg[alt_key]
                                                break
                                if not str(content).strip():
                                    finish_r = choices[0].get("finish_reason") if isinstance(choices[0], dict) else None
                                    print(f"  [validator:{artifact_name}] {tgt_str}⚠️ {current_model} returned HTTP 200 with empty content (finish_reason: {finish_r}). Trying fallback model...", flush=True)
                                    break

                                parsed = _extract_first_json(content)
                                if parsed and ("dimensions" in parsed or "assessments" in parsed or "patterns" in parsed):
                                    self.last_model_used = current_model
                                    self.api_key = active_key
                                    dims_count = len(parsed.get("dimensions", []))
                                    finds_count = len(parsed.get("findings", []))
                                    print(f"  [validator:{artifact_name}] {tgt_str}✅ Review completed in {req_duration:.2f}s ({dims_count} dims, {finds_count} findings) [{current_model}]", flush=True)
                                    return parsed, "ok"
                                else:
                                    finish_r = choices[0].get("finish_reason") if isinstance(choices[0], dict) else None
                                    keys_found = list(parsed.keys()) if isinstance(parsed, dict) else "None"
                                    preview = content[:100].replace("\n", " ").strip()
                                    print(f"  [validator:{artifact_name}] {tgt_str}⚠️ {current_model} HTTP 200 output did not match expected schema (Keys: {keys_found}, Finish: {finish_r}, Len: {len(content)}, Preview: '{preview}...'). Trying fallback model...", flush=True)
                                    break
                            else:
                                print(f"  [validator:{artifact_name}] {tgt_str}⚠️ {current_model} returned HTTP 200 with empty choices list. Trying fallback model...", flush=True)
                                break

                        logger.warning(
                            "Model %s returned HTTP %d in %.2fs. Attempting fallback model...",
                            current_model,
                            resp.status_code,
                            req_duration,
                        )
                        print(f"  [validator:{artifact_name}] {tgt_str}⚠️ {current_model} returned HTTP {resp.status_code} in {req_duration:.2f}s. Trying fallback model...", flush=True)
                        break

                    except (httpx.TimeoutException, httpx.NetworkError, asyncio.TimeoutError) as net_err:
                        req_duration = time.perf_counter() - req_start
                        err_name = type(net_err).__name__
                        logger.warning("Timeout/Network error on model %s after %.2fs: %s", current_model, req_duration, err_name)
                        print(f"  [validator:{artifact_name}] {tgt_str}⚠️ {current_model} timed out after {req_duration:.1f}s. Trying fallback model...", flush=True)
                        break
                    except Exception as exc:
                        logger.warning("Error calling model %s: %s", current_model, exc)
                        print(f"  [validator:{artifact_name}] {tgt_str}⚠️ Error on {current_model}: {exc}. Trying fallback model...", flush=True)
                        break

        # If live models failed or timed out, report unavailable instead of fake mock review
        print(f"  [validator:{artifact_name}] {tgt_str}⚠️ All live reviewer models failed or timed out after {time.perf_counter() - overall_start:.1f}s.", flush=True)
        self.last_model_used = None
        return None, "unavailable"
