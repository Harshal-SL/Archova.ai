from __future__ import annotations

from dataclasses import dataclass

from .langchain_compat import Document, create_recursive_splitter


@dataclass
class RetrievalHit:
    text: str
    metadata: dict
    similarity: float
    score: float


def _to_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if item is not None)
    return str(value)


def _parameter_value(parameters: dict, key: str):
    node = parameters.get(key)
    if isinstance(node, dict):
        return node.get("value")
    return node


def split_documents_for_indexing(
    documents: list,
    chunk_size: int,
    chunk_overlap: int,
) -> list:
    if not documents:
        return []

    splitter = create_recursive_splitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    if splitter is None:
        return _fallback_split(documents, chunk_size, chunk_overlap)

    chunks = splitter.split_documents(documents)
    for idx, chunk in enumerate(chunks):
        metadata = dict(chunk.metadata or {})
        metadata["chunk_index"] = idx
        chunk.metadata = metadata

    return chunks


def _fallback_split(documents: list, chunk_size: int, overlap: int) -> list:
    chunks: list = []
    safe_chunk_size = max(chunk_size, 200)
    safe_overlap = max(0, min(overlap, safe_chunk_size - 1))
    step = safe_chunk_size - safe_overlap

    for doc in documents:
        text = doc.page_content
        start = 0
        part_idx = 0
        while start < len(text):
            piece = text[start : start + safe_chunk_size]
            if piece.strip():
                metadata = dict(doc.metadata or {})
                metadata["chunk_index"] = part_idx
                chunks.append(Document(page_content=piece, metadata=metadata))
            part_idx += 1
            start += step

    return chunks


def build_retrieval_query(parameters: dict) -> str:
    ordered_fields = [
        ("goal", "Goal"),
        ("core_objectives", "Core objectives"),
        ("system_type", "System type"),
        ("actors", "Actors"),
        ("functional_requirements", "Functional requirements"),
        ("inputs", "Inputs"),
        ("outputs", "Outputs"),
        ("external_services", "External services"),
        ("system_behaviour", "System behaviour"),
        ("non_functional_requirements", "Non-functional requirements"),
        ("free_constraint", "Free tier constraint"),
    ]

    lines = []
    for key, label in ordered_fields:
        value = _parameter_value(parameters, key)
        rendered = _to_text(value).strip()
        if rendered:
            lines.append(f"{label}: {rendered}")

    if not lines:
        return "Design a scalable and secure software system architecture with clear HLD and LLD."

    return "\n".join(lines)


def rank_retrieval_hits(
    raw_hits: list[dict],
    max_items: int,
    existing_design_boost: float,
) -> list[RetrievalHit]:
    ranked: list[RetrievalHit] = []

    for hit in raw_hits:
        metadata = dict(hit.get("metadata") or {})
        base_similarity = float(hit.get("similarity", 0.0))
        boost = existing_design_boost if bool(metadata.get("is_existing_design")) else 0.0
        final_score = base_similarity + boost

        ranked.append(
            RetrievalHit(
                text=str(hit.get("text", "")),
                metadata=metadata,
                similarity=base_similarity,
                score=final_score,
            )
        )

    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked[: max(1, max_items)]


def build_context_block(hits: list[RetrievalHit], max_chars: int) -> tuple[str, list[dict]]:
    if not hits:
        return (
            "No relevant documents were retrieved from the corpus. Use conservative assumptions.",
            [],
        )

    snippets = []
    references = []
    total_chars = 0

    for hit in hits:
        text = hit.text.strip().replace("\r\n", "\n")
        if not text:
            continue

        if len(text) > 700:
            text = text[:700].rstrip() + "..."

        source = str(hit.metadata.get("source_path", "unknown"))
        intro = f"[source: {source} | score: {hit.score:.3f}]"
        block = f"{intro}\n{text}"

        if total_chars + len(block) > max_chars:
            break

        snippets.append(block)
        references.append(
            {
                "source": source,
                "why_relevant": f"semantic match score {hit.score:.3f}",
            }
        )
        total_chars += len(block)

    if not snippets:
        return (
            "Context budget prevented adding retrieved content. Use conservative assumptions.",
            references,
        )

    return "\n\n".join(snippets), references
