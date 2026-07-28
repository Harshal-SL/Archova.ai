"""
Base AI Agent

Shared infrastructure for all AI Engineering Team agents.

Key change from Task 3:
  - All LLM calls are now routed through the LLMGateway.
  - Agents declare CAPABILITY (not a model name) on their class.
  - No agent ever imports requests, knows an API key, or knows a model name.
  - JSON parsing is handled inside the gateway; base_agent only receives
    a parsed dict or None.

Usage in a subclass::

    class RequirementEngineerAgent(BaseAIAgent):
        AGENT_NAME = "RequirementEngineer"
        CAPABILITY  = Capability.REASONING

        def run(self, src):
            result = self._call_llm(prompt, max_tokens=900)
            ...
"""

from __future__ import annotations

import logging
import re
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.ree.llm import llm_gateway, LLMGateway
from app.ree.llm.model_registry import Capability
from app.ree.models import SharedRequirementContext

logger = logging.getLogger(__name__)


class BaseAIAgent(ABC):
    """
    Abstract base for all AI Engineering Team agents.

    Provides:
      - CAPABILITY class attribute (override in every subclass)
      - _call_llm()  → routes through LLMGateway, returns parsed dict or None
      - _add_note()  → writes a timestamped discussion note into the SRC
      - _parse_json() → static helper (kept for backward-compat with test mocks)

    Agents must NEVER:
      - Import requests
      - Import OpenRouterClient
      - Know a model name or API key
    """

    #: Override in each subclass with a Capability constant
    AGENT_NAME: str = "BaseAgent"
    STAGE: str = "engineering"
    CAPABILITY: str = Capability.GENERAL

    def __init__(self, gateway: Optional[LLMGateway] = None) -> None:
        """
        Args:
            gateway: Optional LLMGateway override (used in tests).
                     Defaults to the module-level singleton.
        """
        self._gateway = gateway or llm_gateway

    @abstractmethod
    def run(self, src: SharedRequirementContext) -> SharedRequirementContext:
        """Execute this agent's reasoning pass against the SRC."""

    # ── LLM call ──────────────────────────────────────────────────────────────

    def _call_llm(
        self,
        prompt: str,
        max_tokens: int = 800,
        temperature: float = 0.2,
        system_prompt: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Request a JSON-structured completion from the LLM Gateway.

        The gateway resolves the agent's CAPABILITY to a concrete model,
        enforces the paid-model policy, and handles all HTTP details.

        Args:
            prompt: The user message to send.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
            system_prompt: Optional system instruction.

        Returns:
            Parsed JSON dict, or None on failure.
        """
        logger.debug(
            "%s: requesting completion via gateway (capability=%r, max_tokens=%d)",
            self.AGENT_NAME, self.CAPABILITY, max_tokens,
        )
        result = self._gateway.complete(
            capability=self.CAPABILITY,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
            agent_name=self.AGENT_NAME,
        )
        if result is None:
            logger.warning(
                "%s: gateway returned None for capability=%r",
                self.AGENT_NAME, self.CAPABILITY,
            )
        return result

    # ── JSON extraction (kept for test backward-compat) ───────────────────────

    @staticmethod
    def _parse_json(raw: str) -> Optional[Dict[str, Any]]:
        """
        Extract the first valid JSON object from a raw string.

        Kept as a static method so existing tests that call
        BaseAIAgent._parse_json() directly continue to work.
        The gateway has its own copy of this logic internally.
        """
        if not raw:
            return None
        cleaned = re.sub(r"```(?:json)?", "", raw).strip("` \n")
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if not match:
            return None
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None

    # ── Discussion note helper ────────────────────────────────────────────────

    def _add_note(self, src: SharedRequirementContext, note: str) -> None:
        """Append a timestamped discussion note attributed to this agent."""
        src.add_note(self.STAGE, self.AGENT_NAME, note)
