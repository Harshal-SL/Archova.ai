from .tokenizer import is_within_limit
from .chunker import chunk_text
from .extractor import extract_from_chunk, _empty_result
from .merger import merge_results


def run_extraction_pipeline(combined_prompt: str) -> dict:
    """
    Full pipeline:
      1. Estimate token count
      2. Send directly if small; chunk if large
      3. Extract requirements from each chunk via Mistral
      4. Merge all partial results into one structured output
    """
    try:
        if is_within_limit(combined_prompt):
            chunks = [combined_prompt]
        else:
            chunks = chunk_text(combined_prompt)

        partial_results = [extract_from_chunk(chunk) for chunk in chunks]
        return merge_results(partial_results)
    except Exception as exc:
        raise RuntimeError(f"Extraction pipeline failed: {exc}") from exc
