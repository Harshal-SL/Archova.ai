"""
LLM Gateway Package

The ONLY component allowed to communicate with OpenRouter.

Public API:
  from app.ree.llm import llm_gateway, LLMGateway, ModelRegistry

  # Complete a prompt using a capability name (not a model name)
  result = llm_gateway.complete(
      capability="reasoning",
      prompt="...",
      max_tokens=800,
  )

Internal structure:
  openrouter_client.py  — raw HTTP client for the OpenRouter API
  model_registry.py     — maps capability → model, enforces paid-model policy
  gateway.py            — LLMGateway: public interface used by all agents
"""

from .gateway import LLMGateway, llm_gateway
from .model_registry import ModelRegistry, Capability, model_registry
from .openrouter_client import OpenRouterClient

__all__ = [
    "LLMGateway",
    "llm_gateway",
    "ModelRegistry",
    "model_registry",
    "Capability",
    "OpenRouterClient",
]
