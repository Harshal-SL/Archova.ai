from __future__ import annotations

import hashlib
import json
from pathlib import Path
from threading import Lock

from app.config import settings

from .generator import build_design_prompt, generate_design_from_ollama
from .indexer import ChromaDocumentIndex
from .loaders import discover_corpus_files, load_corpus_documents
from .retriever import (
    build_context_block,
    build_retrieval_query,
    rank_retrieval_hits,
    split_documents_for_indexing,
)
from .validator import normalize_design_output

_INDEX_LOCK = Lock()
_INDEX: ChromaDocumentIndex | None = None


def _state_file_path() -> Path:
    persist_dir = Path(settings.rag_persist_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)
    return persist_dir / f"{settings.rag_collection_name}_corpus_state.json"


def _compute_corpus_signature(data_root: Path) -> tuple[str, int]:
    files = discover_corpus_files(data_root)
    digest = hashlib.sha1()

    for file_path in files:
        try:
            stat = file_path.stat()
        except OSError:
            continue

        rel_path = file_path.relative_to(data_root).as_posix()
        digest.update(rel_path.encode("utf-8"))
        digest.update(b"|")
        digest.update(str(stat.st_size).encode("ascii"))
        digest.update(b"|")
        digest.update(str(stat.st_mtime_ns).encode("ascii"))
        digest.update(b"\n")

    return digest.hexdigest(), len(files)


def _build_expected_state() -> dict:
    data_root = Path(settings.rag_data_root)
    signature, file_count = _compute_corpus_signature(data_root)
    return {
        "data_root": str(data_root.resolve()),
        "corpus_signature": signature,
        "corpus_file_count": file_count,
        "chunk_size": settings.rag_chunk_size,
        "chunk_overlap": settings.rag_chunk_overlap,
        "embedding_model": settings.rag_embedding_model,
    }


def _load_saved_state() -> dict | None:
    path = _state_file_path()
    if not path.exists():
        return None

    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

    if not isinstance(loaded, dict):
        return None

    return loaded


def _save_state(state: dict) -> None:
    path = _state_file_path()
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _parameter_value(parameters: dict, key: str):
    node = parameters.get(key)
    if isinstance(node, dict):
        return node.get("value")
    return node


