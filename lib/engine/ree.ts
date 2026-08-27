/**
 * Requirements Engineering Engine (REE)
 * Dynamically analyzes ANY problem statement, extracts domain context,
 * generates tailored clarifying interview questions, and synthesizes formal ARSRS specifications.
 */

export interface InterviewQuestionData {
  question_id: string;
  question: string;
  rationale: string;
  priority: "HIGH" | "MEDIUM" | "LOW" | string;
  options: string[];
  default_option?: string;
}

export interface DomainProfile {
  title: string;
  domain: string;
  actors: string[];
  entities: string[];
  keyActions: string[];
  scaleKeyword: string;
  realtimeTech: string;
  compliance: string;
}

/**
 * Dynamically extracts domain semantics, entities, actors, and architecture constraints
 * from any arbitrary natural language prompt.
 */
export function extractDomainProfile(prompt: string): DomainProfile {
  const p = prompt.toLowerCase();

  // Extract clean title
  let title = prompt.split(".")[0].trim();
  if (title.length > 50) {
    title = title.substring(0, 50) + "...";
  }

  // Healthcare / Medical
  if (p.includes("health") || p.includes("doctor") || p.includes("patient") || p.includes("hospital") || p.includes("medical") || p.includes("clinic") || p.includes("telemedicine")) {
    return {
      title,
      domain: "Healthcare & Telemedicine",
      actors: ["Patients", "Doctors", "Pharmacists", "Hospital Admins"],
      entities: ["ConsultationSession", "MedicalRecord", "Prescription", "VitalTelemetry"],
      keyActions: ["Schedule appointments", "Stream encrypted WebRTC video", "Issue digital prescriptions", "Store audit logs"],
      scaleKeyword: "clinical consultation load (< 50ms latency, 99.99% reliability)",
      realtimeTech: "WebRTC encrypted video streaming + WebSocket telemetry",
      compliance: "HIPAA, HITECH, and GDPR data privacy compliance",
    };
  }

  // Finance / Fintech / Trading / Crypto
  if (p.includes("crypto") || p.includes("trad") || p.includes("bank") || p.includes("pay") || p.includes("fintech") || p.includes("stock") || p.includes("wallet") || p.includes("ledger")) {
    return {
      title,
      domain: "Fintech & High-Frequency Trading",
      actors: ["Traders", "Brokers", "Compliance Officers", "Settlement Engine"],
      entities: ["OrderBook", "TradeExecution", "WalletLedger", "RiskThreshold"],
      keyActions: ["Match limit orders", "Stream depth-of-market feeds", "Enforce margin limits", "Execute ACID ledger settlement"],
      scaleKeyword: "ultra-low latency order matching (< 5ms P99, 50,000+ QPS)",
      realtimeTech: "Bidirectional WebSockets with Redis in-memory orderbook matching",
      compliance: "PCI-DSS Level 1, SOC2 Type II, and FINRA audit compliance",
    };
  }

  // Logistics / Delivery / Drones / Fleet / Transport
  if (p.includes("drone") || p.includes("delivery") || p.includes("fleet") || p.includes("logistics") || p.includes("driver") || p.includes("vehicle") || p.includes("transport") || p.includes("ride") || p.includes("uber")) {
    return {
      title,
      domain: "Autonomous Fleet & Logistics Management",
      actors: ["Dispatchers", "Fleet Operators", "Drivers / Agents", "End Customers"],
      entities: ["VehicleNode", "DeliveryRoute", "TelemetryPacket", "WaypointMission"],
      keyActions: ["Stream live GPS/telemetry", "Compute optimal routing", "Dispatch missions", "Track ETA in real-time"],
      scaleKeyword: "high-frequency telemetry ingestion (10,000+ sensor packets/sec)",
      realtimeTech: "MQTT message broker + Kafka stream processor for live geospatial tracking",
      compliance: "ISO 27001, Geospatial data privacy, and SLA uptime guarantees",
    };
  }

  // E-Commerce / Marketplace
  if (p.includes("shop") || p.includes("store") || p.includes("e-commerce") || p.includes("ecommerce") || p.includes("cart") || p.includes("product") || p.includes("market")) {
    return {
      title,
      domain: "E-Commerce & Digital Marketplace",
      actors: ["Buyers", "Merchants", "Inventory Managers", "Support Agents"],
      entities: ["ProductCatalog", "ShoppingOrder", "InventoryReservation", "PaymentReceipt"],
      keyActions: ["Search catalog", "Reserve inventory atomically", "Process Stripe payments", "Send shipment tracking"],
      scaleKeyword: "flash-sale burst traffic (< 100ms response time, 20,000+ concurrent carts)",
      realtimeTech: "Redis distributed locking for inventory + SSE order progress notifications",
      compliance: "PCI-DSS, GDPR, and consumer data protection standards",
    };
  }

  // Streaming / Media / Gaming / Social / Chat
  if (p.includes("stream") || p.includes("video") || p.includes("chat") || p.includes("social") || p.includes("game") || p.includes("media") || p.includes("music")) {
    return {
      title,
      domain: "Real-Time Media & Interactive Streaming",
      actors: ["Broadcasters", "Viewers", "Content Creators", "Moderators"],
      entities: ["LiveStream", "ChatMessage", "ViewerSession", "ContentAsset"],
      keyActions: ["Ingest RTMP/WebRTC streams", "Distribute low-latency video via CDN", "Broadcast chat messages", "Moderate content"],
      scaleKeyword: "massive concurrent viewer fanout (100,000+ simultaneous viewers)",
      realtimeTech: "WebRTC SFU mesh + Redis Pub/Sub chat fanout with edge CDN distribution",
      compliance: "Content safety moderation, DMCA compliance, and GDPR data portability",
    };
  }

  // IoT / Smart System / Parking
  if (p.includes("iot") || p.includes("park") || p.includes("sensor") || p.includes("smart") || p.includes("hardware")) {
    return {
      title,
      domain: "IoT Telemetry & Smart Automation Platform",
      actors: ["System Operators", "Field Devices", "End Users", "Maintenance Techs"],
      entities: ["SensorDevice", "TelemetryReading", "StateMatrix", "AutomatedTrigger"],
      keyActions: ["Ingest sensor metrics", "Update in-memory state matrix", "Trigger dynamic workflows", "Publish edge alerts"],
      scaleKeyword: "high-throughput device ingestion (25,000+ telemetry readings/sec)",
      realtimeTech: "MQTT message broker + Redis time-series database with WebSocket dashboards",
      compliance: "Edge hardware security, TLS 1.3 telemetry encryption, and fault tolerance",
    };
  }

  // Event / University / Hackathon / Education
  if (p.includes("event") || p.includes("hackathon") || p.includes("college") || p.includes("university") || p.includes("student") || p.includes("library") || p.includes("course") || p.includes("school")) {
    return {
      title,
      domain: "Event & Academic Platform",
      actors: ["Students / Participants", "Judges / Instructors", "Organizers", "Admins"],
      entities: ["RegistrationRecord", "SubmissionArtifact", "ScoringMatrix", "LiveLeaderboard"],
      keyActions: ["Process registrations", "Score submissions with rubric", "Broadcast live leaderboards", "Track attendance"],
      scaleKeyword: "event peak traffic (5,000 to 10,000 concurrent participants)",
      realtimeTech: "Server-Sent Events (SSE) & WebSockets for live score streaming",
      compliance: "FERPA compliance, OAuth 2.0 student SSO, and role-based access control",
    };
  }

  // General Scalable Cloud SaaS
  return {
    title,
    domain: "Distributed Multi-Tenant Cloud Architecture",
    actors: ["Tenants", "Platform Admins", "API Clients", "Background Workers"],
    entities: ["TenantAccount", "CoreResource", "WorkflowTask", "AuditLog"],
    keyActions: ["Process API requests", "Enforce tenant boundaries", "Execute asynchronous workflows", "Maintain audit trails"],
    scaleKeyword: "enterprise multi-tenant scale (P95 latency < 80ms, 10,000+ QPS)",
    realtimeTech: "Event-driven asynchronous queues (BullMQ/Redis) + WebSocket notifications",
    compliance: "SOC2 Type II, TLS 1.3 end-to-end encryption, and Row-Level Security (RLS)",
  };
}

