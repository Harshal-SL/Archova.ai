MAX_DIRECT_TOKENS = 6000
_CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Estimate token count using the ~4 chars/token heuristic."""
    return len(text) // _CHARS_PER_TOKEN


def is_within_limit(text: str, limit: int = MAX_DIRECT_TOKENS) -> bool:
    """Return True if the text fits within the token limit."""
    return estimate_tokens(text) <= limit
