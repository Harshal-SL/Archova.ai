import type { Node, Edge } from "@xyflow/react";
import { getComponentTheme } from "./flow-colors";

function applyColorThemesToGraph(nodes: Node[], edges: Edge[]): { nodes: Node[]; edges: Edge[] } {
  const coloredNodes = nodes.map((n) => {
    if (n.type === "layerGroup") return n;
    const theme = getComponentTheme(n.id, (n.data?.label as string) || "", n.type, (n.data?.color as string) || undefined);
    return {
      ...n,
      data: {
        ...((n.data || {}) as Record<string, unknown>),
        color: theme.primary,
        themeColor: theme.primary,
      },
    };
  });

  const coloredEdges = edges.map((e) => {
    const srcTheme = getComponentTheme(e.source);
    return {
      ...e,
      style: {
        ...e.style,
        stroke: srcTheme.primary,
      },
      data: {
        ...((e.data || {}) as Record<string, unknown>),
        strokeColor: srcTheme.primary,
      },
    };
  });

  return { nodes: coloredNodes, edges: coloredEdges };
}

export interface ArchitecturalComponent {
  id: string;
  label: string;
  code?: string;
  category: "actor" | "frontend" | "gateway" | "service" | "database" | "cache" | "queue" | "devops";
  tech?: string;
  role?: string;
  description?: string;
  protocol?: string;
  schema?: string;
  engine?: string;
  group?: string;
}

/**
 * Intelligent HLD Parser & Hierarchical Layer Synthesizer
 * Converts any HLD JSON into a production-grade, multi-tier architectural topology (matching Image 2)
 */
