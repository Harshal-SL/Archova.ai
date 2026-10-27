import type { Node, Edge } from "@xyflow/react";
import { getComponentTheme } from "./flow-colors";

function applyColorThemesToGraph(nodes: Node[], edges: Edge[]): { nodes: Node[]; edges: Edge[] } {
  const coloredNodes = nodes.map((n, idx) => {
    const raw = n as any;
    const posX = typeof n.position?.x === "number" ? n.position.x : (typeof raw.x === "number" ? raw.x : 100 + (idx % 4) * 360);
    const posY = typeof n.position?.y === "number" ? n.position.y : (typeof raw.y === "number" ? raw.y : 100 + Math.floor(idx / 4) * 220);
    const safePos = { x: posX, y: posY };

    if (n.type === "layerGroup") {
      return {
        ...n,
        position: safePos,
      };
    }
    const theme = getComponentTheme(n.id, (n.data?.label as string) || (raw.label as string) || (raw.name as string) || "", n.type, (n.data?.color as string) || undefined);
    return {
      ...n,
      position: safePos,
      data: {
        label: (raw.label as string) || (raw.name as string) || n.id || `Component ${idx + 1}`,
        ...((n.data || {}) as Record<string, unknown>),
        color: theme.primary,
        themeColor: theme.primary,
      },
    };
  });

  const coloredEdges = edges.map((e, idx) => {
    const srcTheme = getComponentTheme(e.source);
    return {
      ...e,
      id: e.id || `edge-${idx}`,
      type: "animatedFlow",
      animated: true,
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

function toSlug(name: string): string {
  const clean = name
    .toLowerCase()
    .replace(/service|layer|engine|cluster|system|component/gi, "")
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  return clean || "service";
}

function toSchemaName(name: string): string {
  const base = name.replace(/_db|_schema|service|db|layer|engine/gi, "").trim();
  const clean = base.charAt(0).toUpperCase() + base.slice(1);
  return `${clean || "Domain"} Schema`;
}

export function getHandleForType(type: string, direction: "top" | "bottom" | "left" | "right"): string {
  const t = (type || "").toLowerCase();
  if (t === "actor") return `act-${direction}`;
  if (t === "frontend") return `fe-${direction}`;
  if (t === "gateway") return `gw-${direction}`;
  if (t === "service" || t === "microservice") return `svc-${direction}`;
  if (t === "database") return `db-${direction}`;
  if (t === "cache") return `cache-${direction}`;
  if (t === "queue") return `q-${direction}`;
  if (t === "devops") return `dev-${direction}`;
  return `svc-${direction}`;
}

export function getHldNodeTier(n: Record<string, unknown>): number {
  const rawData = (n.data as Record<string, unknown>) || {};
  const type = String(n.type || "").toLowerCase();
  const id = String(n.id || "").toLowerCase();
  const label = String(rawData.label || n.label || n.name || "").toLowerCase();
  const role = String(rawData.role || n.role || "").toLowerCase();

  // Tier 0: External Actors / Stakeholders / Users
  if (
    type === "actor" ||
    id.includes("user") ||
    id.includes("actor") ||
    id.includes("admin") ||
    id.includes("client") ||
    label.includes("user") ||
    label.includes("admin") ||
    label.includes("client") ||
    label.includes("stakeholder") ||
    role.includes("consumer")
  ) {
    return 0;
  }

  // Tier 1: Frontend Applications & User Interfaces
  if (
    type === "frontend" ||
    id.includes("frontend") ||
    id.includes("web") ||
    id.includes("app") ||
    label.includes("web app") ||
    label.includes("next.js") ||
    label.includes("react") ||
    label.includes("frontend") ||
    label.includes("portal")
  ) {
    return 1;
  }

  // Tier 2: Ingress & API Gateway Layer
  if (
    type === "gateway" ||
    id.includes("gateway") ||
    id.includes("gw") ||
    id.includes("ingress") ||
    id.includes("waf") ||
    label.includes("gateway") ||
    label.includes("ingress") ||
    label.includes("reverse proxy") ||
    label.includes("waf") ||
    label.includes("alb")
  ) {
    return 2;
  }

  // Tier 4: Asynchronous Messaging & Event Brokers
  if (
    type === "queue" ||
    id.includes("broker") ||
    id.includes("queue") ||
    id.includes("kafka") ||
    id.includes("rabbitmq") ||
    id.includes("event") ||
    label.includes("broker") ||
    label.includes("queue") ||
    label.includes("kafka") ||
    label.includes("rabbitmq") ||
    label.includes("event bus")
  ) {
    return 4;
  }

  // Tier 5: Persistence, Relational DB & In-Memory Cache
  if (
    type === "database" ||
    type === "cache" ||
    id.includes("database") ||
    id.includes("db") ||
    id.includes("postgres") ||
    id.includes("sql") ||
    id.includes("cache") ||
    id.includes("redis") ||
    label.includes("database") ||
    label.includes("db") ||
    label.includes("postgres") ||
    label.includes("sql") ||
    label.includes("redis") ||
    label.includes("cache")
  ) {
    return 5;
  }

  // Tier 6: Cloud Infrastructure, CI/CD & Observability
  if (
    type === "devops" ||
    id.includes("cicd") ||
    id.includes("github") ||
    id.includes("k8s") ||
    id.includes("ecs") ||
    id.includes("docker") ||
    id.includes("prometheus") ||
    id.includes("grafana") ||
    id.includes("monitoring") ||
    label.includes("ci/cd") ||
    label.includes("github") ||
    label.includes("kubernetes") ||
    label.includes("ecs") ||
    label.includes("prometheus") ||
    label.includes("grafana") ||
    label.includes("monitoring")
  ) {
    return 6;
  }

  // Tier 3: Core Domain Microservices & Business Logic (Default)
  return 3;
}

export function layoutHldTopDown(
  rawNodes: Array<Record<string, unknown>>,
  rawEdges: Array<Record<string, unknown>>
): { nodes: Node[]; edges: Edge[] } {
  const tier0_actors: Array<Record<string, unknown>> = [];
  const tier1_frontend: Array<Record<string, unknown>> = [];
  const tier2_gateway: Array<Record<string, unknown>> = [];
  const tier3_services: Array<Record<string, unknown>> = [];
  const tier4_broker: Array<Record<string, unknown>> = [];
  const tier5_data: Array<Record<string, unknown>> = [];
  const tier6_cloud: Array<Record<string, unknown>> = [];

  rawNodes.forEach((n) => {
    // Skip old layer group nodes if present in rawNodes to avoid duplicate containers
    if (String(n.type) === "layerGroup") return;
    const tier = getHldNodeTier(n);
    if (tier === 0) tier0_actors.push(n);
    else if (tier === 1) tier1_frontend.push(n);
    else if (tier === 2) tier2_gateway.push(n);
    else if (tier === 4) tier4_broker.push(n);
    else if (tier === 5) tier5_data.push(n);
    else if (tier === 6) tier6_cloud.push(n);
    else tier3_services.push(n);
  });

  const hasTwoServiceRows = tier3_services.length > 4;
  const tier3A = hasTwoServiceRows
    ? tier3_services.slice(0, Math.ceil(tier3_services.length / 2))
    : tier3_services;
  const tier3B = hasTwoServiceRows
    ? tier3_services.slice(Math.ceil(tier3_services.length / 2))
    : [];

  // Strictly increasing vertical tier Y coordinates (North to South Top -> Down)
  const y0 = 60;
  const y1 = 210;
  const y2 = 380;
  const y3A = 560;
  const y3B = 740;
  const y4 = hasTwoServiceRows ? 920 : 740;
  const y5 = hasTwoServiceRows ? 1100 : 920;
  const y6 = hasTwoServiceRows ? 1280 : 1100;

  const positionedNodes: Node[] = [];
  const CANVAS_CENTER = 800;

  // Add clean background layer groups for tiers that have nodes
  if (tier0_actors.length > 0) {
    positionedNodes.push({
      id: "hgroup-tier0",
      type: "layerGroup",
      data: {
        label: "Tier 0: Client & Operator Actors",
        subtitle: "External Users · Platform Stakeholders · Administrators",
        count: tier0_actors.length,
      },
      position: { x: 80, y: 30 },
      style: { width: 1440, height: 110, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });
  }

  if (tier1_frontend.length > 0) {
    positionedNodes.push({
      id: "hgroup-tier1",
      type: "layerGroup",
      data: {
        label: "Tier 1: Frontend Client Applications",
        subtitle: "Next.js Web Application · Mobile Clients · Public Ingress",
        count: tier1_frontend.length,
      },
      position: { x: 80, y: 180 },
      style: { width: 1440, height: 155, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });
  }

  if (tier2_gateway.length > 0) {
    positionedNodes.push({
      id: "hgroup-tier2",
      type: "layerGroup",
      data: {
        label: "Tier 2: Ingress & API Gateway Layer",
        subtitle: "NGINX / Kong · TLS 1.3 · Rate Limiting · JWT Authentication",
        count: tier2_gateway.length,
      },
      position: { x: 80, y: 350 },
      style: { width: 1440, height: 155, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });
  }

  if (tier3_services.length > 0) {
    positionedNodes.push({
      id: "hgroup-tier3",
      type: "layerGroup",
      data: {
        label: "Tier 3: Core Domain Microservices Cluster",
        subtitle: "Autonomous Microservices · REST / gRPC Internal APIs",
        count: tier3_services.length,
      },
      position: { x: 80, y: 530 },
      style: { width: 1440, height: hasTwoServiceRows ? 340 : 155, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });
  }

  if (tier4_broker.length > 0) {
    positionedNodes.push({
      id: "hgroup-tier4",
      type: "layerGroup",
      data: {
        label: "Tier 4: Event Messaging & Distributed Broker",
        subtitle: "Kafka / RabbitMQ · Topic Exchanges · Dead-Letter Queues",
        count: tier4_broker.length,
      },
      position: { x: 80, y: hasTwoServiceRows ? 890 : 710 },
      style: { width: 1440, height: 155, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });
  }

  if (tier5_data.length > 0) {
    positionedNodes.push({
      id: "hgroup-tier5",
      type: "layerGroup",
      data: {
        label: "Tier 5: Relational Persistence & In-Memory Cache",
        subtitle: "PostgreSQL 16 Multi-AZ · Redis 7.2 Distributed Cache",
        count: tier5_data.length,
      },
      position: { x: 80, y: hasTwoServiceRows ? 1070 : 890 },
      style: { width: 1440, height: 155, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });
  }

  if (tier6_cloud.length > 0) {
    positionedNodes.push({
      id: "hgroup-tier6",
      type: "layerGroup",
      data: {
        label: "Tier 6: Cloud Infrastructure, CI/CD & Observability",
        subtitle: "AWS ECS Fargate · GitHub Actions CI/CD · Prometheus & Grafana APM",
        count: tier6_cloud.length,
      },
      position: { x: 80, y: hasTwoServiceRows ? 1250 : 1070 },
      style: { width: 1440, height: 155, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });
  }

  function placeRow(items: Array<Record<string, unknown>>, tierY: number, cardW: number = 300, gap: number = 40) {
    const count = items.length;
    if (count === 0) return;
    const totalWidth = count * cardW + (count - 1) * gap;
    const startX = CANVAS_CENTER - totalWidth / 2;
    items.forEach((item, idx) => {
      const id = String(item.id || `node-${positionedNodes.length}`);
      const rawData = (item.data as Record<string, unknown>) || {};
      const nodeLabel = String(rawData.label || item.label || item.name || id);
      const nodeType = String(item.type || "service");
      const x = Math.round(startX + idx * (cardW + gap));

      positionedNodes.push({
        id,
        type: nodeType,
        position: { x, y: tierY },
        data: {
          label: nodeLabel,
          role: String(rawData.role || item.role || ""),
          tech: String(rawData.tech || item.tech || ""),
          description: String(rawData.description || item.description || item.desc || ""),
          division: String(rawData.division || item.division || nodeType),
          ...rawData,
        },
      } as Node);
    });
  }

  placeRow(tier0_actors, y0, 200, 40);
  placeRow(tier1_frontend, y1, 300, 40);
  placeRow(tier2_gateway, y2, 300, 40);
  placeRow(tier3A, y3A, 300, 40);
  if (hasTwoServiceRows) {
    placeRow(tier3B, y3B, 300, 40);
  }
  placeRow(tier4_broker, y4, 300, 40);
  placeRow(tier5_data, y5, 300, 50);
  placeRow(tier6_cloud, y6, 300, 40);

  // Map handles on explicitEdges
  const nodeMap = new Map<string, Node>();
  positionedNodes.forEach((n) => nodeMap.set(n.id, n));

  const resolvedEdges: Edge[] = rawEdges.map((e, idx) => {
    const srcNode = nodeMap.get(String(e.source));
    const tgtNode = nodeMap.get(String(e.target));

    let srcHandle: string | undefined = undefined;
    let tgtHandle: string | undefined = undefined;

    if (srcNode && tgtNode) {
      const srcY = srcNode.position.y;
      const tgtY = tgtNode.position.y;
      const srcX = srcNode.position.x;
      const tgtX = tgtNode.position.x;

      if (srcY < tgtY - 30) {
        srcHandle = getHandleForType(srcNode.type || "service", "bottom");
        tgtHandle = getHandleForType(tgtNode.type || "service", "top");
      } else if (srcY > tgtY + 30) {
        srcHandle = getHandleForType(srcNode.type || "service", "top");
        tgtHandle = getHandleForType(tgtNode.type || "service", "bottom");
      } else {
        srcHandle = getHandleForType(srcNode.type || "service", srcX < tgtX ? "right" : "left");
        tgtHandle = getHandleForType(tgtNode.type || "service", srcX < tgtX ? "left" : "right");
      }
    }

    return {
      ...e,
      id: String(e.id || `edge-${idx}`),
      source: String(e.source),
      target: String(e.target),
      sourceHandle: e.sourceHandle || srcHandle,
      targetHandle: e.targetHandle || tgtHandle,
      type: "animatedFlow",
      animated: true,
      data: (e.data as Record<string, unknown>) || (e.label ? { label: String(e.label) } : {}),
    } as Edge;
  });

  return applyColorThemesToGraph(positionedNodes, resolvedEdges);
}

/**
 * Computes tight dynamic bounding box for an architectural layer group container
 * so it fits exactly around its child nodes with zero unnecessary dead space.
 */
export function computeGroupBounds(
  nodePositions: Array<{ y: number; height?: number }>,
  topPadding: number = 70,
  bottomPadding: number = 30,
  defaultNodeHeight: number = 92
): { y: number; height: number } {
  if (nodePositions.length === 0) return { y: 40, height: 190 };
  const ys = nodePositions.map((p) => p.y);
  const minY = Math.min(...ys);
  const maxItem = nodePositions.reduce(
    (max, curr) => (curr.y > max.y ? curr : max),
    nodePositions[0]
  );
  const lastHeight = maxItem.height || defaultNodeHeight;
  const maxY = maxItem.y + lastHeight;
  const y = Math.max(20, minY - topPadding);
  const height = maxY + bottomPadding - y;
  return { y, height: Math.max(height, 160) };
}

/**
 * Intelligent Left-to-Right Horizontal Tree Layout for HLD
 * Arranges architecture tiers as columns (West to East) with vertical symmetrical branching.
 */
export function layoutHldLeftToRight(
  rawNodes: Array<Record<string, unknown>>,
  rawEdges: Array<Record<string, unknown>>
): { nodes: Node[]; edges: Edge[] } {
  const tier0_actors: Array<Record<string, unknown>> = [];
  const tier1_frontend: Array<Record<string, unknown>> = [];
  const tier2_gateway: Array<Record<string, unknown>> = [];
  const tier3_services: Array<Record<string, unknown>> = [];
  const tier4_broker: Array<Record<string, unknown>> = [];
  const tier5_data: Array<Record<string, unknown>> = [];
  const tier6_cloud: Array<Record<string, unknown>> = [];

  rawNodes.forEach((n) => {
    if (String(n.type) === "layerGroup") return;
    const tier = getHldNodeTier(n);
    if (tier === 0) tier0_actors.push(n);
    else if (tier === 1) tier1_frontend.push(n);
    else if (tier === 2) tier2_gateway.push(n);
    else if (tier === 4) tier4_broker.push(n);
    else if (tier === 5) tier5_data.push(n);
    else if (tier === 6) tier6_cloud.push(n);
    else tier3_services.push(n);
  });

  const cardH = 92;
  const gapY = 32;
  const colPitchY = cardH + gapY;
  const maxColItems = Math.max(
    tier0_actors.length,
    tier1_frontend.length,
    tier2_gateway.length,
    tier3_services.length,
    tier4_broker.length,
    tier5_data.length,
    tier6_cloud.length,
    1
  );
  const treeTotalHeight = Math.max(maxColItems * colPitchY + 100, 680);
  const treeCenterY = Math.round(treeTotalHeight / 2);

  // Column X coordinates for spacious, clean horizontal flow
  const colX0 = 80;
  const colX1 = 580;
  const colX2 = 1120;
  const colX3 = 1720;
  const colX4 = 2360;
  const colX5 = 2940;
  const colX6 = 3560;

  const positionedNodes: Node[] = [];

  function placeColumn(
    items: Array<Record<string, unknown>>,
    colX: number,
    colCardH: number = 92,
    colGap: number = 32
  ) {
    const count = items.length;
    if (count === 0) return;
    const totalH = count * colCardH + (count - 1) * colGap;
    const startY = Math.round(treeCenterY - totalH / 2);

    items.forEach((item, idx) => {
      const id = String(item.id || `node-${positionedNodes.length}`);
      const rawData = (item.data as Record<string, unknown>) || {};
      const nodeLabel = String(rawData.label || item.label || item.name || id);
      const nodeType = String(item.type || "service");
      const y = Math.round(startY + idx * (colCardH + colGap));

      positionedNodes.push({
        id,
        type: nodeType,
        position: { x: colX + 25, y },
        data: {
          label: nodeLabel,
          role: String(rawData.role || item.role || ""),
          tech: String(rawData.tech || item.tech || ""),
          description: String(rawData.description || item.description || item.desc || ""),
          division: String(rawData.division || item.division || nodeType),
          ...rawData,
        },
      } as Node);
    });
  }

  // Add column background layer groups for tiers with tight dynamic bounding and generous spacing
  const tierConfigs = [
    { tier: 0, items: tier0_actors, x: colX0, label: "Tier 0: Client & Operator Actors", subtitle: "Stakeholders & Users", w: 320 },
    { tier: 1, items: tier1_frontend, x: colX1, label: "Tier 1: Frontend Client Apps", subtitle: "Next.js Web Application", w: 360 },
    { tier: 2, items: tier2_gateway, x: colX2, label: "Tier 2: Ingress & API Gateway", subtitle: "NGINX / Kong · TLS 1.3 · WAF", w: 360 },
    { tier: 3, items: tier3_services, x: colX3, label: "Tier 3: Domain Microservices Cluster", subtitle: "Autonomous Core Microservices", w: 420 },
    { tier: 4, items: tier4_broker, x: colX4, label: "Tier 4: Event Messaging Broker", subtitle: "Kafka / RabbitMQ · DLQ", w: 360 },
    { tier: 5, items: tier5_data, x: colX5, label: "Tier 5: Persistence & Cache", subtitle: "PostgreSQL 16 · Redis Cache", w: 400 },
    { tier: 6, items: tier6_cloud, x: colX6, label: "Tier 6: Cloud Infrastructure & CI/CD", subtitle: "AWS ECS Fargate · Observability", w: 380 },
  ];

  tierConfigs.forEach((cfg) => {
    if (cfg.items.length > 0) {
      const colCardH = cfg.tier === 0 ? 70 : 92;
      const colGap = cfg.tier === 0 ? 24 : 32;
      const count = cfg.items.length;
      const totalH = count * colCardH + (count - 1) * colGap;
      const startY = Math.round(treeCenterY - totalH / 2);
      const positions = cfg.items.map((_, idx) => ({
        y: Math.round(startY + idx * (colCardH + colGap)),
        height: colCardH,
      }));
      const bounds = computeGroupBounds(positions, 70, 30, colCardH);
      positionedNodes.push({
        id: `hgroup-lr-tier${cfg.tier}`,
        type: "layerGroup",
        data: {
          label: cfg.label,
          subtitle: cfg.subtitle,
          count: cfg.items.length,
          ...(cfg.tier === 0 ? { hideExplore: true } : {}),
        },
        position: { x: cfg.x - 20, y: bounds.y },
        style: { width: cfg.w, height: bounds.height, zIndex: -1, pointerEvents: "none" },
        draggable: false,
        selectable: false,
      });
    }
  });

  placeColumn(tier0_actors, colX0, 70, 24);
  placeColumn(tier1_frontend, colX1, 92, 32);
  placeColumn(tier2_gateway, colX2, 92, 32);
  placeColumn(tier3_services, colX3, 92, 32);
  placeColumn(tier4_broker, colX4, 92, 32);
  placeColumn(tier5_data, colX5, 92, 32);
  placeColumn(tier6_cloud, colX6, 92, 32);

  // Map handles for Left -> Right flow with proper connectivity
  const nodeMap = new Map<string, Node>();
  positionedNodes.forEach((n) => nodeMap.set(n.id, n));

  const resolvedEdges: Edge[] = rawEdges.map((e, idx) => {
    const srcNode = nodeMap.get(String(e.source));
    const tgtNode = nodeMap.get(String(e.target));

    let srcHandle: string | undefined = undefined;
    let tgtHandle: string | undefined = undefined;

    if (srcNode && tgtNode) {
      const srcX = srcNode.position.x;
      const tgtX = tgtNode.position.x;
      const srcY = srcNode.position.y;
      const tgtY = tgtNode.position.y;

      if (srcX < tgtX - 40) {
        srcHandle = getHandleForType(srcNode.type || "service", "right");
        tgtHandle = getHandleForType(tgtNode.type || "service", "left");
      } else if (srcX > tgtX + 40) {
        srcHandle = getHandleForType(srcNode.type || "service", "left");
        tgtHandle = getHandleForType(tgtNode.type || "service", "right");
      } else {
        if (srcY < tgtY) {
          srcHandle = getHandleForType(srcNode.type || "service", "bottom");
          tgtHandle = getHandleForType(tgtNode.type || "service", "top");
        } else {
          srcHandle = getHandleForType(srcNode.type || "service", "top");
          tgtHandle = getHandleForType(tgtNode.type || "service", "bottom");
        }
      }
    }

    return {
      ...e,
      id: String(e.id || `edge-${idx}`),
      source: String(e.source),
      target: String(e.target),
      sourceHandle: srcHandle || e.sourceHandle,
      targetHandle: tgtHandle || e.targetHandle,
      type: "animatedFlow",
      animated: true,
      data: (e.data as Record<string, unknown>) || (e.label ? { label: String(e.label) } : {}),
    } as Edge;
  });

  return applyColorThemesToGraph(positionedNodes, resolvedEdges);
}

/**
 * Universal Left-to-Right transformer for LLD graphs
 * Groups nodes into horizontal columns and routes edges from right to left
 */
export function layoutLldLeftToRight(
  inputNodes: Node[],
  inputEdges: Edge[]
): { nodes: Node[]; edges: Edge[] } {
  const contentNodes = inputNodes.filter((n) => n.type !== "layerGroup");
  const layerGroups = inputNodes.filter((n) => n.type === "layerGroup");

  if (contentNodes.length === 0) {
    return { nodes: inputNodes, edges: inputEdges };
  }

  // Find unique Y values to identify tiers
  const yValues = contentNodes.map((n) => n.position.y);
  yValues.sort((a, b) => a - b);

  const clusters: number[][] = [];
  yValues.forEach((y) => {
    const existing = clusters.find((c) => Math.abs(c[0] - y) < 60);
    if (existing) {
      existing.push(y);
    } else {
      clusters.push([y]);
    }
  });

  const tierAvgY = clusters.map((c) => c.reduce((sum, v) => sum + v, 0) / c.length).sort((a, b) => a - b);

  const tierBuckets: Node[][] = tierAvgY.map(() => []);
  contentNodes.forEach((n) => {
    let closestTierIdx = 0;
    let minDist = Infinity;
    tierAvgY.forEach((avgY, idx) => {
      const dist = Math.abs(n.position.y - avgY);
      if (dist < minDist) {
        minDist = dist;
        closestTierIdx = idx;
      }
    });
    tierBuckets[closestTierIdx].push(n);
  });

  const maxItemsInTier = Math.max(...tierBuckets.map((b) => b.length), 1);
  const cardH = 92;
  const gapY = 32;
  const colPitchY = cardH + gapY;
  const totalTreeHeight = Math.max(maxItemsInTier * colPitchY + 60, 560);
  const centerY = Math.round(totalTreeHeight / 2);

  const colPitchX = 380;
  const startX = 80;

  const positionedNodes: Node[] = [];

  layerGroups.forEach((g, idx) => {
    if (idx < tierBuckets.length && tierBuckets[idx].length > 0) {
      const colX = startX + idx * colPitchX;
      const bucket = tierBuckets[idx];
      const count = bucket.length;
      const totalColH = count * cardH + (count - 1) * gapY;
      const startY = Math.round(centerY - totalColH / 2);
      const positions = bucket.map((_, nodeIdx) => ({
        y: Math.round(startY + nodeIdx * (cardH + gapY)),
        height: cardH,
      }));
      const bounds = computeGroupBounds(positions, 70, 30, cardH);

      positionedNodes.push({
        ...g,
        id: g.id,
        position: { x: colX - 20, y: bounds.y },
        style: {
          ...g.style,
          width: 320,
          height: bounds.height,
          zIndex: -1,
          pointerEvents: "none",
        },
      });
    }
  });

  tierBuckets.forEach((bucket, tierIdx) => {
    bucket.sort((a, b) => a.position.x - b.position.x);

    const colX = startX + tierIdx * colPitchX;
    const count = bucket.length;
    const totalColH = count * cardH + (count - 1) * gapY;
    const startY = Math.round(centerY - totalColH / 2);

    bucket.forEach((node, nodeIdx) => {
      const y = Math.round(startY + nodeIdx * (cardH + gapY));
      positionedNodes.push({
        ...node,
        position: { x: colX, y },
      });
    });
  });

  const nodeMap = new Map<string, Node>();
  positionedNodes.forEach((n) => nodeMap.set(n.id, n));

  const resolvedEdges: Edge[] = inputEdges.map((e, idx) => {
    const srcNode = nodeMap.get(String(e.source));
    const tgtNode = nodeMap.get(String(e.target));

    let srcHandle: string | undefined = undefined;
    let tgtHandle: string | undefined = undefined;

    if (srcNode && tgtNode) {
      const srcX = srcNode.position.x;
      const tgtX = tgtNode.position.x;
      const srcY = srcNode.position.y;
      const tgtY = tgtNode.position.y;

      if (srcX < tgtX - 40) {
        srcHandle = getHandleForType(srcNode.type || "service", "right");
        tgtHandle = getHandleForType(tgtNode.type || "service", "left");
      } else if (srcX > tgtX + 40) {
        srcHandle = getHandleForType(srcNode.type || "service", "left");
        tgtHandle = getHandleForType(tgtNode.type || "service", "right");
      } else {
        if (srcY < tgtY) {
          srcHandle = getHandleForType(srcNode.type || "service", "bottom");
          tgtHandle = getHandleForType(tgtNode.type || "service", "top");
        } else {
          srcHandle = getHandleForType(srcNode.type || "service", "top");
          tgtHandle = getHandleForType(tgtNode.type || "service", "bottom");
        }
      }
    }

    return {
      ...e,
      id: String(e.id || `edge-${idx}`),
      sourceHandle: srcHandle || e.sourceHandle,
      targetHandle: tgtHandle || e.targetHandle,
      type: "animatedFlow",
      animated: true,
    } as Edge;
  });

  return applyColorThemesToGraph(positionedNodes, resolvedEdges);
}

/**
 * Intelligent HLD Parser & Hierarchical Layer Synthesizer
 * Converts any HLD JSON into a production-grade, multi-tier architectural topology
 */
export function parseHldToReactFlow(
  hldJson: Record<string, unknown> | null,
  rawPrompt?: string,
  layoutDirection: "TB" | "LR" = "TB"
): {
  nodes: Node[];
  edges: Edge[];
} {
  if (!hldJson || typeof hldJson !== "object") {
    return { nodes: [], edges: [] };
  }

  // 1. Support diagrams structure from AI Engine (e.g., diagrams[0].nodes / edges)
  const diagrams = Array.isArray(hldJson.diagrams) ? (hldJson.diagrams as Array<Record<string, unknown>>) : null;
  const firstDiagram = diagrams && diagrams.length > 0 ? diagrams[0] : null;
  const explicitNodes = (
    Array.isArray(hldJson.nodes) && hldJson.nodes.length > 0
      ? (hldJson.nodes as Array<Record<string, unknown>>)
      : firstDiagram && Array.isArray(firstDiagram.nodes) && firstDiagram.nodes.length > 0
      ? (firstDiagram.nodes as Array<Record<string, unknown>>)
      : null
  );

  const explicitEdges = (
    Array.isArray(hldJson.edges)
      ? (hldJson.edges as Array<Record<string, unknown>>)
      : firstDiagram && Array.isArray(firstDiagram.edges)
      ? (firstDiagram.edges as Array<Record<string, unknown>>)
      : []
  );


  // 2. Extract services from major_services, components, or explicit skeleton nodes
  const explicitServices = explicitNodes
    ? explicitNodes.filter((n) => {
        const type = String(n.type || "").toLowerCase();
        const id = String(n.id || "").toLowerCase();
        return (
          type === "service" ||
          type === "microservice" ||
          type === "backend" ||
          type === "worker" ||
          id.includes("service") ||
          id.includes("backend")
        );
      })
    : [];

  const rawDeclaredServices = Array.isArray(hldJson.major_services)
    ? (hldJson.major_services as Array<Record<string, unknown>>)
    : Array.isArray(hldJson.services)
    ? (hldJson.services as Array<Record<string, unknown>>)
    : null;

  const majorServices = (rawDeclaredServices && rawDeclaredServices.length >= 1)
    ? rawDeclaredServices
    : (explicitServices.length >= 1 ? explicitServices : null);

  interface MicroserviceDef {
    code: string;
    label: string;
    tech: string;
    db: string;
    desc: string;
    is_new?: boolean;
    version_added?: string;
  }

  const defaultServices: MicroserviceDef[] = [
    { code: "SVC-01", label: "Authentication & Identity Service", tech: "JWT · OAuth2 · RBAC Guard", db: "auth_schema", desc: "Handles identity, credentials, tokens, and access permissions." },
    { code: "SVC-02", label: "Core Business Domain Service", tech: "Domain Logic · Processing Engine", db: "domain_schema", desc: "Fast execution of primary business domain logic and queries." },
    { code: "SVC-03", label: "Workflow & Transaction Service", tech: "ACID Transactions · State Machine", db: "workflow_schema", desc: "Processes distributed transactions, lifecycle events, and mutations." },
    { code: "SVC-04", label: "Notification & Messaging Service", tech: "Email · Push Alerts · Webhooks", db: "notification_schema", desc: "Dispatches automated reminders, event webhooks, and alerts." },
    { code: "SVC-05", label: "Data Pipeline & Ingestion Service", tech: "Stream Processor · Storage Adapter", db: "ingestion_schema", desc: "Processes asynchronous event telemetry and asset storage." },
    { code: "SVC-06", label: "Reporting & Analytics Service", tech: "Aggregations · BI Pipeline", db: "analytics_schema", desc: "Generates operational metrics, analytical aggregates, and usage trends." },
  ];

  const microservices: MicroserviceDef[] = majorServices && majorServices.length >= 1
    ? majorServices.map((s, idx): MicroserviceDef => {
        const rawS = s as any;
        return {
          code: String(s.service_id || s.code || `SVC-0${idx + 1}`),
          label: String(s.name || s.label || `Service ${idx + 1}`),
          tech: String(s.protocol || s.type || s.database_binding || "Microservice"),
          db: String(s.database_binding || s.db || `${toSlug(String(s.name || s.label || `svc_${idx + 1}`))}_schema`),
          desc: String(s.responsibility || s.description || `${s.name || s.label || 'Service'} core business logic.`),
          is_new: Boolean(rawS.is_new || rawS.data?.is_new || rawS.version_added || rawS.data?.version_added),
          version_added: rawS.version_added || rawS.data?.version_added,
        };
      })
    : defaultServices;

  const nodes: Node[] = [];
  const edges: Edge[] = [];

  const serviceGapY = 180;

  // ── Entity Nodes Placed with Clear Separation & Precision ──
  // ── [Segment 1: Users & Stakeholders (Far Left)] ──
  const explicitActors = explicitNodes
    ? explicitNodes.filter((n) => {
        const type = String(n.type || "").toLowerCase();
        const id = String(n.id || "").toLowerCase();
        return type === "actor" || id.includes("user") || id.includes("actor") || id.includes("client");
      })
    : [];

  const rawActors = Array.isArray(hldJson.primary_actors)
    ? (hldJson.primary_actors as Array<any>)
    : Array.isArray(hldJson.actors)
    ? (hldJson.actors as Array<any>)
    : (explicitActors.length > 0 ? explicitActors : null);

  const actor1Data = rawActors && rawActors[0]
    ? {
        label: typeof rawActors[0] === "string" ? rawActors[0] : String(rawActors[0].label || rawActors[0].name || "Client / End User"),
        role: typeof rawActors[0] === "string" ? "Primary Consumer" : String(rawActors[0].role || "Primary Web & Mobile Consumer"),
        desc: typeof rawActors[0] === "object" && rawActors[0].description ? String(rawActors[0].description) : "Consumes primary client features, services, and public workflows",
      }
    : {
        label: "Client / End User",
        role: "Primary Web & Mobile Consumer",
        desc: "Accesses client interfaces, public APIs, and core platform workflows",
      };

  const actor2Data = rawActors && rawActors[1]
    ? {
        label: typeof rawActors[1] === "string" ? rawActors[1] : String(rawActors[1].label || rawActors[1].name || "System Administrator"),
        role: typeof rawActors[1] === "string" ? "Platform Administrator" : String(rawActors[1].role || "Operations & Administration Staff"),
        desc: typeof rawActors[1] === "object" && rawActors[1].description ? String(rawActors[1].description) : "Manages platform resources, permissions, configurations, and reporting",
      }
    : {
        label: "Admin / Operator",
        role: "Platform Operations & Staff",
        desc: "Oversees system administration, tenant configuration, and operational reporting",
      };

  const actorBounds = computeGroupBounds([
    { y: 340, height: 76 },
    { y: 540, height: 76 },
  ], 80, 35, 76);

  nodes.push({
    id: "group-actors",
    type: "layerGroup",
    data: {
      label: "Users & Stakeholders",
      division: "frontend",
      count: 2,
      subtitle: "Web Browser · Mobile Clients · Administrators",
      hideExplore: true,
    },
    position: { x: 80, y: actorBounds.y },
    style: { width: 360, height: actorBounds.height, zIndex: -1, pointerEvents: "none" },
    draggable: false,
    selectable: false,
  });

  nodes.push({
    id: "actor-1",
    type: "actor",
    data: {
      division: "frontend",
      label: actor1Data.label,
      role: actor1Data.role,
      description: actor1Data.desc,
    },
    position: { x: 135, y: 340 },
  });

  nodes.push({
    id: "actor-2",
    type: "actor",
    data: {
      division: "frontend",
      label: actor2Data.label,
      role: actor2Data.role,
      description: actor2Data.desc,
    },
    position: { x: 135, y: 540 },
  });

  // ── [Segment 2: Client Web Application (Next.js)] ──
  const explicitFe = explicitNodes
    ? explicitNodes.find((n) => {
        const type = String(n.type || "").toLowerCase();
        const id = String(n.id || "").toLowerCase();
        return type === "frontend" || id.includes("front") || id.includes("web") || id.includes("app");
      })
    : null;
  const feLabel = explicitFe
    ? String((explicitFe.data as any)?.label || explicitFe.label || explicitFe.name || "React / Next.js Web Application")
    : "React / Next.js Web Application";

  const feBounds = computeGroupBounds([{ y: 440, height: 92 }], 80, 35, 92);

  nodes.push({
    id: "group-frontend",
    type: "layerGroup",
    data: {
      label: "Client Web Application Tier",
      division: "frontend",
      count: 1,
      subtitle: "Next.js App Router · SSR & Client Hydration",
    },
    position: { x: 620, y: feBounds.y },
    style: { width: 380, height: feBounds.height, zIndex: -1, pointerEvents: "none" },
    draggable: false,
    selectable: false,
  });

  nodes.push({
    id: "node-frontend",
    type: "frontend",
    data: {
      division: "frontend",
      label: feLabel,
      tech: "Next.js App Router · Tailwind CSS · React 19",
      description: "Unified web client with server-side rendering and client interactivity.",
    },
    position: { x: 665, y: 440 },
  });

  // ── [Segment 3: API Gateway & Ingress Segment] ──
  const explicitGw = explicitNodes
    ? explicitNodes.find((n) => {
        const type = String(n.type || "").toLowerCase();
        const id = String(n.id || "").toLowerCase();
        return type === "gateway" || id.includes("gateway") || id.includes("gw") || id.includes("ingress");
      })
    : null;
  const gwLabel = explicitGw
    ? String((explicitGw.data as any)?.label || explicitGw.label || explicitGw.name || "API Gateway & Auth Layer")
    : "API Gateway / Ingress NGINX";
  const gwTech = explicitGw
    ? String((explicitGw.data as any)?.tech || explicitGw.tech || "NGINX · TLS 1.3 · Rate Limiting · RBAC")
    : "TLS 1.3 · Rate Limiting · RBAC Guard";

  const gwBounds = computeGroupBounds([{ y: 440, height: 92 }], 80, 35, 92);

  nodes.push({
    id: "group-gateway",
    type: "layerGroup",
    data: {
      label: "API Gateway & Ingress Segment",
      division: "frontend",
      count: 1,
      subtitle: "Reverse Proxy · TLS 1.3 · Rate Limiter · Auth Guard",
    },
    position: { x: 1180, y: gwBounds.y },
    style: { width: 380, height: gwBounds.height, zIndex: -1, pointerEvents: "none" },
    draggable: false,
    selectable: false,
  });

  nodes.push({
    id: "node-gateway",
    type: "gateway",
    data: {
      division: "frontend",
      label: gwLabel,
      tech: gwTech,
      description: "TLS termination, WAF rate limiting (100 RPS), and route orchestration.",
    },
    position: { x: 1225, y: 440 },
  });

  // ── [Segment 4: Domain Microservices Cluster] ──
  const svcPositions = microservices.map((_, idx) => ({ y: 120 + idx * serviceGapY, height: 92 }));
  const svcBounds = computeGroupBounds(svcPositions, 80, 35, 92);

  nodes.push({
    id: "group-backend",
    type: "layerGroup",
    data: {
      label: "Domain Microservices Cluster",
      division: "backend",
      count: microservices.length,
      subtitle: "Autonomous Microservices · Domain Business Workflows",
    },
    position: { x: 1800, y: svcBounds.y },
    style: { width: 440, height: svcBounds.height, zIndex: -1, pointerEvents: "none" },
    draggable: false,
    selectable: false,
  });

  microservices.forEach((s, idx) => {
    nodes.push({
      id: `svc-${idx + 1}`,
      type: "service",
      data: {
        division: "backend",
        code: s.code || `SVC-0${idx + 1}`,
        label: s.label,
        tech: s.tech,
        protocol: "gRPC / Internal",
        description: s.desc,
        is_new: s.is_new,
        version_added: s.version_added,
      },
      position: { x: 1845, y: 120 + idx * serviceGapY },
    });
  });

  // ── [Segment 5: Event Broker & Messaging] ──
  const commPatterns =
    hldJson.communication_patterns && typeof hldJson.communication_patterns === "object"
      ? (hldJson.communication_patterns as Record<string, unknown>)
      : {};
  const isKafka = String(commPatterns.asynchronous || "").includes("Kafka");

  const brokerBounds = computeGroupBounds([{ y: 440, height: 92 }], 80, 35, 92);

  nodes.push({
    id: "group-broker",
    type: "layerGroup",
    data: {
      label: "Event Streaming & Broker Segment",
      division: "backend",
      count: 1,
      subtitle: "RabbitMQ / Apache Kafka · DLQ · Asynchronous Bus",
    },
    position: { x: 2460, y: brokerBounds.y },
    style: { width: 380, height: brokerBounds.height, zIndex: -1, pointerEvents: "none" },
    draggable: false,
    selectable: false,
  });

  nodes.push({
    id: "node-rabbitmq",
    type: "queue",
    data: {
      division: "backend",
      label: isKafka ? "Apache Kafka Event Broker" : "RabbitMQ Event Broker",
      subtitle: "Event Messaging · DLQ · Retry x3",
      description: "Asynchronous domain event streaming with dead-letter exchange and retry policy.",
    },
    position: { x: 2505, y: 440 },
  });

  // ── [Segment 6: Data Persistence & Storage] ──
  const dataStrategy =
    hldJson.data_strategy && typeof hldJson.data_strategy === "object"
      ? (hldJson.data_strategy as Record<string, unknown>)
      : {};

  const explicitDb = explicitNodes
    ? explicitNodes.find((n) => {
        const type = String(n.type || "").toLowerCase();
        const id = String(n.id || "").toLowerCase();
        return type === "database" || id.includes("db") || id.includes("database") || id.includes("postgres") || id.includes("sql");
      })
    : null;

  const explicitCache = explicitNodes
    ? explicitNodes.find((n) => {
        const type = String(n.type || "").toLowerCase();
        const id = String(n.id || "").toLowerCase();
        return type === "cache" || id.includes("cache") || id.includes("redis");
      })
    : null;

  const primaryDb = explicitDb
    ? String((explicitDb.data as any)?.label || explicitDb.label || explicitDb.name || "PostgreSQL Database")
    : String(dataStrategy.primary_database || "PostgreSQL 16");

  const cachingTier = explicitCache
    ? String((explicitCache.data as any)?.label || explicitCache.label || explicitCache.name || "Redis Cache")
    : String(dataStrategy.caching_tier || "Redis 7.2 Cluster");

  const dbBounds = computeGroupBounds([
    { y: 280, height: 92 },
    { y: 560, height: 92 },
  ], 80, 35, 92);

  nodes.push({
    id: "group-database",
    type: "layerGroup",
    data: {
      label: "Data Persistence & Storage Segment",
      division: "database",
      count: 2,
      subtitle: "PostgreSQL 16 Multi-Schema · Redis 7.2 Cluster",
    },
    position: { x: 3060, y: dbBounds.y },
    style: { width: 420, height: dbBounds.height, zIndex: -1, pointerEvents: "none" },
    draggable: false,
    selectable: false,
  });

  nodes.push({
    id: "node-redis",
    type: "cache",
    data: {
      division: "database",
      label: cachingTier,
      subtitle: "Cache · Session Tokens · PubSub",
      description: "In-memory caching for query acceleration (300s TTL) and session tokens.",
    },
    position: { x: 3105, y: 280 },
  });

  nodes.push({
    id: "node-database",
    type: "database",
    data: {
      division: "database",
      engine: primaryDb,
      label: primaryDb.includes("PostgreSQL") || primaryDb.includes("DB") ? primaryDb : `${primaryDb} Database`,
      schema: "Multi-Schema Relational Storage",
      description:
        "Centralized ACID relational persistence layer with schema isolation for domain services and automated backups.",
    },
    position: { x: 3105, y: 560 },
  });

  // ── [Segment 7: DevOps, CI/CD & Observability] ──
  const devBounds = computeGroupBounds([
    { y: 180, height: 92 },
    { y: 390, height: 92 },
    { y: 600, height: 92 },
  ], 80, 35, 92);

  nodes.push({
    id: "group-deployment",
    type: "layerGroup",
    data: {
      label: "Platform DevOps & Observability",
      division: "deployment",
      count: 3,
      subtitle: "CI/CD Pipeline · Kubernetes EKS · Prometheus",
    },
    position: { x: 3700, y: devBounds.y },
    style: { width: 400, height: devBounds.height, zIndex: -1, pointerEvents: "none" },
    draggable: false,
    selectable: false,
  });

  nodes.push({
    id: "node-github-actions",
    type: "devops",
    data: {
      division: "deployment",
      label: "GitHub Actions CI/CD",
      role: "Build · Test · Scan · Deploy",
      category: "cicd",
      description: "Automated linting, unit tests, Docker builds, and Trivy vulnerability scans.",
    },
    position: { x: 3750, y: 180 },
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
    position: { x: 3750, y: 390 },
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
    position: { x: 3750, y: 600 },
  });

  // ── Connection Edges with Non-Overlapping Systematic Orthogonal Routing ──
  // Users interacting with Next.js Client Application
  edges.push({
    id: "e-act1-fe",
    source: "actor-1",
    target: "node-frontend",
    sourceHandle: "act-right",
    targetHandle: "fe-left",
    type: "animatedFlow",
    data: { label: "Web & Mobile" },
    animated: true,
  });
  edges.push({
    id: "e-act2-fe",
    source: "actor-2",
    target: "node-frontend",
    sourceHandle: "act-right",
    targetHandle: "fe-left",
    type: "animatedFlow",
    data: { label: "Admin & Staff" },
    animated: true,
  });

  // Client Web App to Ingress Gateway (Clean Horizontal Line on y: 440)
  edges.push({
    id: "e-fe-gw",
    source: "node-frontend",
    target: "node-gateway",
    sourceHandle: "fe-right",
    targetHandle: "gw-left",
    type: "animatedFlow",
    data: { label: "HTTPS / REST (TLS 1.3)" },
    animated: true,
  });

  // Ingress Gateway Fan-out to Microservices (gw-right -> svc-left) with clean concise route labels
  microservices.forEach((s, idx) => {
    const rawSlug = toSlug(s.label || `svc_${idx + 1}`)
      .replace(/-service/gi, "")
      .replace(/-management/gi, "")
      .replace(/-tracking/gi, "");
    const shortSlug = rawSlug.split("-").slice(0, 2).join("-") || `svc${idx + 1}`;
    edges.push({
      id: `e-gw-svc${idx + 1}`,
      source: "node-gateway",
      target: `svc-${idx + 1}`,
      sourceHandle: "gw-right",
      targetHandle: "svc-left",
      type: "animatedFlow",
      data: { label: `/api/${shortSlug}` },
      animated: true,
    });
  });

  // Services publishing asynchronous events to RabbitMQ Broker (svc-right -> q-left)
  if (microservices.length >= 3) {
    edges.push({
      id: "e-svc3-q",
      source: "svc-3",
      target: "node-rabbitmq",
      sourceHandle: "svc-right",
      targetHandle: "q-left",
      type: "animatedFlow",
      data: { label: "Publish Events" },
      animated: true,
    });
  }
  if (microservices.length >= 4) {
    edges.push({
      id: "e-svc4-q",
      source: "svc-4",
      target: "node-rabbitmq",
      sourceHandle: "svc-right",
      targetHandle: "q-left",
      type: "animatedFlow",
      data: { label: "Async Tasks" },
      animated: true,
    });
  }

  // Microservices querying Caching Tier (svc-right -> cache-left)
  if (microservices.length >= 2) {
    edges.push({
      id: "e-svc2-redis",
      source: "svc-2",
      target: "node-redis",
      sourceHandle: "svc-right",
      targetHandle: "cache-left",
      type: "animatedFlow",
      data: { label: "Query Cache (300s)" },
      animated: true,
    });
  }

  // Primary Domain Services querying Persistence Database (svc-right -> db-left)
  const dbServices = [0, microservices.length - 1].filter((i) => i >= 0 && i < microservices.length);
  dbServices.forEach((svcIdx) => {
    const rawDb = String(microservices[svcIdx]?.db || microservices[svcIdx]?.label || "domain");
    const cleanDb = rawDb.replace(/_schema|_db|schema/gi, "").trim();
    edges.push({
      id: `e-svc${svcIdx + 1}-db`,
      source: `svc-${svcIdx + 1}`,
      target: "node-database",
      sourceHandle: "svc-right",
      targetHandle: "db-left",
      type: "animatedFlow",
      data: { label: `${cleanDb || "domain"}_schema` },
      animated: true,
    });
  });

  // Event Broker to Persistence
  edges.push({
    id: "e-q-db",
    source: "node-rabbitmq",
    target: "node-database",
    sourceHandle: "q-right",
    targetHandle: "db-left",
    type: "animatedFlow",
    data: { label: "Event Store & Telemetry" },
    animated: true,
  });

  // DevOps & Observability Pipeline (dev-bottom -> dev-top)
  edges.push({
    id: "e-gh-k8s",
    source: "node-github-actions",
    target: "node-k8s",
    sourceHandle: "dev-bottom",
    targetHandle: "dev-top",
    type: "animatedFlow",
    data: { label: "ECR Push & Deploy" },
    animated: true,
  });
  edges.push({
    id: "e-k8s-prom",
    source: "node-k8s",
    target: "node-prometheus",
    sourceHandle: "dev-bottom",
    targetHandle: "dev-top",
    type: "animatedFlow",
    data: { label: "Pod Metrics & Logs" },
    animated: true,
  });

  return applyColorThemesToGraph(nodes, edges);
}

/**
 * Intelligent LLD Parser & Symmetrical Architectural Synthesizer
 * Converts low-level design JSON payloads into balanced, production-grade component blueprints.
 */
export function parseLldToReactFlow(
  lldType: string,
  lldData: Record<string, unknown> | null,
  layoutDirection: "TB" | "LR" = "TB"
): { nodes: Node[]; edges: Edge[] } {
  if (!lldData || typeof lldData !== "object" || Object.keys(lldData).length === 0) {
    return { nodes: [], edges: [] };
  }

  function finalizeLld(nodes: Node[], edges: Edge[]): { nodes: Node[]; edges: Edge[] } {
    return applyColorThemesToGraph(nodes, edges);
  }

  const type = lldType.toLowerCase();

  // ── 1. BACKEND LLD ARCHITECTURE TOPOLOGY ──
  // Spacious Horizontal Architecture Segments (Endpoints -> Security -> Domain Services -> Broker -> Repos -> Models)
  if (type === "backend") {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // ── Tier 1: Ingress Endpoints ──
    const rawEndpoints = Array.isArray(lldData.api_endpoints)
      ? (lldData.api_endpoints as Array<any>)
      : Array.isArray(lldData.endpoints)
      ? (lldData.endpoints as Array<any>)
      : [];

    const defaultEndpoints = [
      { method: "POST", route: "/api/v1/auth/login", protocol: "Public Ingress", desc: "Authenticate user credentials & issue RS256 JWT tokens." },
      { method: "GET", route: "/api/v1/resources", protocol: "Public Ingress", desc: "Query indexed domain resources with filters and pagination." },
      { method: "POST", route: "/api/v1/workflows/submit", protocol: "Protected Route", desc: "Submit domain workflow transaction with validation." },
      { method: "POST", route: "/api/v1/tasks/process", protocol: "Protected Route", desc: "Trigger asynchronous worker pipeline task." },
    ];

    const endpoints = rawEndpoints.length >= 1
      ? rawEndpoints.map((ep, idx) => ({
          method: String(ep.method || "POST").toUpperCase(),
          route: String(ep.route || ep.path || `/api/v1/endpoint-${idx + 1}`),
          protocol: ep.auth_required ? "Protected Route" : "Public Ingress",
          desc: String(ep.description || `${ep.route || ep.path || 'API'} endpoint operation.`),
          is_new: Boolean(ep.is_new || ep.version_added),
          version_added: ep.version_added,
        }))
      : defaultEndpoints;

    // ── Tier 3: Domain Services ──
    const rawServices = Array.isArray(lldData.services) ? (lldData.services as Array<any>) : [];
    const defaultBackendServices = [
      { label: "Auth & Identity Service", tech: "JWT · OAuth2 · RBAC Guard", desc: "Validates credentials and manages session tokens." },
      { label: "Core Domain Service", tech: "Domain Logic · Processing Engine", desc: "Executes primary domain operations and business rules." },
      { label: "Transaction Orchestrator", tech: "ACID Orchestration · State Machine", desc: "Coordinates distributed workflows and state mutations." },
      { label: "Async Task Worker", tech: "Async Event Worker · BullMQ", desc: "Processes background tasks and event dispatch." },
    ];

    const backendServices = rawServices.length >= 1
      ? rawServices.map((s, idx) => ({
          label: String(s.name || `Service ${idx + 1}`),
          tech: Array.isArray(s.dependencies) ? s.dependencies.slice(0, 2).join(" · ") : "Domain Service",
          desc: String(s.responsibility || `${s.name} core logic.`),
          is_new: Boolean(s.is_new || s.version_added),
          version_added: s.version_added,
        }))
      : defaultBackendServices;

    // ── Tier 5: Repositories ──
    const rawRepos = Array.isArray(lldData.repositories) ? (lldData.repositories as Array<any>) : [];
    const defaultRepos = [
      { id: "brepo-1", label: "UserRepository", entity: "User Entity", desc: "SQLAlchemy async repo for user identities" },
      { id: "brepo-2", label: "CoreRepository", entity: "Domain Entity", desc: "SQLAlchemy async repo for domain resources" },
      { id: "brepo-3", label: "WorkflowRepository", entity: "Workflow Entity", desc: "SQLAlchemy async repo for workflow state" },
    ];

    const repos = rawRepos.length >= 1
      ? rawRepos.map((r, idx) => ({
          id: `brepo-${idx + 1}`,
          label: String(r.name || `Repo ${idx + 1}`),
          entity: `${String(r.entity || r.name || "Domain")} Entity`,
          desc: `SQLAlchemy async repo for ${String(r.entity || r.name || "domain")} records`,
          is_new: Boolean(r.is_new || r.version_added),
          version_added: r.version_added,
        }))
      : defaultRepos;

    // ── Tier 6: Domain Models ──
    const rawModels = Array.isArray(lldData.domain_models)
      ? (lldData.domain_models as Array<any>)
      : Array.isArray(lldData.models)
      ? (lldData.models as Array<any>)
      : [];

    const defaultModels = [
      { id: "bmodel-1", label: "User Model", table: "users table", desc: "id, username, email, role, created_at" },
      { id: "bmodel-2", label: "Resource Model", table: "resources table", desc: "id, name, status, config, updated_at" },
      { id: "bmodel-3", label: "Workflow Model", table: "workflows table", desc: "id, user_id, status, payload, timestamp" },
      { id: "bmodel-4", label: "Audit Model", table: "audit_logs table", desc: "id, action, actor_id, ip, timestamp" },
    ];

    const models = rawModels.length >= 1
      ? rawModels.map((m, idx) => {
          const fieldsStr =
            m.fields && typeof m.fields === "object"
              ? Object.keys(m.fields).slice(0, 5).join(", ")
              : "id, name, status, created_at";
          return {
            id: `bmodel-${idx + 1}`,
            label: `${String(m.name || `Model ${idx + 1}`)} Model`,
            table: `${String(m.name || "entity").toLowerCase()}s table`,
            desc: fieldsStr,
            is_new: Boolean(m.is_new || m.version_added),
            version_added: m.version_added,
          };
        })
      : defaultModels;

    const bBoundsEndpoints = computeGroupBounds(endpoints.map((_, idx) => ({ y: 120 + idx * 160, height: 92 })));
    const bBoundsSecurity = computeGroupBounds([{ y: 220, height: 92 }, { y: 420, height: 92 }]);
    const bBoundsServices = computeGroupBounds(backendServices.map((_, idx) => ({ y: 120 + idx * 170, height: 92 })));
    const bBoundsBroker = computeGroupBounds([{ y: 380, height: 92 }]);
    const bBoundsRepos = computeGroupBounds([{ y: 220, height: 92 }, ...repos.map((_, idx) => ({ y: 440 + idx * 160, height: 92 }))]);
    const bBoundsModels = computeGroupBounds(models.map((_, idx) => ({ y: 120 + idx * 160, height: 92 })));

    // ── 6 Systematic Architecture Segments with Dynamic Bounding & Generous Spacing ──
    nodes.push({
      id: "bgroup-endpoints",
      type: "layerGroup",
      data: {
        label: "Tier 1: API Routing & Ingress Endpoints",
        subtitle: "FastAPI REST Route Handlers · Ingress Controllers",
        count: endpoints.length,
      },
      position: { x: 80, y: bBoundsEndpoints.y },
      style: { width: 380, height: bBoundsEndpoints.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "bgroup-security",
      type: "layerGroup",
      data: {
        label: "Tier 2: Ingress Security & Authentication Guard",
        subtitle: "JWT RS256 Bearer Token Authority · WAF Rate Limiter",
        count: 2,
      },
      position: { x: 640, y: bBoundsSecurity.y },
      style: { width: 360, height: bBoundsSecurity.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "bgroup-services",
      type: "layerGroup",
      data: {
        label: "Tier 3: Domain Microservices & Business Logic",
        subtitle: "Core Business Workflows · ACID State Machines",
        count: backendServices.length,
      },
      position: { x: 1200, y: bBoundsServices.y },
      style: { width: 400, height: bBoundsServices.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "bgroup-broker",
      type: "layerGroup",
      data: {
        label: "Tier 4: Asynchronous Messaging & Event Streaming",
        subtitle: "RabbitMQ / Kafka Topic Exchange · Dead Letter Queue",
        count: 1,
      },
      position: { x: 1800, y: bBoundsBroker.y },
      style: { width: 360, height: bBoundsBroker.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "bgroup-repos",
      type: "layerGroup",
      data: {
        label: "Tier 5: Data Access Repositories & Connection Pooling",
        subtitle: "SQLAlchemy 2.0 Async Repositories · PgBouncer Pool",
        count: repos.length + 1,
      },
      position: { x: 2360, y: bBoundsRepos.y },
      style: { width: 400, height: bBoundsRepos.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "bgroup-models",
      type: "layerGroup",
      data: {
        label: "Tier 6: Relational Domain Models & Persistence Schemas",
        subtitle: "PostgreSQL Relational Schema Tables · Entity Mapping",
        count: models.length,
      },
      position: { x: 2960, y: bBoundsModels.y },
      style: { width: 400, height: bBoundsModels.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // ── Tier 1 Nodes: Ingress Endpoints ──
    endpoints.forEach((ep: any, idx: number) => {
      nodes.push({
        id: `bep-${idx + 1}`,
        type: "service",
        data: {
          code: ep.method,
          label: ep.route,
          tech: "FastAPI Route",
          protocol: ep.protocol,
          description: ep.desc,
          is_new: ep.is_new,
          version_added: ep.version_added,
        },
        position: { x: 125, y: 120 + idx * 160 },
      });
    });

    // ── Tier 2 Nodes: Security Middleware ──
    nodes.push({
      id: "bnode-jwt",
      type: "gateway",
      data: {
        label: "JWT RS256 Auth Middleware",
        tech: "OAuth2 Bearer · PyJWT · RBAC",
        description: "Validates incoming bearer tokens and injects authenticated principal context.",
      },
      position: { x: 675, y: 220 },
    });

    nodes.push({
      id: "bnode-waf",
      type: "gateway",
      data: {
        label: "API Rate Limiter & WAF Guard",
        tech: "100 RPS Limit · IP Filtering",
        description: "Enforces rate limiting and blocks malicious payloads before reaching services.",
      },
      position: { x: 675, y: 440 },
    });

    // ── Tier 3 Nodes: Domain Services ──
    const svcCodes = ["SVC-01", "SVC-02", "SVC-03", "SVC-04"];
    backendServices.forEach((s: any, idx: number) => {
      nodes.push({
        id: `bsvc-${idx + 1}`,
        type: "service",
        data: {
          code: svcCodes[idx] || `SVC-${idx + 1}`,
          label: s.label,
          tech: s.tech,
          protocol: "Domain Service",
          description: s.desc,
          is_new: s.is_new,
          version_added: s.version_added,
        },
        position: { x: 1235, y: 120 + idx * 160 },
      });
    });

    // ── Tier 4 Node: Event Broker ──
    nodes.push({
      id: "bnode-queue",
      type: "queue",
      data: {
        label: "RabbitMQ / Kafka Event Broker",
        subtitle: "AMQP 0-9-1 · Topic Exchange · DLQ",
        description: "Asynchronous domain event streaming for decoupled worker jobs and event distribution.",
      },
      position: { x: 1835, y: 340 },
    });

    // ── Tier 5 Nodes: Repositories & Connection Pool ──
    repos.forEach((repo: any, idx: number) => {
      nodes.push({
        id: repo.id,
        type: "database",
        data: {
          engine: "SQLAlchemy ORM",
          label: repo.label,
          schema: repo.entity,
          description: repo.desc,
          is_new: repo.is_new,
          version_added: repo.version_added,
        },
        position: { x: 2395, y: 120 + idx * 160 },
      });
    });

    nodes.push({
      id: "bnode-pool",
      type: "gateway",
      data: {
        label: "PgBouncer Connection Pool",
        tech: "SQLAlchemy 2.0 Asyncpg · 50 Max",
        description: "Maintains reusable async database socket pool with Read Committed transaction isolation.",
      },
      position: { x: 2395, y: 120 + repos.length * 160 },
    });

    // ── Tier 6 Nodes: Domain Models & Tables ──
    models.forEach((model: any, idx: number) => {
      nodes.push({
        id: model.id,
        type: "database",
        data: {
          engine: "PostgreSQL 16",
          label: model.label,
          schema: model.table,
          description: model.desc,
          is_new: model.is_new,
          version_added: model.version_added,
        },
        position: { x: 2995, y: 120 + idx * 160 },
      });
    });

    // ── Edges: Pure Left-to-Right Orthogonal Systematic Flow ──
    // Tier 1 -> Tier 2
    edges.push({ id: "be-ep1-jwt", source: "bep-1", target: "bnode-jwt", sourceHandle: "svc-right", targetHandle: "gw-left", type: "animatedFlow", animated: true });
    if (endpoints.length >= 2) edges.push({ id: "be-ep2-jwt", source: "bep-2", target: "bnode-jwt", sourceHandle: "svc-right", targetHandle: "gw-left", type: "animatedFlow", animated: true });
    if (endpoints.length >= 3) edges.push({ id: "be-ep3-waf", source: "bep-3", target: "bnode-waf", sourceHandle: "svc-right", targetHandle: "gw-left", type: "animatedFlow", animated: true });
    if (endpoints.length >= 4) edges.push({ id: "be-ep4-waf", source: "bep-4", target: "bnode-waf", sourceHandle: "svc-right", targetHandle: "gw-left", type: "animatedFlow", animated: true });

    // Tier 2 -> Tier 3
    edges.push({ id: "be-jwt-s1", source: "bnode-jwt", target: "bsvc-1", sourceHandle: "gw-right", targetHandle: "svc-left", type: "animatedFlow", data: { label: "Verify Claims" }, animated: true });
    if (backendServices.length >= 2) edges.push({ id: "be-jwt-s2", source: "bnode-jwt", target: "bsvc-2", sourceHandle: "gw-right", targetHandle: "svc-left", type: "animatedFlow", data: { label: "Principal Context" }, animated: true });
    if (backendServices.length >= 3) edges.push({ id: "be-waf-s3", source: "bnode-waf", target: "bsvc-3", sourceHandle: "gw-right", targetHandle: "svc-left", type: "animatedFlow", data: { label: "Rate Checked" }, animated: true });
    if (backendServices.length >= 4) edges.push({ id: "be-waf-s4", source: "bnode-waf", target: "bsvc-4", sourceHandle: "gw-right", targetHandle: "svc-left", type: "animatedFlow", data: { label: "Ingress Guard" }, animated: true });

    // Tier 3 -> Tier 4
    if (backendServices.length >= 3) {
      edges.push({ id: "be-s3-q", source: "bsvc-3", target: "bnode-queue", sourceHandle: "svc-right", targetHandle: "q-left", type: "animatedFlow", data: { label: "Publish Events" }, animated: true });
    }

    // Tier 4 -> Tier 3 Worker
    if (backendServices.length >= 4) {
      edges.push({ id: "be-q-s4", source: "bnode-queue", target: "bsvc-4", sourceHandle: "q-right", targetHandle: "svc-left", type: "animatedFlow", data: { label: "Consume Tasks" }, animated: true });
    }

    // Tier 3 -> Tier 5
    edges.push({ id: "be-s1-r1", source: "bsvc-1", target: "brepo-1", sourceHandle: "svc-right", targetHandle: "db-left", type: "animatedFlow", animated: true });
    if (backendServices.length >= 2 && repos.length >= 2) edges.push({ id: "be-s2-r2", source: "bsvc-2", target: "brepo-2", sourceHandle: "svc-right", targetHandle: "db-left", type: "animatedFlow", animated: true });
    if (backendServices.length >= 3 && repos.length >= 3) edges.push({ id: "be-s3-r3", source: "bsvc-3", target: "brepo-3", sourceHandle: "svc-right", targetHandle: "db-left", type: "animatedFlow", animated: true });
    if (backendServices.length >= 4) edges.push({ id: "be-s4-pool", source: "bsvc-4", target: "bnode-pool", sourceHandle: "svc-right", targetHandle: "gw-left", type: "animatedFlow", data: { label: "Pool Conns" }, animated: true });

    // Tier 5 -> Tier 6
    edges.push({ id: "be-r1-m1", source: "brepo-1", target: "bmodel-1", sourceHandle: "db-right", targetHandle: "db-left", type: "animatedFlow", animated: true });
    if (repos.length >= 2 && models.length >= 2) edges.push({ id: "be-r2-m2", source: "brepo-2", target: "bmodel-2", sourceHandle: "db-right", targetHandle: "db-left", type: "animatedFlow", animated: true });
    if (repos.length >= 3 && models.length >= 3) edges.push({ id: "be-r3-m3", source: "brepo-3", target: "bmodel-3", sourceHandle: "db-right", targetHandle: "db-left", type: "animatedFlow", animated: true });
    if (models.length >= 4) edges.push({ id: "be-pool-m4", source: "bnode-pool", target: "bmodel-4", sourceHandle: "gw-right", targetHandle: "db-left", type: "animatedFlow", animated: true });

    return finalizeLld(nodes, edges);
  }

  // ── 2. DATABASE LLD ARCHITECTURE TOPOLOGY ──
  // Spacious Horizontal Architecture Segments (Pooling -> Master Tables -> Child Tables -> Cache -> Migrations/Recovery)
  if (type === "database") {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // ── Database Tables (Dynamic from lldData.tables) ──
    const rawTables = Array.isArray(lldData.tables) ? (lldData.tables as Array<any>) : [];
    const defaultTables = [
      { name: "users", schema: "id (UUID PK) · username · email · role · password_hash", desc: "User accounts, authentication credentials, and roles." },
      { name: "domain_entities", schema: "id (UUID PK) · user_id (FK) · name · status · config", desc: "Master domain entity records and operational configuration." },
      { name: "catalog_items", schema: "id (UUID PK) · category · metadata · version · active", desc: "Indexed catalog definitions, system options, and presets." },
      { name: "workflow_runs", schema: "id (UUID PK) · entity_id (FK) · status · metrics · created_at", desc: "Workflow execution lifecycle logs and telemetry." },
      { name: "audit_records", schema: "id (UUID PK) · actor_id · action · ip_address · recorded_at", desc: "Immutable security compliance audit trail." },
    ];

    const tables = rawTables.length >= 1
      ? rawTables.map((t, idx) => {
          let colSummary = "id (UUID PK)";
          let hasNewCol = false;
          let colVersion: string | undefined = undefined;
          if (Array.isArray(t.columns) && t.columns.length > 0) {
            colSummary = t.columns.slice(0, 5).map((c: any) => {
              const colName = typeof c === "string" ? c : (c.name || c.column_name || "col");
              const isPk = typeof c === "object" && c.primary_key ? " PK" : "";
              const isFk = typeof c === "object" && c.foreign_key ? " FK" : "";
              if (typeof c === "object" && (c.is_new || c.version_added)) {
                hasNewCol = true;
                if (!colVersion) colVersion = c.version_added;
              }
              return `${colName}${isPk}${isFk}`;
            }).join(" · ");
          }
          return {
            name: String(t.table_name || t.name || `table_${idx + 1}`),
            schema: colSummary,
            desc: String(t.description || `${t.table_name || t.name || 'Database'} table record storage.`),
            is_new: Boolean(t.is_new || t.version_added || hasNewCol),
            version_added: t.version_added || colVersion,
          };
        })
      : defaultTables;

    const primaryCount = Math.min(tables.length, 3);
    const dependentCount = Math.max(0, tables.length - 3);

    const dbBoundsTier1 = computeGroupBounds([{ y: 220, height: 92 }, { y: 440, height: 92 }]);
    const dbBoundsTier2 = computeGroupBounds(Array.from({ length: primaryCount }, (_, i) => ({ y: 120 + i * 180, height: 92 })));
    const dbBoundsTier3 = dependentCount > 0
      ? computeGroupBounds(Array.from({ length: dependentCount }, (_, relIdx) => ({ y: 120 + relIdx * 180, height: 92 })))
      : { y: 120, height: 180 };
    const dbBoundsTier4 = computeGroupBounds([{ y: 220, height: 92 }, { y: 440, height: 92 }]);
    const dbBoundsTier5 = computeGroupBounds([{ y: 220, height: 92 }, { y: 440, height: 92 }]);

    // ── 5 Systematic Architecture Segments with Tight Dynamic Bounding & Generous Spacing ──
    nodes.push({
      id: "dbgroup-tier1",
      type: "layerGroup",
      data: {
        label: "Tier 1: Connection Pooling & Ingress Routing",
        subtitle: "PgBouncer Connection Pooler · Asyncpg Driver · Read-Write Query Router",
        count: 2,
      },
      position: { x: 80, y: dbBoundsTier1.y },
      style: { width: 360, height: dbBoundsTier1.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "dbgroup-tier2",
      type: "layerGroup",
      data: {
        label: "Tier 2: Primary Entity Master Tables",
        subtitle: "PostgreSQL 16 Multi-AZ · Primary-Foreign Key Relationships",
        count: primaryCount,
      },
      position: { x: 620, y: dbBoundsTier2.y },
      style: { width: 440, height: dbBoundsTier2.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    if (dependentCount > 0) {
      nodes.push({
        id: "dbgroup-tier3",
        type: "layerGroup",
        data: {
          label: "Tier 3: Dependent Transaction & Event Tables",
          subtitle: "Execution Logs · Foreign Key Child Records · Telemetry",
          count: dependentCount,
        },
        position: { x: 1260, y: dbBoundsTier3.y },
        style: { width: 440, height: dbBoundsTier3.height, zIndex: -1, pointerEvents: "none" },
        draggable: false,
        selectable: false,
      });
    }

    nodes.push({
      id: "dbgroup-tier4",
      type: "layerGroup",
      data: {
        label: "Tier 4: Distributed Cache & Session Acceleration",
        subtitle: "Redis 7.2 Cluster · Write-Through Invalidation · Pub/Sub",
        count: 2,
      },
      position: { x: 1900, y: dbBoundsTier4.y },
      style: { width: 380, height: dbBoundsTier4.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "dbgroup-tier5",
      type: "layerGroup",
      data: {
        label: "Tier 5: Schema Versioning & Disaster Recovery",
        subtitle: "Alembic Versioned Revisions · Continuous S3 WAL-G Recovery",
        count: 2,
      },
      position: { x: 2480, y: dbBoundsTier5.y },
      style: { width: 380, height: dbBoundsTier5.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // ── Tier 1 Nodes: Connection Pooling ──
    nodes.push({
      id: "dnode-pgbouncer",
      type: "gateway",
      data: {
        label: "PgBouncer Connection Pool",
        tech: "20 min, 50 max · Asyncpg Driver",
        description: "Transaction pooling with Read Committed isolation and row-level locking.",
      },
      position: { x: 115, y: 220 },
    });

    nodes.push({
      id: "dnode-router",
      type: "gateway",
      data: {
        label: "Query Router & Read Split",
        tech: "Primary Write · Multi-AZ Replica Read",
        description: "Routes write transactions to Primary PostgreSQL instance and read traffic to replicas.",
      },
      position: { x: 115, y: 440 },
    });

    // ── Tier 2 Nodes: Primary Master Tables (indices 0, 1, 2) ──
    for (let i = 0; i < primaryCount; i++) {
      const tbl: any = tables[i];
      nodes.push({
        id: `dtbl-${i + 1}`,
        type: "database",
        data: {
          engine: "PostgreSQL 16",
          label: `Table: ${tbl.name}`,
          schema: tbl.schema,
          description: tbl.desc,
          is_new: tbl.is_new,
          version_added: tbl.version_added,
        },
        position: { x: 655, y: 120 + i * 180 },
      });
    }

    // ── Tier 3 Nodes: Dependent & Evolved Tables (idx 3 onwards) ──
    for (let i = 3; i < tables.length; i++) {
      const tbl: any = tables[i];
      const relIdx = i - 3;
      nodes.push({
        id: `dtbl-${i + 1}`,
        type: "database",
        data: {
          engine: "PostgreSQL 16",
          label: `Table: ${tbl.name}`,
          schema: tbl.schema,
          description: tbl.desc,
          is_new: tbl.is_new,
          version_added: tbl.version_added,
        },
        position: { x: 1295, y: 120 + relIdx * 180 },
      });
    }

    // ── Tier 4 Nodes: In-Memory Cache ──
    nodes.push({
      id: "dnode-redis",
      type: "cache",
      data: {
        label: "Redis 7.2 Cluster",
        subtitle: "entity_cache (300s) · search_index (120s) · Pub/Sub",
        description: "Write-through caching with proactive key invalidation on entity mutations.",
      },
      position: { x: 1935, y: 220 },
    });

    nodes.push({
      id: "dnode-session",
      type: "cache",
      data: {
        label: "Fast Session & Token Store",
        subtitle: "session_state (900s) · rate_tokens (60s)",
        description: "Ephemeral user session tokens and hot rate-limit sliding windows.",
      },
      position: { x: 1935, y: 440 },
    });

    // ── Tier 5 Nodes: Migrations & Reliability ──
    nodes.push({
      id: "dnode-alembic",
      type: "devops",
      data: {
        label: "Alembic Versioned Migrations",
        role: "Sequential Revision Tracking & Rollback",
        category: "cicd",
        description: "Automated schema migrations executed in pre-deployment CI/CD hooks.",
      },
      position: { x: 2515, y: 220 },
    });

    nodes.push({
      id: "dnode-backup",
      type: "devops",
      data: {
        label: "Automated WAL-G Backup & PITR",
        role: "Continuous Archiving · S3 7-Day PITR",
        category: "monitoring",
        description: "Continuous PostgreSQL write-ahead log shipping to encrypted S3 with Point-In-Time recovery.",
      },
      position: { x: 2515, y: 440 },
    });

    // ── Edges: Pure Left-to-Right Orthogonal Systematic Flow ──
    // Tier 1 -> Tier 2
    edges.push({ id: "de-pgb-t1", source: "dnode-pgbouncer", target: "dtbl-1", sourceHandle: "gw-right", targetHandle: "db-left", type: "animatedFlow", data: { label: "Pool Conns" }, animated: true });
    if (tables.length >= 2) edges.push({ id: "de-pgb-t2", source: "dnode-pgbouncer", target: "dtbl-2", sourceHandle: "gw-right", targetHandle: "db-left", type: "animatedFlow", data: { label: "ACID Conns" }, animated: true });
    if (tables.length >= 3) edges.push({ id: "de-router-t3", source: "dnode-router", target: "dtbl-3", sourceHandle: "gw-right", targetHandle: "db-left", type: "animatedFlow", data: { label: "Replica Reads" }, animated: true });

    // Tier 2 -> Tier 3
    if (tables.length >= 4) {
      edges.push({ id: "de-t1-t4", source: "dtbl-1", target: "dtbl-4", sourceHandle: "db-right", targetHandle: "db-left", type: "animatedFlow", data: { label: "1:N FK (user_id)" }, animated: true });
      edges.push({ id: "de-t2-t4", source: "dtbl-2", target: "dtbl-4", sourceHandle: "db-right", targetHandle: "db-left", type: "animatedFlow", data: { label: "1:N FK (entity_id)" }, animated: true });
    }
    if (tables.length >= 5) {
      edges.push({ id: "de-t2-t5", source: "dtbl-2", target: "dtbl-5", sourceHandle: "db-right", targetHandle: "db-left", type: "animatedFlow", data: { label: "1:N FK (audit)" }, animated: true });
    }

    // Tier 3 -> Tier 4
    if (tables.length >= 4) {
      edges.push({ id: "de-t4-redis", source: "dtbl-4", target: "dnode-redis", sourceHandle: "db-right", targetHandle: "cache-left", type: "animatedFlow", data: { label: "Cache Invalidation" }, animated: true });
    }
    if (tables.length >= 5) {
      edges.push({ id: "de-t5-session", source: "dtbl-5", target: "dnode-session", sourceHandle: "db-right", targetHandle: "cache-left", type: "animatedFlow", data: { label: "Session Audit Log" }, animated: true });
    }

    // Tier 4 -> Tier 5
    edges.push({ id: "de-redis-alembic", source: "dnode-redis", target: "dnode-alembic", sourceHandle: "cache-right", targetHandle: "dev-left", type: "animatedFlow", data: { label: "Pre-Deploy Hook" }, animated: true });
    edges.push({ id: "de-session-backup", source: "dnode-session", target: "dnode-backup", sourceHandle: "cache-right", targetHandle: "dev-left", type: "animatedFlow", data: { label: "WAL Archive" }, animated: true });

    return finalizeLld(nodes, edges);
  }

  // ── 3. FRONTEND LLD ARCHITECTURE TOPOLOGY ──
  // Spacious Horizontal Architecture Segments (App Shell -> Screens -> Components -> Client State/Cache -> Transport)
  if (type === "frontend") {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    interface FrontendPageItem {
      label: string;
      tech: string;
      desc: string;
      is_new?: boolean;
      version_added?: string;
    }

    const rawPages = Array.isArray(lldData.pages) ? (lldData.pages as Array<any>) : [];
    const defaultPages: FrontendPageItem[] = [
      { label: "LoginPage", tech: "/login", desc: "Authentication entry with credentials form and OAuth2 identity provider redirects." },
      { label: "DashboardPage", tech: "/dashboard", desc: "Central user dashboard with key metrics and action shortcuts." },
      { label: "ResourceOverviewPage", tech: "/resources", desc: "Interactive resource explorer with dynamic search, filters, and status cards." },
    ];

    const pages: FrontendPageItem[] = rawPages.length >= 1
      ? rawPages.slice(0, 3).map((p, idx) => ({
          label: String(p.name || p.label || defaultPages[idx]?.label || `Page ${idx + 1}`),
          tech: String(p.path || p.route || defaultPages[idx]?.tech || `/page-${idx + 1}`),
          desc: String(p.description || defaultPages[idx]?.desc || `${p.name || 'Page'} view`),
          is_new: Boolean(p.is_new || p.version_added),
          version_added: p.version_added,
        }))
      : defaultPages;

    const defaultFeaturePages: FrontendPageItem[] = [
      { label: "WorkflowExecutionPage", tech: "/workflows", desc: "Multi-step workflow execution and real-time processing view." },
      { label: "AdministrationPage", tech: "/admin", desc: "Role-based tenant administration, configuration controls, and audit logs." },
    ];

    const featurePages: FrontendPageItem[] = rawPages.length > 3
      ? rawPages.slice(3).map((p, idx) => ({
          label: String(p.name || p.label || `FeaturePage ${idx + 1}`),
          tech: String(p.path || p.route || `/feature-${idx + 1}`),
          desc: String(p.description || "Feature execution screen"),
          is_new: Boolean(p.is_new || p.version_added),
          version_added: p.version_added,
        }))
      : defaultFeaturePages;

    const allPages: FrontendPageItem[] = [...pages, ...featurePages];

    const rawComponents = Array.isArray(lldData.components) ? (lldData.components as Array<any>) : [];
    const defaultComponents: FrontendPageItem[] = [
      { label: "ResourceCard", tech: "React 19 · Tailwind CSS", desc: "Reusable presentation card for domain items with status badges." },
      { label: "ActionDialogModal", tech: "React 19 · Dialog Portal", desc: "Interactive dialog confirming transactions and workflow triggers." },
      { label: "ProcessMonitorTile", tech: "React 19 · Live Telemetry", desc: "Live status indicator showing processing stage, telemetry, and health." },
    ];

    const components: FrontendPageItem[] = rawComponents.length >= 1
      ? rawComponents.map((c, idx) => ({
          label: String(c.name || c.label || `Component ${idx + 1}`),
          tech: String(c.tech || "React 19 · Tailwind CSS"),
          desc: String(c.description || `${c.name || 'UI'} component.`),
          is_new: Boolean(c.is_new || c.version_added),
          version_added: c.version_added,
        }))
      : defaultComponents;

    const fBoundsTier1 = computeGroupBounds([{ y: 340, height: 92 }]);
    const fBoundsTier2 = computeGroupBounds(allPages.map((_, idx) => ({ y: 120 + idx * 150, height: 92 })));
    const fBoundsTier3 = computeGroupBounds(components.map((_, idx) => ({ y: 120 + idx * 150, height: 92 })));
    const fBoundsTier4 = computeGroupBounds([{ y: 220, height: 92 }, { y: 440, height: 92 }]);
    const fBoundsTier5 = computeGroupBounds([{ y: 220, height: 92 }, { y: 440, height: 92 }]);

    // ── 5 Systematic Architecture Segments with Tight Dynamic Bounding & Generous Spacing ──
    nodes.push({
      id: "fgroup-tier1",
      type: "layerGroup",
      data: {
        label: "Tier 1: Global App Shell & Navigation",
        subtitle: "Global App Shell · Auth Guards · Dynamic Route Segments",
        count: 1,
      },
      position: { x: 80, y: fBoundsTier1.y },
      style: { width: 360, height: fBoundsTier1.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "fgroup-tier2",
      type: "layerGroup",
      data: {
        label: "Tier 2: Interactive Screens & Feature Views",
        subtitle: "Next.js Route Segments · Role-Based Execution Views",
        count: allPages.length,
      },
      position: { x: 620, y: fBoundsTier2.y },
      style: { width: 400, height: fBoundsTier2.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "fgroup-tier3",
      type: "layerGroup",
      data: {
        label: "Tier 3: Modular UI Components",
        subtitle: "Presentation Tiles · Interactive Dialog Portals · Live Telemetry",
        count: components.length,
      },
      position: { x: 1220, y: fBoundsTier3.y },
      style: { width: 400, height: fBoundsTier3.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "fgroup-tier4",
      type: "layerGroup",
      data: {
        label: "Tier 4: Reactive Client State & Server Query Cache",
        subtitle: "Zustand Global Store · TanStack Query Stale-While-Revalidate",
        count: 2,
      },
      position: { x: 1820, y: fBoundsTier4.y },
      style: { width: 380, height: fBoundsTier4.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "fgroup-tier5",
      type: "layerGroup",
      data: {
        label: "Tier 5: Form Validation Schemas & HTTP API Transport",
        subtitle: "Zod Schema Parsers · Axios Interceptors · JWT Bearer Injection",
        count: 2,
      },
      position: { x: 2400, y: fBoundsTier5.y },
      style: { width: 380, height: fBoundsTier5.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // ── Tier 1 Node: App Shell ──
    nodes.push({
      id: "fcmp-shell",
      type: "service",
      data: {
        code: "App Shell",
        label: "Navbar & AuthStatus",
        tech: "React 19 · Zustand Session",
        protocol: "Global Header",
        description: "Global header with navigation links, active route indicators, and user token state.",
      },
      position: { x: 115, y: 340 },
    });

    // ── Tier 2 Nodes: Pages & Feature Screens ──
    allPages.forEach((p, idx) => {
      nodes.push({
        id: `fpg-${idx + 1}`,
        type: "frontend",
        data: {
          label: p.label,
          tech: p.tech,
          description: p.desc,
          is_new: p.is_new,
          version_added: p.version_added,
        },
        position: { x: 655, y: 120 + idx * 150 },
      });
    });

    // ── Tier 3 Nodes: Modular Components ──
    components.forEach((c, idx) => {
      nodes.push({
        id: `fcmp-${idx + 2}`,
        type: "service",
        data: {
          code: "UI Component",
          label: c.label,
          tech: c.tech,
          protocol: "Client View",
          description: c.desc,
          is_new: c.is_new,
          version_added: c.version_added,
        },
        position: { x: 1255, y: 120 + idx * 150 },
      });
    });

    // ── Tier 4 Nodes: Client State & Cache ──
    nodes.push({
      id: "fnode-zustand",
      type: "cache",
      data: {
        label: "Zustand Global Store",
        subtitle: "AuthSession · UIState · Theme",
        description: "Lightweight reactive client store managing active user session, auth token, and theme.",
      },
      position: { x: 1855, y: 220 },
    });

    nodes.push({
      id: "fnode-tanstack",
      type: "service",
      data: {
        code: "React Query",
        label: "TanStack Query Cache",
        tech: "Auto Invalidation & Refetch · SWR",
        protocol: "Server State",
        description: "Cached API queries with background revalidation and optimistic mutation updates.",
      },
      position: { x: 1855, y: 440 },
    });

    // ── Tier 5 Nodes: Validation & Transport ──
    nodes.push({
      id: "fnode-zod",
      type: "service",
      data: {
        code: "Zod Validator",
        label: "React Hook Form + Zod",
        tech: "Strict Client Schema Validation",
        protocol: "Form State",
        description: "Type-safe form inputs and field-level validation schemas before API submission.",
      },
      position: { x: 2435, y: 220 },
    });

    nodes.push({
      id: "fnode-axios",
      type: "gateway",
      data: {
        label: "Axios API Interceptor",
        tech: "Bearer Token Injection · Error Toasts",
        description: "Centralized HTTP client with automatic Authorization header injection and 401 refresh handling.",
      },
      position: { x: 2435, y: 440 },
    });

    // ── Edges: Pure Left-to-Right Orthogonal Systematic Flow ──
    // Tier 1 -> Tier 2
    allPages.slice(0, 3).forEach((_, idx) => {
      edges.push({
        id: `fe-shell-p${idx + 1}`,
        source: "fcmp-shell",
        target: `fpg-${idx + 1}`,
        sourceHandle: "svc-right",
        targetHandle: "fe-left",
        type: "animatedFlow",
        data: { label: "App Route" },
        animated: true,
      });
    });

    // Tier 2 -> Tier 3
    if (allPages.length >= 3 && components.length >= 1) {
      edges.push({ id: "fe-p3-c2", source: "fpg-3", target: "fcmp-2", sourceHandle: "fe-right", targetHandle: "svc-left", type: "animatedFlow", data: { label: "Render Cards" }, animated: true });
    }
    if (allPages.length >= 2 && components.length >= 2) {
      edges.push({ id: "fe-p2-c3", source: "fpg-2", target: "fcmp-3", sourceHandle: "fe-right", targetHandle: "svc-left", type: "animatedFlow", data: { label: "Action Modal" }, animated: true });
    }
    if (allPages.length >= 4 && components.length >= 3) {
      edges.push({ id: "fe-p4-c4", source: "fpg-4", target: "fcmp-4", sourceHandle: "fe-right", targetHandle: "svc-left", type: "animatedFlow", data: { label: "Telemetry Stream" }, animated: true });
    }

    // Tier 3 -> Tier 4
    if (components.length >= 1) {
      edges.push({ id: "fe-c2-tanstack", source: "fcmp-2", target: "fnode-tanstack", sourceHandle: "svc-right", targetHandle: "svc-left", type: "animatedFlow", data: { label: "useQuery(resources)" }, animated: true });
    }
    if (components.length >= 2) {
      edges.push({ id: "fe-c3-zustand", source: "fcmp-3", target: "fnode-zustand", sourceHandle: "svc-right", targetHandle: "cache-left", type: "animatedFlow", data: { label: "Session State" }, animated: true });
    }
    if (components.length >= 3) {
      edges.push({ id: "fe-c4-tanstack", source: "fcmp-4", target: "fnode-tanstack", sourceHandle: "svc-right", targetHandle: "svc-left", type: "animatedFlow", data: { label: "Live Query Poll" }, animated: true });
    }

    // Tier 4 -> Tier 5
    edges.push({ id: "fe-zustand-zod", source: "fnode-zustand", target: "fnode-zod", sourceHandle: "cache-right", targetHandle: "svc-left", type: "animatedFlow", data: { label: "Validate Form Input" }, animated: true });
    edges.push({ id: "fe-tanstack-axios", source: "fnode-tanstack", target: "fnode-axios", sourceHandle: "svc-right", targetHandle: "gw-left", type: "animatedFlow", data: { label: "HTTP GET Fetch" }, animated: true });
    edges.push({ id: "fe-zod-axios", source: "fnode-zod", target: "fnode-axios", sourceHandle: "svc-right", targetHandle: "gw-left", type: "animatedFlow", data: { label: "POST Validated Payload" }, animated: true });

    return finalizeLld(nodes, edges);
  }

  // ── 4. CLOUD LLD ARCHITECTURE TOPOLOGY (AWS ECS Fargate) ──
  // Spacious 5-Tier Left-to-Right Architectural Flow matching User Reference Architecture:
  // Col 1: DNS & Global Edge Network (Route 53 & CloudFront)
  // Col 2: Ingress Protection & Load Balancing (AWS WAF & ALB)
  // Col 3: VPC Private Container Compute Cluster (ECS Fargate Tasks)
  // Col 4: Managed Data Persistence & Cache (RDS, ElastiCache, S3)
  // Col 5: DevOps Automation & Observability (GitHub Actions, CloudWatch)
  if (type === "cloud") {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    const rawServices = Array.isArray(lldData.services) ? (lldData.services as Array<any>) : [];
    const defaultTaskNames = ["Auth & Identity", "Core Domain Engine", "Workflow Execution", "Background Worker"];
    const taskList = rawServices.length > 0
      ? rawServices.map((s, idx) => ({
          name: String(s.name || defaultTaskNames[idx] || `Service ${idx + 1}`),
          is_new: Boolean(s.is_new || s.version_added),
          version_added: s.version_added,
        }))
      : defaultTaskNames.map((name) => ({ name, is_new: false, version_added: undefined }));

    const cBoundsTier1 = computeGroupBounds([{ y: 200, height: 92 }, { y: 440, height: 92 }]);
    const cBoundsTier2 = computeGroupBounds([{ y: 200, height: 92 }, { y: 440, height: 92 }]);
    const cBoundsTier3 = computeGroupBounds(taskList.map((_, idx) => ({ y: 120 + idx * 175, height: 92 })));
    const cBoundsTier4 = computeGroupBounds([{ y: 150, height: 92 }, { y: 350, height: 92 }, { y: 550, height: 92 }]);
    const cBoundsTier5 = computeGroupBounds([{ y: 220, height: 92 }, { y: 460, height: 92 }]);

    // Col 1: Tier 1 - Global Edge Network & Authoritative DNS (x = 80, width = 360)
    nodes.push({
      id: "cgroup-tier1",
      type: "layerGroup",
      data: {
        label: "Tier 1: Global Edge Network & DNS",
        subtitle: "Amazon Route 53 DNS · CloudFront Edge CDN · Anycast PoP Routing",
        count: 2,
      },
      position: { x: 80, y: cBoundsTier1.y },
      style: { width: 360, height: cBoundsTier1.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Col 2: Tier 2 - Ingress Protection & Application Load Balancing (x = 620, width = 360)
    nodes.push({
      id: "cgroup-tier2",
      type: "layerGroup",
      data: {
        label: "Tier 2: Ingress Protection & Load Balancing",
        subtitle: "AWS WAF Managed Rules · Application Load Balancer Target Groups",
        count: 2,
      },
      position: { x: 620, y: cBoundsTier2.y },
      style: { width: 360, height: cBoundsTier2.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Col 3: Tier 3 - AWS ECS Fargate Serverless Compute Cluster (x = 1180, width = 440)
    nodes.push({
      id: "cgroup-tier3",
      type: "layerGroup",
      data: {
        label: "Tier 3: AWS ECS Fargate Compute Cluster",
        subtitle: "Stateless Microservice Tasks · Target Tracking Auto-Scaling (min 2, max 10)",
        count: taskList.length,
      },
      position: { x: 1180, y: cBoundsTier3.y },
      style: { width: 440, height: cBoundsTier3.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Col 4: Tier 4 - Managed Data Persistence & In-Memory Cache (x = 1820, width = 400)
    nodes.push({
      id: "cgroup-tier4",
      type: "layerGroup",
      data: {
        label: "Tier 4: Managed Persistence & In-Memory Cache",
        subtitle: "AWS RDS PostgreSQL Multi-AZ · ElastiCache Redis Cluster · Encrypted S3",
        count: 3,
      },
      position: { x: 1820, y: cBoundsTier4.y },
      style: { width: 400, height: cBoundsTier4.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Col 5: Tier 5 - DevOps Automation & Observability (x = 2420, width = 400)
    nodes.push({
      id: "cgroup-tier5",
      type: "layerGroup",
      data: {
        label: "Tier 5: CI/CD & Observability Infrastructure",
        subtitle: "GitHub Actions Container CI/CD · CloudWatch Container Insights & Alarms",
        count: 2,
      },
      position: { x: 2420, y: cBoundsTier5.y },
      style: { width: 400, height: cBoundsTier5.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // ── Tier 1 Nodes: Edge & DNS (Col 1, x = 115) ──
    nodes.push({
      id: "cnode-route53",
      type: "gateway",
      data: {
        label: "Amazon Route 53 DNS",
        tech: "Latency-Based Routing · Health Checks",
        description: "Authoritative global DNS service resolving custom domains to CloudFront distributions.",
      },
      position: { x: 115, y: 200 },
    });

    nodes.push({
      id: "cnode-cloudfront",
      type: "gateway",
      data: {
        label: "CloudFront CDN Edge",
        tech: "Edge Locations · TLS 1.3 Termination",
        description: "Global content delivery network caching static assets and terminating client TLS.",
      },
      position: { x: 115, y: 440 },
    });

    // ── Tier 2 Nodes: Ingress & Load Balancing (Col 2, x = 655) ──
    nodes.push({
      id: "cnode-waf",
      type: "gateway",
      data: {
        label: "AWS WAF Managed Guard",
        tech: "OWASP Top 10 · 100 RPS Rate Limit",
        description: "Inspects HTTP traffic, drops SQL injection/XSS attempts before reaching ALB.",
      },
      position: { x: 655, y: 200 },
    });

    nodes.push({
      id: "cnode-alb",
      type: "gateway",
      data: {
        label: "Application Load Balancer",
        tech: "Path-Based Routing · Target Groups",
        description: "Distributes incoming traffic across private ECS service tasks with automated health checks.",
      },
      position: { x: 655, y: 440 },
    });

    // ── Tier 3 Nodes: ECS Fargate Tasks (Col 3, x = 1215) ──
    taskList.forEach((tItem: any, idx: number) => {
      nodes.push({
        id: `cecs-${idx + 1}`,
        type: "service",
        data: {
          code: "ECS Task",
          label: `${tItem.name} Task`,
          tech: "0.5 vCPU, 1 GB RAM · Fargate",
          protocol: "Fargate Task",
          description: "Containerized task running in private subnets with auto-scaling (min 2, max 10).",
          is_new: tItem.is_new,
          version_added: tItem.version_added,
        },
        position: { x: 1215, y: 120 + idx * 175 },
      });
    });

    // ── Tier 4 Nodes: Managed Storage & Persistence (Col 4, x = 1855) ──
    nodes.push({
      id: "cnode-rds",
      type: "database",
      data: {
        engine: "AWS RDS PostgreSQL 16",
        label: "RDS db.t4g.medium Multi-AZ",
        schema: "100 GB gp3 · 7-day PITR",
        description: "Automated daily snapshots and Multi-AZ failover across Availability Zones.",
      },
      position: { x: 1855, y: 150 },
    });

    nodes.push({
      id: "cnode-elasticache",
      type: "cache",
      data: {
        label: "ElastiCache Redis 7.2 Cluster",
        subtitle: "cache.t4g.small · Multi-AZ",
        description: "In-memory caching and session clustering with automated failover.",
      },
      position: { x: 1855, y: 350 },
    });

    nodes.push({
      id: "cnode-s3",
      type: "database",
      data: {
        engine: "AWS S3 Standard",
        label: "Encrypted Blob Store",
        schema: "AES-256 SSE-S3 · Lifecycle Policies",
        description: "Secure object storage for uploaded assets, export artifacts, and audit archives.",
      },
      position: { x: 1855, y: 550 },
    });

    // ── Tier 5 Nodes: DevOps & Observability (Col 5, x = 2455) ──
    nodes.push({
      id: "cnode-github",
      type: "devops",
      data: {
        label: "GitHub Actions CI/CD Pipeline",
        role: "Build · Test · Push ECR · Deploy",
        category: "cicd",
        description: "Automated multi-stage pipelines triggering ECR container push and ECS task definition update.",
      },
      position: { x: 2455, y: 220 },
    });

    nodes.push({
      id: "cnode-cloudwatch",
      type: "devops",
      data: {
        label: "AWS CloudWatch Container Insights",
        role: "Logs · Metrics · Alarms",
        category: "monitoring",
        description: "Aggregates container stdout logs and triggers SNS alerts when CPU > 75% for 3 periods.",
      },
      position: { x: 1915, y: 460 },
    });

    // ── Edges: Pure Left-to-Right Architectural Flow with Zero Crisscross ──
    // Col 1 -> Col 2
    edges.push({ id: "ce-r53-waf", source: "cnode-route53", target: "cnode-waf", sourceHandle: "gw-right", targetHandle: "gw-left", type: "animatedFlow", data: { label: "Authoritative Ingress" }, animated: true });
    edges.push({ id: "ce-cf-alb", source: "cnode-cloudfront", target: "cnode-alb", sourceHandle: "gw-right", targetHandle: "gw-left", type: "animatedFlow", data: { label: "CDN Cached Traffic" }, animated: true });
    // Inside Col 2: WAF inspected traffic to ALB
    edges.push({ id: "ce-waf-alb", source: "cnode-waf", target: "cnode-alb", sourceHandle: "gw-bottom", targetHandle: "gw-top", type: "animatedFlow", data: { label: "OWASP Inspected" }, animated: true });

    // Col 2 (ALB) -> Col 3 (ECS Tasks)
    taskList.forEach((_, idx) => {
      edges.push({
        id: `ce-alb-ecs${idx + 1}`,
        source: "cnode-alb",
        target: `cecs-${idx + 1}`,
        sourceHandle: "gw-right",
        targetHandle: "svc-left",
        type: "animatedFlow",
        data: { label: `Target Group /route-${idx + 1}` },
        animated: true,
      });
    });

    // Col 3 (ECS Tasks) -> Col 4 (Databases & Cache)
    if (taskList.length >= 1) {
      edges.push({ id: "ce-ecs1-rds", source: "cecs-1", target: "cnode-rds", sourceHandle: "svc-right", targetHandle: "db-left", type: "animatedFlow", data: { label: "Transactional Queries" }, animated: true });
    }
    if (taskList.length >= 2) {
      edges.push({ id: "ce-ecs2-cache", source: "cecs-2", target: "cnode-elasticache", sourceHandle: "svc-right", targetHandle: "cache-left", type: "animatedFlow", data: { label: "Cache Read/Write" }, animated: true });
    }
    if (taskList.length >= 3) {
      edges.push({ id: "ce-ecs3-s3", source: "cecs-3", target: "cnode-s3", sourceHandle: "svc-right", targetHandle: "db-left", type: "animatedFlow", data: { label: "Artifacts & Media" }, animated: true });
    }
    if (taskList.length >= 4) {
      edges.push({ id: "ce-ecs4-rds", source: "cecs-4", target: "cnode-rds", sourceHandle: "svc-right", targetHandle: "db-left", type: "animatedFlow", data: { label: "Worker Sync State" }, animated: true });
    }

    // Col 4 (Databases & Cache) -> Col 5 (Observability & DevOps)
    edges.push({ id: "ce-rds-cw", source: "cnode-rds", target: "cnode-cloudwatch", sourceHandle: "db-right", targetHandle: "dev-left", type: "animatedFlow", data: { label: "RDS CloudWatch Metrics" }, animated: true });
    edges.push({ id: "ce-cache-cw", source: "cnode-elasticache", target: "cnode-cloudwatch", sourceHandle: "cache-right", targetHandle: "dev-left", type: "animatedFlow", data: { label: "Cache Telemetry" }, animated: true });
    edges.push({ id: "ce-s3-gh", source: "cnode-s3", target: "cnode-github", sourceHandle: "db-right", targetHandle: "dev-left", type: "animatedFlow", data: { label: "Artifact Deployments" }, animated: true });

    return finalizeLld(nodes, edges);
  }

  // ── 5. SECURITY LLD ARCHITECTURE TOPOLOGY ──
  // Spacious 6-Tier Left-to-Right Architectural Flow matching User Reference Architecture:
  // Col 1: Perimeter Shield & Ingress Gateway (WAF + TLS 1.3)
  // Col 2: Identity Provider & Cryptographic Token Authority (OAuth2 PKCE + RS256 JWT)
  // Col 3: Fine-Grained Authorization & RBAC Enforcement (RBAC Enforcer)
  // Col 4: Real-time Session & Revocation (Redis Token Blacklist)
  // Col 5: Envelope Encryption & Key Management (AWS KMS AES-256)
  // Col 6: Forensic Audit Logging & Security Trail (Audit Trail + Dynamic Policies)
  if (type === "security") {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Dynamic roles from lldData.authorization
    const authz = lldData.authorization && typeof lldData.authorization === "object"
      ? (lldData.authorization as Record<string, unknown>)
      : {};
    const rawRoles = Array.isArray(authz.roles)
      ? (authz.roles as Array<string>)
      : Array.isArray(lldData.roles)
      ? (lldData.roles as Array<string>)
      : ["End User", "Operator", "Administrator"];
    const rolesStr = rawRoles.slice(0, 3).join(" · ");

    const rawControls = Array.isArray(lldData.security_controls)
      ? (lldData.security_controls as Array<any>)
      : Array.isArray(lldData.controls)
      ? (lldData.controls as Array<any>)
      : [];

    const secBoundsTier1 = computeGroupBounds([{ y: 200, height: 92 }, { y: 440, height: 92 }]);
    const secBoundsTier2 = computeGroupBounds([{ y: 200, height: 92 }, { y: 440, height: 92 }]);
    const secBoundsTier3 = computeGroupBounds([{ y: 320, height: 92 }]);
    const secBoundsTier4 = computeGroupBounds([{ y: 320, height: 92 }]);
    const secBoundsTier5 = computeGroupBounds([{ y: 320, height: 92 }]);
    const secBoundsTier6 = computeGroupBounds([
      { y: 160, height: 92 },
      ...rawControls.map((_, idx) => ({ y: 340 + idx * 160, height: 92 })),
    ]);

    // Tier 1: Perimeter Shield & Transport Layer Security (Col 1, x = 80, width = 380)
    nodes.push({
      id: "secgroup-tier1",
      type: "layerGroup",
      data: {
        label: "Tier 1: Perimeter Shield & TLS",
        subtitle: "AWS WAF Rate Limiting · TLS 1.3 Strict Ingress Guard · Anti-DDoS",
        count: 2,
      },
      position: { x: 80, y: secBoundsTier1.y },
      style: { width: 380, height: secBoundsTier1.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Tier 2: Identity Provider & Cryptographic Token Authority (Col 2, x = 640, width = 380)
    nodes.push({
      id: "secgroup-tier2",
      type: "layerGroup",
      data: {
        label: "Tier 2: Identity & Token Authority",
        subtitle: "OAuth2 & PKCE Flow · RS256 Asymmetric Token Authority",
        count: 2,
      },
      position: { x: 640, y: secBoundsTier2.y },
      style: { width: 380, height: secBoundsTier2.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Tier 3: Fine-Grained Authorization & RBAC Enforcement (Col 3, x = 1220, width = 380)
    nodes.push({
      id: "secgroup-tier3",
      type: "layerGroup",
      data: {
        label: "Tier 3: RBAC Policy Enforcer",
        subtitle: `${rolesStr} Policy Enforcer · Route Guard`,
        count: 1,
      },
      position: { x: 1220, y: secBoundsTier3.y },
      style: { width: 380, height: secBoundsTier3.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Tier 4: Real-time Session Invalidation & Token Revocation (Col 4, x = 1800, width = 380)
    nodes.push({
      id: "secgroup-tier4",
      type: "layerGroup",
      data: {
        label: "Tier 4: Token Revocation & Session Invalidation",
        subtitle: "Redis Token Blacklist · Instant Session Eviction · JTI Kill Switch",
        count: 1,
      },
      position: { x: 1800, y: secBoundsTier4.y },
      style: { width: 380, height: secBoundsTier4.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Tier 5: Envelope Encryption & Customer Master Keys (AWS KMS) (Col 5, x = 2380, width = 380)
    nodes.push({
      id: "secgroup-tier5",
      type: "layerGroup",
      data: {
        label: "Tier 5: KMS Envelope Encryption",
        subtitle: "AWS KMS AES-256 Envelope Encryption · Customer Managed Keys (CMK)",
        count: 1,
      },
      position: { x: 2380, y: secBoundsTier5.y },
      style: { width: 380, height: secBoundsTier5.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // Tier 6: Forensic Audit Logging & Security Trail (Col 6, x = 2960, width = 420)
    nodes.push({
      id: "secgroup-tier6",
      type: "layerGroup",
      data: {
        label: "Tier 6: Forensic Audit & Security Trail",
        subtitle: "Immutable Audit Trail · Tamper-Evident Records · SOC2 / ISO 27001",
        count: 1 + rawControls.length,
      },
      position: { x: 2960, y: secBoundsTier6.y },
      style: { width: 420, height: secBoundsTier6.height, zIndex: -1, pointerEvents: "none" },
      draggable: false,
      selectable: false,
    });

    // ── Tier 1 Nodes: Perimeter (Col 1, x = 115) ──
    nodes.push({
      id: "secnode-waf",
      type: "gateway",
      data: {
        label: "AWS WAF + Rate Limiter",
        tech: "OWASP Top 10 · 100 RPS Threshold",
        description: "Inspects incoming HTTP payloads, drops SQL injection, XSS, and anomalous bot requests.",
      },
      position: { x: 115, y: 200 },
    });

    nodes.push({
      id: "secnode-tls",
      type: "gateway",
      data: {
        label: "TLS 1.3 Strict Ingress Guard",
        tech: "Strict Transport Security (HSTS)",
        description: "Full end-to-end cryptographic transport encryption with forward secrecy and OCSP stapling.",
      },
      position: { x: 115, y: 440 },
    });

    // ── Tier 2 Nodes: Identity Engine (Col 2, x = 675) ──
    nodes.push({
      id: "secnode-oauth",
      type: "service",
      data: {
        code: "OAuth2 / PKCE",
        label: "OAuth2 & PKCE Gateway",
        tech: "Auth Code Flow · Zero Plaintext",
        protocol: "Authorization",
        description: "Authorizes user and staff authentication flows with asymmetric key validation.",
      },
      position: { x: 675, y: 200 },
    });

    nodes.push({
      id: "secnode-jwt",
      type: "service",
      data: {
        code: "JWT RS256",
        label: "JWT Asymmetric Token Authority",
        tech: "15m Access Token · 7d Refresh Token",
        protocol: "Token Authority",
        description: "Issues cryptographically signed RS256 JWT tokens with active key rotation.",
      },
      position: { x: 675, y: 440 },
    });

    // ── Tier 3 Nodes: Authorization (Col 3, x = 1255) ──
    nodes.push({
      id: "secnode-rbac",
      type: "service",
      data: {
        code: "RBAC Guard",
        label: "RBAC Permission Enforcer",
        tech: rolesStr,
        protocol: "Policy Engine",
        description: "Validates granular route permissions and role policies on every microservice invocation.",
      },
      position: { x: 1255, y: 320 },
    });

    // ── Tier 4 Nodes: Token Revocation (Col 4, x = 1835) ──
    nodes.push({
      id: "secnode-blacklist",
      type: "cache",
      data: {
        label: "Redis Token Blacklist",
        subtitle: "Instant Session Revocation · JTI TTL",
        description: "Maintains revoked JWT IDs for immediate logout enforcement and kill switch revocation.",
      },
      position: { x: 1835, y: 320 },
    });

    // ── Tier 5 Nodes: KMS Envelope Encryption (Col 5, x = 2415) ──
    nodes.push({
      id: "secnode-kms",
      type: "database",
      data: {
        engine: "AWS KMS",
        label: "AES-256 Envelope Encryption",
        schema: "Customer Managed Keys (CMK)",
        description: "Transparent envelope encryption protecting database tables, credentials, and S3 data at rest.",
      },
      position: { x: 2415, y: 320 },
    });

    // ── Tier 6 Nodes: Forensic Audit Logging (Col 6, x = 2995) ──
    nodes.push({
      id: "secnode-audit",
      type: "devops",
      data: {
        label: "Immutable Security Audit Trail",
        role: "Append-only Transaction Logs",
        category: "monitoring",
        description: "Tamper-evident audit logging for all critical transactions, auth changes, and access grants.",
      },
      position: { x: 2995, y: 160 },
    });

    // Dynamic & Evolved Security Controls (Col 6, stacked vertically)
    rawControls.forEach((ctrl, idx) => {
      const isNew = Boolean(ctrl.is_new || ctrl.version_added);
      nodes.push({
        id: `secnode-ctrl-${idx + 1}`,
        type: "service",
        data: {
          code: "SEC-POL",
          label: String(ctrl.name || ctrl.label || ctrl.control || `Security Policy ${idx + 1}`),
          tech: String(ctrl.tech || ctrl.type || "Enforced Policy"),
          protocol: "Compliance",
          description: String(ctrl.description || "Active security enforcement control."),
          is_new: isNew,
          version_added: ctrl.version_added,
        },
        position: { x: 2995, y: 340 + idx * 160 },
      });
      edges.push({
        id: `sece-audit-ctrl-${idx + 1}`,
        source: "secnode-audit",
        target: `secnode-ctrl-${idx + 1}`,
        sourceHandle: "dev-bottom",
        targetHandle: "svc-top",
        type: "animatedFlow",
        data: { label: "Audited Control" },
        animated: true,
      });
    });

    // ── Edges: Pure Left-to-Right Architectural Flow with Zero Crisscross ──
    // Col 1 -> Col 2
    edges.push({ id: "sece-waf-oauth", source: "secnode-waf", target: "secnode-oauth", sourceHandle: "gw-right", targetHandle: "svc-left", type: "animatedFlow", data: { label: "Screened Ingress" }, animated: true });
    edges.push({ id: "sece-tls-jwt", source: "secnode-tls", target: "secnode-jwt", sourceHandle: "gw-right", targetHandle: "svc-left", type: "animatedFlow", data: { label: "TLS Decrypted Stream" }, animated: true });

    // Col 2 -> Col 3
    edges.push({ id: "sece-oauth-rbac", source: "secnode-oauth", target: "secnode-rbac", sourceHandle: "svc-right", targetHandle: "svc-left", type: "animatedFlow", data: { label: "Principal Context" }, animated: true });
    edges.push({ id: "sece-jwt-rbac", source: "secnode-jwt", target: "secnode-rbac", sourceHandle: "svc-right", targetHandle: "svc-left", type: "animatedFlow", data: { label: "Verified Claims" }, animated: true });

    // Col 3 -> Col 4
    edges.push({ id: "sece-rbac-blacklist", source: "secnode-rbac", target: "secnode-blacklist", sourceHandle: "svc-right", targetHandle: "cache-left", type: "animatedFlow", data: { label: "JTI Revocation Check" }, animated: true });

    // Col 4 -> Col 5
    edges.push({ id: "sece-blacklist-kms", source: "secnode-blacklist", target: "secnode-kms", sourceHandle: "cache-right", targetHandle: "db-left", type: "animatedFlow", data: { label: "CMK Decrypt Key" }, animated: true });

    // Col 5 -> Col 6
    edges.push({ id: "sece-kms-audit", source: "secnode-kms", target: "secnode-audit", sourceHandle: "db-right", targetHandle: "dev-left", type: "animatedFlow", data: { label: "Signed Audit Record" }, animated: true });

    return finalizeLld(nodes, edges);
  }

  // Fallback for custom objects
  return parseHldToReactFlow(lldData, undefined, layoutDirection);
}
