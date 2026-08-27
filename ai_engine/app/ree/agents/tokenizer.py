"""Tokenizer and token limit estimation utilities for REE input understanding."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

MAX_DIRECT_TOKENS: int = 120000


def estimate_tokens(text: str) -> int:
    """Estimate token count of string using tiktoken or whitespace fallback."""
    if not text:
        return 0

    try:
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        # Fallback estimation: ~4 chars per token
        return max(1, len(text) // 4)


def is_within_limit(text: str, max_tokens: int = MAX_DIRECT_TOKENS) -> bool:
    """Check if token count of string is within maximum threshold."""
    return estimate_tokens(text) <= max_tokens
