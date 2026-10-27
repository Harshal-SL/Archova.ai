/**
 * Predefined Architecture Payloads for HLD and 5 LLDs
 * Provided for instant end-to-end visualization, graphic testing, and offline verification.
 */

export const dummyHld = {
  architecture_style: "Event-Driven Microservices with API Gateway Pattern",
  executive_summary:
    "Enterprise-grade Video Streaming & Adaptive Transcoding Platform designed as an event-driven microservices architecture. The system isolates video processing, edge delivery, subscription billing, and real-time viewing telemetry into resilient services backed by PostgreSQL 16 Multi-AZ, Redis 7.2 Cluster, and AWS ECS Fargate.",
  business_goals: [
    "Achieve 99.99% system availability for global media streaming operations.",
    "Ensure sub-100ms p95 response time for CDN edge delivery and catalog navigation.",
    "Enforce strict transaction consistency and idempotent subscription billing.",
  ],
  major_services: [
    {
      service_id: "SVC-01",
      name: "API Gateway & Auth Layer",
      responsibility: "Reverse proxy, OAuth2 authentication, JWT validation, rate limiting, and request routing.",
      database_binding: "auth_schema",
      scaling_model: "Horizontal Stateless Pods (min 2, max 10)",
      satisfies: ["NFR-001", "FR-004"],
    },
    {
      service_id: "SVC-02",
      name: "Adaptive Bitrate Transcoding Service",
      responsibility: "Manages video transcoding into multiple quality levels, job orchestration, and storage integration.",
      database_binding: "transcoding_schema",
      scaling_model: "Horizontal Stateless Pods (min 2, max 10)",
      satisfies: ["FR-001", "FR-004"],
    },
    {
      service_id: "SVC-03",
      name: "CDN Edge Delivery Service",
      responsibility: "Configures CDN edge nodes, handles caching, regional content distribution, and geo-restriction enforcement.",
      database_binding: "delivery_schema",
      scaling_model: "Horizontal Stateless Pods (min 2, max 10)",
      satisfies: ["FR-002", "FR-005"],
    },
    {
      service_id: "SVC-04",
      name: "Subscription Billing Service",
      responsibility: "Manages subscription plans, recurring billing, plan upgrades/downgrades, and payment processing.",
      database_binding: "billing_schema",
      scaling_model: "Horizontal Stateless Pods (min 2, max 10)",
      satisfies: ["FR-003", "FR-006"],
    },
    {
      service_id: "SVC-05",
      name: "Media Asset & Storage Service",
      responsibility: "Ingests raw video uploads, manages S3 multipart chunking, and tracks media metadata.",
      database_binding: "media_schema",
      scaling_model: "Horizontal Stateless Pods (min 2, max 10)",
      satisfies: ["FR-007"],
    },
    {
      service_id: "SVC-06",
      name: "Analytics & Reporting Service",
      responsibility: "Collects viewer behavior metrics, generates engagement reports, and supports real-time analytics dashboards.",
      database_binding: "analytics_schema",
      scaling_model: "Horizontal Stateless Pods (min 2, max 10)",
      satisfies: ["FR-008", "FR-005"],
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
      pattern: "Asynchronous Event Bus Streaming",
      usage: "Transcoding job distribution, video processing lifecycle, and notification fan-out",
      protocol: "AMQP 0-9-1 RabbitMQ with dead-letter queue",
      resilience: "3x retry exponential backoff",
    },
  ],
  data_strategy: {
    primary_database: "PostgreSQL 16 Multi-AZ",
    caching_tier: "Redis 7.2 Cluster",
    storage_tier: "AWS S3 Multi-Region Object Storage",
    backup_policy: "Automated daily snapshots with 7-day point-in-time recovery",
  },
  primary_actors: [
    {
      name: "Viewer / Subscriber",
      role: "Primary Web & Mobile Consumer",
      description: "Streams high-definition media, browses video catalog, manages personal subscription",
    },
    {
      name: "Platform Administrator",
      role: "Operations & Admin Staff",
      description: "Manages media transcoding pipelines, CDN distribution, and platform billing reports",
    },
  ],
};

export const dummyCloudLld = {
  cloud_provider: "AWS",
  compute: {
    service: "AWS ECS Fargate",
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
    static_assets: "AWS S3 bucket (private, versioned) fronted by CloudFront CDN for frontend Next.js assets and uploaded media",
  },
  container_orchestration: {
    ecs_task_definitions:
      "6 separate ECS services (svc-gateway, svc-transcoding, svc-delivery, svc-billing, svc-media, svc-analytics) each backed by its own ECR image and isolated database schema",
    health_checks: "ECS container health checks on /live and /ready endpoints; ALB target group health checks",
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
      "AWS CloudWatch Container Insights (CPU, memory, network), ALB request metrics, RDS Performance Insights, and custom CloudWatch metrics for JWT auth failures",
    alerting: "SNS alerts on task CPU > 80% for 5 min, 5xx error rate > 1%, and RDS connections > 80% of max",
  },
  scaling_strategy: {
    auto_scaling: "ECS Service Auto Scaling with target tracking on 70% average CPU and on ALB request count per target (>1000 requests/target)",
    min_replicas: 2,
    max_replicas: 10,
  },
};

