import type { Node, Edge } from "@xyflow/react";

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
    return { nodes, edges };
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

  // Container Group Bounding Boxes (Layer Backgrounds)
  nodes.push({
    id: "group-frontend",
    type: "layerGroup",
    data: { label: "Frontend Layer", count: 3 },
    position: { x: 490, y: 90 },
    style: { width: 440, height: 130, zIndex: -1, pointerEvents: "none" },
    draggable: false,
    selectable: false,
  });

  nodes.push({
    id: "group-gateway",
    type: "layerGroup",
    data: { label: "API & Security Layer", count: 1 },
    position: { x: 30, y: 260 },
    style: { width: 1360, height: 120, zIndex: -1, pointerEvents: "none" },
    draggable: false,
    selectable: false,
  });

  nodes.push({
    id: "group-devops",
    type: "layerGroup",
    data: { label: "Deployment & Observability", count: 3 },
    position: { x: 30, y: 410 },
    style: { width: 230, height: 490, zIndex: -1, pointerEvents: "none" },
    draggable: false,
    selectable: false,
  });

  nodes.push({
    id: "group-services",
    type: "layerGroup",
    data: { label: "Modular Layered Microservices", count: 6 },
    position: { x: 290, y: 410 },
    style: { width: 840, height: 350, zIndex: -1, pointerEvents: "none" },
    draggable: false,
    selectable: false,
  });

  nodes.push({
    id: "group-async",
    type: "layerGroup",
    data: { label: "Asynchronous Communication", count: 1 },
    position: { x: 1160, y: 530 },
    style: { width: 230, height: 130, zIndex: -1, pointerEvents: "none" },
    draggable: false,
    selectable: false,
  });

  nodes.push({
    id: "group-data",
    type: "layerGroup",
    data: { label: "Data & Persistence Layer", count: 2 },
    position: { x: 290, y: 800 },
    style: { width: 840, height: 130, zIndex: -1, pointerEvents: "none" },
    draggable: false,
    selectable: false,
  });

  // Entity Nodes
  // Actors
  nodes.push({
    id: "actor-student",
    type: "actor",
    data: { label: "Student / User", role: "Primary Web & Mobile Consumer", description: "Searches catalog, borrows books, views active loans" },
    position: { x: 540, y: 20 },
  });

  nodes.push({
    id: "actor-admin",
    type: "actor",
    data: { label: "Admin / Librarian", role: "Library Management Staff", description: "Manages catalog, inventory, fine overrides, and reporting" },
    position: { x: 730, y: 20 },
  });

  // Frontend App
  nodes.push({
    id: "node-frontend",
    type: "frontend",
    data: {
      label: "React / Next.js Web Application",
      tech: "Next.js App Router · Tailwind CSS · React 19",
      description: "Unified web client with server-side rendering and client interactivity.",
    },
    position: { x: 590, y: 130 },
  });

  // API Gateway
  nodes.push({
    id: "node-gateway",
    type: "gateway",
    data: {
      label: "API Gateway / Ingress NGINX",
      tech: "TLS 1.3 · Rate Limiting · RBAC Guard",
      description: "TLS termination, WAF rate limiting (100 RPS), and route orchestration.",
    },
    position: { x: 570, y: 285 },
  });

  // Microservices
  // Row 1 (SVC-02, SVC-03, SVC-05)
  nodes.push({
    id: "svc-2",
    type: "service",
    data: {
      code: microservices[1]?.code || "SVC-02",
      label: microservices[1]?.label || "Catalog & Search Service",
      tech: microservices[1]?.tech || "Elasticsearch Query Engine",
      protocol: "REST / HTTP2",
      description: microservices[1]?.desc,
    },
    position: { x: 480, y: 450 },
  });

  nodes.push({
    id: "svc-3",
    type: "service",
    data: {
      code: microservices[2]?.code || "SVC-03",
      label: microservices[2]?.label || "Circulation & Borrowing Service",
      tech: microservices[2]?.tech || "ACID Transactions",
      protocol: "gRPC / Internal",
      description: microservices[2]?.desc,
    },
    position: { x: 700, y: 450 },
  });

  nodes.push({
    id: "svc-5",
    type: "service",
    data: {
      code: microservices[4]?.code || "SVC-05",
      label: microservices[4]?.label || "Inventory & Asset Service",
      tech: microservices[4]?.tech || "RFID & Barcode Tracker",
      protocol: "REST / Internal",
      description: microservices[4]?.desc,
    },
    position: { x: 920, y: 450 },
  });

  // Row 2 (SVC-01, SVC-04, SVC-06)
  nodes.push({
    id: "svc-1",
    type: "service",
    data: {
      code: microservices[0]?.code || "SVC-01",
      label: microservices[0]?.label || "Authentication & Role Service",
      tech: microservices[0]?.tech || "JWT · OAuth2 · RBAC",
      protocol: "gRPC / HTTPS",
      description: microservices[0]?.desc,
    },
    position: { x: 310, y: 620 },
  });

  nodes.push({
    id: "svc-4",
    type: "service",
    data: {
      code: microservices[3]?.code || "SVC-04",
      label: microservices[3]?.label || "Notification & Reminder Service",
      tech: microservices[3]?.tech || "Async Event Worker",
      protocol: "Async Event Worker",
      description: microservices[3]?.desc,
    },
    position: { x: 570, y: 620 },
  });

  nodes.push({
    id: "svc-6",
    type: "service",
    data: {
      code: microservices[5]?.code || "SVC-06",
      label: microservices[5]?.label || "Reporting & Analytics Service",
      tech: microservices[5]?.tech || "BI Aggregations",
      protocol: "Async Consumer",
      description: microservices[5]?.desc,
    },
    position: { x: 830, y: 620 },
  });

  // RabbitMQ
  nodes.push({
    id: "node-rabbitmq",
    type: "queue",
    data: {
      label: "RabbitMQ Event Broker",
      subtitle: "Event Messaging · DLQ · Retry x3",
      description: "Asynchronous domain event streaming with dead-letter exchange and 3 retry attempts.",
    },
    position: { x: 1175, y: 570 },
  });

  // DevOps & Observability
  nodes.push({
    id: "node-github-actions",
    type: "devops",
    data: {
      label: "GitHub Actions",
      role: "Build · Test · Scan · Deploy",
      category: "cicd",
      description: "Automated linting, Pytest unit tests, Docker builds, and Trivy vulnerability scans.",
    },
    position: { x: 55, y: 450 },
  });

  nodes.push({
    id: "node-k8s",
    type: "devops",
    data: {
      label: "Kubernetes EKS / GKE",
      role: "Horizontal Pod Auto-Scaling",
      category: "k8s",
      description: "Container orchestration cluster with horizontal pod autoscaling (min 2, max 10).",
    },
    position: { x: 55, y: 580 },
  });

  nodes.push({
    id: "node-prometheus",
    type: "devops",
    data: {
      label: "Prometheus + Grafana",
      role: "OpenTelemetry Distributed Tracing",
      category: "monitoring",
      description: "Real-time metrics, CloudWatch container insights, and APM tracing.",
    },
    position: { x: 55, y: 720 },
  });

  // Data Layer (Unified Database Cluster + Redis Cache)
  const dataStrategy =
    hldJson.data_strategy && typeof hldJson.data_strategy === "object"
      ? (hldJson.data_strategy as Record<string, unknown>)
      : {};
  const primaryDb = String(dataStrategy.primary_database || "PostgreSQL 16");
  const cachingTier = String(dataStrategy.caching_tier || "Redis 7.2 Cluster");

  nodes.push({
    id: "node-database",
    type: "database",
    data: {
      engine: primaryDb,
      label: primaryDb.includes("PostgreSQL") ? "PostgreSQL Database" : primaryDb,
      schema: "Multi-Schema Relational Storage",
      description:
        "Centralized ACID relational persistence layer with schema isolation for domain services and automated backups.",
    },
    position: { x: 430, y: 835 },
  });

  nodes.push({
    id: "node-redis",
    type: "cache",
    data: {
      label: cachingTier,
      subtitle: "Cache · Session Tokens · PubSub",
      description: "In-memory caching for catalog search (300s TTL) and session tokens.",
    },
    position: { x: 730, y: 835 },
  });

  // Edges
  const edges: Edge[] = [
    { id: "e-act1-fe", source: "actor-student", target: "node-frontend", type: "animatedFlow", animated: true },
    { id: "e-act2-fe", source: "actor-admin", target: "node-frontend", type: "animatedFlow", animated: true },
    {
      id: "e-fe-gw",
      source: "node-frontend",
      target: "node-gateway",
      type: "animatedFlow",
      data: { label: "HTTPS / HTTP2 REST JSON" },
      animated: true,
    },
    { id: "e-gw-svc1", source: "node-gateway", target: "svc-1", type: "animatedFlow", animated: true },
    { id: "e-gw-svc2", source: "node-gateway", target: "svc-2", type: "animatedFlow", animated: true },
    { id: "e-gw-svc3", source: "node-gateway", target: "svc-3", type: "animatedFlow", animated: true },
    { id: "e-gw-svc4", source: "node-gateway", target: "svc-4", type: "animatedFlow", animated: true },
    { id: "e-gw-svc5", source: "node-gateway", target: "svc-5", type: "animatedFlow", animated: true },
    { id: "e-gw-svc6", source: "node-gateway", target: "svc-6", type: "animatedFlow", animated: true },

    {
      id: "e-svc3-q",
      source: "svc-3",
      target: "node-rabbitmq",
      type: "animatedFlow",
      data: { label: "Book Borrowed / Returned Events" },
      animated: true,
    },
    {
      id: "e-svc2-q",
      source: "svc-2",
      target: "node-rabbitmq",
      type: "animatedFlow",
      data: { label: "Catalog Events" },
      animated: true,
    },
    {
      id: "e-svc5-q",
      source: "svc-5",
      target: "node-rabbitmq",
      type: "animatedFlow",
      data: { label: "Inventory Events" },
      animated: true,
    },
    { id: "e-q-svc4", source: "node-rabbitmq", target: "svc-4", type: "animatedFlow", animated: true },
    { id: "e-q-svc6", source: "node-rabbitmq", target: "svc-6", type: "animatedFlow", animated: true },

    { id: "e-svc1-db", source: "svc-1", target: "node-database", type: "animatedFlow", animated: true },
    { id: "e-svc2-db", source: "svc-2", target: "node-database", type: "animatedFlow", animated: true },
    { id: "e-svc3-db", source: "svc-3", target: "node-database", type: "animatedFlow", animated: true },
    { id: "e-svc4-db", source: "svc-4", target: "node-database", type: "animatedFlow", animated: true },
    { id: "e-svc5-db", source: "svc-5", target: "node-database", type: "animatedFlow", animated: true },
    { id: "e-svc6-db", source: "svc-6", target: "node-database", type: "animatedFlow", animated: true },

    { id: "e-svc1-redis", source: "svc-1", target: "node-redis", type: "animatedFlow", animated: true },
    { id: "e-svc2-redis", source: "svc-2", target: "node-redis", type: "animatedFlow", animated: true },
    { id: "e-svc3-redis", source: "svc-3", target: "node-redis", type: "animatedFlow", animated: true },
    { id: "e-svc5-redis", source: "svc-5", target: "node-redis", type: "animatedFlow", animated: true },

    { id: "e-gh-k8s", source: "node-github-actions", target: "node-k8s", type: "animatedFlow", animated: true },
    { id: "e-k8s-gw", source: "node-k8s", target: "node-gateway", type: "animatedFlow", animated: true },
    { id: "e-gw-prom", source: "node-gateway", target: "node-prometheus", type: "animatedFlow", animated: true },
    { id: "e-svc1-prom", source: "svc-1", target: "node-prometheus", type: "animatedFlow", animated: true },
  ];

  return { nodes, edges };
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
  if (type === "backend") {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Layer Group Containers
    nodes.push({
      id: "bgroup-endpoints",
      type: "layerGroup",
      data: { label: "API Ingress & Router Endpoints", count: 5 },
      position: { x: 30, y: 30 },
      style: { width: 1300, height: 110, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "bgroup-services",
      type: "layerGroup",
      data: { label: "Domain Microservices Logic Layer", count: 6 },
      position: { x: 30, y: 170 },
      style: { width: 1300, height: 260, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "bgroup-repos",
      type: "layerGroup",
      data: { label: "Repository & Data Access Layer", count: 5 },
      position: { x: 30, y: 460 },
      style: { width: 1300, height: 110, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "bgroup-models",
      type: "layerGroup",
      data: { label: "Domain Models & Entity Schemas", count: 5 },
      position: { x: 30, y: 600 },
      style: { width: 1300, height: 110, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Endpoints (Layer 1)
    const endpoints = [
      { id: "bep-1", code: "POST", label: "/api/v1/auth/login", desc: "Authenticate user or staff and issue JWT RS256 tokens" },
      { id: "bep-2", code: "GET", label: "/api/v1/search-books", desc: "Fast indexed catalog search with pagination and filters" },
      { id: "bep-3", code: "POST", label: "/api/v1/borrow-books", desc: "Checkout borrow transaction with row-level locking" },
      { id: "bep-4", code: "POST", label: "/api/v1/return-books", desc: "Check-in book return and update loan status" },
      { id: "bep-5", code: "DELETE", label: "/api/v1/manage-catalog", desc: "Librarian administrative add/remove catalog items" },
    ];

    endpoints.forEach((ep, idx) => {
      nodes.push({
        id: ep.id,
        type: "service",
        data: {
          code: ep.code,
          label: ep.label,
          tech: "HTTP/2 REST · FastAPI Router",
          protocol: "Public Ingress",
          description: ep.desc,
        },
        position: { x: 50 + idx * 250, y: 50 },
      });
    });

    // Services (Layer 2)
    const services = [
      { id: "bsvc-1", code: "SVC-01", label: "Authentication & Role Service", tech: "JWT · OAuth2 · RBAC Guard", desc: "Handles authentication, tokens, and permission verification." },
      { id: "bsvc-2", code: "SVC-02", label: "Catalog & Search Service", tech: "Elasticsearch · Query Engine", desc: "Catalog queries, metadata indexing, and inventory status." },
      { id: "bsvc-3", code: "SVC-03", label: "Circulation & Borrowing Service", tech: "ACID Orchestration · State Machine", desc: "Coordinates checkouts and returns using distributed transactions." },
      { id: "bsvc-4", code: "SVC-04", label: "Notification & Reminder Service", tech: "Async Event Worker · BullMQ", desc: "Dispatches automated overdue notices and hold alerts." },
      { id: "bsvc-5", code: "SVC-05", label: "Inventory & Asset Service", tech: "RFID · Barcode Tracker", desc: "Tracks physical book copies and shelf allocation." },
      { id: "bsvc-6", code: "SVC-06", label: "Reporting & Analytics Service", tech: "Aggregations · BI Pipeline", desc: "Generates circulation metrics and usage BI dashboards." },
    ];

    services.slice(0, 3).forEach((svc, idx) => {
      nodes.push({
        id: svc.id,
        type: "service",
        data: {
          code: svc.code,
          label: svc.label,
          tech: svc.tech,
          protocol: "Domain Service",
          description: svc.desc,
        },
        position: { x: 80 + idx * 400, y: 190 },
      });
    });

    services.slice(3, 6).forEach((svc, idx) => {
      nodes.push({
        id: svc.id,
        type: "service",
        data: {
          code: svc.code,
          label: svc.label,
          tech: svc.tech,
          protocol: "Domain Service",
          description: svc.desc,
        },
        position: { x: 80 + idx * 400, y: 310 },
      });
    });

    // Repositories (Layer 3)
    const repos = [
      { id: "brepo-1", label: "UserRepository", entity: "User Entity", desc: "SQLAlchemy 2.0 Async repository for users" },
      { id: "brepo-2", label: "BooksRepository", entity: "Books Entity", desc: "SQLAlchemy 2.0 Async repository for books" },
      { id: "brepo-3", label: "BookLoanRepository", entity: "BookLoan Entity", desc: "SQLAlchemy 2.0 Async repository for book loans" },
      { id: "brepo-4", label: "BorrowRepository", entity: "Borrow Entity", desc: "SQLAlchemy 2.0 Async repository for borrow transactions" },
      { id: "brepo-5", label: "ReturnRepository", entity: "Return Entity", desc: "SQLAlchemy 2.0 Async repository for return events" },
    ];

    repos.forEach((repo, idx) => {
      nodes.push({
        id: repo.id,
        type: "database",
        data: {
          engine: "SQLAlchemy ORM",
          label: repo.label,
          schema: repo.entity,
          description: repo.desc,
        },
        position: { x: 50 + idx * 250, y: 480 },
      });
    });

    // Domain Models (Layer 4)
    const models = [
      { id: "bmodel-1", label: "User Model", table: "users table", desc: "id, username, email, hashed_password, role, created_at" },
      { id: "bmodel-2", label: "Books Model", table: "books table", desc: "id, user_id, name, status, description, created_at" },
      { id: "bmodel-3", label: "BookLoan Model", table: "book_loans table", desc: "id, user_id, name, status, created_at, updated_at" },
      { id: "bmodel-4", label: "Borrow Model", table: "borrows table", desc: "id, user_id, name, status, created_at" },
      { id: "bmodel-5", label: "Return Model", table: "returns table", desc: "id, user_id, name, status, created_at" },
    ];

    models.forEach((model, idx) => {
      nodes.push({
        id: model.id,
        type: "database",
        data: {
          engine: "PostgreSQL 16",
          label: model.label,
          schema: model.table,
          description: model.desc,
        },
        position: { x: 50 + idx * 250, y: 620 },
      });
    });

    // Connections
    edges.push({ id: "be-ep1-s1", source: "bep-1", target: "bsvc-1", type: "animatedFlow", animated: true });
    edges.push({ id: "be-ep2-s2", source: "bep-2", target: "bsvc-2", type: "animatedFlow", animated: true });
    edges.push({ id: "be-ep3-s3", source: "bep-3", target: "bsvc-3", type: "animatedFlow", animated: true });
    edges.push({ id: "be-ep4-s3", source: "bep-4", target: "bsvc-3", type: "animatedFlow", animated: true });
    edges.push({ id: "be-ep5-s2", source: "bep-5", target: "bsvc-2", type: "animatedFlow", animated: true });

    edges.push({ id: "be-s1-r1", source: "bsvc-1", target: "brepo-1", type: "animatedFlow", animated: true });
    edges.push({ id: "be-s2-r2", source: "bsvc-2", target: "brepo-2", type: "animatedFlow", animated: true });
    edges.push({ id: "be-s3-r3", source: "bsvc-3", target: "brepo-3", type: "animatedFlow", animated: true });
    edges.push({ id: "be-s3-r4", source: "bsvc-3", target: "brepo-4", type: "animatedFlow", animated: true });
    edges.push({ id: "be-s3-r5", source: "bsvc-3", target: "brepo-5", type: "animatedFlow", animated: true });

    edges.push({ id: "be-r1-m1", source: "brepo-1", target: "bmodel-1", type: "animatedFlow", animated: true });
    edges.push({ id: "be-r2-m2", source: "brepo-2", target: "bmodel-2", type: "animatedFlow", animated: true });
    edges.push({ id: "be-r3-m3", source: "brepo-3", target: "bmodel-3", type: "animatedFlow", animated: true });
    edges.push({ id: "be-r4-m4", source: "brepo-4", target: "bmodel-4", type: "animatedFlow", animated: true });
    edges.push({ id: "be-r5-m5", source: "brepo-5", target: "bmodel-5", type: "animatedFlow", animated: true });

    return { nodes, edges };
  }

  // ── 2. DATABASE LLD ARCHITECTURE TOPOLOGY ──
  if (type === "database") {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Layer Group Containers
    nodes.push({
      id: "dbgroup-tables",
      type: "layerGroup",
      data: { label: "Relational Schema Tables (PostgreSQL 16 Multi-AZ)", count: 5 },
      position: { x: 30, y: 30 },
      style: { width: 900, height: 420, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "dbgroup-cache",
      type: "layerGroup",
      data: { label: "In-Memory Cache Tier", count: 1 },
      position: { x: 960, y: 30 },
      style: { width: 370, height: 180, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "dbgroup-pooling",
      type: "layerGroup",
      data: { label: "Connection Pool & Migrations", count: 2 },
      position: { x: 960, y: 240 },
      style: { width: 370, height: 210, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Database Tables
    const tables = [
      { id: "dtbl-users", name: "users", cols: "id (UUID PK) · username (UQ) · email (UQ) · role · password", desc: "User accounts, auth credentials, and roles" },
      { id: "dtbl-books", name: "books", cols: "id (UUID PK) · user_id (FK) · name · status · description", desc: "Book catalog master items and availability status" },
      { id: "dtbl-loans", name: "book_loans", cols: "id (UUID PK) · user_id (FK) · name · status · created_at", desc: "Active and historical book loan records" },
      { id: "dtbl-borrows", name: "borrows", cols: "id (UUID PK) · user_id (FK) · name · status · borrow_date", desc: "Book checkout transaction events" },
      { id: "dtbl-returns", name: "returns", cols: "id (UUID PK) · user_id (FK) · name · status · return_date", desc: "Book check-in transaction events" },
    ];

    tables.slice(0, 3).forEach((t, idx) => {
      nodes.push({
        id: t.id,
        type: "database",
        data: {
          engine: "PostgreSQL 16",
          label: `Table: ${t.name}`,
          schema: t.cols,
          description: t.desc,
        },
        position: { x: 50 + idx * 280, y: 60 },
      });
    });

    tables.slice(3, 5).forEach((t, idx) => {
      nodes.push({
        id: t.id,
        type: "database",
        data: {
          engine: "PostgreSQL 16",
          label: `Table: ${t.name}`,
          schema: t.cols,
          description: t.desc,
        },
        position: { x: 190 + idx * 280, y: 260 },
      });
    });

    // Redis Cache Node
    nodes.push({
      id: "dnode-redis",
      type: "cache",
      data: {
        label: "Redis 7.2 Cluster",
        subtitle: "search (300s) · session (900s) · loans (120s)",
        description: "Write-through invalidation and multi-instance Pub/Sub fan-out.",
      },
      position: { x: 990, y: 70 },
    });

    // PgBouncer Pool Node
    nodes.push({
      id: "dnode-pgbouncer",
      type: "gateway",
      data: {
        label: "PgBouncer Connection Pool",
        tech: "20 min, 50 max · Asyncpg Driver",
        description: "Transaction pooling with Read Committed isolation and row-level locking.",
      },
      position: { x: 990, y: 270 },
    });

    nodes.push({
      id: "dnode-alembic",
      type: "devops",
      data: {
        label: "Alembic Versioned Migrations",
        role: "Sequential Revision Tracking",
        category: "cicd",
        description: "Automated schema migrations executed in pre-deployment CI/CD hooks.",
      },
      position: { x: 990, y: 360 },
    });

    // Edges
    edges.push({ id: "de-u-books", source: "dtbl-users", target: "dtbl-books", type: "animatedFlow", data: { label: "1:N Foreign Key" }, animated: true });
    edges.push({ id: "de-u-loans", source: "dtbl-users", target: "dtbl-loans", type: "animatedFlow", data: { label: "1:N Foreign Key" }, animated: true });
    edges.push({ id: "de-u-borrows", source: "dtbl-users", target: "dtbl-borrows", type: "animatedFlow", data: { label: "1:N Foreign Key" }, animated: true });
    edges.push({ id: "de-u-returns", source: "dtbl-users", target: "dtbl-returns", type: "animatedFlow", data: { label: "1:N Foreign Key" }, animated: true });
    edges.push({ id: "de-books-cache", source: "dtbl-books", target: "dnode-redis", type: "animatedFlow", data: { label: "Cache Invalidation" }, animated: true });
    edges.push({ id: "de-pgb-users", source: "dnode-pgbouncer", target: "dtbl-users", type: "animatedFlow", animated: true });

    return { nodes, edges };
  }

  // ── 3. FRONTEND LLD ARCHITECTURE TOPOLOGY ──
  if (type === "frontend") {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Layer Group Containers
    nodes.push({
      id: "fgroup-pages",
      type: "layerGroup",
      data: { label: "Next.js 16 App Router (Pages & Routes)", count: 5 },
      position: { x: 30, y: 30 },
      style: { width: 1300, height: 110, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "fgroup-components",
      type: "layerGroup",
      data: { label: "Modular Tailwind UI Components", count: 5 },
      position: { x: 30, y: 170 },
      style: { width: 1300, height: 110, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "fgroup-state",
      type: "layerGroup",
      data: { label: "Client State & Server Cache", count: 2 },
      position: { x: 30, y: 310 },
      style: { width: 630, height: 120, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "fgroup-api",
      type: "layerGroup",
      data: { label: "API Client & Transport Security", count: 2 },
      position: { x: 700, y: 310 },
      style: { width: 630, height: 120, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Pages (Layer 1)
    const pages = [
      { id: "fpg-1", name: "LoginPage", route: "/login", desc: "Authentication form with student/admin role login" },
      { id: "fpg-2", name: "SearchBooksPage", route: "/search-books", desc: "Dynamic catalog search, availability filters, and cards" },
      { id: "fpg-3", name: "BorrowBooksPage", route: "/borrow-books", desc: "Circulation checkout & active loan management" },
      { id: "fpg-4", name: "ReturnBooksPage", route: "/return-books", desc: "Book return scanning and check-in confirmation" },
      { id: "fpg-5", name: "CatalogAdminPage", route: "/manage-catalog", desc: "Librarian catalog CRUD and asset management" },
    ];

    pages.forEach((p, idx) => {
      nodes.push({
        id: p.id,
        type: "frontend",
        data: {
          label: p.name,
          tech: p.route,
          description: p.desc,
        },
        position: { x: 50 + idx * 250, y: 50 },
      });
    });

    // Components (Layer 2)
    const components = [
      { id: "fcmp-1", name: "Navbar & AuthStatus", desc: "Global header with navigation links and token state" },
      { id: "fcmp-2", name: "BookCatalogCard", desc: "Reusable presentation card for book search results" },
      { id: "fcmp-3", name: "BorrowConfirmModal", desc: "Interactive dialog confirming loan due dates" },
      { id: "fcmp-4", name: "ReturnScannerModal", desc: "Barcode/RFID scanner dialog for book returns" },
      { id: "fcmp-5", name: "LoanHistoryTable", desc: "Paginated table showing active and past loans" },
    ];

    components.forEach((c, idx) => {
      nodes.push({
        id: c.id,
        type: "service",
        data: {
          code: "UI Component",
          label: c.name,
          tech: "React 19 · Tailwind CSS",
          protocol: "Client View",
          description: c.desc,
        },
        position: { x: 50 + idx * 250, y: 190 },
      });
    });

    // State & API (Layer 3)
    nodes.push({
      id: "fnode-zustand",
      type: "cache",
      data: {
        label: "Zustand Global Store",
        subtitle: "AuthSession · UIState · DarkTheme",
        description: "Lightweight reactive client store managing active user and navigation state.",
      },
      position: { x: 60, y: 340 },
    });

    nodes.push({
      id: "fnode-tanstack",
      type: "service",
      data: {
        code: "React Query",
        label: "TanStack Query Cache",
        tech: "Auto Invalidation & Refetch",
        protocol: "Server State",
        description: "Cached API queries with background revalidation and optimistic updates.",
      },
      position: { x: 370, y: 340 },
    });

    nodes.push({
      id: "fnode-axios",
      type: "gateway",
      data: {
        label: "Axios API Interceptor",
        tech: "Bearer Token Injection · Error Toasts",
        description: "Centralized HTTP client with automatic Authorization header injection.",
      },
      position: { x: 730, y: 340 },
    });

    nodes.push({
      id: "fnode-zod",
      type: "service",
      data: {
        code: "Zod Validator",
        label: "React Hook Form + Zod",
        tech: "Strict Client Schema Validation",
        protocol: "Form State",
        description: "Type-safe form inputs and field-level error messages.",
      },
      position: { x: 1040, y: 340 },
    });

    // Edges
    edges.push({ id: "fe-p1-c1", source: "fpg-1", target: "fcmp-1", type: "animatedFlow", animated: true });
    edges.push({ id: "fe-p2-c2", source: "fpg-2", target: "fcmp-2", type: "animatedFlow", animated: true });
    edges.push({ id: "fe-p3-c3", source: "fpg-3", target: "fcmp-3", type: "animatedFlow", animated: true });
    edges.push({ id: "fe-p4-c4", source: "fpg-4", target: "fcmp-4", type: "animatedFlow", animated: true });
    edges.push({ id: "fe-p5-c5", source: "fpg-5", target: "fcmp-5", type: "animatedFlow", animated: true });

    edges.push({ id: "fe-c1-zustand", source: "fcmp-1", target: "fnode-zustand", type: "animatedFlow", animated: true });
    edges.push({ id: "fe-c2-tanstack", source: "fcmp-2", target: "fnode-tanstack", type: "animatedFlow", animated: true });
    edges.push({ id: "fe-tanstack-axios", source: "fnode-tanstack", target: "fnode-axios", type: "animatedFlow", animated: true });
    edges.push({ id: "fe-c3-zod", source: "fcmp-3", target: "fnode-zod", type: "animatedFlow", animated: true });

    return { nodes, edges };
  }

  // ── 4. CLOUD LLD ARCHITECTURE TOPOLOGY (AWS ECS Fargate) ──
  if (type === "cloud") {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Layer Group Containers
    nodes.push({
      id: "cgroup-edge",
      type: "layerGroup",
      data: { label: "Edge & DNS Layer (Route 53 + CloudFront CDN)", count: 2 },
      position: { x: 30, y: 30 },
      style: { width: 1300, height: 100, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "cgroup-alb",
      type: "layerGroup",
      data: { label: "Ingress & Traffic Routing (Application Load Balancer)", count: 1 },
      position: { x: 30, y: 150 },
      style: { width: 1300, height: 100, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "cgroup-compute",
      type: "layerGroup",
      data: { label: "Serverless Container Tasks (AWS ECS on Fargate - 6 Services)", count: 6 },
      position: { x: 30, y: 270 },
      style: { width: 1300, height: 260, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "cgroup-data",
      type: "layerGroup",
      data: { label: "Managed Storage Tier (RDS Multi-AZ + ElastiCache)", count: 2 },
      position: { x: 30, y: 550 },
      style: { width: 680, height: 120, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "cgroup-devops",
      type: "layerGroup",
      data: { label: "CI/CD & Monitoring (GitHub Actions + CloudWatch)", count: 2 },
      position: { x: 740, y: 550 },
      style: { width: 590, height: 120, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Edge & DNS (Layer 1)
    nodes.push({
      id: "cnode-route53",
      type: "devops",
      data: { label: "AWS Route 53 + ACM", role: "DNS & TLS 1.3 Termination", category: "cicd", description: "Public hosted zone with automated TLS 1.3 certificates." },
      position: { x: 260, y: 50 },
    });

    nodes.push({
      id: "cnode-cloudfront",
      type: "devops",
      data: { label: "CloudFront CDN + S3 Bucket", role: "Static Assets & Media", category: "cicd", description: "Global edge CDN fronting private S3 bucket." },
      position: { x: 780, y: 50 },
    });

    // Ingress ALB (Layer 2)
    nodes.push({
      id: "cnode-alb",
      type: "gateway",
      data: { label: "AWS Application Load Balancer", tech: "WAF Associated · 100 RPS Rate Limit · Multi-AZ", description: "Dual-AZ Public Subnet Ingress Load Balancer with path routing." },
      position: { x: 500, y: 170 },
    });

    // ECS Fargate Tasks (Layer 3)
    const ecsTasks = [
      { id: "cecs-1", code: "ECS Task", label: "svc-auth Fargate Task", tech: "0.5 vCPU, 1 GB RAM", desc: "ECR Image: svc-auth:latest · Auto Scaling (min 2, max 10)" },
      { id: "cecs-2", code: "ECS Task", label: "svc-catalog Fargate Task", tech: "0.5 vCPU, 1 GB RAM", desc: "ECR Image: svc-catalog:latest · Auto Scaling (min 2, max 10)" },
      { id: "cecs-3", code: "ECS Task", label: "svc-circulation Fargate Task", tech: "0.5 vCPU, 1 GB RAM", desc: "ECR Image: svc-circulation:latest · Auto Scaling (min 2, max 10)" },
      { id: "cecs-4", code: "ECS Task", label: "svc-notification Fargate Task", tech: "0.5 vCPU, 1 GB RAM", desc: "ECR Image: svc-notification:latest · Auto Scaling (min 2, max 10)" },
      { id: "cecs-5", code: "ECS Task", label: "svc-inventory Fargate Task", tech: "0.5 vCPU, 1 GB RAM", desc: "ECR Image: svc-inventory:latest · Auto Scaling (min 2, max 10)" },
      { id: "cecs-6", code: "ECS Task", label: "svc-reporting Fargate Task", tech: "0.5 vCPU, 1 GB RAM", desc: "ECR Image: svc-reporting:latest · Auto Scaling (min 2, max 10)" },
    ];

    ecsTasks.slice(0, 3).forEach((task, idx) => {
      nodes.push({
        id: task.id,
        type: "service",
        data: {
          code: task.code,
          label: task.label,
          tech: task.tech,
          protocol: "Fargate Task",
          description: task.desc,
        },
        position: { x: 80 + idx * 400, y: 290 },
      });
    });

    ecsTasks.slice(3, 6).forEach((task, idx) => {
      nodes.push({
        id: task.id,
        type: "service",
        data: {
          code: task.code,
          label: task.label,
          tech: task.tech,
          protocol: "Fargate Task",
          description: task.desc,
        },
        position: { x: 80 + idx * 400, y: 410 },
      });
    });

    // Managed Data Tier (Layer 4)
    nodes.push({
      id: "cnode-rds",
      type: "database",
      data: {
        engine: "AWS RDS PostgreSQL 16",
        label: "RDS db.t4g.medium Multi-AZ",
        schema: "100 GB gp3 · 7-day PITR",
        description: "Automated daily snapshots and Multi-AZ failover across Availability Zones.",
      },
      position: { x: 60, y: 580 },
    });

    nodes.push({
      id: "cnode-elasticache",
      type: "cache",
      data: {
        label: "ElastiCache Redis 7.2",
        subtitle: "cache.t4g.small · Multi-AZ",
        description: "In-memory caching and session clustering with automated failover.",
      },
      position: { x: 390, y: 580 },
    });

    // CI/CD & Monitoring (Layer 5)
    nodes.push({
      id: "cnode-github",
      type: "devops",
      data: {
        label: "GitHub Actions CI/CD",
        role: "Ruff · Pytest · Docker · Trivy · ECR",
        category: "cicd",
        description: "Automated test gating, vulnerability scans, and ECS rolling deployments.",
      },
      position: { x: 770, y: 580 },
    });

    nodes.push({
      id: "cnode-cloudwatch",
      type: "devops",
      data: {
        label: "AWS CloudWatch & SNS Alerts",
        role: "Container Insights · SNS Alerts",
        category: "monitoring",
        description: "Task CPU/Memory tracking, 5xx error rate alarms, and SNS push alerts.",
      },
      position: { x: 1060, y: 580 },
    });

    // Edges
    edges.push({ id: "ce-r53-alb", source: "cnode-route53", target: "cnode-alb", type: "animatedFlow", animated: true });
    edges.push({ id: "ce-cf-alb", source: "cnode-cloudfront", target: "cnode-alb", type: "animatedFlow", animated: true });

    edges.push({ id: "ce-alb-ecs1", source: "cnode-alb", target: "cecs-1", type: "animatedFlow", animated: true });
    edges.push({ id: "ce-alb-ecs2", source: "cnode-alb", target: "cecs-2", type: "animatedFlow", animated: true });
    edges.push({ id: "ce-alb-ecs3", source: "cnode-alb", target: "cecs-3", type: "animatedFlow", animated: true });
    edges.push({ id: "ce-alb-ecs4", source: "cnode-alb", target: "cecs-4", type: "animatedFlow", animated: true });
    edges.push({ id: "ce-alb-ecs5", source: "cnode-alb", target: "cecs-5", type: "animatedFlow", animated: true });
    edges.push({ id: "ce-alb-ecs6", source: "cnode-alb", target: "cecs-6", type: "animatedFlow", animated: true });

    edges.push({ id: "ce-ecs-rds", source: "cecs-1", target: "cnode-rds", type: "animatedFlow", animated: true });
    edges.push({ id: "ce-ecs-cache", source: "cecs-2", target: "cnode-elasticache", type: "animatedFlow", animated: true });
    edges.push({ id: "ce-gh-ecs", source: "cnode-github", target: "cecs-1", type: "animatedFlow", data: { label: "Deploy to ECR/ECS" }, animated: true });
    edges.push({ id: "ce-ecs-cw", source: "cecs-6", target: "cnode-cloudwatch", type: "animatedFlow", data: { label: "Telemetry & Logs" }, animated: true });

    return { nodes, edges };
  }

  // ── 5. SECURITY LLD ARCHITECTURE TOPOLOGY ──
  if (type === "security") {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Layer Group Containers
    nodes.push({
      id: "secgroup-ingress",
      type: "layerGroup",
      data: { label: "Perimeter & Ingress Security Guard", count: 2 },
      position: { x: 30, y: 30 },
      style: { width: 1300, height: 110, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "secgroup-identity",
      type: "layerGroup",
      data: { label: "Authentication & Cryptographic Token Engine", count: 2 },
      position: { x: 30, y: 170 },
      style: { width: 1300, height: 110, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "secgroup-authz",
      type: "layerGroup",
      data: { label: "Authorization & Token Revocation", count: 2 },
      position: { x: 30, y: 310 },
      style: { width: 1300, height: 110, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "secgroup-protection",
      type: "layerGroup",
      data: { label: "Data Protection & Audit Trail", count: 2 },
      position: { x: 30, y: 450 },
      style: { width: 1300, height: 110, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Ingress (Layer 1)
    nodes.push({
      id: "secnode-waf",
      type: "gateway",
      data: {
        label: "AWS WAF + Rate Limiter",
        tech: "OWASP Top 10 · 100 RPS Threshold",
        description: "Inspects HTTP traffic, drops SQL injection/XSS attempts.",
      },
      position: { x: 260, y: 50 },
    });

    nodes.push({
      id: "secnode-tls",
      type: "gateway",
      data: {
        label: "TLS 1.3 Strict Ingress Guard",
        tech: "Strict Transport Security (HSTS)",
        description: "Full end-to-end cryptographic transport encryption.",
      },
      position: { x: 780, y: 50 },
    });

    // Identity Engine (Layer 2)
    nodes.push({
      id: "secnode-oauth",
      type: "service",
      data: {
        code: "OAuth2 / PKCE",
        label: "OAuth2 & PKCE Gateway",
        tech: "Auth Code Flow · Zero Plaintext",
        protocol: "Authorization",
        description: "Authorizes student and admin login flows.",
      },
      position: { x: 260, y: 190 },
    });

    nodes.push({
      id: "secnode-jwt",
      type: "service",
      data: {
        code: "JWT RS256",
        label: "JWT Asymmetric Token Authority",
        tech: "15m Access Token · 7d Refresh Token",
        protocol: "Token Authority",
        description: "Issues cryptographically signed RS256 JWT tokens.",
      },
      position: { x: 780, y: 190 },
    });

    // Authorization & Revocation (Layer 3)
    nodes.push({
      id: "secnode-rbac",
      type: "service",
      data: {
        code: "RBAC Guard",
        label: "RBAC Permission Enforcer",
        tech: "Student · Librarian · Administrator",
        protocol: "Policy Engine",
        description: "Validates granular route permissions on every microservice call.",
      },
      position: { x: 260, y: 330 },
    });

    nodes.push({
      id: "secnode-blacklist",
      type: "cache",
      data: {
        label: "Redis Token Blacklist",
        subtitle: "Instant Session Revocation",
        description: "Maintains revoked JWT IDs for immediate logout enforcement.",
      },
      position: { x: 780, y: 330 },
    });

    // Data Protection (Layer 4)
    nodes.push({
      id: "secnode-kms",
      type: "database",
      data: {
        engine: "AWS KMS",
        label: "AES-256 Encryption at Rest",
        schema: "Customer Managed Keys (CMK)",
        description: "Transparent encryption for RDS databases and S3 storage.",
      },
      position: { x: 260, y: 470 },
    });

    nodes.push({
      id: "secnode-audit",
      type: "devops",
      data: {
        label: "Immutable Audit Trail",
        role: "Append-only Transaction Logs",
        category: "monitoring",
        description: "3-year tamper-evident audit logging for all checkout and administrative actions.",
      },
      position: { x: 780, y: 470 },
    });

    // Edges
    edges.push({ id: "sece-waf-oauth", source: "secnode-waf", target: "secnode-oauth", type: "animatedFlow", animated: true });
    edges.push({ id: "sece-tls-jwt", source: "secnode-tls", target: "secnode-jwt", type: "animatedFlow", animated: true });
    edges.push({ id: "sece-oauth-jwt", source: "secnode-oauth", target: "secnode-jwt", type: "animatedFlow", animated: true });
    edges.push({ id: "sece-jwt-rbac", source: "secnode-jwt", target: "secnode-rbac", type: "animatedFlow", animated: true });
    edges.push({ id: "sece-jwt-redis", source: "secnode-jwt", target: "secnode-blacklist", type: "animatedFlow", animated: true });
    edges.push({ id: "sece-rbac-kms", source: "secnode-rbac", target: "secnode-kms", type: "animatedFlow", animated: true });
    edges.push({ id: "sece-rbac-audit", source: "secnode-rbac", target: "secnode-audit", type: "animatedFlow", animated: true });

    return { nodes, edges };
  }

  // Fallback for custom objects
  return parseHldToReactFlow(lldData);
}
