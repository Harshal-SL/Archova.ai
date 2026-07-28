"""
LLM Gateway

The single entry point through which ALL AI agents communicate with OpenRouter.

No agent is allowed to import OpenRouterClient or call requests.post directly.
Every LLM call in the REE pipeline goes through this gateway.

Responsibilities:
  1. Accept a capability name (not a model name) from the caller
  2. Resolve the capability to a concrete model via ModelRegistry
  3. Enforce the ALLOW_PAID_MODELS policy
  4. Send the request through OpenRouterClient
  5. Parse JSON from the response text
  6. Retry with a repair prompt on JSON parse failure
  7. Return the parsed dict, or None on complete failure

Usage::

    from app.ree.llm import llm_gateway

    result = llm_gateway.complete(
        capability="reasoning",
        prompt="...",
        max_tokens=800,
    )
    # result is a parsed dict, or None

"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, Optional

from .model_registry import ModelRegistry, Capability, model_registry
from .openrouter_client import OpenRouterClient
from app.ree.logger import ree_logger

logger = logging.getLogger(__name__)


class LLMGateway:
    """
    Central LLM call dispatcher for the REE pipeline.
    """

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        client: Optional[OpenRouterClient] = None,
    ) -> None:
        """
        Initialise the gateway.
        """
        self._registry = registry or model_registry
        self._client = client or OpenRouterClient(
            timeout=_int_env("OPENROUTER_TIMEOUT_SECONDS", 120),
            max_retries=_int_env("LLM_GATEWAY_MAX_RETRIES", 2),
        )
        self._json_retries = _int_env("LLM_GATEWAY_JSON_RETRIES", 1)

    def reload(self) -> None:
        """Reload registry and client settings from current environment."""
        if hasattr(self._registry, "reload"):
            self._registry.reload()
        self._client = OpenRouterClient(
            timeout=_int_env("OPENROUTER_TIMEOUT_SECONDS", 120),
            max_retries=_int_env("LLM_GATEWAY_MAX_RETRIES", 2),
        )
        self._json_retries = _int_env("LLM_GATEWAY_JSON_RETRIES", 1)

    def validate_configured_models(self) -> None:
        """Validate all resolved capability models against OpenRouter available models."""
        resolved = list(self._registry.list_capabilities().values())
        self._client.validate_configured_models(resolved)

    # ── Public API ─────────────────────────────────────────────────────────────

    def complete(
        self,
        capability: str,
        prompt: str,
        max_tokens: int = 800,
        temperature: float = 0.2,
        system_prompt: Optional[str] = None,
        agent_name: str = "UnknownAgent",
    ) -> Optional[Dict[str, Any]]:
        """
        Request a JSON-structured completion with differentiated retry and fallback strategies.
        """
        try:
            entry = self._registry.resolve(capability)
        except Exception as exc:
            ree_logger.debug("LLMGateway: policy/resolution error — %s", exc)
            return None

        model_id = entry.model_id
        fallback_model = os.getenv("FALLBACK_MODEL", "meta-llama/llama-3.3-70b-instruct:free")

        ree_logger.debug(f"[LLM Call Dispatch] Agent: {agent_name:<26} | Capability: {capability:<20} | Model: {model_id}")

        if not self._client.is_configured():
            ree_logger.debug("LLMGateway: OpenRouter API key not configured.")
            return None

        # First attempt (with json_mode=True)
        raw = self._client.complete(
            model=model_id,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
            json_mode=True,
        )

        # ── Case C & D: HTTP Error or Empty Response ─────────────────────────
        if not raw or not raw.strip():
            ree_logger.debug(f"LLMGateway: empty/HTTP failure from model {model_id} for agent {agent_name} — retrying same model")
            raw = self._client.complete(
                model=model_id,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt,
                json_mode=True,
            )
            if not raw or not raw.strip():
                ree_logger.debug(f"LLMGateway: retry failed for {model_id} — failover to fallback model {fallback_model}")
                raw = self._client.complete(
                    model=fallback_model,
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system_prompt=system_prompt,
                    json_mode=True,
                )
                if raw and raw.strip():
                    parsed = _parse_json(raw, agent_name=agent_name, model_id=fallback_model)
                    if parsed is not None:
                        ree_logger.print_agent_status(agent_name, fallback_model, "Recovered using Fallback Model")
                        return parsed

        # ── Parse First Response ─────────────────────────────────────────────
        if raw and raw.strip():
            parsed = _parse_json(raw, agent_name=agent_name, model_id=model_id)
            if parsed is not None:
                ree_logger.print_agent_status(agent_name, model_id, "Success")
                return parsed

        # ── Differentiated Failure Handling (Issue 5) ────────────────────────
        is_truncated = raw is not None and (
            not raw.rstrip().endswith("}") and not raw.rstrip().endswith("]")
        )

        if is_truncated:
            # Case B: Truncated JSON -> Retry Same Model once with higher max_tokens -> Fallback Model
            ree_logger.debug(f"LLMGateway: Truncated JSON detected for agent {agent_name} from model {model_id} — retrying with increased tokens")
            raw_retry = self._client.complete(
                model=model_id,
                prompt=prompt,
                max_tokens=max(max_tokens * 2, 1500),
                temperature=temperature,
                system_prompt=system_prompt,
                json_mode=True,
            )
            if raw_retry and raw_retry.strip():
                parsed = _parse_json(raw_retry, agent_name=agent_name, model_id=model_id)
                if parsed is not None:
                    ree_logger.print_agent_status(agent_name, model_id, "Recovered after Retry")
                    return parsed

            # Fallback model for truncation
            ree_logger.debug(f"LLMGateway: Truncation retry failed on {model_id} — trying fallback model {fallback_model}")
            raw_fb = self._client.complete(
                model=fallback_model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt,
                json_mode=True,
            )
            if raw_fb and raw_fb.strip():
                parsed = _parse_json(raw_fb, agent_name=agent_name, model_id=fallback_model)
                if parsed is not None:
                    ree_logger.print_agent_status(agent_name, fallback_model, "Recovered using Fallback Model")
                    return parsed
        else:
            # Case A: Malformed JSON -> Repair Prompt
            ree_logger.debug(f"LLMGateway: Malformed JSON from model {model_id} for agent {agent_name} — sending repair prompt")
            repair_prompt = (
                "CRITICAL ERROR: Your previous response could not be parsed as valid JSON.\n"
                "You MUST return ONLY a valid, raw JSON object starting with '{' and ending with '}'.\n"
                "Do NOT include Markdown code blocks (NO ```json), NO preamble, NO commentary.\n\n"
                "Your previous invalid output:\n"
                + (raw[:1000] if raw else "")
                + "\n\nReturn raw valid JSON now:"
            )
            raw_repair = self._client.complete(
                model=model_id,
                prompt=repair_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                json_mode=True,
            )
            if raw_repair and raw_repair.strip():
                parsed = _parse_json(raw_repair, agent_name=agent_name, model_id=model_id)
                if parsed is not None:
                    ree_logger.print_agent_status(agent_name, model_id, "Recovered after JSON repair")
                    return parsed

            # If repair failed, try Fallback Model
            ree_logger.debug(f"LLMGateway: JSON repair failed on {model_id} — trying fallback model {fallback_model}")
            raw_fb = self._client.complete(
                model=fallback_model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt,
                json_mode=True,
            )
            if raw_fb and raw_fb.strip():
                parsed = _parse_json(raw_fb, agent_name=agent_name, model_id=fallback_model)
                if parsed is not None:
                    ree_logger.print_agent_status(agent_name, fallback_model, "Recovered using Fallback Model")
                    return parsed

        ree_logger.print_agent_status(agent_name, model_id, "Failed")
        ree_logger.debug(f"LLMGateway CRITICAL: All attempts and fallbacks failed to produce valid JSON for agent {agent_name}")
        return None

    def complete_text(
        self,
        capability: str,
        prompt: str,
        max_tokens: int = 800,
        temperature: float = 0.2,
        system_prompt: Optional[str] = None,
        agent_name: str = "UnknownAgent",
    ) -> Optional[str]:
        """
        Request a raw text completion (not JSON) for a given capability.
        """
        try:
            entry = self._registry.resolve(capability)
        except Exception as exc:
            ree_logger.debug("LLMGateway: policy/resolution error — %s", exc)
            return None

        model_id = entry.model_id
        ree_logger.debug(f"[LLM Call Dispatch] Agent: {agent_name:<26} | Capability: {capability:<20} | Model: {model_id}")

        if not self._client.is_configured():
            ree_logger.debug("LLMGateway: OpenRouter API key not configured.")
            return None

        res = self._client.complete(
            model=model_id,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
            json_mode=False,
        )
        if res:
            ree_logger.print_agent_status(agent_name, model_id, "Success")
        else:
            ree_logger.print_agent_status(agent_name, model_id, "Failed")
        return res

    def is_ready(self) -> bool:
        """Return True if the gateway is configured and ready to use."""
        return self._client.is_configured()

    def resolved_models(self) -> Dict[str, str]:
        """Return capability → model_id mapping for the current configuration."""
        return self._registry.list_capabilities()


# ── Robust Multi-Strategy JSON Parsing ───────────────────────────────────────


def _clean_json_str(s: str) -> str:
    """Sanitise common invalid JSON patterns emitted by LLMs."""
    # Strip single line comments // ...
    s = re.sub(r"//.*", "", s)
    # Strip trailing commas before closing braces or brackets
    s = re.sub(r",\s*([\}\]])", r"\1", s)
    # Replace smart/curly quotes
    s = s.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    return s.strip()


def _parse_json(raw: str, agent_name: str = "UnknownAgent", model_id: str = "UnknownModel") -> Optional[Any]:
    """
    Multi-pass robust JSON parser for LLM completions.

    Strategies:
      1. Direct json.loads (trimmed)
      2. Direct json.loads on sanitized string
      3. Markdown code fence extraction (```json ... ``` or ``` ... ```)
      4. Balanced brace/bracket extraction ({...} or [...])
      5. Final fallback cleanup

    Logs:
      - Raw response before parsing
      - Cleaned JSON candidate string
      - Parsed Python object summary
      - Parse exceptions with detailed diagnostics if all strategies fail.
    """
def _is_corrupted_response(raw: str) -> bool:
    """
    Check if raw response string contains corruption, unreadable tokens, repeated nonsense,
    or upstream HTML error pages (502 Bad Gateway, 503 Service Unavailable, etc.).
    """
    if not raw or not isinstance(raw, str):
        return True

    lower = raw.lower()
    # Check for unk tokens or upstream HTML gateway errors
    if "<unk>" in lower or "502 bad gateway" in lower or "503 service unavailable" in lower or "504 gateway timeout" in lower:
        return True
    if "<!doctype html>" in lower or "<html" in lower:
        return True

    # Check printable text ratio
    printable = sum(1 for c in raw if c.isprintable() or c in "\n\r\t")
    ratio = printable / max(1, len(raw))
    if ratio < 0.85:
        return True

    # Check for repeated nonsense string
    if len(raw) > 50 and len(set(raw)) < 6:
        return True

    return False


def _is_invalid_or_trivial_object(parsed: Any) -> bool:
    """
    Reject parsed outputs if required keys are missing, or response contains only
    trivial placeholders like {"status":"ready"}, {"ok":true}, or {}.
    """
    if parsed is None or parsed == {} or parsed == []:
        return True

    if isinstance(parsed, dict):
        keys = [str(k).lower().strip() for k in parsed.keys()]
        if not keys:
            return True
        if set(keys) in ({"status"}, {"ok"}, {"status", "message"}, {"result", "status"}):
            val_str = str(parsed).lower()
            if "ready" in val_str or "true" in val_str or "ok" in val_str:
                return True

    return False


def _parse_json(raw: str, agent_name: str = "UnknownAgent", model_id: str = "UnknownModel") -> Optional[Any]:
    """
    Multi-pass robust JSON parser for LLM completions.

    Rejects corrupted responses (502 HTML, unk tokens, repeated nonsense) immediately
    without attempting JSON repair, triggering fallback model failover.
    """
    if not raw or not raw.strip():
        logger.error("LLMGateway [_parse_json]: Received empty response string for agent %s", agent_name)
        return None

    if _is_corrupted_response(raw):
        logger.critical("LLMGateway [_parse_json]: Corrupted response or 502 HTML error detected for agent %s. Rejecting response without JSON repair.", agent_name)
        return None

    raw_clean = raw.strip()

    # Pass 1: Direct loads
    try:
        parsed = json.loads(raw_clean)
        if not _is_invalid_or_trivial_object(parsed):
            logger.info("LLMGateway [_parse_json]: Direct JSON parse succeeded for agent %s (keys=%s)", agent_name, list(parsed.keys()) if isinstance(parsed, dict) else len(parsed))
            ree_logger.debug(f"[JSON Parser Success] Agent: {agent_name} | Parsed Keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'Array'}")
            return parsed
        else:
            logger.warning("LLMGateway [_parse_json]: Direct JSON parse produced trivial/invalid object for agent %s: %r", agent_name, parsed)
    except Exception:
        pass

    try:
        sanitized = _clean_json_str(raw_clean)
        parsed = json.loads(sanitized)
        logger.info("LLMGateway [_parse_json]: Sanitized JSON parse succeeded for agent %s", agent_name)
        ree_logger.debug(f"[JSON Parser Success (Sanitized)] Agent: {agent_name}")
        return parsed
    except Exception:
        pass

    # Pass 2: Markdown fence extraction
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    fences = re.findall(fence_pattern, raw, re.IGNORECASE)
    for fence in fences:
        cand = fence.strip()
        try:
            parsed = json.loads(cand)
            logger.info("LLMGateway [_parse_json]: Markdown fence JSON parse succeeded for agent %s", agent_name)
            ree_logger.debug(f"[JSON Parser Success (Markdown Fence)] Agent: {agent_name}")
            return parsed
        except Exception:
            try:
                parsed = json.loads(_clean_json_str(cand))
                logger.info("LLMGateway [_parse_json]: Sanitized Markdown fence JSON parse succeeded for agent %s", agent_name)
                ree_logger.debug(f"[JSON Parser Success (Sanitized Fence)] Agent: {agent_name}")
                return parsed
            except Exception:
                pass

    # Pass 3: Balanced brace/bracket search
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        for start_idx in [i for i, c in enumerate(raw) if c == start_char]:
            depth = 0
            in_str = False
            esc = False
            for i in range(start_idx, len(raw)):
                c = raw[i]
                if c == '"' and not esc:
                    in_str = not in_str
                elif c == '\\' and in_str:
                    esc = not esc
                    continue
                elif not in_str:
                    if c == start_char:
                        depth += 1
                    elif c == end_char:
                        depth -= 1
                        if depth == 0:
                            sub = raw[start_idx : i + 1]
                            try:
                                parsed = json.loads(sub)
                                logger.info("LLMGateway [_parse_json]: Balanced bracket JSON parse succeeded for agent %s", agent_name)
                                ree_logger.debug(f"[JSON Parser Success (Balanced Substring)] Agent: {agent_name}")
                                return parsed
                            except Exception:
                                try:
                                    parsed = json.loads(_clean_json_str(sub))
                                    logger.info("LLMGateway [_parse_json]: Sanitized balanced bracket JSON parse succeeded for agent %s", agent_name)
                                    ree_logger.debug(f"[JSON Parser Success (Sanitized Substring)] Agent: {agent_name}")
                                    return parsed
                                except Exception:
                                    pass
                            break
                esc = False

    # Pass 4: Partial / Truncated JSON Repair Recovery
    repaired = _repair_truncated_json(raw)
    if repaired is not None:
        logger.info("LLMGateway [_parse_json]: Truncation repair JSON parse succeeded for agent %s", agent_name)
        ree_logger.debug(f"[JSON Parser Success (Truncation Repair)] Agent: {agent_name}")
        return repaired

    # All parsing attempts failed — log comprehensive diagnostic error
    logger.error(
        "LLMGateway [_parse_json FAIL] All JSON extraction strategies failed for agent %s (model=%s):\n"
        "  Raw Assistant Response:\n%s\n"
        "  Cleaned Candidate String:\n%s",
        agent_name, model_id, raw, _clean_json_str(raw_clean)[:500]
    )
    ree_logger.debug(f"\n[JSON Parser Failure] Agent: {agent_name} | Model: {model_id}\nRaw Output Preview: {raw[:300]}...\n")
    return None


def _repair_truncated_json(text: str) -> Optional[Any]:
    """Attempt to repair JSON strings truncated mid-output by max_tokens limits."""
    start_idx = text.find('{')
    if start_idx == -1:
        start_idx = text.find('[')
    if start_idx == -1:
        return None

    sub = text[start_idx:].rstrip()
    in_str = False
    esc = False
    open_braces = 0
    open_brackets = 0

    for c in sub:
        if c == '"' and not esc:
            in_str = not in_str
        elif c == '\\' and in_str:
            esc = not esc
            continue
        elif not in_str:
            if c == '{':
                open_braces += 1
            elif c == '}':
                open_braces = max(0, open_braces - 1)
            elif c == '[':
                open_brackets += 1
            elif c == ']':
                open_brackets = max(0, open_brackets - 1)
        esc = False

    repair_cand = sub
    if in_str:
        repair_cand += '"'

    repair_cand = re.sub(r',\s*"[^"]*$', '', repair_cand)
    repair_cand = re.sub(r',\s*$', '', repair_cand)
    repair_cand += ']' * open_brackets
    repair_cand += '}' * open_braces

    try:
        return json.loads(_clean_json_str(repair_cand))
    except Exception:
        return None


# ── Helpers ───────────────────────────────────────────────────────────────────


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


# ── Module-level singleton ────────────────────────────────────────────────────


llm_gateway = LLMGateway()


def reload_gateway() -> LLMGateway:
    """Reload global llm_gateway instance from environment variables."""
    global llm_gateway
    llm_gateway.reload()
    return llm_gateway

