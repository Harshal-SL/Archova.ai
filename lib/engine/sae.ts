/**
 * System Architecture Engine (SAE)
 * Dynamically synthesizes the High-Level Design (HLD) nodes, tiered coordinates,
 * and directed edges tailored to ANY system requirements.
 */

import { extractDomainProfile } from "./ree";

export interface HldNode {
  id: string;
  name: string;
  type: string;
  description: string;
  x: number;
  y: number;
}

export interface HldEdge {
  source: string;
  target: string;
  label: string;
}

export interface HldData {
  title: string;
  pattern: string;
  domain: string;
  nodes: HldNode[];
  edges: HldEdge[];
}

export function synthesizeHldArchitecture(
  prompt: string,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  arsrs?: Record<string, unknown>
): HldData {
  const profile = extractDomainProfile(prompt);

  const clientName = `${profile.actors.slice(0, 2).join(" & ")} Portal (Next.js 16)`;
  const gatewayName = `API Gateway & ${profile.realtimeTech.includes("MQTT") ? "IoT Ingress" : "Edge Router"}`;
  const svc1Name = `${profile.entities[0]} Core Engine`;
  const svc2Name = `${profile.entities[1]} & Analytics Service`;
  const dbName = `Primary Database (${profile.entities.slice(0, 2).join(", ")})`;
  const cacheName = `Redis Cache & ${profile.realtimeTech.includes("WebSocket") ? "Pub/Sub" : "Event Queue"}`;
  const secName = `Auth, Identity & ${profile.compliance.split(" ")[0]} Compliance`;
  const cloudName = `Containerized Cloud Cluster (Kubernetes / ECS)`;

  const nodes: HldNode[] = [
    // Tier 0: Client Presentation (Top)
    {
      id: "client-layer",
      name: clientName,
      type: "frontend",
      description: `React client components supporting ${profile.actors.join(", ")} with responsive Tailwind styling.`,
      x: 180,
      y: 30,
    },
    // Tier 1: API Gateway / Ingress
    {
      id: "gateway-layer",
      name: gatewayName,
      type: "gateway",
      description: `Edge routing, TLS termination, rate limiting, and ${profile.realtimeTech} protocol forwarding.`,
      x: 180,
      y: 140,
    },
    // Tier 2: Domain Microservices (Left & Right)
    {
      id: "core-service-1",
      name: svc1Name,
      type: "backend",
      description: `Core domain logic executing ${profile.keyActions[0]} and ${profile.keyActions[1]}.`,
      x: 40,
      y: 260,
    },
    {
      id: "core-service-2",
      name: svc2Name,
      type: "backend",
      description: `Processes ${profile.keyActions[2] || "background workflows"} and ${profile.keyActions[3] || "audit reporting"}.`,
      x: 320,
      y: 260,
    },
    // Tier 3: Persistence & Distributed Caching
    {
      id: "database-layer",
      name: dbName,
      type: "database",
      description: `PostgreSQL database storing relational schemas for ${profile.entities.join(", ")} with Row-Level Security.`,
      x: 40,
      y: 380,
    },
    {
      id: "cache-layer",
      name: cacheName,
      type: "cache",
      description: `In-memory low-latency state and event bus supporting ${profile.scaleKeyword}.`,
      x: 320,
      y: 380,
    },
    // Tier 4: Security & Cloud Infrastructure
    {
      id: "security-layer",
      name: secName,
      type: "security",
      description: `JWT authentication, RBAC authorization, and data encryption adhering to ${profile.compliance}.`,
      x: 40,
      y: 500,
    },
    {
      id: "cloud-layer",
      name: cloudName,
      type: "cloud",
      description: `Multi-zone container orchestration with auto-scaling, health checks, and Prometheus metrics.`,
      x: 320,
      y: 500,
    },
  ];

  const edges: HldEdge[] = [
    { source: "client-layer", target: "gateway-layer", label: "HTTPS / WSS" },
    { source: "gateway-layer", target: "core-service-1", label: "REST / gRPC" },
    { source: "gateway-layer", target: "core-service-2", label: "REST / gRPC" },
    { source: "core-service-1", target: "database-layer", label: "ACID SQL" },
    { source: "core-service-1", target: "cache-layer", label: "Sub-5ms Cache" },
    { source: "core-service-2", target: "cache-layer", label: "Pub/Sub Stream" },
    { source: "core-service-2", target: "database-layer", label: "Persist State" },
    { source: "core-service-1", target: "security-layer", label: "Verify JWT" },
    { source: "core-service-2", target: "cloud-layer", label: "Health & Telemetry" },
  ];

  return {
    title: `${profile.title} Architecture (HLD)`,
    pattern: "Tiered Microservices Architecture with Real-Time Ingress & Distributed Cache",
    domain: profile.domain,
    nodes,
    edges,
  };
}
