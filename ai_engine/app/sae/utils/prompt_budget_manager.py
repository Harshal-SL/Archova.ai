"""PromptBudgetManager module for tracking token budgets and preventing oversized LLM prompts."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.sae.utils.enums import AgentRole


class TokenUsageMetric(BaseModel):
    """Token usage and latency log item."""

    agent_role: str
    system_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    within_budget: bool = True
    rejection_reason: Optional[str] = None


class PromptBudgetManager:
    """Manages token budgets per agent role, computes token estimates, and logs prompt usage."""

    # Default Token Budgets
    DEFAULT_SYSTEM_TOKEN_BUDGET = 800
    DEFAULT_INPUT_TOKEN_BUDGET = 2500
    DEFAULT_OUTPUT_TOKEN_BUDGET = 2000

    def __init__(
        self,
        system_budget: int = DEFAULT_SYSTEM_TOKEN_BUDGET,
        input_budget: int = DEFAULT_INPUT_TOKEN_BUDGET,
        output_budget: int = DEFAULT_OUTPUT_TOKEN_BUDGET,
    ):
        self.system_budget = system_budget
        self.input_budget = input_budget
        self.output_budget = output_budget
        self.metrics_history: List[TokenUsageMetric] = []

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """Estimate token count from string length using standard ~4 chars per token approximation."""
        if not text:
            return 0
        return math.ceil(len(text) / 4.0)

    def validate_and_record(
        self,
        agent_role: AgentRole | str,
        system_prompt: str,
        user_prompt: str,
        response_text: str = "",
        latency_ms: float = 0.0,
    ) -> TokenUsageMetric:
        """Validate prompt against token budgets and record metrics."""
        sys_tokens = self.estimate_tokens(system_prompt)
        input_tokens = self.estimate_tokens(user_prompt)
        output_tokens = self.estimate_tokens(response_text)
        tot_tokens = sys_tokens + input_tokens + output_tokens

        role_str = str(agent_role)
        rejection_reason = None
        within_budget = True

        if sys_tokens > self.system_budget:
            within_budget = False
            rejection_reason = f"System prompt token estimate ({sys_tokens}) exceeds budget ({self.system_budget})."
        elif input_tokens > self.input_budget:
            within_budget = False
            rejection_reason = f"User context input token estimate ({input_tokens}) exceeds budget ({self.input_budget})."

        metric = TokenUsageMetric(
            agent_role=role_str,
            system_tokens=sys_tokens,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=tot_tokens,
            latency_ms=round(latency_ms, 2),
            within_budget=within_budget,
            rejection_reason=rejection_reason,
        )

        self.metrics_history.append(metric)
        return metric

    def get_summary_report(self) -> Dict[str, Any]:
        """Return aggregated prompt budget statistics."""
        if not self.metrics_history:
            return {
                "total_prompts": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "average_latency_ms": 0.0,
                "budget_violations": 0,
            }

        tot_in = sum(m.input_tokens + m.system_tokens for m in self.metrics_history)
        tot_out = sum(m.output_tokens for m in self.metrics_history)
        tot_all = sum(m.total_tokens for m in self.metrics_history)
        avg_lat = sum(m.latency_ms for m in self.metrics_history) / len(self.metrics_history)
        violations = sum(1 for m in self.metrics_history if not m.within_budget)

        return {
            "total_prompts": len(self.metrics_history),
            "total_input_tokens": tot_in,
            "total_output_tokens": tot_out,
            "total_tokens": tot_all,
            "average_latency_ms": round(avg_lat, 2),
            "budget_violations": violations,
            "metrics": [m.model_dump() for m in self.metrics_history],
        }
