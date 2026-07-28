import type { Node, Edge } from "@xyflow/react";

// ── HLD ──
export const hldNodes: Node[] = [
  {
    id: "frontend",
    data: { label: "Frontend" },
    position: { x: 100, y: 0 },
    style: {
      background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
      color: "#fff",
      borderRadius: 12,
      padding: "12px 24px",
      fontWeight: 600,
      border: "none",
      boxShadow: "0 4px 14px rgba(99,102,241,.4)",
    },
  },
  {
    id: "backend",
    data: { label: "Backend" },
    position: { x: 100, y: 120 },
    style: {
      background: "linear-gradient(135deg, #3b82f6, #2563eb)",
      color: "#fff",
      borderRadius: 12,
      padding: "12px 24px",
      fontWeight: 600,
      border: "none",
      boxShadow: "0 4px 14px rgba(59,130,246,.4)",
    },
  },
  {
    id: "database",
    data: { label: "Database" },
    position: { x: 0, y: 260 },
    style: {
      background: "linear-gradient(135deg, #10b981, #059669)",
      color: "#fff",
      borderRadius: 12,
      padding: "12px 24px",
      fontWeight: 600,
      border: "none",
      boxShadow: "0 4px 14px rgba(16,185,129,.4)",
    },
  },
  {
    id: "vectordb",
    data: { label: "Vector DB" },
    position: { x: 200, y: 260 },
    style: {
      background: "linear-gradient(135deg, #f59e0b, #d97706)",
      color: "#fff",
      borderRadius: 12,
      padding: "12px 24px",
      fontWeight: 600,
      border: "none",
      boxShadow: "0 4px 14px rgba(245,158,11,.4)",
    },
  },
  {
    id: "ai-engine",
    data: { label: "AI Engine" },
    position: { x: 350, y: 120 },
    style: {
      background: "linear-gradient(135deg, #ec4899, #db2777)",
      color: "#fff",
      borderRadius: 12,
      padding: "12px 24px",
      fontWeight: 600,
      border: "none",
      boxShadow: "0 4px 14px rgba(236,72,153,.4)",
    },
  },
  {
    id: "auth",
    data: { label: "Auth Service" },
    position: { x: 350, y: 260 },
    style: {
      background: "linear-gradient(135deg, #8b5cf6, #7c3aed)",
      color: "#fff",
      borderRadius: 12,
      padding: "12px 24px",
      fontWeight: 600,
      border: "none",
      boxShadow: "0 4px 14px rgba(139,92,246,.4)",
    },
  },
];

export const hldEdges: Edge[] = [
  { id: "e-fe-be", source: "frontend", target: "backend", animated: true, style: { stroke: "#6366f1" } },
  { id: "e-be-db", source: "backend", target: "database", animated: true, style: { stroke: "#3b82f6" } },
  { id: "e-be-vec", source: "backend", target: "vectordb", animated: true, style: { stroke: "#f59e0b" } },
  { id: "e-be-ai", source: "backend", target: "ai-engine", animated: true, style: { stroke: "#ec4899" } },
  { id: "e-be-auth", source: "backend", target: "auth", animated: true, style: { stroke: "#8b5cf6" } },
];

