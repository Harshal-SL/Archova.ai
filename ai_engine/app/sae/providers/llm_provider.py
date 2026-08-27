"""Multi-Key LLM Provider for SAE v2.

Features:
- Multi-API-Key distribution with fixed per-role key assignment.
- Both synchronous and async generation (httpx.AsyncClient) for high-concurrency parallel agents.
- Example-driven prompts with response_format={"type": "json_object"} (NO schema injection).
- Direct clean JSON parsing first, with fallback to non-destructive repair.
- Auto-unwrapping of root container keys and field alias normalization.
- Graceful partial failure tolerance (never crashes the whole pipeline for one agent).
- 60s per-call timeout and 8192 default max_tokens.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import threading
import time
from typing import Any, Dict, List, Optional, Type, TypeVar

import httpx
from pydantic import BaseModel

from app.config.model_config import get_model_for_capability
from app.sae.utils.prompt_utils import repair_json_string

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Default per-role API key index mapping (0-based index into keys list)
# Distributes parallel agents evenly across all 4 distinct keys
DEFAULT_ROLE_KEY_INDEX: Dict[str, int] = {
    # Phase 1 & 2
    "requirement_analysis": 0,   # Key 1
    "technology_advisor": 1,     # Key 2
    "hld": 2,                    # Key 3
    # Phase 3 (Parallel LLD & Operations across available keys)
    "backend": 0,                # Key 1
    "backend_lld": 0,            # Key 1
    "database": 1,               # Key 2
    "database_lld": 1,           # Key 2
    "frontend": 2,               # Key 3
    "frontend_lld": 2,           # Key 3
    "security": 3,               # Key 4
    "security_lld": 3,           # Key 4
    "cloud": 0,                  # Key 1
    "cloud_lld": 0,              # Key 1
    "testing_strategy": 1,       # Key 2
    "observability": 2,          # Key 3
    "runbooks": 3,               # Key 4
    # Phase 5 (Sequential Adversarial Review)
    "adversarial_review": 3,     # Key 4
}

# Key normalization map for flexible LLM output mapping
KEY_ALIASES: Dict[str, str] = {
    "endpoints": "api_endpoints",
    "apis": "api_endpoints",
    "domain_entities": "domain_models",
    "entities": "domain_models",
    "daos": "repositories",
    "data_access": "repositories",
    "application_services": "services",
    "database_tables": "tables",
    "table_schemas": "tables",
    "threats": "threat_model",
    "controls": "security_controls",
    "infrastructure": "compute",
    "containers": "container_orchestration",
    "ui_components": "components",
    "views": "pages",
}


def _load_api_keys() -> List[str]:
    """Load all configured OpenRouter API keys from environment."""
    keys: List[str] = []
    for i in range(1, 10):
        k = os.getenv(f"OPENROUTER_API_KEY_{i}", "").strip()
        if k:
            keys.append(k)

    # Fallback to single OPENROUTER_API_KEY
    if not keys:
        single = os.getenv("OPENROUTER_API_KEY", "").strip()
        if single:
            keys.append(single)

    return keys or [""]


class OpenRouterProvider:
    """Multi-Key OpenRouter LLM Provider supporting sync and async execution."""

    def __init__(
        self,
        api_keys: Optional[List[str]] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_retries: int = 2,
        debug: bool = False,
        sae_logger: Optional[Any] = None,
    ) -> None:
        self.api_keys = api_keys or _load_api_keys()
        self.base_url = (base_url or os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")).rstrip("/")
        self.default_model = default_model or os.getenv("LLM_MODEL", "nvidia/nemotron-3.5-lightning:free")
        self.timeout = timeout or float(os.getenv("LLM_TIMEOUT_SECONDS", os.getenv("LLM_TIMEOUT", "60")))
        self.max_tokens = max_tokens or int(os.getenv("LLM_MAX_TOKENS", "3072"))
        self.max_retries = max_retries if max_retries is not None else 3
        self.debug = debug or os.getenv("SAE_DEBUG", "false").lower() in ("true", "1", "yes")
        self.sae_logger = sae_logger
        self._rr_lock = threading.Lock()
        self._rr_counter = 0

    def set_sae_logger(self, sae_logger: Any) -> None:
        """Set or update the active SAELogger instance."""
        self.sae_logger = sae_logger

    def get_api_key_for_role(self, agent_role: str = "general") -> str:
        """Resolve the designated API key for a specific agent role or round-robin if general."""
        if not self.api_keys:
            return ""
        norm_role = agent_role.lower().strip()
        if norm_role in DEFAULT_ROLE_KEY_INDEX:
            target_idx = DEFAULT_ROLE_KEY_INDEX[norm_role]
        else:
            with self._rr_lock:
                target_idx = self._rr_counter
                self._rr_counter = (self._rr_counter + 1) % len(self.api_keys)

        # Wrap around if fewer keys are provided
        idx = target_idx % len(self.api_keys)
        key = self.api_keys[idx]
        logger.info("SAE OpenRouterProvider: Role '%s' assigned API Key #%d (%s...)", agent_role, idx + 1, key[:12] if key else "NONE")
        return key

    def _get_headers(self, api_key: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ai-architecture-platform.local",
            "X-Title": "SAE v2 Architecture Engine",
        }

    # ── Clean Parsing & Sanitization ──────────────────────────────────────────

    def parse_and_validate(
        self,
        raw_text: str,
        response_model: Type[T],
        agent_name: str = "Agent",
    ) -> T:
        """Parse raw LLM response cleanly, stripping reasoning tags and extracting JSON."""
        cleaned = raw_text.strip()

        # 1. Strip reasoning blocks (<think>...</think>, <thought>...</thought>, ```thinking...```)
        cleaned = re.sub(r"<(?:think|thought)>[\s\S]*?</(?:think|thought)>", "", cleaned, flags=re.DOTALL).strip()
        cleaned = re.sub(r"```thinking[\s\S]*?```", "", cleaned, flags=re.DOTALL).strip()

        dict_data: Optional[Dict[str, Any]] = None

        # 2. Try extracting from markdown code blocks first
        code_blocks = re.findall(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", cleaned)
        if code_blocks:
            for block in reversed(code_blocks):
                block_clean = block.strip()
                start = block_clean.find("{")
                end = block_clean.rfind("}")
                cand = block_clean[start : end + 1] if start != -1 and end > start else block_clean
                try:
                    parsed = json.loads(cand, strict=False)
                    if isinstance(parsed, dict) and parsed:
                        dict_data = parsed
                        break
                except Exception:
                    try:
                        repaired = repair_json_string(cand)
                        parsed = json.loads(repaired, strict=False)
                        if isinstance(parsed, dict) and parsed:
                            dict_data = parsed
                            break
                    except Exception:
                        pass

        # 3. Check for unclosed markdown code block at the end (e.g. ```json\n{...)
        if dict_data is None:
            unclosed_match = re.search(r"```(?:json)?\s*\n?(\{[\s\S]*)$", cleaned)
            if unclosed_match:
                unclosed_cand = unclosed_match.group(1).strip()
                try:
                    dict_data = json.loads(unclosed_cand, strict=False)
                except Exception:
                    try:
                        repaired = repair_json_string(unclosed_cand)
                        parsed = json.loads(repaired, strict=False)
                        if isinstance(parsed, dict) and parsed:
                            dict_data = parsed
                    except Exception:
                        pass

        # 4. Backward scan: If text contains reasoning followed by JSON, scan candidate '{' from the end
        if dict_data is None:
            last_close = cleaned.rfind("}")
            if last_close != -1:
                # Find all '{' positions before last_close
                open_positions = [i for i, ch in enumerate(cleaned[:last_close]) if ch == "{"]
                # Try candidate blocks from right to left (final JSON is generated at the end)
                for pos in reversed(open_positions):
                    sub_cand = cleaned[pos : last_close + 1]
                    try:
                        parsed = json.loads(sub_cand, strict=False)
                        if isinstance(parsed, dict) and parsed:
                            dict_data = parsed
                            break
                    except Exception:
                        pass

                # If still not found, try non-destructive repair on top candidate blocks
                if dict_data is None:
                    for pos in reversed(open_positions[-15:]):
                        sub_cand = cleaned[pos : last_close + 1]
                        try:
                            repaired = repair_json_string(sub_cand)
                            parsed = json.loads(repaired, strict=False)
                            if isinstance(parsed, dict) and parsed:
                                dict_data = parsed
                                break
                        except Exception:
                            pass

        if not isinstance(dict_data, dict):
            logger.debug(f"[{agent_name}] Extracted payload is not a dict: {type(dict_data).__name__}. Initializing default model.")
            return response_model()

        # Auto-unwrap root container key only if inner dict matches response_model fields better
        model_field_names = set(response_model.model_fields.keys())
        direct_matches = set(dict_data.keys()).intersection(model_field_names)

        for unwrap_key in [
            "backend_lld", "backend_design", "backend",
            "hld", "hld_document", "high_level_design",
            "database_lld", "database_design", "database",
            "frontend_lld", "frontend_design", "frontend",
            "security_lld", "security_design", "security",
            "cloud_lld", "cloud_design", "cloud",
            "requirement_analysis", "technology_recommendation", "technology_recommendations",
            "data", "result", "response", "output",
        ]:
            if unwrap_key in dict_data and isinstance(dict_data[unwrap_key], dict):
                inner_matches = set(dict_data[unwrap_key].keys()).intersection(model_field_names)
                if len(inner_matches) > len(direct_matches) or (len(direct_matches) == 0 and len(dict_data) <= 2):
                    dict_data = dict_data[unwrap_key]
                    break

        # Normalize key aliases
        for alias, target in KEY_ALIASES.items():
            if alias in dict_data and target not in dict_data:
                dict_data[target] = dict_data.pop(alias)

        # Validate with Pydantic
        try:
            return response_model.model_validate(dict_data)
        except Exception as pydantic_err:
            logger.warning(f"[{agent_name}] Pydantic validation warning: {pydantic_err}. Attempting partial field recovery.")
            # Partial field population
            valid_fields = {}
            for field_name in response_model.model_fields.keys():
                if field_name in dict_data:
                    valid_fields[field_name] = dict_data[field_name]
            try:
                return response_model.model_validate(valid_fields)
            except Exception:
                return response_model()

    # ── Async Generation ──────────────────────────────────────────────────────

    async def generate_structured_async(
        self,
        prompt: str,
        response_model: Type[T],
        model_name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        agent_role: str = "general",
        temperature: float = 0.2,
    ) -> T:
        """Asynchronously call OpenRouter and return validated flat response model."""
        model = model_name or (get_model_for_capability(agent_role) if agent_role != "general" else "") or self.default_model
        api_key = self.get_api_key_for_role(agent_role)
        headers = self._get_headers(api_key)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"},
        }

        key_idx = ((DEFAULT_ROLE_KEY_INDEX.get(agent_role.lower().strip(), 0) % len(self.api_keys)) + 1) if self.api_keys else 0
        if self.sae_logger:
            try:
                self.sae_logger.log_llm_request(
                    agent_role=agent_role,
                    model=model,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    key_idx=key_idx,
                    temperature=temperature,
                )
            except Exception:
                pass

        if self.debug:
            print(f"\n{'━'*78}\n🔍 [DEBUG: LLM REQUEST] Role: {agent_role} | Model: {model} | Key: #{key_idx} | Temp: {temperature}", flush=True)
            if system_prompt:
                sys_lines = system_prompt.strip().splitlines()
                print(f"┌─ [SYSTEM PROMPT] ({len(system_prompt)} chars):\n│ " + "\n│ ".join(sys_lines[:25]) + ("\n│ ... (truncated)" if len(sys_lines) > 25 else ""), flush=True)
            usr_lines = prompt.strip().splitlines()
            print(f"┌─ [USER PROMPT] ({len(prompt)} chars):\n│ " + "\n│ ".join(usr_lines[:45]) + ("\n│ ... (truncated preview)" if len(usr_lines) > 45 else ""), flush=True)
        base_key_idx = DEFAULT_ROLE_KEY_INDEX.get(agent_role.lower().strip(), 0) if self.api_keys else 0
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            # Dynamically rotate across available keys on retry attempts
            active_key_idx = (base_key_idx + attempt - 1) % len(self.api_keys) if self.api_keys else 0
            active_key = self.api_keys[active_key_idx] if self.api_keys else ""
            headers = self._get_headers(active_key)

            t0 = time.perf_counter()
            print(f"  [{agent_role}] ⏳ Sending request to OpenRouter ({model}) [Key #{active_key_idx + 1}]...", flush=True)
            try:
                async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                    resp = await client.post(
                        f"{self.base_url}/chat/completions",
                        json=payload,
                        headers=headers,
                    )
                    latency = round(time.perf_counter() - t0, 2)

                    if resp.status_code == 429 or resp.status_code in (500, 502, 503, 504):
                        wait_time = 1.5 * attempt
                        # If a specific capability model is rate-limited upstream, failover to default_model
                        if attempt >= 2 and payload.get("model") != self.default_model:
                            print(f"  [{agent_role}] 🔄 Failing over from rate-limited model ({payload.get('model')}) to default ({self.default_model})...", flush=True)
                            payload["model"] = self.default_model
                        print(f"  [{agent_role}] ⚠️ HTTP {resp.status_code} on Key #{active_key_idx + 1} (attempt {attempt}/{self.max_retries}). Rotating key & backing off for {wait_time:.1f}s...", flush=True)
                        if attempt < self.max_retries:
                            await asyncio.sleep(wait_time)
                        continue

                    resp.raise_for_status()
                    data = resp.json()

                    if "error" in data:
                        err_msg = data["error"].get("message", str(data["error"]))
                        wait_time = 2.0 * attempt + 1.0
                        if attempt >= 2 and payload.get("model") != self.default_model:
                            print(f"  [{agent_role}] 🔄 Upstream error on {payload.get('model')}. Failing over to default ({self.default_model})...", flush=True)
                            payload["model"] = self.default_model
                        print(f"  [{agent_role}] ⚠️ Upstream API error: {err_msg}. Backing off for {wait_time:.1f}s...", flush=True)
                        if attempt < self.max_retries:
                            await asyncio.sleep(wait_time)
                            continue
                        raise ValueError(f"Upstream API error: {err_msg}")

                    choices = data.get("choices", [])
                    if not choices:
                        raise ValueError(f"Empty choices in response: {data}")

                    content = choices[0].get("message", {}).get("content", "")
                    print(f"  [{agent_role}] ✅ Completed in {latency}s ({len(content)} chars)", flush=True)

                    if self.debug:
                        resp_lines = content.strip().splitlines()
                        print(f"\n{'━'*78}\n📥 [DEBUG: LLM RAW RESPONSE] Role: {agent_role} | Latency: {latency}s | Length: {len(content)} chars", flush=True)
                        print("│ " + "\n│ ".join(resp_lines[:50]) + ("\n│ ... (truncated raw preview)" if len(resp_lines) > 50 else ""), flush=True)
                        print(f"{'━'*78}\n", flush=True)

                    parsed_res = self.parse_and_validate(content, response_model, agent_name=agent_role)
                    fields_list = list(parsed_res.model_dump().keys()) if hasattr(parsed_res, "model_dump") else []
                    
                    if self.sae_logger:
                        try:
                            self.sae_logger.log_llm_response(
                                agent_role=agent_role,
                                latency=latency,
                                content=content,
                                parsed_fields=fields_list,
                                status="SUCCESS",
                            )
                        except Exception:
                            pass

                    if self.debug:
                        print(f"  [{agent_role}] 📋 [DEBUG: PARSED MODEL] Fields: {fields_list}", flush=True)
                    return parsed_res

            except Exception as exc:
                last_error = exc
                latency = round(time.perf_counter() - t0, 2)
                print(f"  [{agent_role}] ⚠️ Attempt {attempt}/{self.max_retries} failed after {latency}s: {exc}", flush=True)
                if attempt < self.max_retries:
                    await asyncio.sleep(2.0 * attempt)

        print(f"  [{agent_role}] ❌ All {self.max_retries} attempts failed: {last_error}. Using fallback model.", flush=True)
        if self.sae_logger:
            try:
                self.sae_logger.log_llm_response(
                    agent_role=agent_role,
                    latency=0.0,
                    content=f"FAILED: {last_error}",
                    status="FAILED",
                )
            except Exception:
                pass
        return response_model()

    # ── Synchronous Generation ────────────────────────────────────────────────

    def generate_structured(
        self,
        prompt: str,
        model_name: Optional[str] = None,
        # pyrefly: ignore [bad-function-definition]
        response_model: Type[T] = None,
        temperature: float = 0.2,
        system_prompt: Optional[str] = None,
        agent_name: str = "general",
    ) -> T:
        """Synchronously call OpenRouter and return validated flat response model."""
        model = model_name or (get_model_for_capability(agent_name) if agent_name != "general" else "") or self.default_model
        api_key = self.get_api_key_for_role(agent_name)
        headers = self._get_headers(api_key)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"},
        }

        key_idx = ((DEFAULT_ROLE_KEY_INDEX.get(agent_name.lower().strip(), 0) % len(self.api_keys)) + 1) if self.api_keys else 0
        if self.sae_logger:
            try:
                self.sae_logger.log_llm_request(
                    agent_role=agent_name,
                    model=model,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    key_idx=key_idx,
                    temperature=temperature,
                )
            except Exception:
                pass

        if self.debug:
            print(f"\n{'━'*78}\n🔍 [DEBUG: LLM REQUEST] Role: {agent_name} | Model: {model} | Key: #{key_idx} | Temp: {temperature}", flush=True)
            if system_prompt:
                sys_lines = system_prompt.strip().splitlines()
                print(f"┌─ [SYSTEM PROMPT] ({len(system_prompt)} chars):\n│ " + "\n│ ".join(sys_lines[:25]) + ("\n│ ... (truncated)" if len(sys_lines) > 25 else ""), flush=True)
            usr_lines = prompt.strip().splitlines()
            print(f"┌─ [USER PROMPT] ({len(prompt)} chars):\n│ " + "\n│ ".join(usr_lines[:45]) + ("\n│ ... (truncated preview)" if len(usr_lines) > 45 else ""), flush=True)
            print(f"{'━'*78}", flush=True)

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            t0 = time.perf_counter()
            print(f"  [{agent_name}] ⏳ Sending request to OpenRouter ({model})...", flush=True)
            try:
                with httpx.Client(timeout=float(self.timeout)) as client:
                    resp = client.post(
                        f"{self.base_url}/chat/completions",
                        json=payload,
                        headers=headers,
                    )
                    latency = round(time.perf_counter() - t0, 2)

                    if resp.status_code == 429 or resp.status_code in (500, 502, 503, 504):
                        wait_time = 3.0 * attempt + 1.0
                        print(f"  [{agent_name}] ⚠️ HTTP {resp.status_code} (attempt {attempt}/{self.max_retries}). Backing off for {wait_time:.1f}s...", flush=True)
                        if attempt < self.max_retries:
                            time.sleep(wait_time)
                        continue

                    resp.raise_for_status()
                    data = resp.json()

                    if "error" in data:
                        err_msg = data["error"].get("message", str(data["error"]))
                        wait_time = 3.0 * attempt + 1.0
                        print(f"  [{agent_name}] ⚠️ Upstream API error: {err_msg}. Backing off for {wait_time:.1f}s...", flush=True)
                        if attempt < self.max_retries:
                            time.sleep(wait_time)
                            continue
                        raise ValueError(f"Upstream API error: {err_msg}")

                    choices = data.get("choices", [])
                    if not choices:
                        raise ValueError(f"Empty choices in response: {data}")

                    content = choices[0].get("message", {}).get("content", "")
                    print(f"  [{agent_name}] ✅ Completed in {latency}s ({len(content)} chars)", flush=True)

                    if self.debug:
                        resp_lines = content.strip().splitlines()
                        print(f"\n{'━'*78}\n📥 [DEBUG: LLM RAW RESPONSE] Role: {agent_name} | Latency: {latency}s | Length: {len(content)} chars", flush=True)
                        print("│ " + "\n│ ".join(resp_lines[:50]) + ("\n│ ... (truncated raw preview)" if len(resp_lines) > 50 else ""), flush=True)
                        print(f"{'━'*78}\n", flush=True)

                    parsed_res = self.parse_and_validate(content, response_model, agent_name=agent_name)
                    fields_list = list(parsed_res.model_dump().keys()) if hasattr(parsed_res, "model_dump") else []

                    if self.sae_logger:
                        try:
                            self.sae_logger.log_llm_response(
                                agent_role=agent_name,
                                latency=latency,
                                content=content,
                                parsed_fields=fields_list,
                                status="SUCCESS",
                            )
                        except Exception:
                            pass

                    if self.debug:
                        print(f"  [{agent_name}] 📋 [DEBUG: PARSED MODEL] Fields: {fields_list}", flush=True)
                    return parsed_res

            except Exception as exc:
                last_error = exc
                latency = round(time.perf_counter() - t0, 2)
                print(f"  [{agent_name}] ⚠️ Attempt {attempt}/{self.max_retries} failed after {latency}s: {exc}", flush=True)
                if attempt < self.max_retries:
                    time.sleep(2.0 * attempt)

        print(f"  [{agent_name}] ❌ All {self.max_retries} attempts failed: {last_error}. Using fallback model.", flush=True)
        if self.sae_logger:
            try:
                self.sae_logger.log_llm_response(
                    agent_role=agent_name,
                    latency=0.0,
                    content=f"FAILED: {last_error}",
                    status="FAILED",
                )
            except Exception:
                pass
        return response_model()
