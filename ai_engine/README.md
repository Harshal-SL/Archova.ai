# AI Architecture Engine

A FastAPI service that converts raw requirements into structured **High-Level Design (HLD)** and **Low-Level Design (LLD)** documents using a Retrieval-Augmented Generation (RAG) pipeline backed by Qdrant and Ollama.

---

## Project Structure

```
ai_engine/
│
├── app/                          # FastAPI application
│   ├── main.py                   # App entry point, CORS, router mounts
│   ├── config.py                 # Settings (env-driven, frozen dataclass)
│   ├── routers/
│   │   ├── input_router.py       # POST /api/input
│   │   ├── extraction_router.py  # POST /api/extract
│   │   ├── elicitation_router.py # POST /api/elicit, /api/elicit/answer
│   │   └── design_router.py      # POST /api/design, /api/design/reindex
│   └── services/
│       ├── design_service.py     # RAG pipeline orchestrator
│       ├── design_generator.py   # HLD/LLD prompt building + Ollama calls
│       ├── design_validator.py   # Output normalisation and defaults
│       ├── file_parser.py        # PDF / DOCX / image parsing
│       ├── prompt_builder.py     # Text block joining utility
│       ├── elicitation/          # Missing-field detection + Q&A
│       ├── requirement_extractor/ # Structured requirement extraction
│       └── rag_design/           # Thin re-export shim → design_service
│
├── backend/
│   └── rag/                      # Production RAG library
│       ├── config.py             # All RAG constants (no hardcoded values elsewhere)
│       ├── loader.py             # Recursive markdown loader → LangChain Documents
│       ├── metadata.py           # Auto metadata extraction from file paths
│       ├── chunker.py            # RecursiveCharacterTextSplitter (pure Python)
│       ├── embeddings.py         # SentenceTransformer BAAI/bge-small-en-v1.5
│       ├── qdrant_manager.py     # Collection lifecycle + query_points() API
│       ├── ingestion.py          # Load → chunk → embed → upload pipeline
│       ├── query_builder.py      # Intent detection + query expansion
│       ├── retriever.py          # MMR + diversity cap + optional reranking
│       ├── context_builder.py    # Dedup + sort + group → LLM context string
│       ├── validator.py          # Collection health checks
│       └── __init__.py           # Public exports
│
├── data/
│   └── RAG/                      # Architecture knowledge corpus (markdown)
│       ├── domain_architectures/
│       ├── category_1_architecture_patterns/
│       ├── category_2_architecture_decisions/
│       ├── category_3_scaling_techniques/
│       ├── category_4_caching_strategies/
│       ├── category_5_database_design/
│       ├── category_6_messaging_systems/
│       ├── category_7_infrastructure_components/
│       ├── category_8_deployment_strategies/
│       ├── category_9_security_architecture/
│       ├── category_10_real_world_systems/
│       ├── category_11_failure_modes/
│       ├── category_12_application_archetypes/
│       ├── ai_systems/
│       ├── architecture_decision_matrix/
│       ├── cloud_architecture/
│       ├── hld_templates/
│       ├── lld_templates/
│       ├── nfr_mapping/
│       ├── production_readiness/
│       ├── system_components/
│       └── technology_guides/
│
├── scripts/
│   ├── rag_query.py              # Interactive Qdrant search REPL
│   └── rag_retrieval_debugger.py # Detailed retrieval debug tool
│
├── .env.example                  # All environment variables documented
├── .gitignore
├── requirements.txt
├── rag_query.bat                 # Windows launcher for scripts/rag_query.py
└── AI_ENGINE_WORKFLOW.md         # Full pipeline documentation
```

---

## Quick Start

### 1. Install dependencies

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 2. Configure environment

```bash
copy .env.example .env
# Edit .env — set OLLAMA_BASE_URL at minimum
```

### 3. Build the vector index

```bash
# Loads all data/RAG/**/*.md files into Qdrant (runs once, ~2-5 min)
venv\Scripts\python.exe scripts\rag_query.py --reindex
```

### 4. Start the API

```bash
venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

### 5. Query the vector DB interactively

```bash
venv\Scripts\python.exe scripts\rag_query.py
# or
rag_query.bat
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/input` | Accept text + files, return combined prompt |
| `POST` | `/api/extract` | Extract structured requirements from prompt |
| `POST` | `/api/elicit` | Detect missing fields, generate questions |
| `POST` | `/api/elicit/answer` | Merge user answers into requirements |
| `POST` | `/api/design` | Generate HLD + LLD from requirements |
| `POST` | `/api/design/reindex` | Rebuild the Qdrant vector index |

Full workflow: `/api/input` → `/api/extract` → `/api/elicit` → `/api/elicit/answer` → `/api/design`

---

## RAG Retrieval Pipeline

```
User query
    │
    ▼
Intent Detection          (scalability, security, messaging, …)
    │
    ▼
Category Routing          (13–17 relevant categories out of 22)
    │
    ▼
Query Expansion           (3 semantic sub-queries)
    │
    ▼
Qdrant Search × N queries (global search, post-filter by category)
    │
    ▼
Deduplication             (by Qdrant point ID)
    │
    ▼
Diversity Cap             (max 1 chunk per source file)
    │
    ▼
Optional Reranking        (BAAI/bge-reranker-base, off by default)
    │
    ▼
Top-K hits → Context Builder → LLM prompt
```

---

## Key Configuration (`.env`)

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server |
| `LLM_MODEL` | `mistral` | Generation model |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant server (falls back to local disk) |
| `RAG_EMBED_MODEL_LOCAL` | `BAAI/bge-small-en-v1.5` | Embedding model |
| `RAG_RETRIEVAL_K` | `10` | Final results per query |
| `MAX_CHUNKS_PER_DOCUMENT` | `1` | Diversity cap per source file |
| `ENABLE_QUERY_EXPANSION` | `true` | Expand single query to multiple sub-queries |
| `ENABLE_RERANKING` | `false` | Cross-encoder reranking (slower but better) |
| `MMR_LAMBDA` | `0.7` | Relevance/diversity trade-off (1=pure relevance) |

---

## Scripts

```bash
# Interactive search REPL
venv\Scripts\python.exe scripts\rag_query.py

# Single query
venv\Scripts\python.exe scripts\rag_query.py -q "kafka vs rabbitmq"

# Show full retrieval report
venv\Scripts\python.exe scripts\rag_query.py -q "food delivery 20M users" --report

# Metadata only (no chunk text)
venv\Scripts\python.exe scripts\rag_query.py -q "redis" --no-text

# Restrict to one category
venv\Scripts\python.exe scripts\rag_query.py -q "kafka" --category category_6_messaging_systems

# Force rebuild vector index
venv\Scripts\python.exe scripts\rag_query.py --reindex
```