export const dummyDatabaseLld = {
  database_type: "PostgreSQL 16",
  tables: [
    {
      table_name: "users",
      description: "User accounts, authentication credentials, and subscriber profiles",
      columns: [
        { name: "id", type: "UUID", constraints: "PRIMARY KEY DEFAULT gen_random_uuid()" },
        { name: "username", type: "VARCHAR(50)", constraints: "UNIQUE NOT NULL" },
        { name: "email", type: "VARCHAR(255)", constraints: "UNIQUE NOT NULL" },
        { name: "hashed_password", type: "VARCHAR(255)", constraints: "NOT NULL" },
        { name: "role", type: "VARCHAR(20)", constraints: "NOT NULL DEFAULT 'viewer'" },
        { name: "created_at", type: "TIMESTAMPTZ", constraints: "NOT NULL DEFAULT NOW()" },
      ],
    },
    {
      table_name: "video_assets",
      description: "Master catalog metadata for uploaded media files and streaming manifests",
      columns: [
        { name: "id", type: "UUID", constraints: "PRIMARY KEY DEFAULT gen_random_uuid()" },
        { name: "user_id", type: "UUID", constraints: "NOT NULL REFERENCES users(id) ON DELETE RESTRICT" },
        { name: "title", type: "VARCHAR(255)", constraints: "NOT NULL" },
        { name: "status", type: "VARCHAR(30)", constraints: "NOT NULL DEFAULT 'ready'" },
        { name: "manifest_url", type: "TEXT", constraints: "DEFAULT NULL" },
        { name: "created_at", type: "TIMESTAMPTZ", constraints: "NOT NULL DEFAULT NOW()" },
      ],
    },
    {
      table_name: "transcoding_jobs",
      description: "Asynchronous video transcoding jobs converting media to multiple bitrates",
      columns: [
        { name: "id", type: "UUID", constraints: "PRIMARY KEY DEFAULT gen_random_uuid()" },
        { name: "video_id", type: "UUID", constraints: "NOT NULL REFERENCES video_assets(id) ON DELETE CASCADE" },
        { name: "resolution", type: "VARCHAR(20)", constraints: "NOT NULL" },
        { name: "status", type: "VARCHAR(30)", constraints: "NOT NULL DEFAULT 'processing'" },
        { name: "progress_percent", type: "INTEGER", constraints: "DEFAULT 0" },
        { name: "created_at", type: "TIMESTAMPTZ", constraints: "NOT NULL DEFAULT NOW()" },
      ],
    },
    {
      table_name: "subscriptions",
      description: "Subscriber membership plans, renewal terms, and recurring billing status",
      columns: [
        { name: "id", type: "UUID", constraints: "PRIMARY KEY DEFAULT gen_random_uuid()" },
        { name: "user_id", type: "UUID", constraints: "NOT NULL REFERENCES users(id) ON DELETE RESTRICT" },
        { name: "plan_tier", type: "VARCHAR(50)", constraints: "NOT NULL DEFAULT 'premium'" },
        { name: "status", type: "VARCHAR(30)", constraints: "NOT NULL DEFAULT 'active'" },
        { name: "expires_at", type: "TIMESTAMPTZ", constraints: "NOT NULL" },
      ],
    },
    {
      table_name: "viewing_events",
      description: "Real-time viewer engagement telemetry, playback watch time, and buffer events",
      columns: [
        { name: "id", type: "UUID", constraints: "PRIMARY KEY DEFAULT gen_random_uuid()" },
        { name: "user_id", type: "UUID", constraints: "NOT NULL REFERENCES users(id) ON DELETE RESTRICT" },
        { name: "video_id", type: "UUID", constraints: "NOT NULL REFERENCES video_assets(id) ON DELETE CASCADE" },
        { name: "watch_duration_seconds", type: "INTEGER", constraints: "NOT NULL DEFAULT 0" },
        { name: "recorded_at", type: "TIMESTAMPTZ", constraints: "NOT NULL DEFAULT NOW()" },
      ],
    },
  ],
  relationships: [
    { from_table: "video_assets", to_table: "users", type: "1:N FK" },
    { from_table: "transcoding_jobs", to_table: "video_assets", type: "1:N FK" },
    { from_table: "subscriptions", to_table: "users", type: "1:N FK" },
    { from_table: "viewing_events", to_table: "video_assets", type: "1:N FK" },
  ],
};

