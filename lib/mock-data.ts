import type { Node, Edge } from "@xyflow/react";

function nodeStyle(color: string) {
  return {
    background: `linear-gradient(135deg, ${color}, ${color}dd)`,
    color: "#fff",
    borderRadius: 14,
    padding: "12px 20px",
    fontWeight: 600,
    fontSize: 13,
    border: "none",
    boxShadow: `0 6px 20px ${color}55`,
    minWidth: 150,
    textAlign: "center" as const,
  };
}

// ── Default Initial HLD Nodes & Edges ──
export const hldNodes: Node[] = [
  {
    id: "frontend",
    data: { label: "Frontend Layer", description: "Next.js App Router client & server components with Tailwind CSS" },
    position: { x: 160, y: 30 },
    style: nodeStyle("#6366f1"),
  },
  {
    id: "gateway",
    data: { label: "API Gateway", description: "Edge routing, rate limiting, and request orchestration" },
    position: { x: 160, y: 150 },
    style: nodeStyle("#3b82f6"),
  },
  {
    id: "backend",
    data: { label: "Core Services", description: "Modular microservices for business logic and workflows" },
    position: { x: 160, y: 270 },
    style: nodeStyle("#0ea5e9"),
  },
  {
    id: "database",
    data: { label: "Primary Database", description: "Supabase PostgreSQL with ACID compliance and RLS" },
    position: { x: 30, y: 390 },
    style: nodeStyle("#10b981"),
  },
  {
    id: "cache",
    data: { label: "Redis Cache & Queue", description: "Low-latency in-memory cache and background job queues" },
    position: { x: 290, y: 390 },
    style: nodeStyle("#f59e0b"),
  },
  {
    id: "security",
    data: { label: "Security & Auth", description: "JWT tokens, OAuth 2.0 provider, and RBAC policies" },
    position: { x: 30, y: 510 },
    style: nodeStyle("#ec4899"),
  },
  {
    id: "cloud",
    data: { label: "Cloud Infrastructure", description: "Containerized deployment with auto-scaling and CDN" },
    position: { x: 290, y: 510 },
    style: nodeStyle("#8b5cf6"),
  },
];

export const hldEdges: Edge[] = [
  { id: "e-fe-gw", source: "frontend", target: "gateway", animated: true, style: { stroke: "#6366f1", strokeWidth: 2 } },
  { id: "e-gw-be", source: "gateway", target: "backend", animated: true, style: { stroke: "#3b82f6", strokeWidth: 2 } },
  { id: "e-be-db", source: "backend", target: "database", animated: true, style: { stroke: "#10b981", strokeWidth: 2 } },
  { id: "e-be-cache", source: "backend", target: "cache", animated: true, style: { stroke: "#f59e0b", strokeWidth: 2 } },
  { id: "e-be-sec", source: "backend", target: "security", animated: true, style: { stroke: "#ec4899", strokeWidth: 2 } },
  { id: "e-be-cloud", source: "backend", target: "cloud", animated: true, style: { stroke: "#8b5cf6", strokeWidth: 2 } },
];