// ── LLD per HLD node ──
export const lldData: Record<string, { nodes: Node[]; edges: Edge[] }> = {
  frontend: {
    nodes: [
      { id: "nextjs", data: { label: "Next.js" }, position: { x: 120, y: 0 }, style: nodeStyle("#6366f1") },
      { id: "tailwind", data: { label: "Tailwind CSS" }, position: { x: 0, y: 120 }, style: nodeStyle("#8b5cf6") },
      { id: "components", data: { label: "Component Structure" }, position: { x: 240, y: 120 }, style: nodeStyle("#a78bfa") },
      { id: "api-client", data: { label: "API Client" }, position: { x: 120, y: 240 }, style: nodeStyle("#c4b5fd") },
    ],
    edges: [
      { id: "l-nj-tw", source: "nextjs", target: "tailwind", animated: true, style: { stroke: "#8b5cf6" } },
      { id: "l-nj-co", source: "nextjs", target: "components", animated: true, style: { stroke: "#8b5cf6" } },
      { id: "l-co-ap", source: "components", target: "api-client", animated: true, style: { stroke: "#a78bfa" } },
    ],
  },
  backend: {
    nodes: [
      { id: "express", data: { label: "Express.js" }, position: { x: 120, y: 0 }, style: nodeStyle("#3b82f6") },
      { id: "rest-api", data: { label: "REST API" }, position: { x: 0, y: 120 }, style: nodeStyle("#2563eb") },
      { id: "middleware", data: { label: "Middleware" }, position: { x: 240, y: 120 }, style: nodeStyle("#1d4ed8") },
      { id: "controllers", data: { label: "Controllers" }, position: { x: 120, y: 240 }, style: nodeStyle("#60a5fa") },
    ],
    edges: [
      { id: "l-ex-ra", source: "express", target: "rest-api", animated: true, style: { stroke: "#3b82f6" } },
      { id: "l-ex-mw", source: "express", target: "middleware", animated: true, style: { stroke: "#3b82f6" } },
      { id: "l-ra-ct", source: "rest-api", target: "controllers", animated: true, style: { stroke: "#2563eb" } },
    ],
  },
  database: {
    nodes: [
      { id: "postgres", data: { label: "PostgreSQL" }, position: { x: 120, y: 0 }, style: nodeStyle("#10b981") },
      { id: "orm", data: { label: "Prisma ORM" }, position: { x: 0, y: 120 }, style: nodeStyle("#059669") },
      { id: "migrations", data: { label: "Migrations" }, position: { x: 240, y: 120 }, style: nodeStyle("#34d399") },
      { id: "seeds", data: { label: "Seed Data" }, position: { x: 120, y: 240 }, style: nodeStyle("#6ee7b7") },
    ],
    edges: [
      { id: "l-pg-or", source: "postgres", target: "orm", animated: true, style: { stroke: "#10b981" } },
      { id: "l-or-mg", source: "orm", target: "migrations", animated: true, style: { stroke: "#059669" } },
      { id: "l-or-sd", source: "orm", target: "seeds", animated: true, style: { stroke: "#059669" } },
    ],
  },
  vectordb: {
    nodes: [
      { id: "pinecone", data: { label: "Pinecone" }, position: { x: 120, y: 0 }, style: nodeStyle("#f59e0b") },
      { id: "embeddings", data: { label: "Embeddings" }, position: { x: 0, y: 120 }, style: nodeStyle("#d97706") },
      { id: "indexing", data: { label: "Indexing" }, position: { x: 240, y: 120 }, style: nodeStyle("#fbbf24") },
    ],
    edges: [
      { id: "l-pc-em", source: "pinecone", target: "embeddings", animated: true, style: { stroke: "#f59e0b" } },
      { id: "l-pc-ix", source: "pinecone", target: "indexing", animated: true, style: { stroke: "#f59e0b" } },
    ],
  },
  "ai-engine": {
    nodes: [
      { id: "llm", data: { label: "LLM (GPT-4)" }, position: { x: 120, y: 0 }, style: nodeStyle("#ec4899") },
      { id: "prompt-eng", data: { label: "Prompt Engineering" }, position: { x: 0, y: 120 }, style: nodeStyle("#db2777") },
      { id: "rag", data: { label: "RAG Pipeline" }, position: { x: 240, y: 120 }, style: nodeStyle("#f472b6") },
      { id: "output-parser", data: { label: "Output Parser" }, position: { x: 120, y: 240 }, style: nodeStyle("#f9a8d4") },
    ],
    edges: [
      { id: "l-ll-pe", source: "llm", target: "prompt-eng", animated: true, style: { stroke: "#ec4899" } },
      { id: "l-ll-rg", source: "llm", target: "rag", animated: true, style: { stroke: "#ec4899" } },
      { id: "l-rg-op", source: "rag", target: "output-parser", animated: true, style: { stroke: "#db2777" } },
    ],
  },
  auth: {
    nodes: [
      { id: "jwt", data: { label: "JWT Tokens" }, position: { x: 120, y: 0 }, style: nodeStyle("#8b5cf6") },
      { id: "oauth", data: { label: "OAuth 2.0" }, position: { x: 0, y: 120 }, style: nodeStyle("#7c3aed") },
      { id: "rbac", data: { label: "RBAC" }, position: { x: 240, y: 120 }, style: nodeStyle("#a78bfa") },
    ],
    edges: [
      { id: "l-jt-oa", source: "jwt", target: "oauth", animated: true, style: { stroke: "#8b5cf6" } },
      { id: "l-jt-rb", source: "jwt", target: "rbac", animated: true, style: { stroke: "#8b5cf6" } },
    ],
  },
};

function nodeStyle(color: string) {
  return {
    background: `linear-gradient(135deg, ${color}, ${color}dd)`,
    color: "#fff",
    borderRadius: 12,
    padding: "12px 24px",
    fontWeight: 600,
    border: "none",
    boxShadow: `0 4px 14px ${color}66`,
  };
}

