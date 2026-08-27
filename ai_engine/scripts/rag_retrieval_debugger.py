"""
RAG retrieval debugger.

Debugging tool that runs the full retrieval pipeline and prints
query text, ranked hits, and assembled context blocks.

Uses the Qdrant-backed backend/rag module exclusively.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path when run directly from scripts/
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
import argparse
import json
import sys
from pathlib import Path

from app.config import settings
from app.services.requirement_extractor.pipeline import run_extraction_pipeline
from backend.rag import (
    QdrantManager,
    RAGRetriever,
    QueryBuilder,
    ContextBuilder,
    RetrievalHit,
)


def _read_input(args: argparse.Namespace) -> str:
    """Read raw input from CLI args, file, or stdin."""
    if args.text:
        return args.text.strip()

    if args.file:
        return Path(args.file).read_text(encoding="utf-8").strip()

    if sys.stdin.isatty():
        print("Paste the input below. Finish with an empty line:")
        lines: list[str] = []
        while True:
            line = input()
            if not line.strip():
                break
            lines.append(line)
        return "\n".join(lines).strip()

    return sys.stdin.read().strip()


def _load_parameters(args: argparse.Namespace, raw_input: str) -> dict:
    """Parse parameters from raw input or use extractor."""
    if args.parameters_json:
        return json.loads(raw_input)

    if args.use_extractor:
        return run_extraction_pipeline(raw_input)

    return {
        "goal": {"value": raw_input, "ai_suggestion": None},
    }


def _format_hit(hit: RetrievalHit, index: int) -> dict:
    """Format a single retrieval hit for display."""
    metadata = dict(hit.metadata or {})
    return {
        "rank": index,
        "score": round(hit.score, 4),
        "title": metadata.get("title"),
        "category": metadata.get("category"),
        "relative_path": metadata.get("relative_path"),
        "domain": metadata.get("domain"),
        "difficulty": metadata.get("difficulty"),
        "text_preview": (hit.text or "")[:800],
        "metadata": metadata,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Debug RAG retrieval quality by printing query text, "
            "ranked hits, and assembled context."
        )
    )
    parser.add_argument("--text", help="Raw input text to inspect.")
    parser.add_argument("--file", help="Read raw input from a file.")
    parser.add_argument(
        "--use-extractor",
        action="store_true",
        help="Run the requirement extractor first and use its structured output.",
    )
    parser.add_argument(
        "--parameters-json",
        action="store_true",
        help="Treat the input as already-structured parameters JSON.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=8,
        help="Number of ranked retrieval hits to print.",
    )
    parser.add_argument(
        "--categories",
        help="Optional comma-separated category filter overriding automatic routing.",
    )
    parser.add_argument(
        "--skip-context",
        action="store_true",
        help="Do not print assembled context.",
    )
    args = parser.parse_args()

    raw_input = _read_input(args)
    if not raw_input:
        print("No input provided.", file=sys.stderr)
        return 1

    try:
        # Build parameters
        parameters = _load_parameters(args, raw_input)

        # Build architecture-aware query
        query_dict = QueryBuilder.build_query(parameters)
        query_text = query_dict["query_text"]

        # Determine target categories
        if args.categories:
            target_categories = [
                item.strip() for item in args.categories.split(",") if item.strip()
            ]
        else:
            target_categories = query_dict["target_categories"]

        # Initialize Qdrant retriever
        manager = QdrantManager(
            url=settings.qdrant_url,
            collection_name=settings.qdrant_collection_name,
        )
        retriever = RAGRetriever(qdrant_manager=manager)

        # Retrieve documents
        category_hits = retriever.retrieve_by_category(
            query=query_text,
            categories=target_categories,
            top_k=args.top_k,
            threshold=settings.rag_similarity_threshold,
        )

        # Flatten and rank by score
        all_hits: list[RetrievalHit] = []
        for hits in category_hits.values():
            all_hits.extend(hits)
        all_hits.sort(key=lambda h: h.score, reverse=True)
        ranked_hits = all_hits[: args.top_k]

        # Build context
        context_str = ""
        if not args.skip_context:
            builder = ContextBuilder(
                max_tokens=settings.rag_context_char_budget // 4,
            )
            context_str = builder.build_context(ranked_hits)

        # Output
        print("=== Input ===")
        print(raw_input)
        print()
        print("=== Structured Parameters ===")
        print(json.dumps(parameters, indent=2, ensure_ascii=False))
        print()
        print("=== Retrieval Query ===")
        print(json.dumps(query_dict, indent=2, ensure_ascii=False))
        print()
        print("=== Ranked Hits ===")
        print(
            json.dumps(
                [_format_hit(hit, idx + 1) for idx, hit in enumerate(ranked_hits)],
                indent=2,
                ensure_ascii=False,
            )
        )

        if not args.skip_context:
            print()
            print("=== Assembled Context ===")
            print(context_str or "(empty)")

        return 0

    except Exception as exc:
        print(f"RAG retrieval debug failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
