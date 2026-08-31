# ArchAI — AI System Architecture Engine

ArchAI is an end-to-end multi-agent AI System Architecture generation platform built entirely with **Next.js 16 (App Router)**, React 19, TypeScript, Tailwind CSS, and React Flow.

It automatically generates:
1. **Interactive Stakeholder Clarification Interview** (REE - Requirements Engineering Engine)
2. **Formal ARSRS Specification Document** (Architecture-Ready Structured Requirements Specification)
3. **Interactive Visual High-Level Design (HLD)** graph topology
4. **5 Low-Level Designs (LLDs)** across Backend, Frontend, Database, Security, and Cloud
5. **Real-time Pipeline Terminal** with Server-Sent Events (SSE) log streaming

---

## Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Environment Variables (Optional)
Create `.env.local` with your Supabase credentials:
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_AI_ENGINE_URL=http://localhost:8000
```

### 3. Run the Application
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Native API Endpoints

The architecture engine is integrated directly into Next.js App Router API routes:

- `GET /api/v1/health` — Engine readiness and active sessions health check
- `POST /api/v1/generations` — Initialize generation session & problem analysis
- `POST /api/v1/generations/[id]/answers` — Submit clarifying interview answers
- `POST /api/v1/generations/[id]/generate` — Synthesize ARSRS & HLD specifications
- `GET /api/v1/generations/[id]/lld/[type]` — Fetch domain-specific LLD (backend, frontend, database, security, cloud)
- `GET /api/v1/generations/[id]/status` — Session & LLD completion status
- `GET /api/v1/generations/[id]/logs` — Historical execution logs
- `GET /api/v1/generations/[id]/logs/stream` — Real-time Server-Sent Events (SSE) log streaming
