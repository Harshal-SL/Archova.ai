# Archova.ai — Autonomous Multi-Agent AI System Architecture Platform

> **Transforming raw, ambiguous requirements into production-ready software architectures, formal specifications, interactive visual topologies, and verified multi-tier low-level designs.**

[![Next.js 16](https://img.shields.io/badge/Next.js-16.1.6-black?style=flat&logo=next.js)](https://nextjs.org/)
[![React 19](https://img.shields.io/badge/React-19.2.3-blue?style=flat&logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue?style=flat&logo=typescript)](https://www.typescriptlang.org/)
[![Tailwind CSS v4](https://img.shields.io/badge/Tailwind_CSS-v4.0-38bdf8?style=flat&logo=tailwind-css)](https://tailwindcss.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python 3.11](https://img.shields.io/badge/Python-3.11.9-3776AB?style=flat&logo=python)](https://www.python.org/)
[![Redis 7](https://img.shields.io/badge/Redis-Upstash_TLS-DC382D?style=flat&logo=redis)](https://upstash.com/)
[![Qdrant Vector DB](https://img.shields.io/badge/Qdrant-Vector_Search-red?style=flat&logo=qdrant)](https://qdrant.tech/)
[![React Flow](https://img.shields.io/badge/React_Flow-@xyflow/react-ff0072?style=flat)](https://reactflow.dev/)
[![Supabase](https://img.shields.io/badge/Supabase-Auth_&_DB-3ECF8E?style=flat&logo=supabase)](https://supabase.com/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-Free_Tier_Optimized-6366f1)](https://openrouter.ai/)

---

## 📌 Executive Summary

**Archova.ai** is an enterprise-grade, multi-agent AI software architecture generation and autonomous verification platform. It automates the entire software architecture lifecycle: from ingesting high-level, unstructured stakeholder problem statements or multimodal documents (PDF, DOCX, TXT, OCR images) to generating complete, verified, and production-ready architectural deliverables.

### The Problem It Solves
Translating vague, ambiguity-ridden stakeholder expectations into resilient, scalable, and enterprise-grade software architectures is traditionally one of the slowest and most expensive phases of software engineering. Manual whiteboarding often misses edge cases, architectural patterns are inconsistently applied, and translating High-Level Designs (HLD) into domain-specific Low-Level Designs (LLDs) across frontend, backend, database, security, and cloud infrastructure takes weeks of senior engineering effort.

When commercial Large Language Models (LLMs) are queried in a single shot:
1. **Ambiguity Blindness**: They hallucinate unstated assumptions without asking clarifying questions regarding SLA targets, throughput, or security compliance.
2. **Unlinked Components**: They output generic boxes that lack syntactic and semantic linkages across database schemas, API contracts, and infrastructure topologies.
3. **Absence of Verifiable Audits**: There is no objective mechanism to audit whether the synthesized architecture respects database normalization, idempotent locks, or zero-trust boundaries.

### The Archova.ai Solution
Archova.ai replaces ad-hoc design processes with a disciplined, multi-agent dual-engine pipeline backed by an in-memory Redis messaging backbone and an independent Validator Engine:
- **Requirements Engineering Engine (REE)**: Extracts requirements, pinpoints ambiguities, conducts an interactive clarification interview with the stakeholder, and synthesizes a formal **ARSRS** (Architecture-Ready Structured Requirements Specification).
- **Software Architecture Engine (SAE)**: Ingests the ARSRS, retrieves verified domain patterns from a Qdrant RAG vector database, and synthesizes an interactive visual **High-Level Design (HLD)** graph topology governed by a **Canonical Architectural Contract (CAC)**.
- **5 Concurrent Low-Level Design (LLD) Synthesizers**: Parallel domain specialists generate technical specs for **Backend**, **Frontend**, **Database**, **Security**, and **Cloud Infrastructure**.
- **Redis Central Backbone**: Decouples generation from validation via an asynchronous FIFO task queue, in-memory artifact staging, LLM response caching (<5ms), and a real-time Pub/Sub event bus.
- **Autonomous Validator Engine v2**: An independent quality gate operating a continuous background queue worker to audit architectures across a 4-layer rubric ($C, R, W, D$), cross-referencing real-world enterprise models and producing automated self-correction plans.
- **Multi-Model Benchmark Suite**: Compares Archova.ai against direct single-shot commercial baselines (ChatGPT / GPT-4o, Google Gemini 2.0 Flash, Nvidia Nemotron 3.5).
- **Ultra-HD 300 DPI Visual Export**: Generates crystal-clear 3x Retina PNG and JPEG architectural diagrams for whitepapers and presentations.

---

## 🏛️ System Architecture

Archova.ai adopts a high-throughput, event-driven microservices architecture connecting the Next.js 16 Web Application, the FastAPI AI Engine, the independent Validator Engine v2, the Redis messaging backbone, Supabase persistence, and the Qdrant vector database.

### High-Level Architecture Flow (HLD)

```mermaid
flowchart LR
    CLIENT["Client<br/>(Next.js Web UI)"] -->|"HTTP"| NEXT_ROUTE["Next.js Route<br/>(/api/ai/...)"]
    
    NEXT_ROUTE <-->|"Auth / Chat History"| DB[("DB Supabase<br/>(PostgreSQL)")]
    
    NEXT_ROUTE -->|"Call / Prompt"| AI_ENGINE["AI Engine<br/>(:8000)"]
    
    AI_ENGINE -->|"Task Queue & Events"| REDIS_PUBSUB[("Redis Pub/Sub<br/>& Task Queue")]
    
    REDIS_PUBSUB -->|"Worker BLPOP"| VAL_ENGINE["Validation Engine<br/>(:8002)"]
    
    VAL_ENGINE -->|"Store Scores & Audits"| REDIS_STORE[("Redis Store<br/>(RAM Cache)")]
    
    REDIS_STORE -.->|"SSE Live Stream"| NEXT_ROUTE
    
    AI_ENGINE <-->|"RAG Architecture Context"| QDRANT[("Qdrant<br/>Vector DB")]
    VAL_ENGINE <-->|"Reference Grounding"| QDRANT
```

---

## 🔄 End-to-End Component & Data Flow

| Component | Port / Route | Responsibility & Data Flow |
|---|---|---|
| **1. Client (Next.js Web UI)** | `:3000` | User enters prompts, uploads design documents/OCR images, conducts clarification interviews, inspects `@xyflow/react` topologies, and reviews audit reports. |
| **2. Next.js Route Handlers** | `/api/ai/...` | Authenticates incoming requests via Supabase JWT cookies, injects user context, proxies generation requests to the AI Engine, and maintains Server-Sent Events (SSE) connections. |
| **3. DB Supabase (PostgreSQL)** | Port `5432` / Cloud | Persists user chat sessions, historical prompt iterations, and final verified architecture packages with strict Row-Level Security (RLS). |
| **4. AI Engine Core** | `:8000` | FastAPI service running the multi-agent swarm: Clarifier Agent, ARSRS Synthesizer, HLD Architect, 5 Parallel LLD Specialists, and Direct LLM benchmark runner. |
| **5. Redis Pub/Sub & Queue** | `:6379` / Upstash TLS | Central broker. The AI Engine pushes generated artifacts and validation jobs via `RPUSH`. The Validator Worker dequeues tasks via `BLPOP`. Events broadcast over `channel:{id}`. |
| **6. Validation Engine v2** | `:8002` | Standalone auditing microservice. Pulls staged artifacts from Redis RAM, runs 4-layer rubric checks ($C, R, W, D$), and formulates automated self-correction proposals. |
| **7. Redis Store (In-Memory RAM)** | `:6379` / Upstash TLS | High-speed cache storing intermediate tier validation scores (`archova:{id}:val:{tier}`) and raw staged JSON trees, eliminating disk I/O bottlenecks. |
| **8. SSE Live Stream (Return Line)** | `/api/ai/stream` | Redis Pub/Sub events stream back to the Next.js API route, pushing real-time log lines and gauge updates to the browser terminal without client polling. |
| **9. Qdrant Vector DB** | `:6333` / Cloud | Houses dense vector embeddings of verified enterprise design patterns and failure modes. Enriches AI generation prompts (**RAG Context**) and audits designs against real-world systems (**Reference Grounding**). |

---

## ⚡ Redis Distributed Memory & Event Backbone

Redis acts as the **central nervous system** of Archova.ai. Instead of burdening the primary database with rapid transient writes or forcing the user to wait for slow sequential generation, Redis provides 6 distinct operational capabilities:

| # | Redis Capability | Key / Channel Pattern | Data Structure | Operational Flow |
|---|---|---|---|---|
| **1** | **LLM Response Semantic Cache** | `llm:{model}:{sha256(prompt)}` | `String (JSON)`<br/>*(TTL: 24h)* | Prevents redundant external LLM calls. If identical prompt inputs are submitted, returns completions in **< 5ms**. |
| **2** | **Validation FIFO Task Queue** | `archova:validation:queue` | `List (FIFO)`<br/>*(`RPUSH` / `BLPOP`)* | Decouples artifact generation from validation. When HLD or any of the 5 LLDs finish generating, the task is enqueued immediately. |
| **3** | **Zero-Disk In-Memory Artifact Store** | `archova:{gen_id}:artifact:{tier}` | `String (JSON)`<br/>*(TTL: 2h)* | Stages transient multi-megabyte JSON trees (ARSRS, HLD, CAC, LLDs) directly in RAM. Downstream validator workers read them with zero disk I/O. |
| **4** | **Progressive Tier Validation Audits** | `archova:{gen_id}:val:{tier}` | `String (JSON)`<br/>*(TTL: 2h)* | Holds intermediate verification audits and rubric scores for each tier as soon as they complete, allowing progressive UI display. |
| **5** | **Real-Time Event Pub/Sub Bus** | `channel:{generation_id}` | `Pub/Sub Channel` | Broadcasts `TIER_VALIDATED`, `COMPOSITE_VALIDATED`, and agent logs directly to FastAPI SSE endpoints for instant browser streaming. |
| **6** | **Pipeline State Tracker** | `gen:{generation_id}:status` | `String (JSON)`<br/>*(TTL: 2h)* | Tracks active stages (`IN_PROGRESS`, `SYNTHESIZING_HLD`, `GENERATING_LLDS`, `COMPLETED`), agent telemetry, and worker heartbeats. |

---

## 🚀 The 5 Pipeline Stages

Archova.ai organizes software architecture synthesis into five progressive, structured steps:

### Stage 1: Problem Ingestion & Multimodal Document Parsing
- **Natural Language Prompts**: Accepts high-level problem statements (e.g., *"Design a fault-tolerant online quiz and proctoring platform handling 500k concurrent students"*).
- **Document Ingestion**: Parses uploaded project documentation (`.pdf`, `.docx`, `.txt`, `.md`).
- **Tesseract OCR**: Extracts textual specifications from hand-drawn sketches or legacy architectural diagrams (`.png`, `.jpg`, `.jpeg`).

### Stage 2: Ambiguity Detection & Clarification Interview
- **11-Parameter Ambiguity Detection**: Flags vague, missing, or conflicting requirements across: *goal, core objectives, system type, actors, functional requirements, inputs, outputs, external services, system behaviour, non-functional requirements (NFRs), and free constraints*.
- **Interactive Multi-Turn Interview**: Generates a dynamic series of contextual multiple-choice questions with recommended architectural defaults to align requirements before synthesis.

### Stage 3: ARSRS Formal Specification Synthesis
- **IEEE-Aligned Spec**: Synthesizes a formal **Architecture-Ready Structured Requirements Specification (ARSRS)** document.
- **Specification Breakdown**: Scope boundaries, user personas, actor taxonomies, prioritized functional requirements ($FR_1 \dots FR_n$), latency/throughput NFRs, and compliance mandates.
- **Live In-Browser Editor**: Users can fine-tune requirements in both formatted UI and raw JSON modes with instantaneous validation.

### Stage 4: High-Level Design (HLD) & Canonical Architectural Contract (CAC)
- **Microservice Topology**: Decomposes the system into client apps, ingress gateways, domain microservices, message queues, distributed caches, and persistence databases.
- **Canonical Architectural Contract (CAC)**: Synthesizes a rigid contract defining exact service IDs, exposed endpoints, inter-service communication protocols (REST, gRPC, WebSocket, Kafka), and shared data models. Every downstream LLD agent is bound by this contract to eliminate cross-tier drift.
- **Interactive Canvas**: Rendered via React Flow (`@xyflow/react`) with hardware-accelerated 60fps pan/zoom, layer filters, and clickable node inspection.

### Stage 5: 5 Concurrent Low-Level Design (LLD) Synthesizers
All 5 LLD domain specialists execute in parallel using `asyncio.gather`:
1. **Backend LLD**: REST/gRPC endpoint specifications, controller methods, background Celery/Redis queues, circuit breaker thresholds, and distributed Redlock patterns.
2. **Frontend LLD**: Component hierarchy, state management stores (Zustand/Redux), client-side routing, data fetching hooks, and asset optimization.
3. **Database LLD**: Relational / NoSQL schemas, primary/foreign key relationships, B-Tree and GIN indexes, partitioning strategies, and database connection pooling.
4. **Security LLD**: Authentication (OAuth2, OIDC, JWT), Role-Based Access Control (RBAC), TLS 1.3 in transit, AES-256 at rest, OWASP Top 10 mitigation, and rate limiting algorithms.
5. **Cloud Infrastructure LLD**: VPC CIDR layout, public/private subnet segregation, multi-AZ deployment, Kubernetes/Docker manifests, and Terraform / OpenTofu Infrastructure-as-Code.

---

## 🛡️ Autonomous Validator Engine v2 & Rubric Scoring

The **Validator Engine v2** operates as a physically separated, objective verification microservice on port `8002`. It runs a continuous background worker loop consuming tasks from Redis via `BLPOP`.

### 4-Layer Verification Pipeline
1. **Layer 0 (Ingestion & Schema Normalizer)**: Normalizes incoming package payloads, validates structural schemas, and ensures all required fields are present.
2. **Layer 1 (Structural Evidence Extraction)**: Uses AST analysis to inspect code scaffolds, verifying bounded contexts, migration files, and zero-trust perimeter configurations.
3. **Layer 2 (Real-World Enterprise Grounding)**: Cross-references synthesized topologies against verified enterprise reference architectures stored in the Qdrant vector database.
4. **Layer 3 (Multi-Dimensional Rubric Decision)**: Computes four dimensional scores to calculate the final composite quality rating:
   $$\text{Final Score} = \text{round}\left(\frac{C + R + W - D}{3}\right)$$

| Dimension | Metric Focus | Description |
|---|---|---|
| **$C$ (Consistency)** | Structure & Standards | Validates strict conformance to the ARSRS specification and CAC contract. |
| **$R$ (Resilience)** | Architecture Review | Evaluates circuit breakers, retry backoffs, fault isolation, and rate-limiting. |
| **$W$ (Real-World)** | Benchmark Patterns | Compares synthesized components against verified production architectures. |
| **$D$ (Defect Deductions)** | Penalties | Heavy deduction for single points of failure, missing encryption, or concurrency gaps. |

### Automated AI Self-Correction Loop
If the Validator Engine detects architectural gaps (e.g., missing distributed lock on reservation state, absent rate limiter), it generates an **Actionable Correction Plan**. The user can approve proposed patches, triggering the AI Engine's Targeted Correction Agent to update the design without regenerating the entire architecture.

---

## 📊 Multi-Model Benchmark & Head-to-Head Comparison

Archova.ai includes a dedicated benchmark suite that compares the autonomous multi-agent output against direct single-shot prompt generations from leading commercial LLMs:

```
┌─────────────────────────────────┬───────────────────┬──────────────┬─────────────────────────────────────────────────────────────┐
│ Model Architecture              │ Execution Mode    │ Audit Score  │ Architectural Character & Trade-Offs                        │
├─────────────────────────────────┼───────────────────┼──────────────┼─────────────────────────────────────────────────────────────┤
│ 🏆 Archova.ai (SAE Multi-Agent) │ 14+ Agents + CAC  │ 90% APPROVED │ Full 6-tier contract, zero-trust mTLS, multi-AZ resilience  │
│ 🤖 ChatGPT / GPT-4o             │ Direct 1-Shot     │ 76% COND.    │ Strong REST schemas; omits multi-region failover & DLQs     │
│ ⚡ Google Gemini 2.0 Flash       │ Direct 1-Shot     │ 72% COND.    │ Good GCP cloud topology; omits DB lock semantics & retry    │
│ 🟢 Nvidia Nemotron 3.5          │ Direct 1-Shot     │ 66% COND.    │ Strong Kafka streaming ingest; weak frontend state & auth   │
└─────────────────────────────────┴───────────────────┴──────────────┴─────────────────────────────────────────────────────────────┘
```

---

## 🎨 Ultra-HD 300 DPI Visual Export

Architectural diagrams in both the High-Level Design (HLD) canvas and Low-Level Design (LLD) studio can be exported directly to high-resolution images via the **Download Design** dropdown:
- **3x Ultra-HD Retina Resolution**: Generates 300 DPI print-ready graphics (`pixelRatio: 3`).
- **Complete Node Bounding Box**: Captures all nodes, service groupings, and edge labels even if they extend beyond the visible screen.
- **Anti-Aliasing Font Smoothing**: Leverages subpixel antialiasing and geometric precision text rendering.
- **Formats Supported**: PNG (lossless transparent) and JPEG (100% quality).

---

## 📂 Project Repository Structure

```
Archova.ai/
│
├── README.md                           # Master project documentation (this file)
├── PROJECT_DETAILS.md                  # Comprehensive technical whitepaper & specifications
├── render.yaml                         # One-click multi-service deployment for Render
│
├── next_app/                           # Presentation & Application Layer (Next.js 16)
│   ├── app/
│   │   ├── api/
│   │   │   ├── ai/generate/            # Generation API router & token forwarder
│   │   │   ├── ai/stream/              # SSE live log streaming bridge
│   │   │   └── chat/                   # Session persistence endpoints
│   │   ├── chat/page.tsx               # Main 5-step architecture generation workbench
│   │   ├── signin/ & signup/           # User authentication pages
│   │   ├── landing.tsx                 # High-converting landing page
│   │   └── layout.tsx & globals.css    # Root layout & Tailwind v4 styles
│   ├── components/
│   │   ├── ArsrsEditor.tsx             # Interactive ARSRS specification editor
│   │   ├── ChatWindow.tsx              # Main chat interaction & prompt submission
│   │   ├── ComparisonView.tsx          # Multi-model head-to-head benchmark comparison
│   │   ├── DownloadDesignDropdown.tsx  # 3x Retina PNG / JPEG export dropdown
│   │   ├── HLDGraph.tsx                # React Flow High-Level Design visual canvas
│   │   ├── LLDGraph.tsx                # React Flow Low-Level Design visual canvas
│   │   ├── TerminalConsole.tsx         # Live SSE log streaming terminal
│   │   └── ValidationReportView.tsx    # 4-layer validation scorecard & audit view
│   ├── lib/
│   │   ├── ai-engine-client.ts         # Unified API client for FastAPI AI Engine
│   │   ├── download-design.ts          # High-resolution canvas snapshot engine
│   │   ├── graph-parser.ts             # Raw LLM JSON → React Flow nodes/edges parser
│   │   ├── store.ts                    # Global reactive state management (Zustand)
│   │   └── validator-client.ts         # HTTP client for Validator Engine v2
│   └── package.json                    # Next.js dependencies & scripts
│
├── ai_engine/                          # Core Intelligence & Synthesis Layer (FastAPI :8000)
│   ├── app/
│   │   ├── main.py                     # FastAPI application entrypoint & CORS
│   │   ├── api/routes/
│   │   │   ├── generations.py          # Pipeline execution & SSE streaming endpoints
│   │   │   └── interview.py            # Clarification interview endpoints
│   │   ├── core/
│   │   │   ├── redis_client.py         # Upstash Redis client (caching, queues, pub/sub)
│   │   │   └── queue_client.py         # Background worker queue manager
│   │   ├── ree/                        # Requirements Engineering Engine (REE)
│   │   │   └── agents/                 # Specialized requirement elicitation agents
│   │   ├── sae/                        # Software Architecture Engine (SAE)
│   │   │   ├── agents/                 # HLD Architect & 5 LLD Specialized Generators
│   │   │   └── cac.py                  # Canonical Architectural Contract generator
│   │   ├── rag/                        # Production Qdrant RAG Library
│   │   │   ├── retriever.py            # Vector search, MMR & category filtering
│   │   │   └── qdrant_manager.py       # Qdrant client lifecycle & collections
│   │   └── services/
│   │       ├── generation_service.py   # State machine for generation pipeline
│   │       └── direct_llm_generator.py # Multi-model benchmark execution service
│   ├── data/RAG/                       # 22 Architecture Knowledge Base Domains
│   └── requirements.txt                # Python dependencies for AI Engine
│
└── Validator_Engine_v2/                # Independent Quality Gate Service (FastAPI :8002)
    ├── main.py                         # Validator FastAPI entrypoint & health checks
    ├── pipeline.py                     # 4-layer validation pipeline engine
    ├── queue_worker.py                 # Continuous Redis BLPOP queue consumer
    ├── config.py                       # Validator thresholds & OpenRouter settings
    ├── schemas.py                      # Pydantic schemas for audits & reports
    ├── decision/                       # Layer 3: Rubric scoring & verdict evaluator
    ├── l0_normalize/                   # Layer 0: Schema normalizer
    ├── l1_evidence/                    # Layer 1: Structural evidence extraction
    ├── real_world/                     # Layer 2: Enterprise topology grounding
    └── requirements.txt                # Python dependencies for Validator Engine
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend UI** | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, Lucide React |
| **Interactive Graph Canvas** | `@xyflow/react` (React Flow v12), HTML5 Canvas, `html-to-image` |
| **Client State Management** | Zustand (with bounded 400-entry log buffers & memoized selectors) |
| **Backend AI Engine** | FastAPI, Python 3.11, Pydantic v2, Uvicorn, Asyncio |
| **Validator Engine v2** | FastAPI, Python 3.11, AST Analysis, OpenAPI Spec Validator |
| **In-Memory & Messaging** | Upstash Redis (Serverless TLS), Redis Queues (`BLPOP`), Redis Pub/Sub |
| **Vector Database & RAG** | Qdrant (Cloud / Local), SentenceTransformers (`bge-small-en-v1.5`) |
| **Persistence & Auth** | Supabase (PostgreSQL with Row-Level Security), Supabase Auth (JWT) |
| **Model Inference Gateway** | OpenRouter (Free tier optimized: Gemini 2.5 Flash, Nemotron 3.5), Local Ollama |

---

## 🚀 Quickstart & Local Setup

### Prerequisites
- **Node.js**: v18.18+ or v20+
- **Python**: v3.10+ (v3.11 recommended)
- **Redis**: Local Redis instance or free [Upstash Redis](https://upstash.com/) account
- **API Keys**: Free [OpenRouter](https://openrouter.ai/) API key for model inference

### 1. Clone the Repository
```bash
git clone https://github.com/Harshal-SL/Archova.ai.git
cd Archova.ai
```

### 2. Configure Environment Variables
Create a root `.env` file (or populate existing template):
```env
# Model Inference (OpenRouter Free Tier)
OPENROUTER_API_KEY=sk-or-v1-your-key-here
LLM_MODEL=google/gemini-2.5-flash-lite:free
VALIDATOR_MODEL=nvidia/nemotron-3.5-lightning:free

# Redis (Upstash Serverless TLS or local)
REDIS_URL=rediss://default:your-token@your-host.upstash.io:6379

# Service Endpoints
AI_ENGINE_URL=http://localhost:8000
NEXT_PUBLIC_AI_ENGINE_URL=http://localhost:8000
NEXT_PUBLIC_VALIDATOR_V2_URL=http://localhost:8002

# Supabase (Optional for local mock mode)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### 3. Run the Services

#### Terminal 1: AI Engine (:8000)
```bash
cd ai_engine
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Terminal 2: Validator Engine v2 (:8002)
```bash
cd Validator_Engine_v2
pip install -r requirements.txt
uvicorn Validator_Engine_v2.main:app --host 0.0.0.0 --port 8002 --reload
```

#### Terminal 3: Next.js Frontend (:3000)
```bash
cd next_app
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## ☁️ Production Deployment

Archova.ai is architected for zero-hassle cloud deployment:

- **Frontend**: Deploy the `next_app` directory to **Vercel** with one click.
  - Set `NEXT_PUBLIC_AI_ENGINE_URL=https://<your-ai-engine>.onrender.com`
  - Set `NEXT_PUBLIC_VALIDATOR_V2_URL=https://<your-validator-engine>.onrender.com`
- **AI Engine & Validator Engine**: Deploy directly to **Render** using the bundled `render.yaml` Blueprint.
  - `archova-ai-engine`: Runs `uvicorn app.main:app --app-dir ai_engine --host 0.0.0.0 --port $PORT`
  - `archova-validator-engine`: Runs `uvicorn Validator_Engine_v2.main:app --host 0.0.0.0 --port $PORT`
- **Redis**: Hosted on **Upstash Redis** (Serverless TLS, zero maintenance).
- **Database & Auth**: Hosted on **Supabase** (Managed PostgreSQL with automated backups).

---

## 📄 License & Attribution

This project was engineered as a Capstone / Major Project in Advanced Software Engineering & Multi-Agent Systems. Distributed under the **MIT License**.