/**
 * Dynamically generates 3 intelligent clarifying interview questions tailored
 * specifically to the user's domain and problem statement.
 */
export function generateInterviewQuestions(prompt: string): InterviewQuestionData[] {
  const profile = extractDomainProfile(prompt);

  return [
    {
      question_id: "Q1",
      question: `What is the expected peak throughput and latency SLA for ${profile.domain}?`,
      rationale: `Guides horizontal microservice auto-scaling, database connection pooling, and multi-layer caching for ${profile.domain}.`,
      priority: "HIGH",
      options: [
        `High throughput (${profile.scaleKeyword})`,
        "Moderate standard web load (1,000 to 5,000 concurrent active users)",
        "Enterprise multi-region distributed workload with global CDN caching",
      ],
      default_option: `High throughput (${profile.scaleKeyword})`,
    },
    {
      question_id: "Q2",
      question: `How should real-time communication, events, and data synchronization be orchestrated for ${profile.entities[0]} and ${profile.entities[1]}?`,
      rationale: `Dictates whether ${profile.realtimeTech} or transactional REST polling provides the optimal balance of throughput and battery/network efficiency.`,
      priority: "HIGH",
      options: [
        `Real-time: ${profile.realtimeTech}`,
        "Server-Sent Events (SSE) for one-way streaming updates and alerts",
        "Optimistic UI updates with standard REST API polling and Redis caching",
      ],
      default_option: `Real-time: ${profile.realtimeTech}`,
    },
    {
      question_id: "Q3",
      question: `What security architecture, identity provider, and compliance model should govern ${profile.actors.slice(0, 2).join(" & ")}?`,
      rationale: `Ensures adherence to ${profile.compliance}, role-based access control (RBAC), and encryption standards.`,
      priority: "MEDIUM",
      options: [
        `JWT + Supabase Auth / OAuth 2.0 with strict ${profile.compliance}`,
        "Enterprise SAML 2.0 SSO with active directory integration and audit logging",
        "API Key authentication with HMAC request signature verification",
      ],
      default_option: `JWT + Supabase Auth / OAuth 2.0 with strict ${profile.compliance}`,
    },
  ];
}

