/**
 * Predefined Dummy Architecture Payloads for HLD and 5 LLDs
 * Provided for instant end-to-end visualization, graphic testing, and offline verification.
 */

export const dummyHld = {
  architecture_style: "Modular Layered Microservices",
  executive_summary:
    "Enable students to search, borrow, and return books through a web application is designed as an enterprise-grade Modular Layered Microservices architecture for Education & Library Management. The system isolates core domain workflows into resilient, independently deployable services backed by PostgreSQL 16 and Redis 7.2 Cluster.",
  business_goals: [
    "Achieve 99.9% system availability for Education & Library Management operations.",
    "Ensure sub-250ms p95 response time under concurrent user load.",
    "Enforce strict transaction consistency and data auditability.",
  ],
  major_services: [
    {
      service_id: "SVC-01",
      name: "Authentication & Role Service",
      responsibility: "Handles core domain transactions and workflows for authentication & role service.",
      database_binding: "authentication_db_schema",
      scaling_model: "Horizontal Stateless Pods (min 2, max 10)",
      satisfies: ["FR-009"],
    },
    {
      service_id: "SVC-02",
      name: "Catalog & Search Service",
      responsibility: "Handles core domain transactions and workflows for catalog & search service.",
      database_binding: "catalog_db_schema",
      scaling_model: "Horizontal Stateless Pods (min 2, max 10)",
      satisfies: ["FR-001"],
    },
    {
      service_id: "SVC-03",
      name: "Circulation & Borrowing Service",
      responsibility: "Handles core domain transactions and workflows for circulation & borrowing service.",
      database_binding: "circulation_db_schema",
      scaling_model: "Horizontal Stateless Pods (min 2, max 10)",
      satisfies: ["FR-001"],
    },
    {
      service_id: "SVC-04",
      name: "Notification & Reminder Service",
      responsibility: "Handles core domain transactions and workflows for notification & reminder service.",
      database_binding: "notification_db_schema",
      scaling_model: "Horizontal Stateless Pods (min 2, max 10)",
      satisfies: ["FR-001"],
    },
    {
      service_id: "SVC-05",
      name: "Inventory & Asset Service",
      responsibility: "Handles core domain transactions and workflows for inventory & asset service.",
      database_binding: "inventory_db_schema",
      scaling_model: "Horizontal Stateless Pods (min 2, max 10)",
      satisfies: ["FR-001"],
    },
    {
      service_id: "SVC-06",
      name: "Reporting & Analytics Service",
      responsibility: "Handles core domain transactions and workflows for reporting & analytics service.",
      database_binding: "reporting_db_schema",
      scaling_model: "Horizontal Stateless Pods (min 2, max 10)",
      satisfies: ["FR-001"],
    },
  ],
  communication_patterns: [
    {
      pattern: "Synchronous REST / JSON over TLS",
      usage: "Client-to-Gateway and Gateway-to-Core Service request-response APIs",
      protocol: "HTTP/2, OpenAPI 3.0",
      resilience: "Circuit breaker (50% failure threshold), 2500ms timeout",
    },
    {
      pattern: "Asynchronous Event Messaging",
      usage: "Domain event notification reminders, transaction history audits, and background tasks",
      protocol: "RabbitMQ / Redis PubSub",
      resilience: "Dead-letter exchange with exponential retry backoff (3 attempts)",
    },
  ],
  data_strategy: {
    primary_database: "PostgreSQL 16",
    caching_tier: "Redis 7.2 Cluster",
    replication: "Primary-Replica configuration with automated failover and read-replica offloading",
    migration_tool: "Alembic Versioned Migrations",
    backup_policy: "Point-in-Time Recovery (PITR) with continuous WAL archiving and daily full snapshots",
  },
  security_overview: {
    authentication: "Stateless JWT access tokens with Redis-backed refresh token rotation",
    authorization: "Role-Based Access Control (RBAC) enforced at API Gateway and Service boundary",
    data_protection: "AES-256 encryption at rest, TLS 1.3 encryption in transit",
    audit_logging: "Immutable audit log trail for all administrative and modification transactions",
  },
  deployment_strategy: {
    infrastructure: "Kubernetes Container Orchestration (EKS/GKE)",
    ingress: "Ingress-NGINX with TLS Termination and Rate Limiting",
    ci_cd: "GitHub Actions automated build, container vulnerability scan, and rolling deployment",
    monitoring: "Prometheus metrics, Grafana dashboards, OpenTelemetry distributed tracing",
  },
  technology_stack: {
    backend: {
      selected_option: "FastAPI (Python 3.12)",
      reasoning: "Asynchronous high-performance framework with native OpenAPI schema generation and typed Pydantic data validation.",
    },
    frontend: {
      selected_option: "React (Next.js App Router)",
      reasoning: "Component modularity, server-side rendering for catalog search performance, and rich ecosystem.",
    },
    database: {
      selected_option: "PostgreSQL 16 (Relational ACID)",
      reasoning: "ACID compliance for critical domain workflows, row-level locking for transactional state concurrency, and JSONB support.",
    },
    cache: {
      selected_option: "Redis 7.2 (In-Memory Key-Value)",
      reasoning: "High-throughput in-memory caching for low-latency search queries and distributed session state.",
    },
    authentication: {
      selected_option: "OAuth2 with Authorization Code Flow & PKCE (JWT RS256)",
      reasoning: "Stateless token authorization, fine-grained role-based access control (RBAC), and zero plain-text token exposure.",
    },
    cloud: {
      selected_option: "AWS (ECS Fargate & Managed RDS PostgreSQL)",
      reasoning: "Serverless container orchestration eliminating OS management overhead with automated Multi-AZ database backups.",
    },
  },
};

