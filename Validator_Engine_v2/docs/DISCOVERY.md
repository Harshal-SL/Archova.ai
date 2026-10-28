# Validator Engine v2 — Discovery Document

## 1. AI Engine Endpoint Shapes

Discovered from `ai_engine/app/api/routes/generations.py` and `ai_engine/app/schemas/requests.py`, `ai_engine/app/schemas/responses.py`:

### a. `POST /api/v1/generations`
- **Request Body**: `StartGenerationRequest`
  ```json
  {
    "prompt": "string (min_length=1)"
  }
  ```
- **Response**: `StartGenerationResponse` (HTTP 200)
  ```json
  {
    "generation_id": "string",
    "status": "string (e.g. INTERVIEW_IN_PROGRESS | INTERVIEW_COMPLETED)",
    "current_question": {
      "question_id": "string",
      "question": "string",
      "options": ["string"],
      "default_option": "string | null",
      "rationale": "string | null",
      "target_section": "string | null",
      "target_field": "string | null",
      "priority": "string | null (high | medium | low)"
    }
  }
  ```

### b. `POST /api/v1/generations/{generation_id}/answers`
- **Request Body**: `SubmitAnswerRequest`
  ```json
  {
    "question_id": "string",
    "answer": "string"
  }
  ```
- **Response**: `SubmitAnswerResponse` (HTTP 200)
  ```json
  {
    "generation_id": "string",
    "status": "string (INTERVIEW_IN_PROGRESS | INTERVIEW_COMPLETED)",
    "next_question": {
      "question_id": "string",
      "question": "string",
      "options": ["string"],
      "default_option": "string | null",
      "rationale": "string | null",
      "target_section": "string | null",
      "target_field": "string | null",
      "priority": "string | null"
    }
  }
  ```

### c. `POST /api/v1/generations/{generation_id}/generate`
- **Request**: No body (path parameter `generation_id`).
- **Response**: `GenerateArchitectureResponse` (HTTP 200)
  ```json
  {
    "generation_id": "string",
    "status": "string (e.g. HLD_READY)",
    "arsrs": {},
    "hld": {}
  }
  ```

### d. `GET /api/v1/generations/{generation_id}/status`
- **Response**: `GenerationStatusResponse` (HTTP 200)
  ```json
  {
    "generation_id": "string",
    "status": "string",
    "interview": "string (IN_PROGRESS | COMPLETED)",
    "arsrs": "string (NOT_STARTED | GENERATING | READY | FAILED)",
    "hld": "string (NOT_STARTED | GENERATING | READY | FAILED)",
    "llds": {
      "backend": "string",
      "frontend": "string",
      "database": "string",
      "security": "string",
      "cloud": "string"
    }
  }
  ```

### e. `GET /api/v1/generations/{generation_id}/arsrs` and `GET /api/v1/generations/{generation_id}/hld`
- **Response**: `ArtifactResponse` (HTTP 200)
  ```json
  {
    "generation_id": "string",
    "status": "string (NOT_STARTED | GENERATING | READY | FAILED)",
    "data": {},
    "message": "string | null"
  }
  ```

### f. `GET /api/v1/generations/{generation_id}/lld/{lld_type}`
- **Supported types**: `backend`, `frontend`, `database`, `security`, `cloud`.
- **Response**: `LLDDetailResponse` (HTTP 200)
  ```json
  {
    "generation_id": "string",
    "lld_type": "string",
    "status": "string (NOT_STARTED | GENERATING | READY | FAILED)",
    "data": {},
    "message": "string | null",
    "error": "string | null"
  }
  ```

### g. `GET /api/v1/generations/{generation_id}/package`
- **Response**: Dict containing the full synthesized package (HTTP 200):
  ```json
  {
    "generation_id": "string",
    "prompt": "string",
    "status": "string",
    "arsrs": {},
    "hld": {},
    "llds": {
      "backend": {"status": "READY", "data": {}, "error": null},
      "frontend": {"status": "READY", "data": {}, "error": null},
      "database": {"status": "READY", "data": {}, "error": null},
      "security": {"status": "READY", "data": {}, "error": null},
      "cloud": {"status": "READY", "data": {}, "error": null}
    },
    "created_at": "string",
    "completed_at": "string"
  }
  ```

