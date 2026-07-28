# AI Engine Workflow

This repository exposes a FastAPI-based workflow that turns raw user requirements into a structured system design.

## What The System Does

The pipeline has four main stages:

1. Ingest raw text and files.
2. Extract structured requirements from that input.
3. Ask follow-up questions for missing fields and merge the answers.
4. Generate a high-level and low-level system design using RAG over the internal architecture corpus.

## End-To-End Flow

```mermaid
flowchart TD
    A[User text / uploaded files] --> B[/api/input]
    B --> C[Combined prompt]
    C --> D[/api/extract]
    D --> E[Structured parameters]
    E --> F[/api/elicit]
    F --> G[Missing parameters + clarification questions]
    G --> H[/api/elicit/answer]
    H --> I[Completed parameters]
    I --> J[/api/design]
    J --> K[RAG retrieval from Qdrant]
    K --> L[Ollama generation of HLD]
    L --> M[Ollama generation of LLD sections]
    M --> N[Normalized design output]
```

## API Workflow

### 1. `POST /api/input`

File: [app/routers/input_router.py](app/routers/input_router.py)

Accepts:
- `text`: plain requirement text
- `files`: optional uploads in `.pdf`, `.docx`, `.txt`, `.md`, `.png`, `.jpg`, `.jpeg`

What happens:
- Text is added directly.
- Files are parsed with the appropriate extractor.
- The extracted text blocks are joined into a single prompt.

Response:
- `combined_prompt`
- `sources`
- `block_count`

### 2. `POST /api/extract`

File: [app/routers/extraction_router.py](app/routers/extraction_router.py)

Input:
- `combined_prompt`

What happens:
- The prompt is token-estimated.
- If small enough, it is sent as one chunk.
- If large, it is split into overlapping chunks.
- Each chunk is sent to Ollama for requirement extraction.
- Chunk results are merged into one structured parameter object.

Response:
- `parameters`

### 3. `POST /api/elicit`

File: [app/routers/elicitation_router.py](app/routers/elicitation_router.py)

Input:
- `parameters`
- `prompt`

What happens:
- Missing parameters are detected.
- Ollama generates clarification questions for those missing fields.

Response:
- `missing_parameters`
- `questions`

### 4. `POST /api/elicit/answer`

File: [app/routers/elicitation_router.py](app/routers/elicitation_router.py)

Input:
- `parameters`
- `answers`

What happens:
- User answers are merged back into the parameter structure.
- List fields are split by commas.
- `free_constraint` is normalized to boolean when possible.

Response:
- `parameters`

### 5. `POST /api/design`

File: [app/routers/design_router.py](app/routers/design_router.py)

Input:
- `parameters`

What happens:
- The Qdrant collection is checked and rebuilt if it does not exist.
- An architecture-aware retrieval query is built from the parameters.
- Relevant documents are retrieved from Qdrant using cosine similarity search.
- HLD is generated first using the retrieved context.
- Then LLD sections are generated for:
  - frontend
  - backend
  - database
  - cloud
  - security
- The result is normalized into the final design schema.

Response:
- `parameters`
- `design_output`

### 6. `POST /api/design/reindex`

File: [app/routers/design_router.py](app/routers/design_router.py)

What happens:
- Rebuilds the full design corpus index in Qdrant.
- Loads all markdown files from `data/RAG`.
- Extracts metadata, chunks documents, generates embeddings, and uploads vectors.

Response:
- `status`
- `index`

## Internal Pipeline Details

### Input Parsing

File: [app/services/file_parser.py](app/services/file_parser.py)

Supported sources:
- `.txt` and `.md` are read as UTF-8 text.
- `.pdf` is parsed with `pypdf`.
- `.docx` is parsed with `python-docx` when installed.
- Images are OCR'd with `pytesseract` and the local Tesseract binary on Windows.

### Requirement Extraction

Files:
- [app/services/requirement_extractor/pipeline.py](app/services/requirement_extractor/pipeline.py)
- [app/services/requirement_extractor/extractor.py](app/services/requirement_extractor/extractor.py)
- [app/services/requirement_extractor/chunker.py](app/services/requirement_extractor/chunker.py)
- [app/services/requirement_extractor/tokenizer.py](app/services/requirement_extractor/tokenizer.py)
- [app/services/requirement_extractor/merger.py](app/services/requirement_extractor/merger.py)

Behavior:
- Uses Ollama chat/generation API.
- Default model: `mistral`.
- Extracts these fields:
  - goal
  - core_objectives
  - system_type
  - actors
  - functional_requirements
  - inputs
  - outputs
  - external_services
  - system_behaviour
  - non_functional_requirements
  - free_constraint
- Returns JSON only.
- Retries malformed JSON responses.

### Elicitation

Files:
- [app/services/elicitation/pipeline.py](app/services/elicitation/pipeline.py)
- [app/services/elicitation/detector.py](app/services/elicitation/detector.py)
- [app/services/elicitation/question_generator.py](app/services/elicitation/question_generator.py)
- [app/services/elicitation/answer_merger.py](app/services/elicitation/answer_merger.py)

