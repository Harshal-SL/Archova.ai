_CHARS_PER_TOKEN = 4


def chunk_text(
    text: str,
    chunk_size: int = 2000,
    overlap: int = 200,
) -> list[str]:
    """
    Split text into overlapping chunks.

    chunk_size and overlap are in tokens.
    Overlap prevents losing context at chunk boundaries.

    Example for chunk_size=2000, overlap=200:
      chunk1 → tokens 0–2000
      chunk2 → tokens 1800–3800
      chunk3 → tokens 3600–5600
    """
    chunk_chars = chunk_size * _CHARS_PER_TOKEN
    step_chars = (chunk_size - overlap) * _CHARS_PER_TOKEN

    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + chunk_chars])
        start += step_chars

    return chunks