export function parseHldToReactFlow(
  hldJson: Record<string, unknown> | null,
  rawPrompt?: string
): {
  nodes: Node[];
  edges: Edge[];
} {
  if (!hldJson || typeof hldJson !== "object") {
    return { nodes: [], edges: [] };
  }

  // 1. If explicit nodes & edges are provided
  if (
    Array.isArray(hldJson.nodes) &&
    hldJson.nodes.length > 0 &&
    (hldJson.nodes[0] as Record<string, unknown>).type
  ) {
    const nodes = (hldJson.nodes as Node[]).map((n) => ({
      ...n,
      type: n.type || "service",
    }));
    const edges = ((hldJson.edges || []) as Edge[]).map((e, idx) => ({
      ...e,
      id: e.id || `edge-${idx}`,
      type: "animatedFlow",
      animated: true,
    }));
    return applyColorThemesToGraph(nodes, edges);
  }

  // 2. Extract services from major_services or components
  const majorServices = Array.isArray(hldJson.major_services)
    ? (hldJson.major_services as Array<Record<string, unknown>>)
    : Array.isArray(hldJson.services)
    ? (hldJson.services as Array<Record<string, unknown>>)
    : null;

  const defaultServices = [
    { code: "SVC-01", label: "Authentication & Role Service", tech: "JWT · OAuth2 · RBAC Guard", db: "authentication_db_schema", desc: "Handles identity, credentials, tokens, and permissions." },
    { code: "SVC-02", label: "Catalog & Search Service", tech: "Elasticsearch · Query Engine", db: "catalog_db_schema", desc: "Fast indexing, book cataloging, metadata queries, and filtering." },
    { code: "SVC-03", label: "Circulation & Borrowing Service", tech: "ACID Transactions · Due Dates", db: "circulation_db_schema", desc: "Processes checkouts, returns, renewals, fines, and reservations." },
    { code: "SVC-04", label: "Notification & Reminder Service", tech: "Email · SMS · Push Alerts", db: "notification_db_schema", desc: "Dispatches automated reminders for due dates, holds, and fines." },
    { code: "SVC-05", label: "Inventory & Asset Service", tech: "RFID · Barcode Tracker", db: "inventory_db_schema", desc: "Tracks physical copy availability, shelf locations, barcodes, and damaged assets." },
    { code: "SVC-06", label: "Reporting & Analytics Service", tech: "Aggregations · BI Pipeline", db: "reporting_db_schema", desc: "Generates circulation metrics, overdue reports, and usage trends." },
  ];

  const microservices = majorServices && majorServices.length >= 3
    ? majorServices.slice(0, 6).map((s, idx) => ({
        code: String(s.service_id || `SVC-0${idx + 1}`),
        label: String(s.name || `Service ${idx + 1}`),
        tech: String(s.database_binding || s.responsibility || "Microservice"),
        db: String(s.database_binding || `service_${idx + 1}_db`),
        desc: String(s.responsibility || `${s.name} core business logic.`),
      }))
    : defaultServices;

  const nodes: Node[] = [];

  // ── 4 Systematic Architecture Divisions (Spacious Master Bounding Containers) ──
  // 1. Frontend Division (Top Center)
  nodes.push({
    id: "group-frontend",
    type: "layerGroup",
    data: {
      label: "Frontend Division",
      division: "frontend",
      count: 4,
      subtitle: "Actors · Web App · API Gateway",
    },
    position: { x: 550, y: 20 },
    style: { width: 840, height: 430, zIndex: -1, pointerEvents: "none" },
    draggable: false,
    selectable: false,
  });

  // 2. Deployment Division (Left Column)
  nodes.push({
    id: "group-deployment",
    type: "layerGroup",
    data: {
      label: "Deployment Division",
      division: "deployment",
      count: 3,
      subtitle: "CI/CD Pipeline · Kubernetes · Observability",
    },
    position: { x: 40, y: 280 },
    style: { width: 330, height: 600, zIndex: -1, pointerEvents: "none" },
    draggable: false,
    selectable: false,
  });

  // 3. Backend Division (Main Center & Right Flank: 2x3 Grid + Event Bus)
  nodes.push({
    id: "group-backend",
    type: "layerGroup",
    data: {
      label: "Backend Division",
      division: "backend",
      count: 7,
      subtitle: "Microservices Cluster · Event Bus Broker",
    },
    position: { x: 420, y: 570 },
    style: { width: 1460, height: 450, zIndex: -1, pointerEvents: "none" },
    draggable: false,
    selectable: false,
  });

  // 4. Database Division (Bottom Center)
  nodes.push({
    id: "group-database",
    type: "layerGroup",
    data: {
      label: "Database Division",
      division: "database",
      count: 2,
      subtitle: "Relational Persistence & In-Memory Cache",
    },
    position: { x: 560, y: 1130 },
    style: { width: 880, height: 210, zIndex: -1, pointerEvents: "none" },
    draggable: false,
    selectable: false,
  });

  // ── Entity Nodes Symmetrically Positioned Inside Divisions ──
  // ── [FRONTEND DIVISION] ──
  // Top Actors (Centered inside group-frontend)
  nodes.push({
    id: "actor-student",
    type: "actor",
    data: {
      division: "frontend",
      label: "Student / User",
      role: "Primary Web & Mobile Consumer",
      description: "Searches catalog, borrows books, views active loans",
    },
    position: { x: 670, y: 75 },
  });

  nodes.push({
    id: "actor-admin",
    type: "actor",
    data: {
      division: "frontend",
      label: "Admin / Librarian",
      role: "Library Management Staff",
      description: "Manages catalog, inventory, fine overrides, and reporting",
    },
    position: { x: 1040, y: 75 },
  });

  // Frontend App (Centered inside group-frontend)
  nodes.push({
    id: "node-frontend",
    type: "frontend",
    data: {
      division: "frontend",
      label: "React / Next.js Web Application",
      tech: "Next.js App Router · Tailwind CSS · React 19",
      description: "Unified web client with server-side rendering and client interactivity.",
    },
    position: { x: 825, y: 175 },
  });

  // API Gateway (Centered inside group-frontend)
  nodes.push({
    id: "node-gateway",
    type: "gateway",
    data: {
      division: "frontend",
      label: "API Gateway / Ingress NGINX",
      tech: "TLS 1.3 · Rate Limiting · RBAC Guard",
      description: "TLS termination, WAF rate limiting (100 RPS), and route orchestration.",
    },
    position: { x: 810, y: 310 },
  });

  // ── [BACKEND DIVISION] ──
  // Microservices Grid (Row 1: SVC-01, SVC-02, SVC-03; Row 2: SVC-05, SVC-06, SVC-04)
  // Row 1: Direct Ingress Domain Services
  nodes.push({
    id: "svc-1",
    type: "service",
    data: {
      division: "backend",
      code: microservices[0]?.code || "SVC-01",
      label: microservices[0]?.label || "Authentication & Role Service",
      tech: microservices[0]?.tech || "JWT · OAuth2 · RBAC",
      protocol: "gRPC / HTTPS",
      description: microservices[0]?.desc,
    },
    position: { x: 470, y: 650 },
  });

  nodes.push({
    id: "svc-2",
    type: "service",
    data: {
      division: "backend",
      code: microservices[1]?.code || "SVC-02",
      label: microservices[1]?.label || "Catalog & Search Service",
      tech: microservices[1]?.tech || "Elasticsearch Query Engine",
      protocol: "REST / HTTP2",
      description: microservices[1]?.desc,
    },
    position: { x: 840, y: 650 },
  });

  nodes.push({
    id: "svc-3",
    type: "service",
    data: {
      division: "backend",
      code: microservices[2]?.code || "SVC-03",
      label: microservices[2]?.label || "Circulation & Borrowing Service",
      tech: microservices[2]?.tech || "ACID Transactions",
      protocol: "gRPC / Internal",
      description: microservices[2]?.desc,
    },
    position: { x: 1210, y: 650 },
  });

  // Row 2: Operational & Event-Driven Domain Services (Directly aligned under Row 1)
  // Col 1: SVC-05 Inventory directly under SVC-01 Auth
  nodes.push({
    id: "svc-5",
    type: "service",
    data: {
      division: "backend",
      code: microservices[4]?.code || "SVC-05",
      label: microservices[4]?.label || "Inventory & Asset Service",
      tech: microservices[4]?.tech || "RFID & Barcode Tracker",
      protocol: "REST / Internal",
      description: microservices[4]?.desc,
    },
    position: { x: 470, y: 850 },
  });

  // Col 2: SVC-06 Reporting directly under SVC-02 Catalog
  nodes.push({
    id: "svc-6",
    type: "service",
    data: {
      division: "backend",
      code: microservices[5]?.code || "SVC-06",
      label: microservices[5]?.label || "Reporting & Analytics Service",
      tech: microservices[5]?.tech || "BI Aggregations",
      protocol: "Async Consumer",
      description: microservices[5]?.desc,
    },
    position: { x: 840, y: 850 },
  });

  // Col 3: SVC-04 Notification directly under SVC-03 Circulation and next to RabbitMQ
  nodes.push({
    id: "svc-4",
    type: "service",
    data: {
      division: "backend",
      code: microservices[3]?.code || "SVC-04",
      label: microservices[3]?.label || "Notification & Reminder Service",
      tech: microservices[3]?.tech || "Async Event Worker",
      protocol: "Async Consumer",
      description: microservices[3]?.desc,
    },
    position: { x: 1210, y: 850 },
  });

  // Right Flank: RabbitMQ Event Broker (Inside Backend Division)
  nodes.push({
    id: "node-rabbitmq",
    type: "queue",
    data: {
      division: "backend",
      label: "RabbitMQ Event Broker",
      subtitle: "Event Messaging · DLQ · Retry x3",
      description: "Asynchronous domain event streaming with dead-letter exchange and 3 retry attempts.",
    },
    position: { x: 1570, y: 745 },
  });

  // ── [DEPLOYMENT DIVISION] ──
  // Left Column: DevOps, CI/CD, Containerization & Observability
  nodes.push({
    id: "node-github-actions",
    type: "devops",
    data: {
      division: "deployment",
      label: "GitHub Actions",
      role: "Build · Test · Scan · Deploy",
      category: "cicd",
      description: "Automated linting, Pytest unit tests, Docker builds, and Trivy vulnerability scans.",
    },
    position: { x: 75, y: 350 },
  });

  nodes.push({
    id: "node-k8s",
    type: "devops",
    data: {
      division: "deployment",
      label: "Kubernetes EKS / GKE",
      role: "Horizontal Pod Auto-Scaling",
      category: "k8s",
      description: "Container orchestration cluster with horizontal pod autoscaling (min 2, max 10).",
    },
    position: { x: 75, y: 520 },
  });

  nodes.push({
    id: "node-prometheus",
    type: "devops",
    data: {
      division: "deployment",
      label: "Prometheus + Grafana",
      role: "OpenTelemetry Distributed Tracing",
      category: "monitoring",
      description: "Real-time metrics, CloudWatch container insights, and APM tracing.",
    },
    position: { x: 75, y: 690 },
  });

  // ── [DATABASE DIVISION] ──
  // Bottom Center: Persistence & Cache Tier
  const dataStrategy =
    hldJson.data_strategy && typeof hldJson.data_strategy === "object"
      ? (hldJson.data_strategy as Record<string, unknown>)
      : {};
  const primaryDb = String(dataStrategy.primary_database || "PostgreSQL 16");
  const cachingTier = String(dataStrategy.caching_tier || "Redis 7.2 Cluster");

  nodes.push({
    id: "node-redis",
    type: "cache",
    data: {
      division: "database",
      label: cachingTier,
      subtitle: "Cache · Session Tokens · PubSub",
      description: "In-memory caching for catalog search (300s TTL) and session tokens.",
    },
    position: { x: 620, y: 1210 },
  });

  nodes.push({
    id: "node-database",
    type: "database",
    data: {
      division: "database",
      engine: primaryDb,
      label: primaryDb.includes("PostgreSQL") ? "PostgreSQL Database" : primaryDb,
      schema: "Multi-Schema Relational Storage",
      description:
        "Centralized ACID relational persistence layer with schema isolation for domain services and automated backups.",
    },
    position: { x: 1020, y: 1210 },
  });

  // ── Connection Edges with Non-Overlapping Systematic Routing & Explicit Handles ──
  const edges: Edge[] = [
    // Top Actors to Frontend
    {
      id: "e-act1-fe",
      source: "actor-student",
      target: "node-frontend",
      sourceHandle: "act-bottom",
      targetHandle: "fe-top",
      type: "animatedFlow",
      animated: true,
    },
    {
      id: "e-act2-fe",
      source: "actor-admin",
      target: "node-frontend",
      sourceHandle: "act-bottom",
      targetHandle: "fe-top",
      type: "animatedFlow",
      animated: true,
    },

    // Frontend to Gateway
    {
      id: "e-fe-gw",
      source: "node-frontend",
      target: "node-gateway",
      sourceHandle: "fe-bottom",
      targetHandle: "gw-top",
      type: "animatedFlow",
      data: { label: "HTTPS / HTTP2 REST JSON" },
      animated: true,
    },

    // Ingress Gateway to Public Row 1 Services
    {
      id: "e-gw-svc1",
      source: "node-gateway",
      target: "svc-1",
      sourceHandle: "gw-bottom",
      targetHandle: "svc-top",
      type: "animatedFlow",
      data: { label: "/api/v1/auth" },
      animated: true,
    },
    {
      id: "e-gw-svc2",
      source: "node-gateway",
      target: "svc-2",
      sourceHandle: "gw-bottom",
      targetHandle: "svc-top",
      type: "animatedFlow",
      data: { label: "/api/v1/catalog" },
      animated: true,
    },
    {
      id: "e-gw-svc3",
      source: "node-gateway",
      target: "svc-3",
      sourceHandle: "gw-bottom",
      targetHandle: "svc-top",
      type: "animatedFlow",
      data: { label: "/api/v1/circulation" },
      animated: true,
    },

    // Clean Vertical Inter-Service Feeds (Row 1 straight down to Row 2)
    {
      id: "e-svc1-svc5",
      source: "svc-1",
      target: "svc-5",
      sourceHandle: "svc-bottom",
      targetHandle: "svc-top",
      type: "animatedFlow",
      data: { label: "RBAC Guard" },
      animated: true,
    },
    {
      id: "e-svc2-svc6",
      source: "svc-2",
      target: "svc-6",
      sourceHandle: "svc-bottom",
      targetHandle: "svc-top",
      type: "animatedFlow",
      data: { label: "Search Metrics" },
      animated: true,
    },
    {
      id: "e-svc3-svc4",
      source: "svc-3",
      target: "svc-4",
      sourceHandle: "svc-bottom",
      targetHandle: "svc-top",
      type: "animatedFlow",
      data: { label: "Due Date Alerts" },
      animated: true,
    },

    // Event Producers to RabbitMQ (clean rightward flow)
    {
      id: "e-svc3-q",
      source: "svc-3",
      target: "node-rabbitmq",
      sourceHandle: "svc-right",
      targetHandle: "q-left",
      type: "animatedFlow",
      data: { label: "Borrow / Return Events" },
      animated: true,
    },

    // Event Consumers from RabbitMQ (clean right-to-left flow)
    {
      id: "e-q-svc4",
      source: "node-rabbitmq",
      target: "svc-4",
      sourceHandle: "q-left",
      targetHandle: "svc-right",
      type: "animatedFlow",
      data: { label: "Send Reminders" },
      animated: true,
    },
    {
      id: "e-q-svc6",
      source: "node-rabbitmq",
      target: "svc-6",
      sourceHandle: "q-bottom",
      targetHandle: "svc-right",
      type: "animatedFlow",
      data: { label: "Analytics Stream" },
      animated: true,
    },

    // In-Memory Caching Tier (Direct downward connections into Redis)
    {
      id: "e-svc5-redis",
      source: "svc-5",
      target: "node-redis",
      sourceHandle: "svc-bottom",
      targetHandle: "cache-top",
      type: "animatedFlow",
      data: { label: "Session Tokens" },
      animated: true,
    },
    {
      id: "e-svc6-redis",
      source: "svc-6",
      target: "node-redis",
      sourceHandle: "svc-bottom",
      targetHandle: "cache-top",
      type: "animatedFlow",
      data: { label: "Hot Cache (300s)" },
      animated: true,
    },

    // Persistence Tier to PostgreSQL Database (Clean downward connections)
    {
      id: "e-svc5-db",
      source: "svc-5",
      target: "node-database",
      sourceHandle: "svc-right",
      targetHandle: "db-left",
      type: "animatedFlow",
      data: { label: "Inventory Schema" },
      animated: true,
    },
    {
      id: "e-svc6-db",
      source: "svc-6",
      target: "node-database",
      sourceHandle: "svc-bottom",
      targetHandle: "db-top",
      type: "animatedFlow",
      data: { label: "Reporting Schema" },
      animated: true,
    },
    {
      id: "e-svc4-db",
      source: "svc-4",
      target: "node-database",
      sourceHandle: "svc-bottom",
      targetHandle: "db-top",
      type: "animatedFlow",
      data: { label: "Loans Schema" },
      animated: true,
    },

    // DevOps & Observability Infrastructure (Left Flank)
    {
      id: "e-gh-k8s",
      source: "node-github-actions",
      target: "node-k8s",
      sourceHandle: "dev-bottom",
      targetHandle: "dev-top",
      type: "animatedFlow",
      data: { label: "Deploy Pipeline" },
      animated: true,
    },
    {
      id: "e-k8s-gw",
      source: "node-k8s",
      target: "node-gateway",
      sourceHandle: "dev-right",
      targetHandle: "gw-left",
      type: "animatedFlow",
      data: { label: "Cluster Ingress" },
      animated: true,
    },
    {
      id: "e-k8s-prom",
      source: "node-k8s",
      target: "node-prometheus",
      sourceHandle: "dev-bottom",
      targetHandle: "dev-top",
      type: "animatedFlow",
      data: { label: "Pod Telemetry" },
      animated: true,
    },
    {
      id: "e-svc1-prom",
      source: "svc-1",
      target: "node-prometheus",
      sourceHandle: "svc-left",
      targetHandle: "dev-right",
      type: "animatedFlow",
      data: { label: "Auth APM Tracing" },
      animated: true,
    },
  ];

  return applyColorThemesToGraph(nodes, edges);
}

