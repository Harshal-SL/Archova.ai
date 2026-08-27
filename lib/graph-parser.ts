import type { Node, Edge } from "@xyflow/react";

// Predefined modern gradient palettes for dynamic node categories
const PALETTES: Record<string, { bg: string; stroke: string }> = {
  client: { bg: "linear-gradient(135deg, #6366f1, #8b5cf6)", stroke: "#6366f1" },
  frontend: { bg: "linear-gradient(135deg, #ec4899, #db2777)", stroke: "#ec4899" },
  gateway: { bg: "linear-gradient(135deg, #3b82f6, #2563eb)", stroke: "#3b82f6" },
  backend: { bg: "linear-gradient(135deg, #0ea5e9, #0284c7)", stroke: "#0ea5e9" },
  service: { bg: "linear-gradient(135deg, #8b5cf6, #7c3aed)", stroke: "#8b5cf6" },
  database: { bg: "linear-gradient(135deg, #10b981, #059669)", stroke: "#10b981" },
  storage: { bg: "linear-gradient(135deg, #14b8a6, #0d9488)", stroke: "#14b8a6" },
  cache: { bg: "linear-gradient(135deg, #f59e0b, #d97706)", stroke: "#f59e0b" },
  security: { bg: "linear-gradient(135deg, #ef4444, #dc2626)", stroke: "#ef4444" },
  auth: { bg: "linear-gradient(135deg, #f43f5e, #e11d48)", stroke: "#f43f5e" },
  cloud: { bg: "linear-gradient(135deg, #06b6d4, #0891b2)", stroke: "#06b6d4" },
  ai: { bg: "linear-gradient(135deg, #a855f7, #9333ea)", stroke: "#a855f7" },
  queue: { bg: "linear-gradient(135deg, #eab308, #ca8a04)", stroke: "#eab308" },
  default: { bg: "linear-gradient(135deg, #475569, #334155)", stroke: "#64748b" },
};

function getPalette(name: string, type?: string) {
  const str = `${name} ${type || ""}`.toLowerCase();
  for (const [key, val] of Object.entries(PALETTES)) {
    if (str.includes(key)) return val;
  }
  return PALETTES.default;
}

/**
 * Dynamically converts ANY valid HLD JSON structure received from the backend
 * into interactive React Flow Nodes and Edges.
 */
export function parseHldToReactFlow(hldJson: Record<string, unknown> | null): {
  nodes: Node[];
  edges: Edge[];
} {
  if (!hldJson || typeof hldJson !== "object" || Object.keys(hldJson).length === 0) {
    return { nodes: [], edges: [] };
  }

  const nodes: Node[] = [];
  const edges: Edge[] = [];

  // Case 1: Backend provides explicit nodes and edges arrays
  if (Array.isArray(hldJson.nodes) && hldJson.nodes.length > 0) {
    hldJson.nodes.forEach((item: unknown, idx: number) => {
      const n = (typeof item === "object" && item !== null ? item : {}) as Record<string, unknown>;
      const id = String(n.id || `node-${idx}`);
      const label = String(n.label || n.name || n.title || id);
      const category = String(n.type || n.category || "");
      const palette = getPalette(label, category);

      nodes.push({
        id,
        data: {
          label,
          description: String(n.description || n.details || n.role || ""),
          category,
          raw: n,
        },
        position: {
          x: typeof n.x === "number" ? n.x : (idx % 3) * 230 + 40,
          y: typeof n.y === "number" ? n.y : Math.floor(idx / 3) * 140 + 40,
        },
        style: {
          background: palette.bg,
          color: "#fff",
          borderRadius: 14,
          padding: "12px 20px",
          fontWeight: 600,
          fontSize: 13,
          border: "none",
          boxShadow: `0 8px 24px rgba(0,0,0,0.35)`,
          minWidth: 160,
          textAlign: "center",
        },
      });
    });

    if (Array.isArray(hldJson.edges)) {
      hldJson.edges.forEach((item: unknown, idx: number) => {
        const e = (typeof item === "object" && item !== null ? item : {}) as Record<string, unknown>;
        const source = String(e.source || e.from || "");
        const target = String(e.target || e.to || "");
        if (source && target) {
          edges.push({
            id: String(e.id || `edge-${idx}`),
            source,
            target,
            animated: true,
            label: String(e.label || e.relation || ""),
            style: { stroke: "#6366f1", strokeWidth: 2 },
          });
        }
      });
    }

    return { nodes, edges };
  }

  // Case 2: HLD provides components / services / layers / architecture list
  const candidateKeys = [
    "components",
    "services",
    "layers",
    "modules",
    "architecture",
    "system_components",
    "subsystems",
    "entities",
  ];

  let rawList: Record<string, unknown>[] = [];

  for (const key of candidateKeys) {
    if (Array.isArray(hldJson[key])) {
      rawList = hldJson[key] as Record<string, unknown>[];
      break;
    }
  }

  // If HLD is a structured dictionary of sections/layers
  if (rawList.length === 0) {
    Object.entries(hldJson).forEach(([key, val]) => {
      if (typeof val === "object" && val !== null && !Array.isArray(val)) {
        rawList.push({
          id: key,
          name: (val as Record<string, unknown>).name || key.replace(/_/g, " "),
          description: (val as Record<string, unknown>).description || (val as Record<string, unknown>).role || "",
          type: key,
          ...(val as Record<string, unknown>),
        });
      } else if (typeof val === "string" && val.trim()) {
        rawList.push({
          id: key,
          name: key.replace(/_/g, " "),
          description: val,
          type: "component",
        });
      }
    });
  }

  // Tiered architecture row mapping for visual layout
  const rowMapping: Record<string, number> = {
    client: 0,
    frontend: 0,
    ui: 0,
    gateway: 1,
    ingress: 1,
    proxy: 1,
    api: 1,
    backend: 2,
    service: 2,
    core: 2,
    worker: 2,
    database: 3,
    db: 3,
    storage: 3,
    cache: 3,
    redis: 3,
    security: 4,
    auth: 4,
    cloud: 4,
    infra: 4,
    ai: 4,
  };

  const rowCounts: Record<number, number> = {};

  rawList.forEach((comp, idx) => {
    const id = String(comp.id || comp.name || `comp-${idx}`)
      .toLowerCase()
      .replace(/\s+/g, "-");
    const name = String(comp.name || comp.title || comp.id || `Component ${idx + 1}`);
    const palette = getPalette(name, String(comp.type || ""));

    let targetRow = 1;
    const searchStr = `${id} ${name} ${comp.type || ""}`.toLowerCase();
    for (const [kw, r] of Object.entries(rowMapping)) {
      if (searchStr.includes(kw)) {
        targetRow = r;
        break;
      }
    }

    const colIndex = rowCounts[targetRow] || 0;
    rowCounts[targetRow] = colIndex + 1;

    nodes.push({
      id,
      data: {
        label: name,
        description: String(comp.description || comp.details || ""),
        category: String(comp.type || ""),
        raw: comp,
      },
      position: {
        x: colIndex * 220 + 40,
        y: targetRow * 130 + 40,
      },
      style: {
        background: palette.bg,
        color: "#fff",
        borderRadius: 14,
        padding: "12px 18px",
        fontWeight: 600,
        fontSize: 13,
        border: "none",
        boxShadow: `0 8px 24px rgba(0,0,0,0.35)`,
        minWidth: 160,
        textAlign: "center",
      },
    });
  });

  // Connect tiered layers sequentially
  for (let i = 0; i < nodes.length - 1; i++) {
    const curr = nodes[i];
    const next = nodes[i + 1];
    if (curr.position.y < next.position.y) {
      edges.push({
        id: `e-${curr.id}-${next.id}`,
        source: curr.id,
        target: next.id,
        animated: true,
        style: { stroke: "#6366f1", strokeWidth: 2 },
      });
    }
  }

  return { nodes, edges };
}

