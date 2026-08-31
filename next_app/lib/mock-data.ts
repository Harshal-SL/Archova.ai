import type { Node, Edge } from "@xyflow/react";
import { parseHldToReactFlow, parseLldToReactFlow } from "./graph-parser";
import { dummyHld, dummyAllLlds } from "./dummy-data";

const initialGraph = parseHldToReactFlow(dummyHld);

export const hldNodes: Node[] = initialGraph.nodes;
export const hldEdges: Edge[] = initialGraph.edges;

// ── 5 LLD Fallback Diagrams (Backend, Frontend, Database, Security, Cloud) ──
export const lldData: Record<string, { nodes: Node[]; edges: Edge[] }> = {
  backend: parseLldToReactFlow("backend", dummyAllLlds.backend),
  frontend: parseLldToReactFlow("frontend", dummyAllLlds.frontend),
  database: parseLldToReactFlow("database", dummyAllLlds.database),
  cloud: parseLldToReactFlow("cloud", dummyAllLlds.cloud),
  security: parseLldToReactFlow("security", dummyAllLlds.security),
};

export const dummyHldData = dummyHld;
export const dummyAllLldData = dummyAllLlds;

// ── Explanations ──
export const explanations: Record<string, string> = {
  frontend:
    "The Frontend layer handles all user-facing interactions. Built with Next.js 16 and React, it provides server-side rendering, client-side interactivity, and responsive Tailwind styling.",
  gateway:
    "The API Gateway acts as the single entry point for all client requests. It handles authentication, rate limiting, SSL termination, and routes requests to downstream microservices.",
  backend:
    "The Core Services layer contains domain-specific business logic. Built as modular microservices, services communicate synchronously via REST/gRPC and asynchronously via RabbitMQ.",
  database:
    "The Database layer provides ACID transactional persistence. Built with PostgreSQL 16 with separate schemas per service and PgBouncer connection pooling.",
  cache:
    "The Redis 7.2 Cluster provides sub-millisecond in-memory caching for high-frequency queries and distributed session token storage.",
  security:
    "The Security tier enforces OAuth2 authorization code flows, asymmetric JWT RS256 token verification, and granular Role-Based Access Control (RBAC).",
  cloud:
    "The Cloud Infrastructure layer provisions AWS ECS Fargate serverless container tasks, Multi-AZ RDS PostgreSQL, Route 53 DNS, and ALB Ingress.",
};