/**
 * Dynamically synthesizes the formal Architecture-Ready Structured Requirements (ARSRS) specification
 * tailored to any problem statement and user answers.
 */
export function synthesizeArsrsDocument(
  prompt: string,
  answers: Record<string, string>
): Record<string, unknown> {
  const profile = extractDomainProfile(prompt);

  return {
    metadata: {
      document_type: "ARSRS (Architecture-Ready Structured Requirements Specification)",
      version: "2.0.0",
      system_name: profile.title,
      domain: profile.domain,
      status: "APPROVED_FOR_ARCHITECTURE",
      generated_at: new Date().toISOString(),
    },
    system_overview: {
      problem_statement: prompt,
      architecture_pattern: "Modular Cloud Microservices with Reactive Event-Driven Ingestion & Distributed Cache",
      primary_actors: profile.actors,
      clarified_specifications: answers,
    },
    functional_requirements: [
      {
        id: "FR-01",
        title: `${profile.actors[0]} Authentication & Authorization`,
        description: `Secure sign-up, sign-in, token refresh, and role-based access control (RBAC) supporting ${profile.actors.join(", ")}.`,
        priority: "P0",
      },
      {
        id: "FR-02",
        title: `${profile.entities[0]} Core Management & Lifecycle`,
        description: `Full CRUD capabilities, validation constraints, and transactional consistency for ${profile.entities[0]} and ${profile.entities[1]}.`,
        priority: "P0",
      },
      {
        id: "FR-03",
        title: "Real-Time Telemetry & Event Synchronization",
        description: `High-frequency event broadcasting and state updates powered by ${profile.realtimeTech}.`,
        priority: "P1",
      },
      {
        id: "FR-04",
        title: "Audit Logging, Metrics & Administrative Insights",
        description: `Structured operational telemetry, immutable audit trails, and compliance monitoring adhering to ${profile.compliance}.`,
        priority: "P2",
      },
    ],
    non_functional_requirements: {
      availability: "99.95% multi-zone high-availability SLA",
      latency: `P95 API response time < 80ms; in-memory cache lookups < 5ms (${profile.scaleKeyword})`,
      scalability: "Horizontal pod auto-scaling (HPA) driven by CPU and request throughput metrics",
      security: `TLS 1.3 in-transit, AES-256 at-rest, Row-Level Security (RLS), and ${profile.compliance}`,
      data_integrity: "ACID guarantees for transactional operations with distributed locking",
    },
    domain_entities: profile.entities.map((ent, idx) => ({
      entity_name: ent,
      table_name: ent.toLowerCase() + "s",
      primary_key: "id (UUID)",
      key_attributes: ["id", "created_at", "updated_at", "status", "metadata"],
      description: `Primary domain entity managing ${ent} lifecycle and state in ${profile.domain}.`,
    })),
    constraints_and_assumptions: [
      "Containerized microservice architecture using Docker and Kubernetes orchestration",
      "Stateless compute layer enabling seamless rolling deployments and horizontal scaling",
      "Strict separation of concerns across Frontend Presentation, API Ingress, Domain Services, and Persistence Layers",
      `Mandatory compliance with ${profile.compliance}`,
    ],
  };
}