// ── 5 LLD Fallback Diagrams (Backend, Frontend, Database, Security, Cloud) ──
export const lldData: Record<string, { nodes: Node[]; edges: Edge[] }> = {
  backend: {
    nodes: [
      { id: "api-router", data: { label: "API Router" }, position: { x: 120, y: 20 }, style: nodeStyle("#0ea5e9") },
      { id: "middleware", data: { label: "Auth & Rate Limit" }, position: { x: 120, y: 140 }, style: nodeStyle("#0284c7") },
      { id: "controllers", data: { label: "Service Controllers" }, position: { x: 20, y: 260 }, style: nodeStyle("#38bdf8") },
      { id: "orm", data: { label: "Prisma / Data Access" }, position: { x: 220, y: 260 }, style: nodeStyle("#0369a1") },
    ],
    edges: [
      { id: "l-ar-mw", source: "api-router", target: "middleware", animated: true, style: { stroke: "#0ea5e9" } },
      { id: "l-mw-ct", source: "middleware", target: "controllers", animated: true, style: { stroke: "#0ea5e9" } },
      { id: "l-ct-orm", source: "controllers", target: "orm", animated: true, style: { stroke: "#0ea5e9" } },
    ],
  },
  frontend: {
    nodes: [
      { id: "next-app", data: { label: "Next.js App Router" }, position: { x: 120, y: 20 }, style: nodeStyle("#ec4899") },
      { id: "ui-components", data: { label: "Tailwind UI Components" }, position: { x: 20, y: 140 }, style: nodeStyle("#db2777") },
      { id: "state-store", data: { label: "Zustand Global Store" }, position: { x: 220, y: 140 }, style: nodeStyle("#f472b6") },
      { id: "sse-client", data: { label: "SSE Log Streamer" }, position: { x: 120, y: 260 }, style: nodeStyle("#be185d") },
    ],
    edges: [
      { id: "l-nx-ui", source: "next-app", target: "ui-components", animated: true, style: { stroke: "#ec4899" } },
      { id: "l-nx-st", source: "next-app", target: "state-store", animated: true, style: { stroke: "#ec4899" } },
      { id: "l-st-sse", source: "state-store", target: "sse-client", animated: true, style: { stroke: "#ec4899" } },
    ],
  },
  database: {
    nodes: [
      { id: "pg-primary", data: { label: "PostgreSQL Database" }, position: { x: 120, y: 20 }, style: nodeStyle("#10b981") },
      { id: "tables-schema", data: { label: "Relational Schema & FKs" }, position: { x: 20, y: 140 }, style: nodeStyle("#059669") },
      { id: "indices-perf", data: { label: "B-Tree Indexes" }, position: { x: 220, y: 140 }, style: nodeStyle("#34d399") },
      { id: "rls-policies", data: { label: "Row Level Security" }, position: { x: 120, y: 260 }, style: nodeStyle("#047857") },
    ],
    edges: [
      { id: "l-pg-tb", source: "pg-primary", target: "tables-schema", animated: true, style: { stroke: "#10b981" } },
      { id: "l-pg-idx", source: "pg-primary", target: "indices-perf", animated: true, style: { stroke: "#10b981" } },
      { id: "l-tb-rls", source: "tables-schema", target: "rls-policies", animated: true, style: { stroke: "#10b981" } },
    ],
  },
  security: {
    nodes: [
      { id: "jwt-engine", data: { label: "JWT Token Engine" }, position: { x: 120, y: 20 }, style: nodeStyle("#f43f5e") },
      { id: "oauth-providers", data: { label: "OAuth 2.0 (Google/GitHub)" }, position: { x: 20, y: 140 }, style: nodeStyle("#e11d48") },
      { id: "rbac-rules", data: { label: "RBAC & Permissions" }, position: { x: 220, y: 140 }, style: nodeStyle("#fb7185") },
      { id: "encryption", data: { label: "TLS 1.3 & AES-256" }, position: { x: 120, y: 260 }, style: nodeStyle("#be123c") },
    ],
    edges: [
      { id: "l-jwt-oa", source: "jwt-engine", target: "oauth-providers", animated: true, style: { stroke: "#f43f5e" } },
      { id: "l-jwt-rb", source: "jwt-engine", target: "rbac-rules", animated: true, style: { stroke: "#f43f5e" } },
      { id: "l-rb-enc", source: "rbac-rules", target: "encryption", animated: true, style: { stroke: "#f43f5e" } },
    ],
  },
  cloud: {
    nodes: [
      { id: "cloud-vpc", data: { label: "VPC & Subnets" }, position: { x: 120, y: 20 }, style: nodeStyle("#8b5cf6") },
      { id: "k8s-cluster", data: { label: "Kubernetes / Containers" }, position: { x: 20, y: 140 }, style: nodeStyle("#7c3aed") },
      { id: "cdn-dns", data: { label: "Cloudflare CDN & WAF" }, position: { x: 220, y: 140 }, style: nodeStyle("#a78bfa") },
      { id: "observability", data: { label: "Prometheus & Grafana" }, position: { x: 120, y: 260 }, style: nodeStyle("#6d28d9") },
    ],
    edges: [
      { id: "l-vpc-k8s", source: "cloud-vpc", target: "k8s-cluster", animated: true, style: { stroke: "#8b5cf6" } },
      { id: "l-vpc-cdn", source: "cloud-vpc", target: "cdn-dns", animated: true, style: { stroke: "#8b5cf6" } },
      { id: "l-k8s-obs", source: "k8s-cluster", target: "observability", animated: true, style: { stroke: "#8b5cf6" } },
    ],
  },
};

// ── Explanations ──
export const explanations: Record<string, string> = {
  frontend:
    "The Frontend layer handles all user-facing interactions. Built with Next.js 16 and React, it provides server-side rendering, client-side interactivity, and responsive Tailwind styling.",
  gateway:
    "The API Gateway serves as the single entry point for client requests, providing intelligent routing, authentication verification, rate limiting, and CORS handling.",
  backend:
    "The Backend core services implement the domain business logic, data validation, and asynchronous task orchestration.",
  database:
    "The Primary Database stores transactional and relational data using Supabase PostgreSQL with automated schema migrations and Row Level Security.",
  cache:
    "Redis caching minimizes latency for high-frequency queries and manages background job queues for asynchronous processing.",
  security:
    "Security architecture enforces strict authentication using JWT, OAuth 2.0 integrations, and fine-grained Role-Based Access Control (RBAC).",
  cloud:
    "Cloud infrastructure provides scalable containerized deployment, automated CI/CD pipelines, CDN edge caching, and real-time observability.",
};