// ── Explanations ──
export const explanations: Record<string, string> = {
  // HLD
  frontend:
    "The Frontend layer handles all user-facing interactions. Built with Next.js and React, it provides server-side rendering, client-side interactivity, and an optimized developer experience.",
  backend:
    "The Backend is the core server handling API requests, business logic, and orchestration between services. It uses Express.js with a layered architecture for scalability.",
  database:
    "The Database stores persistent application data. PostgreSQL is used for its reliability, ACID compliance, and rich querying capabilities via Prisma ORM.",
  vectordb:
    "The Vector DB (Pinecone) stores high-dimensional embeddings for semantic search and similarity matching, enabling RAG-based AI responses.",
  "ai-engine":
    "The AI Engine powers intelligent architecture generation using GPT-4 with prompt engineering and a RAG pipeline for context-aware, accurate outputs.",
  auth:
    "The Auth Service manages user authentication and authorization using JWT tokens, OAuth 2.0 for third-party login, and RBAC for fine-grained access control.",
  // LLD
  nextjs:
    "Next.js is used because it supports server-side rendering, fast routing, and optimized React performance. It enables both static and dynamic pages.",
  tailwind:
    "Tailwind CSS provides utility-first styling that enables rapid UI development with consistent design tokens and responsive layouts.",
  components:
    "The Component Structure follows atomic design principles — atoms, molecules, and organisms — for reusable, maintainable UI building blocks.",
  "api-client":
    "The API Client module centralizes all HTTP requests, handling authentication headers, error responses, and request/response transformations.",
  express:
    "Express.js is a minimal Node.js web framework that provides robust routing, middleware support, and easy integration with databases and services.",
  "rest-api":
    "The REST API layer defines endpoints following RESTful conventions with proper HTTP methods, status codes, and JSON payloads.",
  middleware:
    "Middleware handles cross-cutting concerns like authentication, logging, rate limiting, CORS, and request validation before reaching controllers.",
  controllers:
    "Controllers contain the business logic for each route, orchestrating calls to services, databases, and external APIs.",
  postgres:
    "PostgreSQL is a powerful open-source relational database known for data integrity, complex queries, and extensibility.",
  orm:
    "Prisma ORM provides type-safe database access, auto-generated migrations, and an intuitive data modeling syntax.",
  migrations:
    "Database migrations track schema changes over time, enabling version-controlled, reproducible database updates.",
  seeds:
    "Seed data provides initial dataset for development and testing, ensuring consistent starting state across environments.",
  pinecone:
    "Pinecone is a managed vector database optimized for similarity search at scale with low-latency queries.",
  embeddings:
    "Embeddings convert text into high-dimensional vectors that capture semantic meaning for similarity comparisons.",
  indexing:
    "Indexing organizes vectors for efficient nearest-neighbor search, balancing speed and accuracy.",
  llm:
    "GPT-4 is a large language model that generates human-quality text, powering the architecture generation and explanation features.",
  "prompt-eng":
    "Prompt Engineering crafts structured instructions to guide the LLM toward accurate, well-formatted architecture outputs.",
  rag:
    "The RAG (Retrieval-Augmented Generation) Pipeline retrieves relevant context from the vector store before generating responses.",
  "output-parser":
    "The Output Parser transforms raw LLM responses into structured JSON data for graph rendering and UI display.",
  jwt:
    "JWT (JSON Web Tokens) provide stateless authentication by encoding user identity and claims in signed tokens.",
  oauth:
    "OAuth 2.0 enables secure third-party authentication (Google, GitHub) without exposing user credentials.",
  rbac:
    "Role-Based Access Control restricts system access based on user roles, ensuring proper authorization for each action.",
};

// ── Mock AI responses ──
export const mockAIResponses: string[] = [
  "I've analyzed your requirements and generated a system architecture. The design follows a microservices pattern with clear separation of concerns.\n\nHere's what I've designed:\n• **Frontend**: Next.js with Tailwind CSS for a responsive, performant UI\n• **Backend**: Express.js REST API with middleware layers\n• **Database**: PostgreSQL with Prisma ORM\n• **Vector DB**: Pinecone for semantic search\n• **AI Engine**: GPT-4 with RAG pipeline\n• **Auth**: JWT + OAuth 2.0 with RBAC\n\nYou can explore the HLD and LLD in the Architecture Panel on the right. Click any node for details!",
  "Great question! I've updated the architecture to reflect your needs. The system uses a layered approach:\n\n1. **Presentation Layer** — React components with SSR\n2. **API Layer** — RESTful endpoints with validation\n3. **Business Layer** — Domain logic and orchestration\n4. **Data Layer** — PostgreSQL + Vector DB\n\nCheck the Architecture Panel to visualize the updated design.",
  "Based on best practices, I recommend this architecture pattern. It emphasizes:\n\n• **Scalability** — Horizontal scaling via microservices\n• **Security** — Multi-layer auth with JWT & RBAC\n• **Performance** — Caching, CDN, and optimized queries\n• **Maintainability** — Clean separation and typed interfaces\n\nThe architecture visualization is now available in the panel.",
];
