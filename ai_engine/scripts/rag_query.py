"""
Interactive Qdrant RAG query tool.

Features:
  - Query expansion + intent detection
  - MMR-based diversity
  - Per-document chunk cap
  - Optional cross-encoder reranking
  - Retrieval report (--report flag)

Usage:
    venv\\Scripts\\python.exe rag_query.py
    venv\\Scripts\\python.exe rag_query.py -q "food delivery 20M users"
    venv\\Scripts\\python.exe rag_query.py -q "kafka vs rabbitmq" --report
    venv\\Scripts\\python.exe rag_query.py -q "redis" -k 5 --no-text
    venv\\Scripts\\python.exe rag_query.py --reindex
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

# Ensure project root is on sys.path when run directly from scripts/
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.rag.config import (
    COLLECTION_NAME,
    ENABLE_QUERY_EXPANSION,
    FETCH_K,
    MAX_CHUNKS_PER_DOCUMENT,
    MMR_LAMBDA,
    QDRANT_LOCAL_PATH,
    QDRANT_URL,
    SIMILARITY_THRESHOLD,
    TOP_K,
)
from app.rag.qdrant_manager import QdrantManager
from app.rag.query_builder import QueryBuilder
from app.rag.retriever import RAGRetriever, RetrievalHit

# ── ANSI colour helpers ────────────────────────────────────────────────────────

_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_CYAN   = "\033[36m"
_GREEN  = "\033[32m"
_YELLOW = "\033[33m"
_RED    = "\033[31m"
_DIM    = "\033[2m"
_MAGENTA = "\033[35m"


def _c(text: str, *codes: str) -> str:
    return "".join(codes) + text + _RESET


def _score_color(score: float) -> str:
    if score >= 0.7:
        return _GREEN
    if score >= 0.5:
        return _YELLOW
    return _RED


# ── Startup banner ────────────────────────────────────────────────────────────

def _startup_banner(manager: QdrantManager, vector_count: int) -> None:
    mode = "local disk" if manager.is_local else "remote server"
    loc  = manager.local_path if manager.is_local else manager.url

    print(_c("\n  ╔══════════════════════════════════════════════════════════╗", _CYAN))
    print(_c("  ║         QDRANT RAG  Query Tool  (production)             ║", _CYAN, _BOLD))
    print(_c("  ╚══════════════════════════════════════════════════════════╝", _CYAN))
    print(f"  Mode         : {_c(mode, _BOLD)}")
    print(f"  Storage      : {loc}")
    print(f"  Collection   : {COLLECTION_NAME}")
    print(f"  Vectors      : {_c(str(vector_count), _BOLD, _GREEN)}")
    print(f"  Top-K        : {TOP_K}  │  Fetch-K: {FETCH_K}  │  MMR λ: {MMR_LAMBDA}")
    print(f"  Max/doc      : {MAX_CHUNKS_PER_DOCUMENT}  │  Expansion: {ENABLE_QUERY_EXPANSION}")
    print(_c("  ─" * 32, _DIM))
    print(f"  Type a query and press Enter.  "
          f"{_c('Ctrl+C', _BOLD)} or {_c('quit', _BOLD)} to exit.")
    print(f"  Inline tips  : {_c('/top 5 your query', _DIM)} · "
          f"{_c('/report your query', _DIM)}")
    print()


# ── Result display ────────────────────────────────────────────────────────────

def _print_header(query: str, count: int, top_k: int, threshold: float) -> None:
    print()
    print(_c("  ═" * 33, _CYAN))
    print(f"  {_c('Query', _BOLD)}      : {query}")
    print(f"  Top-K      : {top_k}  │  Threshold : {threshold}  │  Hits : {_c(str(count), _BOLD)}")
    print(_c("  ═" * 33, _CYAN))


def _print_hit(rank: int, hit: RetrievalHit, show_text: bool) -> None:
    meta      = hit.metadata
    score     = hit.final_score
    color     = _score_color(score)
    title     = meta.get("title", "—")
    category  = meta.get("category", "—")
    rel_path  = meta.get("relative_path", "—")
    domain    = meta.get("domain", "—")
    diff      = meta.get("difficulty", "—")
    keywords  = meta.get("keywords", [])
    kw_str    = ", ".join(keywords[:6]) if isinstance(keywords, list) else str(keywords)
    src_file  = meta.get("source_file", "—")
    chunk_no  = meta.get("chunk_number", "?")

    rer_str = ""
    if hit.reranker_score is not None:
        rer_str = f"  reranker: {_c(f'{hit.reranker_score:.4f}', _MAGENTA)}"

    print(
        f"\n  {_c(f'#{rank}', _BOLD, _CYAN)}  "
        f"{_c(title, _BOLD)}  "
        f"[score: {_c(f'{score:.4f}', color, _BOLD)}]{rer_str}"
    )
    print(f"  {_c('Category ', _DIM)}: {category}")
    print(f"  {_c('File     ', _DIM)}: {src_file}  chunk #{chunk_no}")
    print(f"  {_c('Path     ', _DIM)}: {rel_path}")
    print(f"  {_c('Domain   ', _DIM)}: {domain}   {_c('Difficulty', _DIM)}: {diff}")
    if kw_str:
        print(f"  {_c('Keywords ', _DIM)}: {kw_str}")

    if show_text and hit.text:
        wrapped = textwrap.fill(
            hit.text.strip(), width=66,
            initial_indent="    ", subsequent_indent="    ",
        )
        print()
        print(_c("  ── chunk text " + "─" * 48, _DIM))
        print(wrapped)
        print(_c("  " + "─" * 62, _DIM))


def _print_no_results(threshold: float) -> None:
    print()
    print(_c("  No results above the similarity threshold.", _YELLOW))
    print(f"  Try:  --threshold {max(0.1, threshold - 0.1):.1f}  for a looser search.")
    print()


def _print_diversity_summary(hits: list[RetrievalHit]) -> None:
    """Show which documents contributed to the final result set."""
    doc_counts: dict[str, int] = {}
    for h in hits:
        src = h.metadata.get("source_file", "?")
        doc_counts[src] = doc_counts.get(src, 0) + 1
    print(_c(f"  Unique documents: {len(doc_counts)}", _DIM))
    for src, cnt in sorted(doc_counts.items(), key=lambda x: -x[1]):
        bar = "█" * cnt
        print(_c(f"    {bar:10s} {cnt}  {src}", _DIM))


# ── Ingestion ─────────────────────────────────────────────────────────────────

def _run_ingestion(manager: QdrantManager) -> bool:
    print()
    print(_c("  Building the vector index from data/RAG …", _YELLOW, _BOLD))
    print(_c("  This runs once and typically takes 2–5 minutes.", _DIM))
    print()
    try:
        from backend.rag.ingestion import IngestionPipeline
        pipeline = IngestionPipeline(qdrant_manager=manager)
        stats = pipeline.ingest_all(force_recreate=True)
        print()
        print(_c("  ✓ Ingestion complete!", _GREEN, _BOLD))
        print(f"    Files   : {stats['files_loaded']}")
        print(f"    Chunks  : {stats['chunks_created']}")
        print(f"    Vectors : {stats['vectors_uploaded']}")
        print(f"    Time    : {stats['total_time']:.1f}s")
        print()
        return True
    except Exception as exc:
        print()
        print(_c(f"  ✗ Ingestion failed: {exc}", _RED, _BOLD))
        print()
        return False


def _ensure_collection(manager: QdrantManager) -> bool:
    if manager.collection_exists() and manager.count_vectors() > 0:
        return True

    print()
    if not manager.collection_exists():
        print(_c("  Collection 'architecture_rag' does not exist yet.", _YELLOW, _BOLD))
    else:
        print(_c("  Collection exists but is empty.", _YELLOW, _BOLD))

    print("  The corpus needs to be indexed before you can search.")
    print()
    try:
        answer = input(_c("  Build index now? [Y/n] > ", _CYAN, _BOLD)).strip().lower()
    except (KeyboardInterrupt, EOFError):
        print()
        return False

    if answer in ("", "y", "yes"):
        return _run_ingestion(manager)

    print(_c("\n  Skipping ingestion.\n", _DIM))
    return False


# ── Core search ───────────────────────────────────────────────────────────────

def search(
    query: str,
    manager: QdrantManager,
    retriever: RAGRetriever,
    top_k: int,
    threshold: float,
    category: str | None,
    show_text: bool,
    print_report: bool,
) -> None:
    """Run the full retrieval pipeline and pretty-print results."""
    print(_c("  Searching …", _DIM), end="", flush=True)

    try:
        plan = QueryBuilder.plan(query)
        if category:
            plan.target_categories = [category]
            plan.expanded_queries = []

        hits, report = retriever.retrieve_from_plan(
            plan,
            top_k=top_k,
            threshold=threshold,
            print_report=print_report,
        )
    except RuntimeError as exc:
        print("\r" + " " * 20 + "\r", end="")
        print(_c(f"\n  ERROR: {exc}\n", _RED, _BOLD))
        return

    print("\r" + " " * 20 + "\r", end="")
    _print_header(query, len(hits), top_k, threshold)

    if not hits:
        _print_no_results(threshold)
        return

    for rank, hit in enumerate(hits, start=1):
        _print_hit(rank, hit, show_text)

    print()
    _print_diversity_summary(hits)
    print(_c(
        f"\n  {len(hits)} result(s)  │  "
        f"{len(set(h.metadata.get('source_file','?') for h in hits))} documents  │  "
        f"intents: {', '.join(report.detected_intents[:3])}",
        _DIM,
    ))
    print()


# ── Interactive REPL ──────────────────────────────────────────────────────────

def interactive_loop(
    manager: QdrantManager,
    retriever: RAGRetriever,
    top_k: int,
    threshold: float,
    category: str | None,
    show_text: bool,
) -> None:
    vector_count = manager.count_vectors() if manager.collection_exists() else 0
    _startup_banner(manager, vector_count)

    print_report = False

    while True:
        try:
            raw = input(_c("  Query > ", _CYAN, _BOLD)).strip()
        except (KeyboardInterrupt, EOFError):
            print(_c("\n  Bye!\n", _DIM))
            break

        if not raw:
            continue

        if raw.lower() in {"quit", "exit", "q"}:
            print(_c("\n  Bye!\n", _DIM))
            break

        # /top N <query>
        if raw.startswith("/top "):
            parts = raw.split(maxsplit=2)
            try:
                top_k = int(parts[1])
                raw = parts[2] if len(parts) > 2 else ""
                print(_c(f"  Top-K set to {top_k}.", _DIM))
            except (IndexError, ValueError):
                print(_c("  Usage: /top <N> <query>", _YELLOW))
                continue

        # /report <query>  — show detailed retrieval report
        if raw.startswith("/report "):
            raw = raw[len("/report "):]
            print_report = True
        else:
            print_report = False

        if raw:
            search(raw, manager, retriever, top_k, threshold, category,
                   show_text, print_report)


# ── CLI ───────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Query the Qdrant RAG vector database with production retrieval.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              venv\\Scripts\\python.exe rag_query.py
              venv\\Scripts\\python.exe rag_query.py -q "food delivery 20M users"
              venv\\Scripts\\python.exe rag_query.py -q "microservices" --report
              venv\\Scripts\\python.exe rag_query.py -q "redis" -k 5 --no-text
              venv\\Scripts\\python.exe rag_query.py -q "kafka" --category category_6_messaging_systems
              venv\\Scripts\\python.exe rag_query.py --reindex
        """),
    )
    parser.add_argument("--query", "-q", help="Query string (omit for interactive mode).")
    parser.add_argument("--top-k", "-k", type=int, default=TOP_K, metavar="N",
                        help=f"Final results to return (default: {TOP_K}).")
    parser.add_argument("--threshold", "-t", type=float, default=SIMILARITY_THRESHOLD,
                        metavar="FLOAT",
                        help=f"Min cosine similarity (default: {SIMILARITY_THRESHOLD}).")
    parser.add_argument("--category", "-c", default=None, metavar="NAME",
                        help="Restrict to one category (e.g. category_6_messaging_systems).")
    parser.add_argument("--no-text", action="store_true",
                        help="Show metadata only, hide chunk text.")
    parser.add_argument("--report", action="store_true",
                        help="Print full retrieval report (intents, categories, stats).")
    parser.add_argument("--reindex", action="store_true",
                        help="Force-rebuild the vector index, then exit.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    show_text = not args.no_text

    print(_c("\n  Connecting to Qdrant …", _DIM), end="", flush=True)
    try:
        manager = QdrantManager()
    except RuntimeError as exc:
        print()
        print(_c(f"\n  ERROR: Cannot initialise Qdrant: {exc}\n", _RED, _BOLD))
        return 1
    mode = "local disk" if manager.is_local else "remote server"
    print(f"\r  Connected ({_c(mode, _BOLD)}).          ")

    if args.reindex:
        ok = _run_ingestion(manager)
        return 0 if ok else 1

    ready = _ensure_collection(manager)
    retriever = RAGRetriever(qdrant_manager=manager)

    if args.query:
        if not ready:
            print(_c("  Index is empty — run with --reindex first.\n", _YELLOW))
            return 1
        search(
            args.query, manager, retriever,
            args.top_k, args.threshold, args.category,
            show_text, args.report,
        )
    else:
        interactive_loop(
            manager, retriever,
            args.top_k, args.threshold, args.category, show_text,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