/**
 * High-Aesthetic Multi-Layer LLD Graph Synthesizers
 */
export function parseLldToReactFlow(
  lldType: string,
  lldData: Record<string, unknown> | null
): { nodes: Node[]; edges: Edge[] } {
  if (!lldData || typeof lldData !== "object" || Object.keys(lldData).length === 0) {
    return { nodes: [], edges: [] };
  }

  const type = lldType.toLowerCase();

  // ── 1. BACKEND LLD ARCHITECTURE TOPOLOGY ──
  // Hierarchical Structure (Ingress -> Domain Services Grid -> Repositories & Models + Left Flank Infra)
  if (type === "backend") {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Left Flank Division: Security, Event Broker & DB Pooling
    nodes.push({
      id: "bgroup-infra",
      type: "layerGroup",
      data: {
        label: "Security & Async Broker Layer",
        subtitle: "JWT Guard · RabbitMQ Broker · PgBouncer Pool",
        count: 3,
      },
      position: { x: 40, y: 30 },
      style: { width: 340, height: 750, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Top Center Division: API Ingress Endpoints
    nodes.push({
      id: "bgroup-endpoints",
      type: "layerGroup",
      data: {
        label: "API Ingress & Router Endpoints",
        subtitle: "FastAPI REST Endpoints & Route Orchestration",
        count: 5,
      },
      position: { x: 420, y: 30 },
      style: { width: 1080, height: 260, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Center Division: Domain Microservices (2-Row Balanced Grid matching HLD)
    nodes.push({
      id: "bgroup-services",
      type: "layerGroup",
      data: {
        label: "Domain Microservices Logic Layer",
        subtitle: "Core Business Workflows · ACID State Machines",
        count: 5,
      },
      position: { x: 420, y: 310 },
      style: { width: 1080, height: 260, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Bottom Center Division: Persistence & Domain Entities (Repos & Models)
    nodes.push({
      id: "bgroup-repos",
      type: "layerGroup",
      data: {
        label: "Repository & Domain Model Layer",
        subtitle: "SQLAlchemy 2.0 Async Repositories & Relational Schemas",
        count: 8,
      },
      position: { x: 420, y: 590 },
      style: { width: 1080, height: 350, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // ── Left Flank Nodes ──
    nodes.push({
      id: "bnode-jwt",
      type: "gateway",
      parentId: "bgroup-infra",
      data: {
        label: "JWT RS256 Auth Middleware",
        tech: "OAuth2 Bearer · PyJWT · RBAC",
        description: "Validates incoming bearer tokens and injects authenticated principal context.",
      },
      position: { x: 70, y: 100 },
    });

    nodes.push({
      id: "bnode-queue",
      type: "queue",
      parentId: "bgroup-infra",
      data: {
        label: "RabbitMQ Event Broker",
        subtitle: "AMQP 0-9-1 · Topic Exchange",
        description: "Asynchronous domain event streaming for due date reminders and loan lifecycle events.",
      },
      position: { x: 70, y: 350 },
    });

    nodes.push({
      id: "bnode-pool",
      type: "gateway",
      parentId: "bgroup-infra",
      data: {
        label: "PgBouncer Connection Pool",
        tech: "SQLAlchemy 2.0 Asyncpg · 50 Max",
        description: "Maintains reusable async database socket pool with Read Committed transaction isolation.",
      },
      position: { x: 70, y: 600 },
    });

    // ── Endpoints (Layer 1 - Balanced 2 Rows) ──
    nodes.push({
      id: "bep-1",
      type: "service",
      parentId: "bgroup-endpoints",
      data: {
        code: "POST",
        label: "/api/v1/auth/login",
        tech: "FastAPI Public Route",
        protocol: "Public Ingress",
        description: "Authenticate user or staff credentials and issue RS256 JWT tokens.",
      },
      position: { x: 480, y: 85 },
    });

    nodes.push({
      id: "bep-2",
      type: "service",
      parentId: "bgroup-endpoints",
      data: {
        code: "GET",
        label: "/api/v1/search-books",
        tech: "Elasticsearch Query Router",
        protocol: "Public Ingress",
        description: "Fast indexed catalog search with pagination, filters, and availability status.",
      },
      position: { x: 800, y: 85 },
    });

    nodes.push({
      id: "bep-3",
      type: "service",
      parentId: "bgroup-endpoints",
      data: {
        code: "POST",
        label: "/api/v1/borrow-books",
        tech: "FastAPI Protected Route",
        protocol: "Public Ingress",
        description: "Checkout borrow transaction with ACID row-level locking.",
      },
      position: { x: 1120, y: 85 },
    });

    nodes.push({
      id: "bep-4",
      type: "service",
      parentId: "bgroup-endpoints",
      data: {
        code: "POST",
        label: "/api/v1/return-books",
        tech: "FastAPI Protected Route",
        protocol: "Public Ingress",
        description: "Check-in book return, fine assessment, and loan status update.",
      },
      position: { x: 640, y: 180 },
    });

    nodes.push({
      id: "bep-5",
      type: "service",
      parentId: "bgroup-endpoints",
      data: {
        code: "DELETE",
        label: "/api/v1/manage-catalog",
        tech: "Librarian RBAC Route",
        protocol: "Public Ingress",
        description: "Administrative catalog lifecycle management to retire or update items.",
      },
      position: { x: 960, y: 180 },
    });

    // ── Domain Services (Layer 2 - Balanced 2 Rows matching HLD) ──
    nodes.push({
      id: "bsvc-1",
      type: "service",
      parentId: "bgroup-services",
      data: {
        code: "SVC-01",
        label: "Authentication & Role Service",
        tech: "JWT · OAuth2 · RBAC Guard",
        protocol: "Domain Service",
        description: "Handles identity, token issuance, and granular permission checks.",
      },
      position: { x: 480, y: 360 },
    });

    nodes.push({
      id: "bsvc-2",
      type: "service",
      parentId: "bgroup-services",
      data: {
        code: "SVC-02",
        label: "Catalog & Search Service",
        tech: "Elasticsearch · Query Engine",
        protocol: "Domain Service",
        description: "Fast indexing, book cataloging, metadata queries, and availability filters.",
      },
      position: { x: 800, y: 360 },
    });

    nodes.push({
      id: "bsvc-3",
      type: "service",
      parentId: "bgroup-services",
      data: {
        code: "SVC-03",
        label: "Circulation & Borrowing Service",
        tech: "ACID Orchestration · State Machine",
        protocol: "Domain Service",
        description: "Coordinates checkouts and returns using distributed transactions.",
      },
      position: { x: 1120, y: 360 },
    });

    nodes.push({
      id: "bsvc-5",
      type: "service",
      parentId: "bgroup-services",
      data: {
        code: "SVC-05",
        label: "Inventory & Asset Service",
        tech: "RFID · Barcode Tracker",
        protocol: "Domain Service",
        description: "Tracks physical book copies, shelf allocation, and stock counts.",
      },
      position: { x: 640, y: 470 },
    });

    nodes.push({
      id: "bsvc-4",
      type: "service",
      parentId: "bgroup-services",
      data: {
        code: "SVC-04",
        label: "Notification & Reminder Service",
        tech: "Async Event Worker · BullMQ",
        protocol: "Async Consumer",
        description: "Dispatches automated overdue notices and hold alerts.",
      },
      position: { x: 960, y: 470 },
    });

    // ── Repositories & Domain Models (Layer 3 - Paired Columns) ──
    const repos = [
      { id: "brepo-1", label: "UserRepository", entity: "User Entity", desc: "SQLAlchemy async repo for user identities" },
      { id: "brepo-2", label: "BooksRepository", entity: "Books Entity", desc: "SQLAlchemy async repo for catalog books" },
      { id: "brepo-4", label: "BorrowRepository", entity: "Borrow Entity", desc: "SQLAlchemy async repo for borrow logs" },
      { id: "brepo-5", label: "ReturnRepository", entity: "Return Entity", desc: "SQLAlchemy async repo for return logs" },
    ];

    const models = [
      { id: "bmodel-1", label: "User Model", table: "users table", desc: "id, username, email, hashed_password, role" },
      { id: "bmodel-2", label: "Books Model", table: "books table", desc: "id, user_id, name, status, description" },
      { id: "bmodel-4", label: "Borrow Model", table: "borrows table", desc: "id, user_id, name, status, borrow_date" },
      { id: "bmodel-5", label: "Return Model", table: "returns table", desc: "id, user_id, name, status, return_date" },
    ];

    const repoX = [460, 720, 980, 1240];

    repos.forEach((repo, idx) => {
      nodes.push({
        id: repo.id,
        type: "database",
        parentId: "bgroup-repos",
        data: {
          engine: "SQLAlchemy ORM",
          label: repo.label,
          schema: repo.entity,
          description: repo.desc,
        },
        position: { x: repoX[idx], y: 645 },
      });
    });

    models.forEach((model, idx) => {
      nodes.push({
        id: model.id,
        type: "database",
        parentId: "bgroup-repos",
        data: {
          engine: "PostgreSQL 16",
          label: model.label,
          schema: model.table,
          description: model.desc,
        },
        position: { x: repoX[idx], y: 775 },
      });
    });

    // ── Edges: Pristine Hierarchical Flow ──
    // Endpoints -> Services
    edges.push({ id: "be-ep1-s1", source: "bep-1", target: "bsvc-1", sourceHandle: "svc-bottom", targetHandle: "svc-top", type: "animatedFlow", animated: true });
    edges.push({ id: "be-ep2-s2", source: "bep-2", target: "bsvc-2", sourceHandle: "svc-bottom", targetHandle: "svc-top", type: "animatedFlow", animated: true });
    edges.push({ id: "be-ep3-s3", source: "bep-3", target: "bsvc-3", sourceHandle: "svc-bottom", targetHandle: "svc-top", type: "animatedFlow", animated: true });
    edges.push({ id: "be-ep4-s3", source: "bep-4", target: "bsvc-3", sourceHandle: "svc-bottom", targetHandle: "svc-top", type: "animatedFlow", animated: true });
    edges.push({ id: "be-ep5-s2", source: "bep-5", target: "bsvc-2", sourceHandle: "svc-bottom", targetHandle: "svc-top", type: "animatedFlow", animated: true });

    // Endpoints & Services -> Left Flank Infrastructure
    edges.push({ id: "be-ep1-jwt", source: "bep-1", target: "bnode-jwt", sourceHandle: "svc-left", targetHandle: "gw-right", type: "animatedFlow", data: { label: "Verify Bearer" }, animated: true });
    edges.push({ id: "be-s3-queue", source: "bsvc-3", target: "bnode-queue", sourceHandle: "svc-left", targetHandle: "q-right", type: "animatedFlow", data: { label: "Emit Domain Event" }, animated: true });
    edges.push({ id: "be-queue-s4", source: "bnode-queue", target: "bsvc-4", sourceHandle: "q-right", targetHandle: "svc-left", type: "animatedFlow", data: { label: "Consume Task" }, animated: true });
    edges.push({ id: "be-s3-s5", source: "bsvc-3", target: "bsvc-5", sourceHandle: "svc-bottom", targetHandle: "svc-top", type: "animatedFlow", data: { label: "Stock Decrement" }, animated: true });

    // Services -> Repositories
    edges.push({ id: "be-s1-r1", source: "bsvc-1", target: "brepo-1", sourceHandle: "svc-bottom", targetHandle: "db-top", type: "animatedFlow", animated: true });
    edges.push({ id: "be-s2-r2", source: "bsvc-2", target: "brepo-2", sourceHandle: "svc-bottom", targetHandle: "db-top", type: "animatedFlow", animated: true });
    edges.push({ id: "be-s3-r4", source: "bsvc-3", target: "brepo-4", sourceHandle: "svc-bottom", targetHandle: "db-top", type: "animatedFlow", animated: true });
    edges.push({ id: "be-s3-r5", source: "bsvc-3", target: "brepo-5", sourceHandle: "svc-bottom", targetHandle: "db-top", type: "animatedFlow", animated: true });

    // Repositories -> Models
    edges.push({ id: "be-r1-m1", source: "brepo-1", target: "bmodel-1", sourceHandle: "db-bottom", targetHandle: "db-top", type: "animatedFlow", animated: true });
    edges.push({ id: "be-r2-m2", source: "brepo-2", target: "bmodel-2", sourceHandle: "db-bottom", targetHandle: "db-top", type: "animatedFlow", animated: true });
    edges.push({ id: "be-r4-m4", source: "brepo-4", target: "bmodel-4", sourceHandle: "db-bottom", targetHandle: "db-top", type: "animatedFlow", animated: true });
    edges.push({ id: "be-r5-m5", source: "brepo-5", target: "bmodel-5", sourceHandle: "db-bottom", targetHandle: "db-top", type: "animatedFlow", animated: true });

    // Repositories -> Connection Pool
    edges.push({ id: "be-r1-pool", source: "brepo-1", target: "bnode-pool", sourceHandle: "db-left", targetHandle: "gw-right", type: "animatedFlow", data: { label: "Pool Session" }, animated: true });

    return applyColorThemesToGraph(nodes, edges);
  }

  // ── 2. DATABASE LLD ARCHITECTURE TOPOLOGY ──
  // Hierarchical Structure (Master Relational Schema Tables + Flank Cache & Connection Pool)
  if (type === "database") {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Left Container: Relational Schema Tables (PostgreSQL 16 Multi-AZ)
    nodes.push({
      id: "dbgroup-tables",
      type: "layerGroup",
      data: {
        label: "Relational Schema Tables (PostgreSQL 16 Multi-AZ)",
        subtitle: "Primary-Foreign Key Relationships · ACID Transactions",
        count: 5,
      },
      position: { x: 30, y: 30 },
      style: { width: 1060, height: 500, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Right Flank Container: Performance, Pooling & Migrations
    nodes.push({
      id: "dbgroup-pooling",
      type: "layerGroup",
      data: {
        label: "Cache, Pooling & Migrations",
        subtitle: "Redis 7.2 · PgBouncer Pool · Alembic Migrations",
        count: 3,
      },
      position: { x: 1120, y: 30 },
      style: { width: 380, height: 500, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Database Tables - Symmetrical Hierarchical Order
    // Row 1 (Master Entities)
    nodes.push({
      id: "dtbl-users",
      type: "database",
      parentId: "dbgroup-tables",
      data: {
        engine: "PostgreSQL 16",
        label: "Table: users",
        schema: "id (UUID PK) · username · email · role · password",
        description: "User accounts, auth credentials, and role memberships.",
      },
      position: { x: 60, y: 90 },
    });

    nodes.push({
      id: "dtbl-loans",
      type: "database",
      parentId: "dbgroup-tables",
      data: {
        engine: "PostgreSQL 16",
        label: "Table: book_loans",
        schema: "id (UUID PK) · user_id (FK) · name · status · dates",
        description: "Central junction table: active and historical book loan records.",
      },
      position: { x: 410, y: 90 },
    });

    nodes.push({
      id: "dtbl-books",
      type: "database",
      parentId: "dbgroup-tables",
      data: {
        engine: "PostgreSQL 16",
        label: "Table: books",
        schema: "id (UUID PK) · user_id (FK) · name · status · desc",
        description: "Book catalog master items and availability status.",
      },
      position: { x: 760, y: 90 },
    });

    // Row 2 (Transaction Records)
    nodes.push({
      id: "dtbl-borrows",
      type: "database",
      parentId: "dbgroup-tables",
      data: {
        engine: "PostgreSQL 16",
        label: "Table: borrows",
        schema: "id (UUID PK) · user_id (FK) · name · borrow_date",
        description: "Book checkout transaction events and audit history.",
      },
      position: { x: 235, y: 320 },
    });

    nodes.push({
      id: "dtbl-returns",
      type: "database",
      parentId: "dbgroup-tables",
      data: {
        engine: "PostgreSQL 16",
        label: "Table: returns",
        schema: "id (UUID PK) · user_id (FK) · name · return_date",
        description: "Book check-in transaction events and fine assessments.",
      },
      position: { x: 585, y: 320 },
    });

    // Right Flank: Performance & Tooling Nodes
    nodes.push({
      id: "dnode-redis",
      type: "cache",
      parentId: "dbgroup-pooling",
      data: {
        label: "Redis 7.2 Cluster",
        subtitle: "search (300s) · session (900s) · loans (120s)",
        description: "Write-through invalidation and multi-instance Pub/Sub fan-out.",
      },
      position: { x: 1150, y: 90 },
    });

    nodes.push({
      id: "dnode-pgbouncer",
      type: "gateway",
      parentId: "dbgroup-pooling",
      data: {
        label: "PgBouncer Pool",
        tech: "20 min, 50 max · Asyncpg Driver",
        description: "Transaction pooling with Read Committed isolation and row-level locking.",
      },
      position: { x: 1150, y: 230 },
    });

    nodes.push({
      id: "dnode-alembic",
      type: "devops",
      parentId: "dbgroup-pooling",
      data: {
        label: "Alembic Versioned Migrations",
        role: "Sequential Revision Tracking",
        category: "cicd",
        description: "Automated schema migrations executed in pre-deployment CI/CD hooks.",
      },
      position: { x: 1150, y: 370 },
    });

    // Clean Database Relationships
    edges.push({ id: "de-u-loans", source: "dtbl-users", target: "dtbl-loans", sourceHandle: "db-right", targetHandle: "db-left", type: "animatedFlow", data: { label: "1:N FK (user_id)" }, animated: true });
    edges.push({ id: "de-b-loans", source: "dtbl-books", target: "dtbl-loans", sourceHandle: "db-left", targetHandle: "db-right", type: "animatedFlow", data: { label: "1:N FK (book_id)" }, animated: true });
    edges.push({ id: "de-l-borrows", source: "dtbl-loans", target: "dtbl-borrows", sourceHandle: "db-bottom", targetHandle: "db-top", type: "animatedFlow", data: { label: "1:N FK Checkout" }, animated: true });
    edges.push({ id: "de-l-returns", source: "dtbl-loans", target: "dtbl-returns", sourceHandle: "db-bottom", targetHandle: "db-top", type: "animatedFlow", data: { label: "1:N FK Return" }, animated: true });
    edges.push({ id: "de-books-cache", source: "dtbl-books", target: "dnode-redis", sourceHandle: "db-right", targetHandle: "cache-left", type: "animatedFlow", data: { label: "Cache Invalidate" }, animated: true });
    edges.push({ id: "de-pgb-loans", source: "dnode-pgbouncer", target: "dtbl-loans", sourceHandle: "gw-left", targetHandle: "db-right", type: "animatedFlow", data: { label: "Pool Conns" }, animated: true });
    edges.push({ id: "de-alembic-returns", source: "dnode-alembic", target: "dtbl-returns", sourceHandle: "dev-left", targetHandle: "db-right", type: "animatedFlow", data: { label: "Auto Migrate" }, animated: true });

    return applyColorThemesToGraph(nodes, edges);
  }

  // ── 3. FRONTEND LLD ARCHITECTURE TOPOLOGY ──
  // Hierarchical Structure (App Router & Routes -> Modular Components + Left Flank Reactive State & Transport)
  if (type === "frontend") {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Left Flank Division: Reactive Client State, Cache & API Transport (matching HLD left column)
    nodes.push({
      id: "fgroup-state-api",
      type: "layerGroup",
      data: {
        label: "Client State, Cache & API Transport",
        subtitle: "Zustand · TanStack Query · Axios · Zod",
        count: 4,
      },
      position: { x: 40, y: 30 },
      style: { width: 340, height: 680, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Top Center Division: Next.js 16 App Router & Navigation Shell
    nodes.push({
      id: "fgroup-pages",
      type: "layerGroup",
      data: {
        label: "Next.js 16 App Router (Pages & Routes)",
        subtitle: "App Shell · Auth Entry · Dynamic Route Handlers",
        count: 5,
      },
      position: { x: 420, y: 30 },
      style: { width: 1080, height: 330, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Bottom Center Division: Modular Tailwind UI Components (aligned directly under corresponding pages)
    nodes.push({
      id: "fgroup-components",
      type: "layerGroup",
      data: {
        label: "Modular Tailwind UI Components",
        subtitle: "Presentation Tiles · Interactive Dialogs · Paginated Tables",
        count: 4,
      },
      position: { x: 420, y: 380 },
      style: { width: 1080, height: 330, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // ── Left Flank Nodes: Client State & Transport Stack ──
    nodes.push({
      id: "fnode-zustand",
      type: "cache",
      parentId: "fgroup-state-api",
      data: {
        label: "Zustand Global Store",
        subtitle: "AuthSession · UIState · Theme",
        description: "Lightweight reactive client store managing active user session, auth token, and theme.",
      },
      position: { x: 70, y: 100 },
    });

    nodes.push({
      id: "fnode-tanstack",
      type: "service",
      parentId: "fgroup-state-api",
      data: {
        code: "React Query",
        label: "TanStack Query Cache",
        tech: "Auto Invalidation & Refetch",
        protocol: "Server State",
        description: "Cached API queries with background revalidation and optimistic mutation updates.",
      },
      position: { x: 70, y: 250 },
    });

    nodes.push({
      id: "fnode-axios",
      type: "gateway",
      parentId: "fgroup-state-api",
      data: {
        label: "Axios API Interceptor",
        tech: "Bearer Token Injection · Error Toasts",
        description: "Centralized HTTP client with automatic Authorization header injection and 401 refresh handling.",
      },
      position: { x: 70, y: 400 },
    });

    nodes.push({
      id: "fnode-zod",
      type: "service",
      parentId: "fgroup-state-api",
      data: {
        code: "Zod Validator",
        label: "React Hook Form + Zod",
        tech: "Strict Client Schema Validation",
        protocol: "Form State",
        description: "Type-safe form inputs and field-level validation schemas before API submission.",
      },
      position: { x: 70, y: 550 },
    });

    // ── Top Center Division: App Shell & Pages ──
    // Tier 1 (Root Shell & Auth Entry)
    nodes.push({
      id: "fcmp-1",
      type: "service",
      parentId: "fgroup-pages",
      data: {
        code: "App Shell",
        label: "Navbar & AuthStatus",
        tech: "React 19 · Zustand Session",
        protocol: "Global Header",
        description: "Global header with navigation links, active route indicators, and user token state.",
      },
      position: { x: 580, y: 90 },
    });

    nodes.push({
      id: "fpg-1",
      type: "frontend",
      parentId: "fgroup-pages",
      data: {
        label: "LoginPage",
        tech: "/login",
        description: "Authentication entry with role-based credentials form (Student / Librarian / Admin).",
      },
      position: { x: 980, y: 90 },
    });

    // Tier 2 (Core Application Route Pages)
    nodes.push({
      id: "fpg-2",
      type: "frontend",
      parentId: "fgroup-pages",
      data: {
        label: "SearchBooksPage",
        tech: "/search-books",
        description: "Dynamic catalog search, availability filters, and card presentations.",
      },
      position: { x: 450, y: 230 },
    });

    nodes.push({
      id: "fpg-3",
      type: "frontend",
      parentId: "fgroup-pages",
      data: {
        label: "BorrowBooksPage",
        tech: "/borrow-books",
        description: "Circulation checkout & active loan management workflow view.",
      },
      position: { x: 720, y: 230 },
    });

    nodes.push({
      id: "fpg-4",
      type: "frontend",
      parentId: "fgroup-pages",
      data: {
        label: "ReturnBooksPage",
        tech: "/return-books",
        description: "Book return scanning and check-in confirmation workflow view.",
      },
      position: { x: 990, y: 230 },
    });

    nodes.push({
      id: "fpg-5",
      type: "frontend",
      parentId: "fgroup-pages",
      data: {
        label: "CatalogAdminPage",
        tech: "/manage-catalog",
        description: "Librarian administrative catalog CRUD and inventory asset management.",
      },
      position: { x: 1260, y: 230 },
    });

    // ── Bottom Center Division: Modular UI Components (Aligned under Pages) ──
    nodes.push({
      id: "fcmp-2",
      type: "service",
      parentId: "fgroup-components",
      data: {
        code: "UI Component",
        label: "BookCatalogCard",
        tech: "React 19 · Tailwind CSS",
        protocol: "Client View",
        description: "Reusable presentation card for book catalog search results.",
      },
      position: { x: 450, y: 470 },
    });

    nodes.push({
      id: "fcmp-3",
      type: "service",
      parentId: "fgroup-components",
      data: {
        code: "UI Component",
        label: "BorrowConfirmModal",
        tech: "React 19 · Dialog Portal",
        protocol: "Client View",
        description: "Interactive modal dialog confirming loan due dates and checkout.",
      },
      position: { x: 720, y: 470 },
    });

    nodes.push({
      id: "fcmp-4",
      type: "service",
      parentId: "fgroup-components",
      data: {
        code: "UI Component",
        label: "ReturnScannerModal",
        tech: "React 19 · Barcode Scanner",
        protocol: "Client View",
        description: "Barcode and RFID scanner dialog for book return check-in.",
      },
      position: { x: 990, y: 470 },
    });

    nodes.push({
      id: "fcmp-5",
      type: "service",
      parentId: "fgroup-components",
      data: {
        code: "UI Component",
        label: "LoanHistoryTable",
        tech: "React 19 · TanStack Table",
        protocol: "Client View",
        description: "Paginated table showing active and past book loan records.",
      },
      position: { x: 1260, y: 470 },
    });

    // ── Edges: Clean Hierarchical Parent-to-Child & State Connections ──
    // Shell & Auth Entry Hierarchy
    edges.push({ id: "fe-login-nav", source: "fpg-1", target: "fcmp-1", sourceHandle: "fe-left", targetHandle: "svc-right", type: "animatedFlow", data: { label: "On Auth Success" }, animated: true });
    edges.push({ id: "fe-login-zustand", source: "fpg-1", target: "fnode-zustand", sourceHandle: "fe-left", targetHandle: "cache-right", type: "animatedFlow", data: { label: "Store Session" }, animated: true });
    edges.push({ id: "fe-nav-zustand", source: "fcmp-1", target: "fnode-zustand", sourceHandle: "svc-left", targetHandle: "cache-right", type: "animatedFlow", data: { label: "Read User" }, animated: true });

    // Navigation Shell -> Route Pages
    edges.push({ id: "fe-nav-search", source: "fcmp-1", target: "fpg-2", sourceHandle: "svc-bottom", targetHandle: "fe-top", type: "animatedFlow", data: { label: "/search-books" }, animated: true });
    edges.push({ id: "fe-nav-borrow", source: "fcmp-1", target: "fpg-3", sourceHandle: "svc-bottom", targetHandle: "fe-top", type: "animatedFlow", data: { label: "/borrow-books" }, animated: true });
    edges.push({ id: "fe-login-return", source: "fpg-1", target: "fpg-4", sourceHandle: "fe-bottom", targetHandle: "fe-top", type: "animatedFlow", animated: true });
    edges.push({ id: "fe-login-admin", source: "fpg-1", target: "fpg-5", sourceHandle: "fe-bottom", targetHandle: "fe-top", data: { label: "Admin RBAC" }, animated: true });

    // Pages -> Modular UI Components (Direct Vertical Flow)
    edges.push({ id: "fe-p2-c2", source: "fpg-2", target: "fcmp-2", sourceHandle: "fe-bottom", targetHandle: "svc-top", type: "animatedFlow", data: { label: "Render Tile" }, animated: true });
    edges.push({ id: "fe-p3-c3", source: "fpg-3", target: "fcmp-3", sourceHandle: "fe-bottom", targetHandle: "svc-top", type: "animatedFlow", data: { label: "Checkout Modal" }, animated: true });
    edges.push({ id: "fe-p4-c4", source: "fpg-4", target: "fcmp-4", sourceHandle: "fe-bottom", targetHandle: "svc-top", type: "animatedFlow", data: { label: "Scanner Modal" }, animated: true });
    edges.push({ id: "fe-p5-c5", source: "fpg-5", target: "fcmp-5", sourceHandle: "fe-bottom", targetHandle: "svc-top", type: "animatedFlow", data: { label: "History Grid" }, animated: true });

    // UI Components -> Client State & API Transport (Left Flank)
    edges.push({ id: "fe-c2-tanstack", source: "fcmp-2", target: "fnode-tanstack", sourceHandle: "svc-left", targetHandle: "svc-right", type: "animatedFlow", data: { label: "useQuery(books)" }, animated: true });
    edges.push({ id: "fe-tanstack-axios", source: "fnode-tanstack", target: "fnode-axios", sourceHandle: "svc-bottom", targetHandle: "gw-top", type: "animatedFlow", data: { label: "HTTP GET" }, animated: true });
    edges.push({ id: "fe-c3-zod", source: "fcmp-3", target: "fnode-zod", sourceHandle: "svc-left", targetHandle: "svc-right", type: "animatedFlow", data: { label: "Validate Form" }, animated: true });
    edges.push({ id: "fe-zod-axios", source: "fnode-zod", target: "fnode-axios", sourceHandle: "svc-top", targetHandle: "gw-bottom", type: "animatedFlow", data: { label: "Submit Payload" }, animated: true });
    edges.push({ id: "fe-c4-axios", source: "fcmp-4", target: "fnode-axios", sourceHandle: "svc-left", targetHandle: "gw-right", type: "animatedFlow", data: { label: "POST /return" }, animated: true });
    edges.push({ id: "fe-c5-tanstack", source: "fcmp-5", target: "fnode-tanstack", sourceHandle: "svc-left", targetHandle: "svc-right", type: "animatedFlow", data: { label: "useQuery(loans)" }, animated: true });

    return applyColorThemesToGraph(nodes, edges);
  }

  // ── 4. CLOUD LLD ARCHITECTURE TOPOLOGY (AWS ECS Fargate) ──
  // Hierarchical Structure (Edge & Ingress -> ECS Fargate Compute -> Managed Storage + Left Flank DevOps)
  if (type === "cloud") {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Left Flank Division: DevOps, CI/CD & Observability Pipeline
    nodes.push({
      id: "cgroup-devops",
      type: "layerGroup",
      data: {
        label: "DevOps & Monitoring Pipeline",
        subtitle: "GitHub Actions CI/CD · CloudWatch Container Insights",
        count: 2,
      },
      position: { x: 40, y: 30 },
      style: { width: 340, height: 750, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Top Center Division: Edge & Ingress Routing
    nodes.push({
      id: "cgroup-edge",
      type: "layerGroup",
      data: {
        label: "Edge & Ingress Routing Tier",
        subtitle: "AWS Route 53 DNS · CloudFront CDN · Application Load Balancer",
        count: 3,
      },
      position: { x: 420, y: 30 },
      style: { width: 1040, height: 260, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Center Division: Serverless Container Tasks (ECS on Fargate)
    nodes.push({
      id: "cgroup-compute",
      type: "layerGroup",
      data: {
        label: "Serverless Container Tasks (AWS ECS on Fargate)",
        subtitle: "Auto-Scaling Microservices (min 2, max 10)",
        count: 6,
      },
      position: { x: 420, y: 310 },
      style: { width: 1040, height: 270, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Bottom Center Division: Managed Persistence & Storage Tier
    nodes.push({
      id: "cgroup-storage",
      type: "layerGroup",
      data: {
        label: "Managed Storage Tier",
        subtitle: "AWS RDS PostgreSQL Multi-AZ & ElastiCache Redis 7.2",
        count: 2,
      },
      position: { x: 420, y: 600 },
      style: { width: 1040, height: 180, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Left Flank Nodes
    nodes.push({
      id: "cnode-github",
      type: "devops",
      parentId: "cgroup-devops",
      data: {
        label: "GitHub Actions CI/CD",
        role: "Ruff · Pytest · Docker · Trivy · ECR",
        category: "cicd",
        description: "Automated test gating, vulnerability scans, and ECS rolling deployments.",
      },
      position: { x: 75, y: 160 },
    });

    nodes.push({
      id: "cnode-cloudwatch",
      type: "devops",
      parentId: "cgroup-devops",
      data: {
        label: "AWS CloudWatch & SNS Alerts",
        role: "Container Insights · SNS Alerts",
        category: "monitoring",
        description: "Task CPU/Memory tracking, 5xx error rate alarms, and SNS push alerts.",
      },
      position: { x: 75, y: 460 },
    });

    // Edge & DNS (Layer 1)
    nodes.push({
      id: "cnode-route53",
      type: "devops",
      parentId: "cgroup-edge",
      data: {
        label: "AWS Route 53 + ACM",
        role: "DNS & TLS 1.3 Termination",
        category: "cicd",
        description: "Public hosted zone with automated TLS 1.3 certificates.",
      },
      position: { x: 580, y: 85 },
    });

    nodes.push({
      id: "cnode-cloudfront",
      type: "devops",
      parentId: "cgroup-edge",
      data: {
        label: "CloudFront CDN + S3 Bucket",
        role: "Static Assets & Media",
        category: "cicd",
        description: "Global edge CDN fronting private S3 bucket.",
      },
      position: { x: 960, y: 85 },
    });

    nodes.push({
      id: "cnode-alb",
      type: "gateway",
      parentId: "cgroup-edge",
      data: {
        label: "AWS Application Load Balancer",
        tech: "WAF Associated · 100 RPS Rate Limit · Multi-AZ",
        description: "Dual-AZ Public Subnet Ingress Load Balancer with path routing.",
      },
      position: { x: 770, y: 195 },
    });

    // ECS Fargate Tasks (Layer 2 - 2 rows x 3 columns)
    nodes.push({
      id: "cecs-1",
      type: "service",
      parentId: "cgroup-compute",
      data: { code: "ECS Task", label: "svc-auth Fargate Task", tech: "0.5 vCPU, 1 GB RAM", protocol: "Fargate Task", desc: "Auto Scaling (min 2, max 10)" },
      position: { x: 460, y: 360 },
    });

    nodes.push({
      id: "cecs-2",
      type: "service",
      parentId: "cgroup-compute",
      data: { code: "ECS Task", label: "svc-catalog Fargate Task", tech: "0.5 vCPU, 1 GB RAM", protocol: "Fargate Task", desc: "Auto Scaling (min 2, max 10)" },
      position: { x: 780, y: 360 },
    });

    nodes.push({
      id: "cecs-3",
      type: "service",
      parentId: "cgroup-compute",
      data: { code: "ECS Task", label: "svc-circulation Fargate Task", tech: "0.5 vCPU, 1 GB RAM", protocol: "Fargate Task", desc: "Auto Scaling (min 2, max 10)" },
      position: { x: 1100, y: 360 },
    });

    nodes.push({
      id: "cecs-4",
      type: "service",
      parentId: "cgroup-compute",
      data: { code: "ECS Task", label: "svc-notification Fargate Task", tech: "0.5 vCPU, 1 GB RAM", protocol: "Fargate Task", desc: "Auto Scaling (min 2, max 10)" },
      position: { x: 460, y: 475 },
    });

    nodes.push({
      id: "cecs-5",
      type: "service",
      parentId: "cgroup-compute",
      data: { code: "ECS Task", label: "svc-inventory Fargate Task", tech: "0.5 vCPU, 1 GB RAM", protocol: "Fargate Task", desc: "Auto Scaling (min 2, max 10)" },
      position: { x: 780, y: 475 },
    });

    nodes.push({
      id: "cecs-6",
      type: "service",
      parentId: "cgroup-compute",
      data: { code: "ECS Task", label: "svc-reporting Fargate Task", tech: "0.5 vCPU, 1 GB RAM", protocol: "Fargate Task", desc: "Auto Scaling (min 2, max 10)" },
      position: { x: 1100, y: 475 },
    });

    // Managed Storage (Layer 3)
    nodes.push({
      id: "cnode-rds",
      type: "database",
      parentId: "cgroup-storage",
      data: {
        engine: "AWS RDS PostgreSQL 16",
        label: "RDS db.t4g.medium Multi-AZ",
        schema: "100 GB gp3 · 7-day PITR",
        description: "Automated daily snapshots and Multi-AZ failover across Availability Zones.",
      },
      position: { x: 600, y: 655 },
    });

    nodes.push({
      id: "cnode-elasticache",
      type: "cache",
      parentId: "cgroup-storage",
      data: {
        label: "ElastiCache Redis 7.2",
        subtitle: "cache.t4g.small · Multi-AZ",
        description: "In-memory caching and session clustering with automated failover.",
      },
      position: { x: 960, y: 655 },
    });

    // Clean Cloud Pipeline Edges
    edges.push({ id: "ce-r53-alb", source: "cnode-route53", target: "cnode-alb", sourceHandle: "dev-bottom", targetHandle: "gw-top", type: "animatedFlow", animated: true });
    edges.push({ id: "ce-cf-alb", source: "cnode-cloudfront", target: "cnode-alb", sourceHandle: "dev-bottom", targetHandle: "gw-top", type: "animatedFlow", animated: true });

    edges.push({ id: "ce-alb-ecs1", source: "cnode-alb", target: "cecs-1", sourceHandle: "gw-bottom", targetHandle: "svc-top", type: "animatedFlow", animated: true });
    edges.push({ id: "ce-alb-ecs2", source: "cnode-alb", target: "cecs-2", sourceHandle: "gw-bottom", targetHandle: "svc-top", type: "animatedFlow", animated: true });
    edges.push({ id: "ce-alb-ecs3", source: "cnode-alb", target: "cecs-3", sourceHandle: "gw-bottom", targetHandle: "svc-top", type: "animatedFlow", animated: true });

    edges.push({ id: "ce-ecs1-ecs4", source: "cecs-1", target: "cecs-4", sourceHandle: "svc-bottom", targetHandle: "svc-top", type: "animatedFlow", animated: true });
    edges.push({ id: "ce-ecs2-ecs5", source: "cecs-2", target: "cecs-5", sourceHandle: "svc-bottom", targetHandle: "svc-top", type: "animatedFlow", animated: true });
    edges.push({ id: "ce-ecs3-ecs6", source: "cecs-3", target: "cecs-6", sourceHandle: "svc-bottom", targetHandle: "svc-top", type: "animatedFlow", animated: true });

    edges.push({ id: "ce-ecs-rds", source: "cecs-4", target: "cnode-rds", sourceHandle: "svc-bottom", targetHandle: "db-top", type: "animatedFlow", animated: true });
    edges.push({ id: "ce-ecs-cache", source: "cecs-5", target: "cnode-elasticache", sourceHandle: "svc-bottom", targetHandle: "cache-top", type: "animatedFlow", animated: true });
    edges.push({ id: "ce-gh-ecs", source: "cnode-github", target: "cecs-2", sourceHandle: "dev-right", targetHandle: "svc-left", type: "animatedFlow", data: { label: "Deploy ECR/ECS" }, animated: true });
    edges.push({ id: "ce-ecs-cw", source: "cecs-6", target: "cnode-cloudwatch", sourceHandle: "svc-left", targetHandle: "dev-right", type: "animatedFlow", data: { label: "Telemetry & Logs" }, animated: true });

    return applyColorThemesToGraph(nodes, edges);
  }

  // ── 5. SECURITY LLD ARCHITECTURE TOPOLOGY ──
  // Hierarchical Structure (Perimeter Guard -> Identity & Tokens -> RBAC Enforcement + Left Flank Audit/KMS)
  if (type === "security") {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Left Flank Division: Cryptographic Key Management & Audit Trail
    nodes.push({
      id: "secgroup-storage",
      type: "layerGroup",
      data: {
        label: "Audit & Key Management Guard",
        subtitle: "AWS KMS Customer Keys · Immutable Audit Trail · Token Blacklist",
        count: 3,
      },
      position: { x: 40, y: 30 },
      style: { width: 340, height: 640, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Top Center Division: Perimeter & Ingress Security Guard
    nodes.push({
      id: "secgroup-ingress",
      type: "layerGroup",
      data: {
        label: "Perimeter & Ingress Security Guard",
        subtitle: "WAF Rate Limiting · TLS 1.3 Strict Ingress",
        count: 2,
      },
      position: { x: 420, y: 30 },
      style: { width: 840, height: 180, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Center Division: Authentication & Cryptographic Token Engine
    nodes.push({
      id: "secgroup-identity",
      type: "layerGroup",
      data: {
        label: "Authentication & Cryptographic Token Engine",
        subtitle: "OAuth2 PKCE Flow · RS256 Asymmetric Signing",
        count: 2,
      },
      position: { x: 420, y: 230 },
      style: { width: 840, height: 180, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Bottom Center Division: Authorization & RBAC Enforcement
    nodes.push({
      id: "secgroup-authz",
      type: "layerGroup",
      data: {
        label: "Authorization & RBAC Permission Enforcer",
        subtitle: "Student · Librarian · Administrator Policies",
        count: 1,
      },
      position: { x: 420, y: 430 },
      style: { width: 840, height: 180, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Left Flank Nodes
    nodes.push({
      id: "secnode-kms",
      type: "database",
      parentId: "secgroup-storage",
      data: {
        engine: "AWS KMS",
        label: "AES-256 Encryption at Rest",
        schema: "Customer Managed Keys (CMK)",
        description: "Transparent envelope encryption for RDS databases and S3 storage.",
      },
      position: { x: 70, y: 100 },
    });

    nodes.push({
      id: "secnode-blacklist",
      type: "cache",
      parentId: "secgroup-storage",
      data: {
        label: "Redis Token Blacklist",
        subtitle: "Instant Session Revocation",
        description: "Maintains revoked JWT IDs for immediate logout enforcement.",
      },
      position: { x: 70, y: 300 },
    });

    nodes.push({
      id: "secnode-audit",
      type: "devops",
      parentId: "secgroup-storage",
      data: {
        label: "Immutable Audit Trail",
        role: "Append-only Transaction Logs",
        category: "monitoring",
        description: "3-year tamper-evident audit logging for all checkout and administrative actions.",
      },
      position: { x: 70, y: 500 },
    });

    // Perimeter (Layer 1)
    nodes.push({
      id: "secnode-waf",
      type: "gateway",
      parentId: "secgroup-ingress",
      data: {
        label: "AWS WAF + Rate Limiter",
        tech: "OWASP Top 10 · 100 RPS Threshold",
        description: "Inspects HTTP traffic, drops SQL injection/XSS attempts.",
      },
      position: { x: 470, y: 85 },
    });

    nodes.push({
      id: "secnode-tls",
      type: "gateway",
      parentId: "secgroup-ingress",
      data: {
        label: "TLS 1.3 Strict Ingress Guard",
        tech: "Strict Transport Security (HSTS)",
        description: "Full end-to-end cryptographic transport encryption.",
      },
      position: { x: 860, y: 85 },
    });

    // Identity Engine (Layer 2)
    nodes.push({
      id: "secnode-oauth",
      type: "service",
      parentId: "secgroup-identity",
      data: {
        code: "OAuth2 / PKCE",
        label: "OAuth2 & PKCE Gateway",
        tech: "Auth Code Flow · Zero Plaintext",
        protocol: "Authorization",
        description: "Authorizes student and admin login flows.",
      },
      position: { x: 470, y: 285 },
    });

    nodes.push({
      id: "secnode-jwt",
      type: "service",
      parentId: "secgroup-identity",
      data: {
        code: "JWT RS256",
        label: "JWT Asymmetric Token Authority",
        tech: "15m Access Token · 7d Refresh Token",
        protocol: "Token Authority",
        description: "Issues cryptographically signed RS256 JWT tokens.",
      },
      position: { x: 860, y: 285 },
    });

    // Authorization (Layer 3)
    nodes.push({
      id: "secnode-rbac",
      type: "service",
      parentId: "secgroup-authz",
      data: {
        code: "RBAC Guard",
        label: "RBAC Permission Enforcer",
        tech: "Student · Librarian · Administrator",
        protocol: "Policy Engine",
        description: "Validates granular route permissions on every microservice call.",
      },
      position: { x: 665, y: 485 },
    });

    // Pristine Symmetrical Defense-in-Depth Edges
    edges.push({ id: "sece-waf-oauth", source: "secnode-waf", target: "secnode-oauth", sourceHandle: "gw-bottom", targetHandle: "svc-top", type: "animatedFlow", animated: true });
    edges.push({ id: "sece-tls-jwt", source: "secnode-tls", target: "secnode-jwt", sourceHandle: "gw-bottom", targetHandle: "svc-top", type: "animatedFlow", animated: true });
    edges.push({ id: "sece-oauth-jwt", source: "secnode-oauth", target: "secnode-jwt", sourceHandle: "svc-right", targetHandle: "svc-left", type: "animatedFlow", data: { label: "PKCE Verify" }, animated: true });
    edges.push({ id: "sece-jwt-rbac", source: "secnode-jwt", target: "secnode-rbac", sourceHandle: "svc-bottom", targetHandle: "svc-top", type: "animatedFlow", data: { label: "Token Verify" }, animated: true });
    edges.push({ id: "sece-jwt-redis", source: "secnode-jwt", target: "secnode-blacklist", sourceHandle: "svc-left", targetHandle: "cache-right", type: "animatedFlow", data: { label: "Revocation Check" }, animated: true });
    edges.push({ id: "sece-rbac-kms", source: "secnode-rbac", target: "secnode-kms", sourceHandle: "svc-left", targetHandle: "db-right", type: "animatedFlow", data: { label: "CMK Decrypt" }, animated: true });
    edges.push({ id: "sece-rbac-audit", source: "secnode-rbac", target: "secnode-audit", sourceHandle: "svc-left", targetHandle: "dev-right", type: "animatedFlow", data: { label: "Audit Event" }, animated: true });

    return applyColorThemesToGraph(nodes, edges);
  }

  // Fallback for custom objects
  return parseHldToReactFlow(lldData);
}