/**
 * Dynamically converts ANY valid LLD JSON response from the backend
 * (Backend, Frontend, Database, Security, Cloud) into interactive React Flow Nodes and Edges.
 */
export function parseLldToReactFlow(
  lldType: string,
  lldData: Record<string, unknown> | null
): { nodes: Node[]; edges: Edge[] } {
  if (!lldData || typeof lldData !== "object" || Object.keys(lldData).length === 0) {
    return { nodes: [], edges: [] };
  }

  const nodes: Node[] = [];
  const edges: Edge[] = [];
  const palette = getPalette(lldType);

  let rawComponents: Array<{ id: string; label: string; description?: string; details?: unknown }> = [];

  // 1. Check if LLD has explicit nodes & edges
  if (Array.isArray(lldData.nodes) && lldData.nodes.length > 0) {
    return parseHldToReactFlow(lldData);
  }

  // 2. Extract nested arrays or objects (e.g. endpoints, schemas, tables, services, modules)
  Object.entries(lldData).forEach(([key, val], keyIdx) => {
    if (Array.isArray(val)) {
      val.forEach((item, itemIdx) => {
        const itemObj = typeof item === "object" && item !== null ? item : { name: String(item) };
        const obj = itemObj as Record<string, unknown>;
        const labelText = String(
          obj.name || obj.endpoint || obj.title || obj.table_name || obj.module || `${key} #${itemIdx + 1}`
        );
        rawComponents.push({
          id: `${key}-${itemIdx}`,
          label: labelText,
          description: String(obj.description || obj.method || obj.type || ""),
          details: itemObj,
        });
      });
    } else if (typeof val === "object" && val !== null) {
      const obj = val as Record<string, unknown>;
      rawComponents.push({
        id: `lld-${key}-${keyIdx}`,
        label: String(obj.name || obj.title || key.replace(/_/g, " ").toUpperCase()),
        description: String(obj.description || ""),
        details: val,
      });
    } else if (typeof val === "string" && val.trim()) {
      rawComponents.push({
        id: `lld-prop-${keyIdx}`,
        label: `${key.replace(/_/g, " ")}: ${val}`,
        details: val,
      });
    }
  });

  if (rawComponents.length === 0) {
    rawComponents.push({
      id: `${lldType}-core`,
      label: `${lldType.toUpperCase()} Architecture Specification`,
      details: lldData,
    });
  }

  // Arrange in responsive grid
  rawComponents.slice(0, 20).forEach((item, idx) => {
    const col = idx % 3;
    const row = Math.floor(idx / 3);

    nodes.push({
      id: item.id,
      data: {
        label: item.label,
        description: item.description || "",
        details: item.details,
      },
      position: {
        x: col * 220 + 40,
        y: row * 120 + 40,
      },
      style: {
        background: palette.bg,
        color: "#fff",
        borderRadius: 12,
        padding: "10px 16px",
        fontWeight: 600,
        fontSize: 12,
        border: "none",
        boxShadow: `0 6px 18px rgba(0,0,0,0.3)`,
        minWidth: 150,
      },
    });
  });

  // Connect adjacent nodes with animated paths
  for (let i = 0; i < nodes.length - 1; i++) {
    edges.push({
      id: `e-lld-${nodes[i].id}-${nodes[i + 1].id}`,
      source: nodes[i].id,
      target: nodes[i + 1].id,
      animated: true,
      style: { stroke: palette.stroke, strokeWidth: 1.8 },
    });
  }

  return { nodes, edges };
}
