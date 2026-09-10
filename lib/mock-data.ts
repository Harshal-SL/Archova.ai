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
    system_name: "Education & Campus Library Management System",
    domain: "Higher Education & Digital Content Management",
    status: "APPROVED_FOR_ARCHITECTURE",
    generated_at: "2026-09-06T18:00:00.000Z",
  },
  system_overview: {
    problem_statement:
      "Build a modern College Library Management System with online catalog search, student self-service borrowing, inventory circulation tracking, reservation workflows, and automated overdue fine calculation.",
    architecture_pattern:
      "Modular Cloud Microservices with Reactive Event-Driven Ingestion & Distributed Cache",
    primary_actors: [
      "Student / Borrower",
      "Faculty Member",
      "Librarian / Circulation Staff",
      "System Administrator",
    ],
    clarified_specifications: {
      scaling_requirements:
        "High concurrency (10,000+ daily active campus users, 500 peak borrows/min)",
      primary_database:
        "PostgreSQL 16 Multi-AZ with PgBouncer connection pooling",
      caching_layer:
        "Redis 7.2 Cluster for session tokens and hot catalog queries",
      authentication_protocol:
        "OAuth2 PKCE with asymmetric RS256 JWT tokens & RBAC",
      deployment_target:
        "Kubernetes (EKS/GKE) with Ingress-NGINX and TLS 1.3 termination",
    },
  },
  functional_requirements: [
    {
      id: "FR-01",
      title: "Authentication & Role-Based Access Control (RBAC)",
      description:
        "Students, librarians, and faculty authenticate via campus SSO/OAuth2. Granular permissions govern catalog edits, borrowing limits, and overrides.",
      priority: "P0",
      compliance: "FERPA, OAuth2 RFC 7636",
    },
    {
      id: "FR-02",
      title: "Full-Text Catalog Search & Inventory Filtering",
      description:
        "Fast multi-attribute search across 100,000+ ISBN titles, authors, and genres with sub-50ms latency using PostgreSQL full-text indexing and Redis caching.",
      priority: "P0",
      compliance: "ISO 2709, MARC21 standard",
    },
    {
      id: "FR-03",
      title: "Circulation Lifecycle & Automated Overdue Reminders",
      description:
        "Manage book checkouts, returns, renewals, and holds. Automated event-driven notification queue dispatches email/SMS reminders before due dates.",
      priority: "P0",
      compliance: "ACID Transaction guarantees",
    },
    {
      id: "FR-04",
      title: "Fine Calculation & Digital Payment Gateway",
      description:
        "Automated daily fee calculation for overdue assets with waiver authorization controls and digital receipt reconciliation.",
      priority: "P1",
      compliance: "PCI-DSS Level 1 compliant gateway integration",
    },
    {
      id: "FR-05",
      title: "Administrative Analytics & Usage Auditing",
      description:
        "Comprehensive reporting on peak borrowing hours, underutilized titles, inventory turnover, and immutable audit logs of all role overrides.",
      priority: "P2",
      compliance: "SOC2 Type II data retention",
    },
  ],
  non_functional_requirements: {
    availability: "99.95% multi-zone high-availability SLA",
    latency:
      "P95 API response time < 80ms; in-memory cache lookups < 5ms under 5,000 RPS load",
    scalability:
      "Horizontal pod auto-scaling (min 3, max 15 pods) driven by CPU and request throughput metrics",
    security:
      "TLS 1.3 in-transit, AES-256 at-rest, Row-Level Security (RLS), and OWASP Top 10 WAF protections",
    data_integrity:
      "ACID guarantees for all transactional borrowing operations with distributed Redis redlock",
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
      entity_name: "Book Title",
      table_name: "books",
      primary_key: "id (UUID)",
      key_attributes: [
        "id",
        "isbn",
        "title",
        "author",
        "publisher",
        "total_copies",
        "available_copies",
      ],
    },
    {
      entity_name: "Loan Transaction",
      table_name: "loans",
      primary_key: "id (UUID)",
      key_attributes: [
        "id",
        "user_id",
        "book_id",
        "borrowed_at",
        "due_at",
        "returned_at",
        "fine_amount",
      ],
    },
    {
      entity_name: "Reservation / Hold",
      table_name: "reservations",
      primary_key: "id (UUID)",
      key_attributes: [
        "id",
        "user_id",
        "book_id",
        "queue_position",
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
    question: "What is your projected concurrent user scale and expected peak transaction volume?",
    priority: "high",
    rationale:
      "Determines horizontal pod autoscaling parameters, caching tier size, and database connection pooling.",
    options: [
      "Campus Scale (10,000+ daily active users, 500 requests/sec peak)",
      "Department Scale (<1,000 daily users, low write throughput)",
      "Multi-University Enterprise (100,000+ users, geo-distributed clustering)",
    ],
    default_option: "Campus Scale (10,000+ daily active users, 500 requests/sec peak)",
  },
  {
    question_id: "Q-DATA-02",
    question: "What data consistency model is required for book reservations and checkout transactions?",
    priority: "high",
    rationale:
      "Ensures strict ACID compliance prevents double-borrowing of single copies under concurrent requests.",
    options: [
      "Strict ACID Transactions (PostgreSQL with Serializable Isolation & Redis Redlock)",
      "Eventual Consistency with Optimistic Locking (NoSQL Document Store)",
      "Hybrid Transactional/Analytical (PostgreSQL + ClickHouse)",
    ],
    default_option: "Strict ACID Transactions (PostgreSQL with Serializable Isolation & Redis Redlock)",
  },
  {
    question_id: "Q-AUTH-03",
    question: "Which authentication and authorization architecture should be provisioned for user access?",
    priority: "medium",
    rationale:
      "Establishes identity federation, token lifetimes, and Role-Based Access Control (RBAC).",
    options: [
      "OAuth2 PKCE with Campus SSO Federation & RS256 JWT (Recommended)",
      "Stateless Session Cookies with Redis Token Blacklist",
      "LDAP / Active Directory Integration with SAML 2.0",
    ],
    default_option: "OAuth2 PKCE with Campus SSO Federation & RS256 JWT (Recommended)",
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
