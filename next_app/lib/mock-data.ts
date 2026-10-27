import type { Node, Edge } from "@xyflow/react";
import { parseHldToReactFlow, parseLldToReactFlow } from "./graph-parser";
import { dummyHld, dummyAllLlds } from "./dummy-data";
import type { InterviewQuestion } from "./ai-engine-client";

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

// ── Sample ARSRS Document ──
export const dummyArsrs = {
  metadata: {
    document_type: "ARSRS (Architecture-Ready Structured Requirements Specification)",
    version: "2.5.0",
    system_name: "Enterprise Video Streaming & Transcoding Platform",
    domain: "Cloud Video Streaming & Content Distribution",
    status: "APPROVED_FOR_ARCHITECTURE",
    generated_at: "2026-10-16T15:00:00.000Z",
  },
  system_overview: {
    problem_statement:
      "Build a high-scale Enterprise Video Streaming Platform with adaptive bitrate transcoding, CDN edge distribution, subscription billing, and real-time viewer analytics.",
    architecture_pattern:
      "Event-Driven Microservices with Distributed CDN & In-Memory Cache",
    primary_actors: [
      "Viewer / Subscriber",
      "Content Creator",
      "Platform Administrator",
    ],
    clarified_specifications: {
      scaling_requirements:
        "High concurrency (100,000+ concurrent viewers, 50,000 peak stream requests/sec)",
      primary_database:
        "PostgreSQL 16 Multi-AZ with PgBouncer connection pooling",
      caching_layer:
        "Redis 7.2 Cluster for session tokens and streaming manifest cache",
      authentication_protocol:
        "OAuth2 PKCE with asymmetric RS256 JWT tokens & RBAC",
      deployment_target:
        "AWS ECS Fargate with CloudFront CDN and TLS 1.3 termination",
    },
  },
  functional_requirements: [
    {
      id: "FR-01",
      title: "Authentication & Role-Based Access Control (RBAC)",
      description:
        "Viewers, creators, and administrators authenticate via OAuth2 PKCE. Granular permissions govern media uploads, stream access, and billing management.",
      priority: "P0",
      compliance: "OAuth2 RFC 7636, SOC2",
    },
    {
      id: "FR-02",
      title: "Video Ingestion & Adaptive Bitrate Transcoding",
      description:
        "Fast multipart media uploads with automated background transcoding into 1080p, 720p, 480p, and 360p HLS streaming manifests.",
      priority: "P0",
      compliance: "HLS / MPEG-DASH standard",
    },
    {
      id: "FR-03",
      title: "Global CDN Edge Delivery & Signed URL Authorization",
      description:
        "Low-latency global edge caching via CloudFront with regional geo-restriction checks and signed streaming tokens.",
      priority: "P0",
      compliance: "Sub-100ms first-chunk playback",
    },
    {
      id: "FR-04",
      title: "Subscription Billing & Tiered Membership",
      description:
        "Recurring subscription billing with automated card payment processing, tier upgrades/downgrades, and proration calculations.",
      priority: "P1",
      compliance: "PCI-DSS Level 1 compliant gateway integration",
    },
    {
      id: "FR-05",
      title: "Real-Time Viewing Analytics & Engagement Telemetry",
      description:
        "Live aggregation of concurrent stream viewers, buffer health telemetry, and regional engagement analytics.",
      priority: "P2",
      compliance: "GDPR, telemetry retention policy",
    },
  ],
  non_functional_requirements: {
    availability: "99.99% multi-zone high-availability SLA",
    latency:
      "P95 API response time < 80ms; video manifest fetch < 30ms under 50,000 RPS load",
    scalability:
      "Horizontal pod auto-scaling (min 3, max 15 pods) driven by CPU and stream concurrency metrics",
    security:
      "TLS 1.3 in-transit, AES-256 at-rest, Row-Level Security (RLS), and OWASP Top 10 WAF protections",
    data_integrity:
      "ACID guarantees for subscription billing with distributed Redis redlock",
    disaster_recovery:
      "RPO < 1 minute via streaming WAL replication; RTO < 15 minutes with automated multi-region failover",
  },
  domain_entities: [
    {
      entity_name: "User Account",
      table_name: "users",
      primary_key: "id (UUID)",
      key_attributes: ["id", "email", "name", "role", "created_at", "status"],
    },
    {
      entity_name: "Video Asset",
      table_name: "video_assets",
      primary_key: "id (UUID)",
      key_attributes: [
        "id",
        "user_id",
        "title",
        "manifest_url",
        "status",
        "duration_seconds",
        "created_at",
      ],
    },
    {
      entity_name: "Transcoding Job",
      table_name: "transcoding_jobs",
      primary_key: "id (UUID)",
      key_attributes: [
        "id",
        "video_id",
        "resolution",
        "status",
        "progress_percent",
        "created_at",
      ],
    },
    {
      entity_name: "Subscription Membership",
      table_name: "subscriptions",
      primary_key: "id (UUID)",
      key_attributes: [
        "id",
        "user_id",
        "plan_tier",
        "status",
        "expires_at",
      ],
    },
  ],
};

// ── Sample Interactive Questions for Frontend Walkthrough ──
export const sampleInterviewQuestions: InterviewQuestion[] = [
  {
    question_id: "Q-SCALE-01",
    question: "What is your projected concurrent viewer scale and peak video streaming bandwidth?",
    priority: "high",
    rationale:
      "Determines CDN edge caching topology, transcoding cluster worker sizing, and database connection pooling.",
    options: [
      "Global Platform (100,000+ concurrent viewers, 50 Gbps peak throughput)",
      "Regional Platform (10,000+ concurrent viewers, 5 Gbps peak throughput)",
      "Enterprise Private Studio (<1,000 viewers, internal high security)",
    ],
    default_option: "Global Platform (100,000+ concurrent viewers, 50 Gbps peak throughput)",
  },
  {
    question_id: "Q-DATA-02",
    question: "What data persistence model is required for subscription transactions and viewer telemetry?",
    priority: "high",
    rationale:
      "Ensures ACID consistency for billing while providing high-throughput ingest for viewing event streams.",
    options: [
      "Strict ACID for Billing (PostgreSQL 16) + In-Memory Telemetry Stream (Redis Cluster)",
      "Single Relational Database for all workloads",
      "Distributed NoSQL Document Store with Eventual Consistency",
    ],
    default_option: "Strict ACID for Billing (PostgreSQL 16) + In-Memory Telemetry Stream (Redis Cluster)",
  },
  {
    question_id: "Q-AUTH-03",
    question: "Which authentication and authorization architecture should be provisioned for subscriber access?",
    priority: "medium",
    rationale:
      "Establishes identity federation, signed playback tokens, and Role-Based Access Control (RBAC).",
    options: [
      "OAuth2 PKCE with Asymmetric RS256 JWT & Signed CDN URLs (Recommended)",
      "Stateless Session Cookies with Redis Token Blacklist",
      "SAML 2.0 Enterprise Identity Federation",
    ],
    default_option: "OAuth2 PKCE with Asymmetric RS256 JWT & Signed CDN URLs (Recommended)",
  },
];

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
