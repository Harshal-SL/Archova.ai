"""
OpenRouter Client

The ONLY module in the codebase that makes HTTP calls to OpenRouter.
No other module is allowed to contact OpenRouter directly.

API reference: https://openrouter.ai/docs/requests

All requests use the OpenRouter Chat Completions endpoint:
  POST https://openrouter.ai/api/v1/chat/completions

Authentication: Bearer token from OPENROUTER_API_KEY env var.

Responsibilities:
  - Build and send requests to OpenRouter
  - Handle HTTP errors and rate limits (429 → retry with backoff)
  - Parse the response and return the raw text content
  - Never interpret or transform the content — that is the gateway's job
"""

from __future__ import annotations

import json
import logging
import os
import time
import threading
from typing import List, Optional


import requests
from app.config import settings
from app.ree.logger import ree_logger

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_COMPLETIONS_URL = f"{OPENROUTER_BASE_URL}/chat/completions"

# HTTP headers sent on every request
_APP_NAME = "AI-Architecture-Engine"
_APP_URL = "https://github.com/your-org/ai-architecture-engine"

# Retry configuration for rate limits
_RATE_LIMIT_BACKOFF_SECONDS = [2, 5, 10]   # wait times between retries on 429


class OpenRouterClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 120,
        max_retries: int = 2,
    ) -> None:
        """
        Initialise the client.
        """
        # Load all configured API keys for parallel distribution & rotation
        self._keys: List[str] = []
        for i in range(1, 10):
            k = os.getenv(f"OPENROUTER_API_KEY_{i}", "").strip()
            if k:
                self._keys.append(k)
        if not self._keys:
            single = (api_key or os.getenv("OPENROUTER_API_KEY", "") or getattr(settings, "openrouter_api_key", "")).strip()
            if single:
                self._keys.append(single)

        self._api_key = self._keys[0] if self._keys else ""
        self._timeout = timeout
        self._max_retries = max(max_retries, 3)
        self._key_lock = threading.Lock()
        self._key_counter = 0

        key_exists = bool(self._keys)
        masked_keys = [f"Key #{idx + 1}: {k[:12]}..." for idx, k in enumerate(self._keys)]
        logger.info("OpenRouterClient initialized | %d active API key(s): %s", len(self._keys), ", ".join(masked_keys) if masked_keys else "NONE")

        if not key_exists:
            logger.warning(
                "OpenRouterClient: OPENROUTER_API_KEY is not set. "
                "All requests will fail with 401 Unauthorized."
            )

    def _get_key(self, base_offset: int, attempt: int) -> str:
        """Retrieve key for a given base offset and retry attempt."""
        if not self._keys:
            return self._api_key
        idx = (base_offset + attempt) % len(self._keys)
        return self._keys[idx]

    # ── Public API ─────────────────────────────────────────────────────────────

    def get_available_models(self) -> List[str]:
        """Call GET https://openrouter.ai/api/v1/models and return available model IDs."""
        if not self._api_key:
            raise RuntimeError("Cannot fetch OpenRouter models: OPENROUTER_API_KEY is not configured.")

        url = f"{OPENROUTER_BASE_URL}/models"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "HTTP-Referer": _APP_URL,
            "X-Title": _APP_NAME,
        }
        try:
            res = requests.get(url, headers=headers, timeout=self._timeout)
            res.raise_for_status()
            data = res.json()
            model_list = [item["id"] for item in data.get("data", []) if isinstance(item, dict) and "id" in item]
            return model_list
        except Exception as exc:
            logger.error("OpenRouterClient: failed to fetch available models from %s — %s", url, exc)
            raise RuntimeError(f"Failed to fetch models from OpenRouter API: {exc}") from exc

    def validate_configured_models(self, configured_models: List[str]) -> None:
        """
        Validate that every model ID in configured_models exists on OpenRouter.
        Fails immediately with RuntimeError if any model is invalid.
        """
        if not self._api_key or not self._api_key.strip():
            logger.warning("OPENROUTER_API_KEY is not configured — skipping remote OpenRouter model validation.")
            return

        models_to_check = [m for m in configured_models if m and m.strip()]
        if not models_to_check:
            return

        logger.info("Validating configured models against OpenRouter API: %s", models_to_check)
        try:
            available = set(self.get_available_models())
        except Exception as exc:
            logger.warning("Could not fetch OpenRouter models for validation: %s — continuing execution", exc)
            return

        invalid_models = [m for m in models_to_check if m not in available]

        if invalid_models:
            err_msg = (
                f"\nCRITICAL: The following configured OpenRouter model(s) DO NOT exist or are unavailable:\n"
                f"  Invalid Model(s): {invalid_models}\n"
                f"Please update .env with valid model IDs returned by OpenRouter."
            )
            logger.critical(err_msg)
            raise RuntimeError(err_msg)

        logger.info("OpenRouter Model Validation Passed — All configured models are valid.")

    def complete(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 800,
        temperature: float = 0.2,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
    ) -> Optional[str]:
        """
        Send a prompt to OpenRouter and return the raw response text.
        If the primary model fails after all retries, automatically failover
        to FALLBACK_MODEL.
        """
        if not self._api_key:
            logger.error(
                "OpenRouterClient: cannot complete — OPENROUTER_API_KEY not configured."
            )
            return None

        # 1. Primary Model Attempt Loop
        content = self._send_completion_for_model(
            model=model,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
            json_mode=json_mode,
        )

        if content is not None:
            return content

        # 2. Determine Fallback Model
        fallback_model = (
            os.getenv("FALLBACK_MODEL", "").strip()
            or getattr(settings, "fallback_model", "")
            or "nvidia/nemotron-3-nano-30b-a3b:free"
        )

        if not fallback_model or fallback_model == model:
            logger.error(
                "OpenRouterClient: primary model %s failed after %d attempts and no distinct fallback model is configured.",
                model, self._max_retries + 1,
            )
            return None

        # 3. Log Failover Event
        attempts_count = self._max_retries + 1
        logger.warning(
            "OpenRouterClient: Primary model %s failed after %d attempts.",
            model, attempts_count,
        )
        logger.warning("Switching to fallback model %s...", fallback_model)
        ree_logger.debug(
            "\nOpenRouterClient: Primary model %s failed after %d attempts.\n"
            "Switching to fallback model %s...\n",
            model, attempts_count, fallback_model
        )

        # 4. Fallback Model Attempt Loop
        fallback_content = self._send_completion_for_model(
            model=fallback_model,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
            json_mode=json_mode,
        )

        if fallback_content is not None:
            logger.info("OpenRouterClient: Failover to fallback model %s succeeded.", fallback_model)
            return fallback_content

        logger.error(
            "OpenRouterClient: Both primary model %s and fallback model %s failed after retries.",
            model, fallback_model,
        )
        return None

    def _send_completion_for_model(
        self,
        model: str,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str],
        json_mode: bool,
    ) -> Optional[str]:
        """
        Execute request retry loop for a single target model.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": _APP_URL,
            "X-Title": _APP_NAME,
        }

        masked_headers = dict(headers)
        auth_val = masked_headers.get("Authorization", "")
        masked_headers["Authorization"] = f"{auth_val[:19]}..." if len(auth_val) > 19 else "Bearer ***"

        logger.info(
            "Sending OpenRouter Request:\n"
            "  URL     : %s\n"
            "  Model   : %s\n"
            "  Headers : %s\n"
            "  Payload : %s",
            OPENROUTER_COMPLETIONS_URL,
            model,
            masked_headers,
            json.dumps({"model": payload["model"], "json_mode": json_mode, "messages_count": len(messages), "max_tokens": max_tokens, "temperature": temperature}, indent=2),
        )

        last_error: Optional[Exception] = None

        with self._key_lock:
            key_offset = self._key_counter
            self._key_counter = (self._key_counter + 1) % max(1, len(self._keys))

        active_first_key = self._get_key(key_offset, 0)
        key_num = (self._keys.index(active_first_key) + 1) if active_first_key in self._keys else (key_offset + 1)
        logger.info("OpenRouterClient: Dispatching model %s using API Key #%d (%s...)", model, key_num, active_first_key[:12] if active_first_key else "NONE")

        for attempt in range(self._max_retries + 1):
            active_key = self._get_key(key_offset, attempt)
            current_headers = dict(headers)
            current_headers["Authorization"] = f"Bearer {active_key}"

            try:
                response = requests.post(
                    OPENROUTER_COMPLETIONS_URL,
                    json=payload,
                    headers=current_headers,
                    timeout=self._timeout,
                )

                if response.status_code == 400 and "response_format" in payload:
                    logger.warning("OpenRouterClient: model %s returned 400 with response_format — retrying without json_mode", model)
                    payload.pop("response_format", None)
                    response = requests.post(
                        OPENROUTER_COMPLETIONS_URL,
                        json=payload,
                        headers=current_headers,
                        timeout=self._timeout,
                    )

                if response.status_code == 429:
                    wait = _RATE_LIMIT_BACKOFF_SECONDS[
                        min(attempt, len(_RATE_LIMIT_BACKOFF_SECONDS) - 1)
                    ]
                    next_key = self._get_key(key_offset, attempt + 1)
                    key_num = (self._keys.index(next_key) + 1) if next_key in self._keys else 1
                    logger.warning(
                        "OpenRouterClient: 429 rate limit on attempt %d for model %s — switching to Key #%d and waiting %ds before retry",
                        attempt + 1, model, key_num, wait,
                    )
                    time.sleep(wait)
                    continue

                response.raise_for_status()
                data = response.json()

                content = self._extract_content(data)
                if content is not None:
                    ree_logger.debug(f"\n[Raw Assistant Response ({model})]:\n{content}\n" + "-" * 60)
                    return content

                ree_logger.debug(
                    "OpenRouterClient: empty or malformed response on attempt %d for model %s: %s",
                    attempt + 1, model, str(data)[:200],
                )

            except requests.Timeout as exc:
                last_error = exc
                ree_logger.debug(
                    "OpenRouterClient: timeout on attempt %d/%d for model %s",
                    attempt + 1, self._max_retries + 1, model,
                )
            except requests.RequestException as exc:
                last_error = exc
                res = exc.response
                status = res.status_code if res is not None else "N/A"
                body = res.text if res is not None else str(exc)

                ree_logger.debug(
                    "OpenRouter HTTP Error on attempt %d/%d:\n"
                    "  Status Code     : %s\n"
                    "  Requested Model : %s\n"
                    "  Response Body   : %s",
                    attempt + 1,
                    self._max_retries + 1,
                    status,
                    model,
                    body[:300],
                )

        ree_logger.debug(
            "OpenRouterClient: all %d attempts failed for model %s — %s",
            self._max_retries + 1, model, last_error,
        )
        return None

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_content(data: dict) -> Optional[str]:
        choices = data.get("choices")
        if not choices or not isinstance(choices, list):
            return None
        first = choices[0]
        if not isinstance(first, dict):
            return None
        message = first.get("message", {})
        content = message.get("content", "")
        if isinstance(content, str) and content.strip():
            return content.strip()
        return None

    def is_configured(self) -> bool:
        """Return True if an API key is present."""
        return bool(self._api_key)