Behavior:
- Detects parameters whose `value` is missing.
- Uses Ollama to produce clarification questions.
- Merges answer text back into the parameter dictionary.

### RAG Design Generation

Files:
- [app/services/design_service.py](app/services/design_service.py) — pipeline orchestrator
- [app/services/design_generator.py](app/services/design_generator.py) — prompt building and Ollama calls
- [app/services/design_validator.py](app/services/design_validator.py) — output normalization
- [backend/rag/loader.py](backend/rag/loader.py) — recursive markdown document loader
- [backend/rag/metadata.py](backend/rag/metadata.py) — automatic metadata extraction
- [backend/rag/chunker.py](backend/rag/chunker.py) — RecursiveCharacterTextSplitter
- [backend/rag/embeddings.py](backend/rag/embeddings.py) — SentenceTransformer embedding generation
- [backend/rag/qdrant_manager.py](backend/rag/qdrant_manager.py) — Qdrant collection lifecycle
- [backend/rag/ingestion.py](backend/rag/ingestion.py) — full ingestion pipeline with progress reporting
- [backend/rag/retriever.py](backend/rag/retriever.py) — semantic search with metadata filtering
- [backend/rag/query_builder.py](backend/rag/query_builder.py) — architecture-aware query routing
- [backend/rag/context_builder.py](backend/rag/context_builder.py) — context assembly with deduplication
- [backend/rag/validator.py](backend/rag/validator.py) — collection health checks
- [backend/rag/config.py](backend/rag/config.py) — centralized RAG configuration

Behavior:
- Loads all `.md` files recursively from `data/RAG` on first run or reindex.
- Extracts rich metadata (title, category, subcategory, keywords, domain, difficulty).
- Chunks documents using RecursiveCharacterTextSplitter (chunk_size=600, overlap=100).
- Generates embeddings locally using `BAAI/bge-small-en-v1.5` via SentenceTransformers.
- Stores vectors in Qdrant with cosine similarity, collection `architecture_rag`.
- Uses architecture-aware query building to route queries to relevant categories.
- Retrieves top-K documents per category, deduplicates, and assembles context.
- Generates HLD first, then LLD sections independently with section-specific context.
- Normalizes final output for schema consistency.

## Technologies Used

### API And Backend

- FastAPI
- Uvicorn for serving the app
- Pydantic for request models
- CORS middleware enabled for all origins, methods, and headers

### LLM And Generation

- Ollama API at `OLLAMA_BASE_URL` or `OLLAMA_URL`
- Default text model: `mistral`
- Same Ollama endpoint is used for requirement extraction, elicitation, and design generation

### Embeddings And Vector Search

- SentenceTransformers for local embedding generation
- Embedding model: `BAAI/bge-small-en-v1.5`
- Qdrant vector store (collection: `architecture_rag`)
- Cosine similarity search

### Document Processing

- `pypdf` for PDFs
- `python-docx` for DOCX files
- `pytesseract` + Tesseract OCR for images

## Key Configuration

File: [app/config.py](app/config.py)

Important environment variables:

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server base URL |
| `OLLAMA_URL` | `<base>/api/generate` | Ollama generate endpoint |
| `LLM_MODEL` | `mistral` | Model for extraction, elicitation, and design |
| `RAG_GENERATION_MODEL` | `LLM_MODEL` | Model used for RAG design generation |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant server URL |
| `QDRANT_COLLECTION_NAME` | `architecture_rag` | Qdrant collection name |
| `RAG_EMBED_MODEL_LOCAL` | `BAAI/bge-small-en-v1.5` | SentenceTransformer embedding model |
| `RAG_DATA_ROOT` | `data/RAG` | Root folder for the RAG corpus |
| `RAG_CHUNK_SIZE` | `600` | Token size per chunk |
| `RAG_CHUNK_OVERLAP` | `100` | Overlap between consecutive chunks |
| `RAG_RETRIEVAL_K` | `10` | Top-K results per retrieval query |
| `RAG_SIMILARITY_THRESHOLD` | `0.3` | Minimum cosine similarity for retrieval |

## Data Flow Summary

1. The user submits text and/or files.
2. The engine normalizes them into one combined prompt.
3. Ollama extracts requirement fields into a structured schema.
4. Missing fields are detected and clarified.
5. Answers are merged back into the structured requirement set.
6. The final parameter set drives RAG retrieval over the architecture corpus in Qdrant.
7. Ollama generates HLD and then LLD sections using the retrieved context.
8. The normalized design is returned to the caller.

## Notes

- On the first request to `/api/design`, if the Qdrant collection does not exist, it is automatically built by running the ingestion pipeline.
- To force a full reindex at any time, call `POST /api/design/reindex`.
- If Ollama returns invalid JSON, the system retries and may fall back to a minimal design.
- The repository contains a curated `data/RAG` corpus of architecture patterns, decisions, scaling techniques, security patterns, failure modes, and real-world system designs.