export const dummyCloudLld = {
  cloud_provider: "AWS",
  compute: {
    platform: "AWS ECS on Fargate",
    instance_specs: "0.5 vCPU, 1 GB RAM per Fargate task replica per microservice (6 services)",
    base_os: "Alpine-based multi-stage Docker container images (Python 3.12 slim runtime)",
  },
  networking: {
    vpc_topology:
      "Custom VPC with Public subnets (ALB + NAT Gateway) and Private subnets (ECS Fargate tasks + RDS + ElastiCache) across 2 Availability Zones",
    dns_ssl: "AWS Route 53 public hosted zone with ACM-issued TLS 1.3 certificates terminated at ALB",
    api_gateway: "AWS Application Load Balancer (ALB) with path-based routing, WAF association, and rate limiting at 100 RPS per client IP",
  },
  storage: {
    database: "AWS RDS for PostgreSQL 16 (db.t4g.medium, Multi-AZ, 100 GB gp3 storage, automated daily snapshots with 7-day retention and PITR)",
    cache: "AWS ElastiCache for Redis 7.2 (cache.t4g.small, 2-node cluster mode disabled, Multi-AZ replication group)",
    static_assets: "AWS S3 bucket (private, versioned) fronted by CloudFront CDN for frontend Next.js assets and user-uploaded media",
  },
  container_orchestration: {
    ecs_task_definitions:
      "6 separate ECS services (svc-auth, svc-catalog, svc-circulation, svc-notification, svc-inventory, svc-reporting) each backed by its own ECR image and its own PostgreSQL schema (authentication_db, catalog_db, circulation_db, notification_db, inventory_db, reporting_db)",
    health_checks: "ECS container health checks on /live (every 15s) and /ready (every 30s) endpoints; ALB target group health checks with 3 failure threshold, deregistration delay 30s",
  },
  ci_cd_pipeline: {
    tool: "GitHub Actions",
    stages: [
      "Lint (ruff/mypy) and Pytest unit + integration tests",
      "Docker multi-stage build and Trivy vulnerability scan",
      "Push image to Amazon ECR (immutable tags per commit SHA)",
      "Run Alembic database migrations against RDS",
      "ECS rolling deployment with circuit breaker enabled",
    ],
  },
  monitoring: {
    metrics:
      "AWS CloudWatch Container Insights (CPU, memory, network), ALB request metrics, RDS Performance Insights, custom CloudWatch metrics for JWT auth failures and RabbitMQ queue depth",
    alerting: "SNS alerts on task CPU > 80% for 5 min, 5xx error rate > 1%, RDS connections > 80% of max, and DLQ message count > 0",
  },
  scaling_strategy: {
    auto_scaling: "ECS Service Auto Scaling with target tracking on 70% average CPU and on ALB request count per target (>1000 requests/target)",
    min_replicas: 2,
    max_replicas: 10,
  },
  cost_estimation: {
    status: "ASSUMPTION_BASED_ESTIMATE",
    monthly_cost_breakdown_usd: {
      ecs_fargate_compute: 95.0,
      rds_postgresql_db_t4g_medium_multi_az: 145.0,
      elasticache_redis_cache_t4g_small: 30.0,
      application_load_balancer: 22.0,
      nat_gateway_2_az: 65.0,
      s3_and_cloudfront_cdn: 12.0,
      cloudwatch_logs_metrics_and_sns: 20.0,
      secrets_manager_and_acm: 5.0,
      data_transfer_out: 18.0,
      total_estimated_monthly_usd: 412.0,
    },
  },
};