def _as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _fallback_design(parameters: dict, retrieval_refs: list[dict], reason: str) -> dict:
    goal = _parameter_value(parameters, "goal") or "the target system"
    system_type = _parameter_value(parameters, "system_type") or "a distributed application"
    actors = _as_list(_parameter_value(parameters, "actors"))[:5]
    functional_requirements = _as_list(_parameter_value(parameters, "functional_requirements"))[:5]
    non_functional_requirements = _as_list(_parameter_value(parameters, "non_functional_requirements"))[:5]
    external_services = _as_list(_parameter_value(parameters, "external_services"))[:4]
    cleaned_reason = (reason or "unknown generation failure").strip()
    if len(cleaned_reason) > 320:
        cleaned_reason = cleaned_reason[:320].rstrip() + "..."

    actor_entries = [
        {
            "actor": str(actor),
            "description": "Participates in core business workflows.",
        }
        for actor in actors
    ]
    if not actor_entries:
        actor_entries = [
            {"actor": "User", "description": "End user interacting with the system."},
            {"actor": "Admin", "description": "Manages system operations and configuration."},
        ]

    request_flow_steps = [
        "User interacts with Frontend",
        "Frontend calls API Gateway",
        "API Gateway authenticates and routes request",
        "Backend Service handles business logic",
        "Backend Service reads/writes Database and Cache",
        "Response returned to Frontend",
    ]
    if functional_requirements:
        request_flow_steps.append(
            "Primary workflows include: " + ", ".join(str(item) for item in functional_requirements[:3])
        )

    def _pick_nfr(keyword: str, default: str) -> str:
        keyword_lower = keyword.lower()
        for item in non_functional_requirements:
            text = str(item)
            if keyword_lower in text.lower():
                return text
        return default

    external_component_services = [
        {
            "name": str(service),
            "interaction": "REST",
            "data_format": "JSON",
        }
        for service in external_services
    ]
    if not external_component_services:
        external_component_services = [
            {
                "name": "Payment API",
                "interaction": "REST",
                "data_format": "JSON",
            }
        ]

    backend_steps = [str(item) for item in functional_requirements[:3]]
    if not backend_steps:
        backend_steps = [
            "Validate input",
            "Process business logic",
            "Return response",
        ]

    return {
        "design_output": {
            "high_level_design": {
                "system_name": str(goal),
                "version": "1.0",
                "description": f"Fallback HLD for {goal} ({system_type}).",
                "architecture": {
                    "type": "Service-oriented architecture",
                    "pattern": ["Client-Server", "Layered", "Event-Driven"],
                    "deployment": "Cloud",
                },
                "actors": actor_entries,
                "core_components": [
                    {
                        "name": "Frontend",
                        "type": "Client Layer",
                        "description": "User-facing web/mobile interface",
                        "interacts_with": ["API Gateway"],
                        "technology_options": ["React", "Angular"],
                    },
                    {
                        "name": "API Gateway",
                        "type": "Entry Layer",
                        "description": "Routes requests and applies auth/rate limits",
                        "interacts_with": ["Auth Service", "Backend Service"],
                        "technology_options": ["Kong", "NGINX"],
                    },
                    {
                        "name": "Auth Service",
                        "type": "Service",
                        "description": "Authentication and authorization",
                        "interacts_with": ["API Gateway", "Database"],
                        "technology_options": ["Keycloak", "OAuth2 Server"],
                    },
                    {
                        "name": "Core Backend Service",
                        "type": "Service",
                        "description": "Business workflow execution",
                        "interacts_with": ["Database", "Cache", "External Services"],
                        "technology_options": ["FastAPI", "Spring Boot"],
                    },
                    {
                        "name": "Database",
                        "type": "Storage",
                        "description": "Persistent transactional data",
                        "interacts_with": ["Core Backend Service", "Auth Service"],
                        "technology_options": ["PostgreSQL", "MySQL"],
                    },
                    {
                        "name": "Cache",
                        "type": "Performance Layer",
                        "description": "Low-latency reads for hot paths",
                        "interacts_with": ["Core Backend Service"],
                        "technology_options": ["Redis", "Memcached"],
                    },
                    {
                        "name": "External Services",
                        "type": "Third-party",
                        "description": "Third-party APIs and integrations",
                        "interacts_with": ["Core Backend Service"],
                        "technology_options": ["REST APIs", "Webhooks"],
                    },
                ],
                "data_flow": [
                    {
                        "use_case": "User Request Flow",
                        "steps": request_flow_steps,
                    }
                ],
                "scalability": {
                    "approach": _pick_nfr("scal", "Horizontal scaling"),
                    "load_balancer": "Yes",
                    "auto_scaling": True,
                },
                "security": {
                    "authentication": "JWT / OAuth",
                    "authorization": "RBAC",
                    "data_security": ["HTTPS", "Encryption"],
                },
                "non_functional_requirements": {
                    "availability": _pick_nfr("availability", "99.9%"),
                    "latency": _pick_nfr("latency", "<200ms"),
                    "throughput": _pick_nfr("throughput", "High"),
                    "fault_tolerance": _pick_nfr("fault", "Retry + Circuit Breaker"),
                },
            },
            "low_level_design": {
                "system_name": str(goal),
                "version": "1.0",
                "components": [
                    {
                        "name": "Frontend",
                        "type": "Client",
                        "pages": [
                            {
                                "name": "Home Page",
                                "components": ["Navbar", "Search Bar", "Cards"],
                            }
                        ],
                        "state_management": {
                            "tool": "Redux / Context API",
                            "states": ["user", "data", "loading", "error"],
                        },
                        "api_integration": [
                            {
                                "endpoint": "/api/resource",
                                "method": "GET",
                            }
                        ],
                    },
                    {
                        "name": "API Gateway",
                        "type": "Routing Layer",
                        "routes": [
                            {
                                "path": "/api/*",
                                "destination": "Backend Services",
                            }
                        ],
                        "middleware": ["Authentication", "Rate Limiting", "Logging"],
                    },
                    {
                        "name": "Backend Service",
                        "type": "Business Logic",
                        "modules": [
                            {
                                "name": "Core Module",
                                "responsibility": "Main business logic",
                            }
                        ],
                        "classes": [
                            {
                                "name": "ServiceClass",
                                "methods": [
                                    {
                                        "name": "processRequest",
                                        "steps": backend_steps,
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "name": "Authentication Service",
                        "type": "Security",
                        "flows": [
                            "User login",
                            "Validate credentials",
                            "Generate JWT",
                            "Return token",
                        ],
                    },
                    {
                        "name": "Database",
                        "type": "Storage",
                        "schema": {
                            "tables": [
                                {
                                    "name": "entities",
                                    "columns": [
                                        {"name": "id", "type": "UUID"},
                                        {"name": "field", "type": "String"},
                                    ],
                                }
                            ]
                        },
                        "queries": [
                            {
                                "name": "findById",
                                "query": "SELECT * FROM entities WHERE id = ?",
                            }
                        ],
                    },
                    {
                        "name": "Cache",
                        "type": "Performance",
                        "strategy": "Read-through / Write-through",
                        "ttl": "300 seconds",
                    },
                    {
                        "name": "External Integration",
                        "type": "Third-party",
                        "services": external_component_services,
                    },
                    {
                        "name": "Error Handling",
                        "type": "Cross-cutting",
                        "exceptions": [
                            {
                                "name": "GenericException",
                                "status": 500,
                            }
                        ],
                    },
                    {
                        "name": "Logging",
                        "type": "Monitoring",
                        "levels": ["INFO", "ERROR"],
                        "tools": ["ELK", "CloudWatch"],
                    },
                ],
            },
            "references": retrieval_refs,
            "assumptions": [
                "Fallback design was generated because the model response could not be parsed.",
                f"Generation issue: {cleaned_reason}",
            ],
        }
    }


def _get_index() -> ChromaDocumentIndex:
    global _INDEX
    if _INDEX is not None:
        return _INDEX

    with _INDEX_LOCK:
        if _INDEX is None:
            _INDEX = ChromaDocumentIndex(
                persist_dir=Path(settings.rag_persist_dir),
                collection_name=settings.rag_collection_name,
                ollama_base_url=settings.ollama_base_url,
                embedding_model=settings.rag_embedding_model,
                timeout_seconds=settings.ollama_timeout_seconds,
            )

    return _INDEX


def _build_index(index: ChromaDocumentIndex) -> dict:
    data_root = Path(settings.rag_data_root)
    documents = load_corpus_documents(data_root, settings.rag_existing_design_folder)
    if not documents:
        raise RuntimeError(
            f"No .md/.pdf/.docx documents found under corpus root: {data_root}"
        )

    chunks = split_documents_for_indexing(
        documents,
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
    )
    if not chunks:
        raise RuntimeError("No chunks were produced from the corpus documents.")

    index.reset_collection()
    indexed_chunk_count = index.index_documents(chunks)
    state = _build_expected_state()
    _save_state(state)

    return {
        "document_count": len(documents),
        "chunk_count": len(chunks),
        "indexed_chunk_count": indexed_chunk_count,
        "collection_count": index.count(),
        "corpus_file_count": state.get("corpus_file_count", 0),
    }


def _ensure_index_ready(index: ChromaDocumentIndex) -> None:
    with _INDEX_LOCK:
        expected_state = _build_expected_state()
        saved_state = _load_saved_state()
        if index.count() == 0 or saved_state != expected_state:
            _build_index(index)


def reindex_corpus() -> dict:
    index = _get_index()
    with _INDEX_LOCK:
        return _build_index(index)


def run_design_pipeline(parameters: dict) -> dict:
    if not isinstance(parameters, dict) or not parameters:
        raise RuntimeError("parameters must be a non-empty object.")

    index = _get_index()
    _ensure_index_ready(index)

    retrieval_query = build_retrieval_query(parameters)
    raw_hits = index.query(retrieval_query, n_results=settings.rag_retrieval_k)
    ranked_hits = rank_retrieval_hits(
        raw_hits,
        max_items=settings.rag_context_docs,
        existing_design_boost=settings.rag_existing_design_boost,
    )

    context_block, retrieval_refs = build_context_block(
        ranked_hits,
        max_chars=settings.rag_context_char_budget,
    )

    prompt = build_design_prompt(
        parameters=parameters,
        retrieval_query=retrieval_query,
        context_block=context_block,
    )

    try:
        generated = generate_design_from_ollama(
            prompt=prompt,
            ollama_generate_url=settings.ollama_generate_url,
            model=settings.rag_generation_model,
            timeout_seconds=settings.ollama_timeout_seconds,
            max_retries=settings.rag_generation_retries,
        )
    except RuntimeError as exc:
        generated = _fallback_design(parameters, retrieval_refs, str(exc))

    design_output = normalize_design_output(generated, retrieval_refs)
    return {
        "parameters": parameters,
        "design_output": design_output,
    }