---

## 2. Real JSON Structure of Artifacts

Discovered from actual pipeline fixtures (`ai_engine/output/run_20261004_200235_gen_415ece685f85/10_architecture_package.json`) and Pydantic models (`ai_engine/app/sae/models/response_models.py`):

1. **ARSRS (`arsrs`)**:
   - `session_id`: UUID string
   - `project_profile`: `{goal, system_type, domain, input_sources, success_criteria}`
   - `business_context`: `{business_objectives, stakeholders, constraints, kpis, business_rules}`
   - `domain_context`: `{system_type, industry, domain_concepts, architecture_patterns, compliance, domain_constraints}`
   - `functional_requirements`: Array of `{id: "FR-...", title: "...", description: "...", priority: "..."}`
   - `non_functional_requirements`: Array of `{id: "NFR-...", category: "...", description: "..."}`
   - `metadata`: `{arsrs_version, generated_at, statistics}`

2. **HLD (`hld`)**:
   - `architecture_style`: string (e.g. "Event-Driven Microservices" or "Modular Monolith")
   - `executive_summary`: string
   - `business_goals`: list
   - `major_services`: Array of `{name: "...", responsibility: "...", tech_stack: "...", interfaces: [...]}`
   - `communication_patterns`: list / dict
   - `data_strategy`: dict
   - `security_overview`: dict
   - `deployment_strategy`: dict

3. **Backend LLD (`llds.backend.data`)**:
   - `api_endpoints`: Array of `{route: "...", method: "GET|POST|...", description: "...", auth_required: bool, request: {...}, response: {...}, error_responses: [...]}`
   - `services`: Array of domain/application services
   - `domain_models`: Entities, value objects
   - `framework_config`: Language, framework
   - `error_handling`, `security_config`, `data_lifecycle`, `dependencies`

4. **Database LLD (`llds.database.data`)**:
   - `database_type`: string (e.g. "PostgreSQL 16")
   - `tables`: Array of `{name: "...", columns: [{name: "...", type: "...", primary_key: bool, nullable: bool}], indexes: [...]}`
   - `relationships`: Array of FK relationships
   - `indexes`: Array of table indexes
   - `caching_strategy`: Redis/memory config
   - `backup_strategy`, `locking_and_concurrency`

5. **Frontend LLD (`llds.frontend.data`)**:
   - `framework`: e.g. "Next.js 14 / React 18"
   - `pages`: Array of views/routes
   - `components`: Array of UI components
   - `state_management`: Zustand / Redux
   - `routing`, `api_integration`, `styling_approach`

6. **Security LLD (`llds.security.data`)**:
   - `authentication`: JWT, OAuth2, Session
   - `authorization`: RBAC, ABAC policies
   - `encryption`: At rest (AES-256) and in transit (TLS 1.3)
   - `threat_model`: STRIDE threat list
   - `security_controls`: Specific defenses
   - `secrets_management`, `audit_logging`

7. **Cloud LLD (`llds.cloud.data`)**:
   - `cloud_provider`: "AWS" | "GCP" | "Azure"
   - `compute`: ECS / EKS / Lambda
   - `networking`: VPC, Subnets, ALB
   - `storage`: S3 / EBS
   - `scaling_strategy`, `disaster_recovery`

8. **Canonical Architecture Contract (CAC)**:
   - Contains canonical services, database schemas, communication contracts, domain boundaries, security invariants.