export const dummyBackendLld = {
  api_endpoints: [
    {
      route: "/api/v1/auth/login",
      method: "POST",
      operation_id: "loginUser",
      description: "Authenticates viewer or creator credentials and issues RS256 JWT tokens",
      auth_required: false,
    },
    {
      route: "/api/v1/video/transcode",
      method: "POST",
      operation_id: "initiateTranscode",
      description: "Initiates asynchronous adaptive bitrate transcoding job for uploaded video",
      auth_required: true,
    },
    {
      route: "/api/v1/cdn/delivery",
      method: "POST",
      operation_id: "configureCdnDelivery",
      description: "Configures CDN edge caching rules and signed cookies for media asset",
      auth_required: true,
    },
    {
      route: "/api/v1/billing/subscribe",
      method: "POST",
      operation_id: "createSubscription",
      description: "Processes recurring subscription checkout and payment authorization",
      auth_required: true,
    },
    {
      route: "/api/v1/analytics/metrics",
      method: "GET",
      operation_id: "getViewingMetrics",
      description: "Retrieves aggregated viewer watch time and regional traffic metrics",
      auth_required: true,
    },
  ],
  services: [
    {
      name: "Authentication & Role Service",
      responsibility: "Handles identity, credentials validation, and RBAC permission guards.",
      dependencies: ["UserRepository"],
    },
    {
      name: "Adaptive Transcoding Service",
      responsibility: "Orchestrates multi-bitrate video transcoding jobs and HLS manifest generation.",
      dependencies: ["TranscodingRepository", "VideoRepository"],
    },
    {
      name: "CDN Edge Delivery Service",
      responsibility: "Coordinates regional edge node distribution, cache invalidations, and signed URLs.",
      dependencies: ["VideoRepository"],
    },
    {
      name: "Subscription Billing Service",
      responsibility: "Manages subscription tier state machines, payment webhooks, and invoice generation.",
      dependencies: ["SubscriptionRepository"],
    },
    {
      name: "Viewing Analytics Service",
      responsibility: "Ingests real-time viewing telemetry events and calculates engagement aggregates.",
      dependencies: ["AnalyticsRepository"],
    },
  ],
  domain_models: [
    { name: "User", database_table: "users" },
    { name: "VideoAsset", database_table: "video_assets" },
    { name: "TranscodingJob", database_table: "transcoding_jobs" },
    { name: "Subscription", database_table: "subscriptions" },
    { name: "ViewingEvent", database_table: "viewing_events" },
  ],
  repositories: [
    { name: "UserRepository", entity: "User", database: "PostgreSQL" },
    { name: "VideoRepository", entity: "VideoAsset", database: "PostgreSQL" },
    { name: "TranscodingRepository", entity: "TranscodingJob", database: "PostgreSQL" },
    { name: "SubscriptionRepository", entity: "Subscription", database: "PostgreSQL" },
  ],
};

export const dummyFrontendLld = {
  app_shell: {
    framework: "Next.js 16 (App Router) + React 19",
    styling: "Tailwind CSS + Lucide Icons",
    state_management: "Zustand (client session) + TanStack Query (server state)",
  },
  pages: [
    { route: "/login", name: "LoginPage", description: "Authentication entry with email/password form" },
    { route: "/dashboard", name: "DashboardPage", description: "Central user dashboard with subscriber overview" },
    { route: "/videos", name: "VideoExplorerPage", description: "Browse media catalog with search, filters, and streaming player" },
    { route: "/studio", name: "StudioTranscoderPage", description: "Creator studio for video uploads and transcode tracking" },
    { route: "/billing", name: "SubscriptionBillingPage", description: "Manage subscription plans, invoices, and billing history" },
  ],
  components: [
    { name: "VideoPlayerCard", description: "Adaptive HLS streaming player with resolution toggle" },
    { name: "TranscodeJobModal", description: "Interactive dialog displaying transcoding progress and bitrates" },
    { name: "StreamMetricsTile", description: "Live viewer telemetry chart showing active concurrent streams" },
    { name: "SubscriptionPlanTable", description: "Plan comparison matrix with upgrade/downgrade actions" },
  ],
};

export const dummySecurityLld = {
  perimeter: {
    waf: "AWS WAF with OWASP Core Rule Set and 100 RPS IP rate limiting",
    tls: "Strict TLS 1.3 encryption for all public ingress endpoints",
  },
  identity: {
    protocol: "OAuth2 with PKCE flow for web clients",
    tokens: "RS256 asymmetric signed JWT (15-min access token, 7-day refresh token)",
  },
  authorization: {
    model: "Role-Based Access Control (RBAC)",
    roles: ["Viewer", "Creator", "Administrator"],
  },
  cryptography: {
    at_rest: "AWS KMS Customer Managed Keys (AES-256) for RDS and S3 storage",
    in_transit: "mTLS for inter-service gRPC communication within VPC",
  },
};

export const dummyAllLlds = {
  backend: dummyBackendLld,
  database: dummyDatabaseLld,
  frontend: dummyFrontendLld,
  cloud: dummyCloudLld,
  security: dummySecurityLld,
};