export const dummyDatabaseLld = {
  database_type: "PostgreSQL 16",
  tables: [
    {
      table_name: "users",
      description: "User accounts and authentication credentials with role-based access control",
      columns: [
        { name: "id", type: "UUID", constraints: "PRIMARY KEY DEFAULT gen_random_uuid()" },
        { name: "username", type: "VARCHAR(50)", constraints: "UNIQUE NOT NULL" },
        { name: "email", type: "VARCHAR(255)", constraints: "UNIQUE NOT NULL" },
        { name: "hashed_password", type: "VARCHAR(255)", constraints: "NOT NULL" },
        { name: "role", type: "VARCHAR(20)", constraints: "NOT NULL DEFAULT 'student'" },
        { name: "created_at", type: "TIMESTAMPTZ", constraints: "NOT NULL DEFAULT NOW()" },
      ],
    },
    {
      table_name: "books",
      description: "Library book catalog master records and availability status",
      columns: [
        { name: "id", type: "UUID", constraints: "PRIMARY KEY DEFAULT gen_random_uuid()" },
        { name: "user_id", type: "UUID", constraints: "NOT NULL REFERENCES users(id) ON DELETE RESTRICT" },
        { name: "name", type: "VARCHAR(255)", constraints: "NOT NULL" },
        { name: "status", type: "VARCHAR(30)", constraints: "NOT NULL DEFAULT 'available'" },
        { name: "description", type: "TEXT", constraints: "DEFAULT NULL" },
        { name: "created_at", type: "TIMESTAMPTZ", constraints: "NOT NULL DEFAULT NOW()" },
        { name: "updated_at", type: "TIMESTAMPTZ", constraints: "NOT NULL DEFAULT NOW()" },
      ],
    },
    {
      table_name: "book_loans",
      description: "Canonical book loan records representing an active or historical loan lifecycle",
      columns: [
        { name: "id", type: "UUID", constraints: "PRIMARY KEY DEFAULT gen_random_uuid()" },
        { name: "user_id", type: "UUID", constraints: "NOT NULL REFERENCES users(id) ON DELETE RESTRICT" },
        { name: "name", type: "VARCHAR(255)", constraints: "NOT NULL" },
        { name: "status", type: "VARCHAR(30)", constraints: "NOT NULL DEFAULT 'active'" },
        { name: "created_at", type: "TIMESTAMPTZ", constraints: "NOT NULL DEFAULT NOW()" },
        { name: "updated_at", type: "TIMESTAMPTZ", constraints: "NOT NULL DEFAULT NOW()" },
      ],
    },
    {
      table_name: "borrows",
      description: "Borrow transaction events recording book checkouts by users",
      columns: [
        { name: "id", type: "UUID", constraints: "PRIMARY KEY DEFAULT gen_random_uuid()" },
        { name: "user_id", type: "UUID", constraints: "NOT NULL REFERENCES users(id) ON DELETE RESTRICT" },
        { name: "name", type: "VARCHAR(255)", constraints: "NOT NULL" },
        { name: "status", type: "VARCHAR(30)", constraints: "NOT NULL DEFAULT 'borrowed'" },
        { name: "created_at", type: "TIMESTAMPTZ", constraints: "NOT NULL DEFAULT NOW()" },
      ],
    },
    {
      table_name: "returns",
      description: "Return transaction events recording book check-ins by users",
      columns: [
        { name: "id", type: "UUID", constraints: "PRIMARY KEY DEFAULT gen_random_uuid()" },
        { name: "user_id", type: "UUID", constraints: "NOT NULL REFERENCES users(id) ON DELETE RESTRICT" },
        { name: "name", type: "VARCHAR(255)", constraints: "NOT NULL" },
        { name: "status", type: "VARCHAR(30)", constraints: "NOT NULL DEFAULT 'returned'" },
        { name: "created_at", type: "TIMESTAMPTZ", constraints: "NOT NULL DEFAULT NOW()" },
      ],
    },
  ],
  indexes: [
    { table: "users", columns: ["username"], type: "UNIQUE BTREE", purpose: "Fast unique login credential lookups" },
    { table: "users", columns: ["email"], type: "UNIQUE BTREE", purpose: "Fast unique email lookups for authentication" },
    { table: "users", columns: ["role"], type: "BTREE", purpose: "Role-based access control filter queries" },
    { table: "books", columns: ["user_id", "status"], type: "BTREE", purpose: "Filter catalog books by owner and status" },
    { table: "books", columns: ["name"], type: "BTREE", purpose: "Catalog search by book title" },
    { table: "book_loans", columns: ["user_id", "status"], type: "BTREE", purpose: "Active loan lookups per user" },
    { table: "borrows", columns: ["user_id", "status"], type: "BTREE", purpose: "Active borrow event lookups" },
    { table: "returns", columns: ["user_id", "status"], type: "BTREE", purpose: "Return event lookups per user" },
  ],
  caching_strategy: {
    engine: "Redis 7.2 Cluster",
    ttl_policies: {
      book_search: "300s",
      book_detail: "1800s",
      user_session: "900s",
      active_loans: "120s",
    },
  },
  migrations_strategy: {
    tool: "Alembic",
    deployment: "Automated migration execution via GitHub Actions pre-deployment hook per microservice schema",
  },
  performance_tuning: {
    connection_pool_size: "20 min, 50 max via PgBouncer transaction pooling with SQLAlchemy asyncpg driver",
    concurrency_control: "Read Committed isolation with explicit row-level locking (SELECT FOR UPDATE) on books.status during borrow/return",
  },
};

