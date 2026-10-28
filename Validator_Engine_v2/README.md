# Validator Engine v2 (Archova.ai)

Validator Engine v2 is a high-assurance, multi-layered architectural validation service for Archova.ai running independently on **FastAPI port 8002**.

Unlike rule-based phase checks, Validator Engine v2 introduces 5 distinct layers:
- **Layer 0 (Normalization & Graph Synthesis)**: Parses the complete architecture package (`NormalizedPackage`), detects structural discrepancies, and identifies orphan references (`L0.ORPHAN_REF`).
- **Layer 1 (Executable Evidence)**: Performs deterministic static and tool-based verification on scaffolded source files:
  - `openapi_check`: Validates `openapi.yaml` via `openapi-spec-validator` and verifies full endpoint mapping against Backend LLD.
  - `dockerfile_check`: Runs `hadolint` if on PATH; otherwise executes deterministic static checks (non-root USER, pinned base tag, HEALTHCHECK).
  - `terraform_check`: Runs `terraform fmt -check` and `terraform validate` if on PATH; otherwise checks Cloud LLD resource alignment in `main.tf`.
  - `migration_check`: Parses Alembic migrations using Python `ast` to verify table, column, and foreign key definitions against Database LLD.
- **Layers 2–4 (Unified LLM Review)**: One parallel LLM call per artifact (HLD, Backend, Database, Frontend, Security, Cloud) with weighted rubric dimensions, engineering checklists, and strict anti-hallucination evidence resolution.
- **Layer 5 (Decision Engine & Autonomous Correction)**: Computes weighted scores, applies L0/L1 deductions and caps, diffs finding identities across iterations, and drives targeted regeneration loops.

---

## 1. Quick Start

### Prerequisites
- Python 3.10+
- Installed dependencies:
  ```bash
  pip install -r Validator_Engine_v2/requirements.txt
  ```

### Start the Service
```bash
# Run standalone service on port 8002
uvicorn Validator_Engine_v2.main:app --port 8002 --reload
```

---

## 2. Configuration & Environment Variables

Create `.env` inside `Validator_Engine_v2/` or set variables in your shell:

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8002` | Port to run Validator Engine v2 |
| `HOST` | `0.0.0.0` | Bind host address |
| `AI_ENGINE_URL` | `http://localhost:8000` | AI Engine base URL |
| `NEXT_APP_ORIGIN` | `http://localhost:3000` | Allowed CORS origin for Next.js app |
| `VALIDATOR_API_BASE` | `https://openrouter.ai/api/v1` | OpenAI-compatible endpoint |
| `VALIDATOR_API_KEY` | `""` | OpenRouter API Key |
| `VALIDATOR_MODEL` | `anthropic/claude-3.5-sonnet` | Model used for rubric evaluations |
| `VALIDATOR_MOCK` | `1` | `1` = offline mock review; `0` = live LLM reviewer |
| `VALIDATOR_API_KEY_INBOUND`| `""` | Inbound API key check (optional) |
| `ACCEPT_THRESHOLD` | `80` | Minimum score (0-100) for `ACCEPTED` verdict |
| `MAX_ROUNDS` | `2` | Max autonomous correction iterations |
| `LLM_TIMEOUT_SECONDS` | `60.0` | Timeout per LLM call |
| `ITERATION_TIMEOUT_SECONDS` | `180.0`| Timeout per validation round |
| `TOTAL_PIPELINE_TIMEOUT_SECONDS` | `600.0`| Total timeout per pipeline run |

### Switching Between Mock and Live LLM
- **Mock Mode (Default & Testing)**:
  ```bash
  export VALIDATOR_MOCK=1
  ```
  Returns deterministic, repeatable rubric scores and findings without network calls or API token usage.
- **Live LLM Reviewer Mode**:
  ```bash
  export VALIDATOR_MOCK=0
  export VALIDATOR_API_KEY=sk-or-v1-...
  export VALIDATOR_MODEL=anthropic/claude-3.5-sonnet
  ```
  > **Note**: Always configure a different model family from the AI Engine generator to preserve reviewer independence.

---

## 3. API Endpoints & Examples

### Health Check
```bash
curl http://localhost:8002/health
```

### Direct Validation (Dev / Single-Shot, No Regeneration Loop)
```bash
curl -X POST http://localhost:8002/v1/validate \
  -H "Content-Type: application/json" \
  -d @Validator_Engine_v2/tests/fixtures/sample_package.json
```

### Start Autonomous Pipeline (Background Task)
```bash
curl -X POST http://localhost:8002/v1/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"generation_id": "gen_sample_123"}'
```

### Poll Pipeline Status
```bash
curl http://localhost:8002/v1/pipeline/gen_sample_123/status
```

### Fetch Validation Report & Final Package
```bash
curl http://localhost:8002/v1/reports/gen_sample_123
```

---

## 4. Running Tests
Run all unit and integration tests with offline mock mode enabled:
```bash
python -m pytest -p no:capture Validator_Engine_v2/tests
```