9. **Deterministic Scaffolds**:
   - `openapi.yaml`: OpenAPI 3.1.0 document derived from backend LLD endpoints.
   - `Dockerfile`: Multi-stage Dockerfile (builder + runner, non-root user, healthcheck).
   - `docker-compose.yml`: Local orchestrator with backend, db, cache services.
   - `alembic/versions/0001_initial_schema.py`: Alembic migration script using `op.create_table`.
   - `terraform/main.tf`: AWS VPC, Subnet, and Cloud resources.

---

## 3. Artifact Regeneration & Feedback Analysis

From `ai_engine/app/api/routes/generations.py` and `ai_engine/app/services/generation_service.py`:
- **Endpoint Analysis**:
  - `GET /api/v1/generations/{generation_id}/lld/{lld_type}` is strictly a `GET` endpoint. No `POST /lld/{lld_type}` exists.
  - `POST /api/v1/generations/{generation_id}/generate` takes NO body/feedback. In `generation_service.py:generate_arsrs_and_hld`:
    ```python
    if context.status in ("HLD_READY", "COMPLETED") and context.hld is not None:
        return context  # Idempotent return without regeneration
    ```
  - The internal methods `apply_correction_feedback_to_package` and `validate_and_correct` in `generation_service.py` are coupled to the legacy `Validator_Engine` on port 8001 and are invoked via `POST /api/v1/generations/{generation_id}/validate-and-correct`.

### STOP CONDITION 1 TRIGGERED:
Because the AI Engine does not expose an HTTP endpoint to accept feedback for regenerating a specific HLD or LLD:
- We do **NOT** modify `ai_engine/`.
- We implement the regeneration loop behind a clean `RegenerationAdapter` interface.
- When regenerating via AI Engine HTTP endpoints, the fallback marks the iteration `regenerated_with_feedback: false` (or `regenerated_without_feedback`) in the report.
- We also allow in-memory / local simulation adapters for end-to-end multi-round testing.

---

## 4. Next.js Integration Flow

From `next_app/lib/store.ts`, `next_app/lib/ai-engine-client.ts`, and `next_app/components/HldWorkspace.tsx`:
- State fields in `store.ts`:
  - `hldData`, `hldNodes`, `hldEdges`, `lldData` (Record<LldType, unknown>), `lldStatus`, `arsrsData`.
  - `hldWorkspaceTab`: `"hld" | "lld" | "validation"`.
  - `validationData`: Stores old validator response from port 8001.
- `HldWorkspace.tsx`:
  - Renders top tabs: "HLD Topology" (`hld`), "5 LLD Blueprints" (`lld`), and "Validation Audit" (`validation`).
  - Displays `HLDGraph`, `LldsView`, and `ValidationView`.
- Required Additions:
  - Add tab `"validation-v2"` (labelled "Validation Report" with V2 badge) without removing or breaking `ValidationView`.
  - Store fields: `validationReport` (Report v2), `validationStatus` (`idle` | `running` | `completed` | `error`), `validationCurrentStep`.
  - Client: `next_app/lib/validator-v2-client.ts` to call port 8002 (`/v1/pipeline/run`, `/v1/pipeline/{id}/status`, `/v1/reports/{id}`).
  - Component: `next_app/components/ValidationReportView.tsx`.
  - Update visualization feeding to use the report's final package.

---

## 5. Existing Environment Variables

Discovered from `ai_engine/.env.example`:
- `OPENROUTER_API_KEY`
- `ALLOW_PAID_MODELS`
- `LLM_MODEL`
- `RAG_GENERATION_MODEL`
- `INPUT_UNDERSTANDING_MODEL`
- `REQUIREMENT_ENGINEER_MODEL`
- `HLD_GENERATION_MODEL`
- `BACKEND_LLD_MODEL`
- `DATABASE_LLD_MODEL`
- `FRONTEND_LLD_MODEL`
- `SECURITY_LLD_MODEL`
- `CLOUD_LLD_MODEL`
- `OPENROUTER_TIMEOUT_SECONDS`
- `LLM_GATEWAY_MAX_RETRIES`
- `LLM_GATEWAY_JSON_RETRIES`
*(Variable names only; no secret values).*