export const dummyBackendLld = {
  framework_config: {
    framework: "FastAPI",
    language: "Python 3.12",
    orm: "SQLAlchemy 2.0 (Async)",
    migration_tool: "Alembic",
    driver: "asyncpg",
  },
  api_endpoints: [
    {
      route: "/api/v1/auth/login",
      method: "POST",
      operation_id: "loginUser",
      description: "Authenticate user or staff and issue JWT tokens",
      auth_required: false,
    },
    {
      route: "/api/v1/search-books",
      method: "GET",
      operation_id: "searchBooks",
      description: "Search books across catalog with pagination and query filters",
      auth_required: true,
    },
    {
      route: "/api/v1/borrow-books",
      method: "POST",
      operation_id: "borrowBooks",
      description: "Executes borrow checkout transaction with row-level locking",
      auth_required: true,
    },
    {
      route: "/api/v1/return-books",
      method: "POST",
      operation_id: "returnBooks",
      description: "Executes book check-in and updates loan status",
      auth_required: true,
    },
    {
      route: "/api/v1/manage-book-catalog-add-remove",
      method: "DELETE",
      operation_id: "manageBookCatalogAddRemove",
      description: "Librarian administrative endpoint to add or retire catalog books",
      auth_required: true,
    },
    {
      route: "/api/v1/secure-authentication-role-based-access",
      method: "POST",
      operation_id: "secureAuthenticationRoleBasedAccess",
      description: "Validates role permissions and refresh token rotations",
      auth_required: true,
    },
  ],
  services: [
    {
      name: "Authentication & Role Service",
      responsibility: "Handles identity, token issuance, and RBAC permission guards.",
      dependencies: ["UserRepository"],
    },
    {
      name: "Catalog & Search Service",
      responsibility: "Manages catalog indexing, text queries, and book availability caching.",
      dependencies: ["BooksRepository"],
    },
    {
      name: "Circulation & Borrowing Service",
      responsibility: "Coordinates checkout and return lifecycles using distributed ACID transactions.",
      dependencies: ["BorrowRepository", "ReturnRepository", "BookLoanRepository"],
    },
    {
      name: "Notification & Reminder Service",
      responsibility: "Dispatches automated reminders for due dates and overdue fines.",
      dependencies: ["UserRepository"],
    },
    {
      name: "Inventory & Asset Service",
      responsibility: "Tracks physical book copies, shelf barcode tags, and asset condition.",
      dependencies: ["BooksRepository"],
    },
    {
      name: "Reporting & Analytics Service",
      responsibility: "Generates circulation metrics, overdue aggregations, and usage BI dashboards.",
      dependencies: ["BookLoanRepository"],
    },
  ],
  domain_models: [
    { name: "User", database_table: "users" },
    { name: "Books", database_table: "books" },
    { name: "BookLoan", database_table: "book_loans" },
    { name: "Borrow", database_table: "borrows" },
    { name: "Return", database_table: "returns" },
  ],
  repositories: [
    { name: "UserRepository", entity: "User", database: "PostgreSQL" },
    { name: "BooksRepository", entity: "Books", database: "PostgreSQL" },
    { name: "BookLoanRepository", entity: "BookLoan", database: "PostgreSQL" },
    { name: "BorrowRepository", entity: "Borrow", database: "PostgreSQL" },
    { name: "ReturnRepository", entity: "Return", database: "PostgreSQL" },
  ],
  security_config: {
    auth_strategy: "OAuth2 Bearer Tokens (JWT RS256)",
    password_hashing: "Passlib with BCrypt (12 rounds)",
    rbac_roles: ["Student", "Librarian", "Administrator"],
  },
};

export const dummyFrontendLld = {
  framework: {
    selected_option: "React (Next.js App Router)",
    reasoning: "Component modularity, server-side rendering for catalog search performance, and rich ecosystem.",
  },
  pages: [
    { route: "/login", name: "LoginPage", description: "Authentication entry with role-based login form" },
    { route: "/search-books", name: "SearchBooksPage", description: "Interactive catalog search with dynamic filters" },
    { route: "/borrow-books", name: "BorrowBooksPage", description: "Book checkout & circulation management page" },
    { route: "/return-books", name: "ReturnBooksPage", description: "Book return scanning & confirmation view" },
    { route: "/manage-book-catalog", name: "CatalogAdminPage", description: "Librarian catalog management & inventory" },
  ],
  components: [
    { name: "Navbar", description: "Global header with navigation links and auth state" },
    { name: "BookCard", description: "Reusable presentation tile for book catalog items" },
    { name: "BorrowModal", description: "Interactive form dialog for checkout confirmation" },
    { name: "ReturnScannerModal", description: "Barcode scanner dialog for book returns" },
    { name: "LoanHistoryTable", description: "Paginated list of historical and active book loans" },
  ],
  state_management: {
    global_state: "Zustand (AuthSession, UIState)",
    server_state: "TanStack Query (Cached API queries with automatic invalidation)",
    form_state: "React Hook Form + Zod schema validation",
  },
  api_integration: {
    client: "Axios instance with centralized interceptor injecting Authorization Bearer token",
  },
};

export const dummySecurityLld = {
  authentication: {
    protocol: "OAuth2 with Authorization Code Flow & PKCE",
    token_type: "JWT RS256 Asymmetric Signed Tokens",
    token_expiry: "15 minutes Access Token, 7 days Refresh Token with Rotation",
    session_store: "Redis 7.2 Cluster with Blacklist Token Revocation",
  },
  authorization: {
    model: "Role-Based Access Control (RBAC)",
    roles: [
      { role: "Student", permissions: ["catalog:read", "borrow:create", "return:create", "loans:read_own"] },
      { role: "Librarian", permissions: ["catalog:manage", "inventory:manage", "fines:override", "loans:read_all"] },
      { role: "Administrator", permissions: ["*"] },
    ],
  },
  network_security: {
    ingress_waf: "AWS WAF with OWASP Top 10 rule group and rate-limiting (100 RPS per IP)",
    tls_version: "TLS 1.3 Strict HTTPS Enforcement via Route 53 + ACM",
    cors_policy: "Restricted origin domain whitelist with credentials enabled",
  },
  data_protection: {
    at_rest: "AES-256 AWS KMS Customer Managed Keys for RDS PostgreSQL and S3 Buckets",
    in_transit: "TLS 1.3 end-to-end between Client, ALB, and ECS Fargate microservices",
  },
  audit_logging: {
    trail: "Immutable append-only audit trail for all checkout, fine, and role change events",
    retention: "3 years in encrypted CloudWatch Logs with S3 Glacier archiving",
  },
};

export const dummyAllLlds = {
  backend: dummyBackendLld,
  frontend: dummyFrontendLld,
  database: dummyDatabaseLld,
  cloud: dummyCloudLld,
  security: dummySecurityLld,
};
