"use client";

import { useCallback, useEffect, useState, useMemo, useRef } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MarkerType,
  useNodesState,
  useEdgesState,
  type NodeMouseHandler,
  type Node,
} from "@xyflow/react";
import {
  ArrowRight,
  Server,
  Database,
  ShieldCheck,
  Globe,
  Radio,
  Cloud,
  Cpu,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/lib/store";
import { parseLldToReactFlow } from "@/lib/graph-parser";
import { dummyAllLlds } from "@/lib/dummy-data";
import { architectureNodeTypes } from "./flow/ArchitectureNodes";
import { architectureEdgeTypes } from "./flow/AnimatedFlowEdge";
import { getEdgeTheme, getComponentTheme } from "@/lib/flow-colors";

interface Props {
  customLldType?: string;
  customLldData?: Record<string, unknown> | null;
}

export default function LLDGraph({ customLldType, customLldData }: Props) {
  const {
    activeLldType,
    lldData,
    setSelectedNode,
    openExplain,
    theme,
  } = useAppStore();

  const isDark = theme === "dark";

  const type = customLldType || activeLldType || "backend";
  const rawData = customLldData || lldData[activeLldType as keyof typeof lldData] || null;
  const effectiveData = rawData || (dummyAllLlds as Record<string, unknown>)[type] || null;

  // Parse nodes and edges from custom LLD data or fallback
  const initialData = useMemo(() => {
    if (effectiveData) {
      return parseLldToReactFlow(type, effectiveData as Record<string, unknown>);
    }
    return { nodes: [], edges: [] };
  }, [type, effectiveData]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialData.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialData.edges);

  // Inspector Drawer state
  const [selectedNodeData, setSelectedNodeData] = useState<Node | null>(null);
  const [inspectorOpen, setInspectorOpen] = useState(false);

  // Search & Filter
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedLayer, setSelectedLayer] = useState<string>("all");
  const [animationsEnabled, setAnimationsEnabled] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);


  // Sync state when dynamic LLD data or type changes
  useEffect(() => {
    const activeData = rawData || (dummyAllLlds as Record<string, unknown>)[type] || null;
    const updated = activeData
      ? parseLldToReactFlow(type, activeData as Record<string, unknown>)
      : { nodes: [], edges: [] };
    setNodes(updated.nodes);
    setEdges(updated.edges);
    setSelectedLayer("all");
    setSelectedNodeData(null);
    setInspectorOpen(false);
  }, [type, rawData, setNodes, setEdges]);

  // Extract layer group containers
  const layerGroups = useMemo(() => {
    return nodes.filter((n) => n.type === "layerGroup");
  }, [nodes]);

  // Helper to determine which layer group a node belongs to
  const getNodeGroup = useCallback(
    (node: Node): Node | undefined => {
      if (node.parentId) {
        return layerGroups.find((g) => g.id === node.parentId);
      }
      const nid = node.id.toLowerCase();
      for (const g of layerGroups) {
        const gid = g.id.toLowerCase();
        // Backend LLD
        if (gid.includes("infra") && (nid.startsWith("bnode-") || nid.includes("jwt") || nid.includes("queue") || nid.includes("pool"))) return g;
        if (gid.includes("endpoint") && (nid.startsWith("bep-") || nid.includes("endpoint") || nid.includes("route"))) return g;
        if (gid.includes("service") && (nid.startsWith("bsvc-") || nid.includes("service"))) return g;
        if (gid.includes("repo") && (nid.startsWith("brepo-") || nid.includes("repo") || nid.startsWith("bmodel-") || nid.includes("model"))) return g;
        if (gid.includes("model") && (nid.startsWith("bmodel-") || nid.includes("model"))) return g;
        // Database LLD
        if (gid.includes("table") && (nid.startsWith("dtbl-") || nid.includes("table"))) return g;
        if (gid.includes("pooling") && (nid.startsWith("dnode-") || nid.includes("pool") || nid.includes("cache") || nid.includes("migration"))) return g;
        // Frontend LLD
        if (gid.includes("page") && (nid.startsWith("fpg-") || nid.includes("page") || nid.includes("fcmp-1"))) return g;
        if (gid.includes("component") && (nid.startsWith("fcmp-") || nid.includes("component"))) return g;
        if (gid.includes("state") && (nid.startsWith("fnode-") || nid.includes("store") || nid.includes("query") || nid.includes("axios") || nid.includes("zod"))) return g;
        // Cloud LLD
        if (gid.includes("devops") && (nid.includes("github") || nid.includes("cloudwatch"))) return g;
        if (gid.includes("edge") && (nid.includes("route53") || nid.includes("cloudfront") || nid.includes("dns") || nid.includes("alb"))) return g;
        if (gid.includes("alb") && (nid.includes("alb") || nid.includes("ingress"))) return g;
        if (gid.includes("compute") && (nid.startsWith("cecs-") || nid.includes("ecs") || nid.includes("task"))) return g;
        if (gid.includes("storage") && (nid.includes("rds") || nid.includes("elasticache") || nid.includes("s3"))) return g;
        // Security LLD
        if (gid.includes("ingress") && (nid.includes("waf") || nid.includes("tls") || nid.includes("firewall"))) return g;
        if ((gid.includes("auth") || gid.includes("identity")) && (nid.includes("oauth") || nid.includes("jwt") || nid.includes("cognito"))) return g;
        if (gid.includes("rbac") && (nid.includes("rbac") || nid.includes("policy"))) return g;
        if (gid.includes("storage") && (nid.includes("kms") || nid.includes("blacklist") || nid.includes("audit") || nid.includes("encryption"))) return g;
        if (gid.includes("data") && (nid.includes("kms") || nid.includes("audit") || nid.includes("encryption"))) return g;
      }
      // Fallback: geometric containment
      const nx = node.position.x;
      const ny = node.position.y;
      for (const g of layerGroups) {
        const gx = g.position.x;
        const gy = g.position.y;
        const gw = (g.style?.width as number) || 1200;
        const gh = (g.style?.height as number) || 200;
        if (nx >= gx - 20 && nx <= gx + gw + 20 && ny >= gy - 20 && ny <= gy + gh + 20) {
          return g;
        }
      }
      return undefined;
    },
    [layerGroups]
  );

  // Friendly short label for layer tabs
  const getGroupShortLabel = useCallback((group: Node): string => {
    const gid = group.id.toLowerCase();
    const label = String(group.data?.label || "");
    if (gid.includes("infra")) return "Infrastructure";
    if (gid.includes("endpoint")) return "Endpoints";
    if (gid.includes("service")) return "Services";
    if (gid.includes("repo")) return "Repositories";
    if (gid.includes("model")) return "Models";
    if (gid.includes("table")) return "Schema Tables";
    if (gid.includes("pooling")) return "Cache & Tools";
    if (gid.includes("page")) return "App Pages";
    if (gid.includes("component")) return "UI Components";
    if (gid.includes("state")) return "State & API";
    if (gid.includes("devops")) return "DevOps Pipeline";
    if (gid.includes("edge")) return "Edge & Ingress";
    if (gid.includes("alb")) return "ALB Ingress";
    if (gid.includes("compute")) return "ECS Tasks";
    if (gid.includes("storage")) return "Storage Tier";
    if (gid.includes("ingress")) return "Perimeter";
    if (gid.includes("identity") || gid.includes("auth")) return "Identity Engine";
    if (gid.includes("rbac")) return "RBAC Policy";
    if (gid.includes("data")) return "Data Guard";
    const clean = label.replace(/\(.*?\)/g, "").trim();
    return clean.length > 18 ? clean.slice(0, 16) + "..." : clean || "Layer";
  }, []);

  // Compute segmented filter tabs with dynamic counts
  const layerTabs = useMemo(() => {
    const componentNodes = nodes.filter((n) => n.type !== "layerGroup");
    const allTab = { id: "all", label: "All Layers", count: componentNodes.length };

    const groupTabs = layerGroups.map((g) => {
      const count = componentNodes.filter((n) => getNodeGroup(n)?.id === g.id).length;
      return {
        id: g.id,
        label: getGroupShortLabel(g),
        count: count || (typeof g.data?.count === "number" ? g.data.count : 0),
      };
    });

    return [allTab, ...groupTabs];
  }, [nodes, layerGroups, getNodeGroup, getGroupShortLabel]);

  // Click to open inspector
  const onNodeClick: NodeMouseHandler = useCallback(
    (_event, node) => {
      if (node.type === "layerGroup") return;
      setSelectedNode(node.id);
      setSelectedNodeData(node);
      setInspectorOpen(true);
    },
    [setSelectedNode]
  );

  // Hover highlighting
  const onNodeMouseEnter: NodeMouseHandler = useCallback((_event, node) => {
    if (node.type !== "layerGroup") {
      setHoveredNodeId(node.id);
    }
  }, []);

  const onNodeMouseLeave: NodeMouseHandler = useCallback(() => {
    setHoveredNodeId(null);
  }, []);

  const connectedEdgesSet = useMemo(() => {
    if (!hoveredNodeId) return null;
    const set = new Set<string>();
    edges.forEach((e) => {
      if (e.source === hoveredNodeId || e.target === hoveredNodeId) {
        set.add(e.id);
      }
    });
    return set;
  }, [hoveredNodeId, edges]);

  const connectedNodesSet = useMemo(() => {
    if (!hoveredNodeId) return null;
    const set = new Set<string>([hoveredNodeId]);
    edges.forEach((e) => {
      if (e.source === hoveredNodeId) set.add(e.target);
      if (e.target === hoveredNodeId) set.add(e.source);
    });
    return set;
  }, [hoveredNodeId, edges]);

  // Visual node styling with layer filtering & hover dimming
  const displayNodes = useMemo(() => {
    return nodes.map((n) => {
      if (n.type === "layerGroup") {
        let groupOpacity = 1;
        if (selectedLayer !== "all") {
          groupOpacity = n.id === selectedLayer ? 1 : 0.2;
        }
        return {
          ...n,
          style: {
            ...n.style,
            opacity: groupOpacity,
            transition: "opacity 0.2s ease",
          },
        };
      }

      let opacity = 1;
      if (hoveredNodeId && connectedNodesSet && !connectedNodesSet.has(n.id)) {
        opacity = 0.25;
      }

      // Filter by architecture layer / group
      if (selectedLayer !== "all") {
        const grp = getNodeGroup(n);
        if (grp?.id !== selectedLayer) {
          opacity = 0.12;
        }
      }

      // Filter by search query
      if (searchQuery.trim()) {
        const str = `${n.data?.label || ""} ${n.data?.code || ""} ${n.data?.tech || ""} ${n.data?.description || ""}`.toLowerCase();
        if (!str.includes(searchQuery.toLowerCase())) {
          opacity = 0.15;
        }
      }

      return {
        ...n,
        style: {
          ...n.style,
          opacity,
          transition: "opacity 0.2s ease, transform 0.2s ease",
        },
      };
    });
  }, [nodes, hoveredNodeId, connectedNodesSet, selectedLayer, searchQuery, getNodeGroup]);

  // Visual edge styling with component-matching colors & layer dimming
  const displayEdges = useMemo(() => {
    return edges.map((e) => {
      const isConnected = connectedEdgesSet ? connectedEdgesSet.has(e.id) : true;
      const isDimmed = connectedEdgesSet && !isConnected;

      // Check layer filtering for edges
      let layerDimmed = false;
      if (selectedLayer !== "all") {
        const sNode = nodes.find((n) => n.id === e.source);
        const tNode = nodes.find((n) => n.id === e.target);
        const sGrp = sNode ? getNodeGroup(sNode) : undefined;
        const tGrp = tNode ? getNodeGroup(tNode) : undefined;
        if (sGrp?.id !== selectedLayer && tGrp?.id !== selectedLayer) {
          layerDimmed = true;
        }
      }

      // Connection uses the exact same color as its originating component
      const edgeTheme = getEdgeTheme(e.source, e.target, (e.data?.strokeColor as string) || (e.style?.stroke as string));
      const strokeColor = isDark ? edgeTheme.darkColor : edgeTheme.lightColor;
      const isHovered = isConnected && hoveredNodeId !== null;

      return {
        ...e,
        animated: animationsEnabled,
        selected: isHovered,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 18,
          height: 18,
          color: strokeColor,
        },
        data: {
          ...((e.data || {}) as Record<string, unknown>),
          strokeColor,
        },
        style: {
          ...e.style,
          opacity: isDimmed ? 0.12 : layerDimmed ? 0.08 : 1,
          stroke: strokeColor,
          strokeWidth: isHovered ? 3.4 : (isDark ? 2.0 : 2.4),
          filter: isHovered
            ? (isDark ? `drop-shadow(0 0 8px ${strokeColor})` : `drop-shadow(0 0 6px ${strokeColor}aa)`)
            : undefined,
          transition: "opacity 0.2s ease, stroke 0.2s ease, stroke-width 0.2s ease",
        },
      };
    });
  }, [edges, nodes, connectedEdgesSet, hoveredNodeId, selectedLayer, animationsEnabled, isDark, getNodeGroup]);

  const selectedNodeGroup = selectedNodeData ? getNodeGroup(selectedNodeData) : undefined;

  return (
    <div className={`relative h-full w-full text-slate-900 dark:text-white ${isFullscreen ? "fixed inset-0 z-50 bg-white dark:bg-black" : "bg-transparent"}`}>
      {/* ── React Flow Canvas or Empty State ── */}
      {nodes.length === 0 ? (
        <div className="flex h-full w-full flex-col items-center justify-center p-8 text-center bg-transparent text-black dark:text-white">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-xl border border-neutral-300 bg-neutral-100 text-black dark:border-neutral-700 dark:bg-neutral-900 dark:text-white">
            <Server className="h-8 w-8" />
          </div>
          <h3 className="font-heading text-lg font-bold text-black dark:text-white">
            No {type.toUpperCase()} LLD Generated Yet
          </h3>
          <p className="mt-1.5 max-w-md text-xs text-neutral-500 dark:text-neutral-400 leading-relaxed">
            Low-Level Designs will be synthesized in the background once the High-Level Architecture is generated.
          </p>
        </div>
      ) : (
        <ReactFlow
          key={`${type}-${nodes.length}`}
          nodes={displayNodes}
          edges={displayEdges}
          nodeTypes={architectureNodeTypes}
          edgeTypes={architectureEdgeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          onNodeMouseEnter={onNodeMouseEnter}
          onNodeMouseLeave={onNodeMouseLeave}
          fitView
          fitViewOptions={{ padding: 0.15 }}
          minZoom={0.2}
          maxZoom={2.5}
          proOptions={{ hideAttribution: true }}
        >
          <Background gap={24} size={1.2} color={isDark ? "rgba(255, 255, 255, 0.08)" : "rgba(100, 116, 139, 0.22)"} />
          <Controls className="!border-neutral-300 !bg-white !text-black [&>button]:!border-neutral-200 [&>button]:!bg-white [&>button]:!text-neutral-800 [&>button:hover]:!bg-neutral-100 [&>button:hover]:!text-black dark:!border-neutral-700 dark:!bg-neutral-900 dark:!text-white dark:[&>button]:!border-neutral-800 dark:[&>button]:!bg-neutral-900 dark:[&>button]:!text-neutral-200 dark:[&>button:hover]:!bg-neutral-800 dark:[&>button:hover]:!text-white" />
        </ReactFlow>
      )}

      {/* ── Interactive Component Inspector Drawer (Slide-over) ── */}
      {inspectorOpen && selectedNodeData && (
        <div className="absolute top-0 right-0 z-30 flex h-full w-96 flex-col border-l border-neutral-300 bg-white/98 p-6 backdrop-blur-xl shadow-2xl animate-in slide-in-from-right duration-200 dark:border-neutral-800 dark:bg-black/98">
          {/* Drawer Header */}
          <div className="flex items-center justify-between pb-4 border-b border-neutral-200 dark:border-neutral-800">
            <div className="flex items-center gap-2.5">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-black text-white dark:bg-white dark:text-black">
                {selectedNodeData.type === "database" ? (
                  <Database className="h-5 w-5" />
                ) : selectedNodeData.type === "gateway" ? (
                  <ShieldCheck className="h-5 w-5" />
                ) : selectedNodeData.type === "frontend" ? (
                  <Globe className="h-5 w-5" />
                ) : selectedNodeData.type === "queue" ? (
                  <Radio className="h-5 w-5" />
                ) : selectedNodeData.type === "devops" ? (
                  <Cloud className="h-5 w-5" />
                ) : (
                  <Server className="h-5 w-5" />
                )}
              </div>
              <div>
                <div className="flex items-center gap-1.5 mb-0.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                    {String(selectedNodeData.data?.code || selectedNodeData.type || "Component")}
                  </span>
                  {selectedNodeGroup && (
                    <span className="rounded-sm border border-neutral-300 bg-neutral-100 px-1.5 py-0.2 text-[9px] font-bold uppercase tracking-wider text-neutral-700 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">
                      {getGroupShortLabel(selectedNodeGroup)} Layer
                    </span>
                  )}
                </div>
                <h3 className="font-heading text-sm font-bold text-black dark:text-white leading-tight">
                  {String(selectedNodeData.data?.label || selectedNodeData.id)}
                </h3>
              </div>
            </div>

            <button
              onClick={() => setInspectorOpen(false)}
              className="rounded-lg p-1 text-neutral-400 hover:bg-neutral-100 hover:text-black dark:hover:bg-neutral-800 dark:hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Drawer Body Specs */}
          <div className="flex-1 overflow-y-auto py-4 space-y-4 text-xs">
            {/* LLD Role & Specification */}
            <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3.5 dark:border-neutral-800 dark:bg-neutral-900">
              <span className="text-[11px] font-bold text-black dark:text-white">LLD Specification</span>
              <p className="mt-1 text-neutral-700 dark:text-neutral-300 leading-relaxed font-normal">
                {String(
                  selectedNodeData.data?.description ||
                  `${selectedNodeData.data?.label} detailed architectural component in ${type.toUpperCase()} LLD.`
                )}
              </p>
            </div>

            {/* Technical Specifications */}
            <div className="space-y-2">
              <span className="text-[11px] font-bold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
                Technical Specifications
              </span>
              <div className="grid grid-cols-2 gap-2">
                <div className="rounded-lg border border-neutral-200 bg-white p-2.5 dark:border-neutral-800 dark:bg-neutral-900">
                  <span className="text-[10px] text-neutral-500 font-semibold">Technology</span>
                  <p className="font-bold text-black dark:text-white truncate">
                    {String(
                      selectedNodeData.data?.tech ||
                      selectedNodeData.data?.engine ||
                      selectedNodeData.data?.role ||
                      `${type.toUpperCase()} Module`
                    )}
                  </p>
                </div>
                <div className="rounded-lg border border-neutral-200 bg-white p-2.5 dark:border-neutral-800 dark:bg-neutral-900">
                  <span className="text-[10px] text-neutral-500 font-semibold">Protocol / Engine</span>
                  <p className="font-bold text-black dark:text-white truncate">
                    {String(
                      selectedNodeData.data?.protocol ||
                      selectedNodeData.data?.schema ||
                      selectedNodeData.data?.category ||
                      "Standard Protocol"
                    )}
                  </p>
                </div>
              </div>
            </div>

            {/* Ingress / Egress Topology Connections */}
            <div className="space-y-2">
              <span className="text-[11px] font-bold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
                Topology Connections
              </span>
              <div className="space-y-1.5">
                {edges
                  .filter((e) => e.source === selectedNodeData.id || e.target === selectedNodeData.id)
                  .map((e) => {
                    const isSource = e.source === selectedNodeData.id;
                    const otherNodeId = isSource ? e.target : e.source;
                    const otherNode = nodes.find((n) => n.id === otherNodeId);
                    const connTheme = getComponentTheme(e.source);
                    const connColor = isDark ? connTheme.darkColor : connTheme.lightColor;

                    return (
                      <div
                        key={e.id}
                        className="flex items-center justify-between rounded-lg border border-neutral-200 bg-white p-2 text-[11px] dark:border-neutral-800 dark:bg-neutral-900"
                        style={{ borderLeftColor: connColor, borderLeftWidth: 3 }}
                      >
                        <span className="font-bold shrink-0 text-[10px]" style={{ color: connColor }}>
                          {isSource ? "Outflow ➔" : "Inflow ⬅"}
                        </span>
                        <span className="font-medium text-neutral-800 dark:text-neutral-200 truncate mx-2">
                          {String(otherNode?.data?.label || otherNodeId)}
                        </span>
                        {Boolean((e.data as Record<string, unknown> | undefined)?.label) ? (
                          <span
                            className="rounded border px-1.5 py-0.5 text-[9px] font-mono shrink-0"
                            style={{
                              borderColor: `${connColor}55`,
                              color: connColor,
                              backgroundColor: `${connColor}15`,
                            }}
                          >
                            {String((e.data as Record<string, unknown>).label)}
                          </span>
                        ) : null}
                      </div>
                    );
                  })}
              </div>
            </div>

            {/* Raw Component Node Details */}
            <div className="rounded-lg border border-neutral-200 bg-white p-3 dark:border-neutral-800 dark:bg-neutral-900 font-mono text-[10px]">
              <span className="text-neutral-500 block mb-1 font-sans font-semibold text-[10px] uppercase tracking-wider">
                Raw Node Attributes
              </span>
              <pre className="whitespace-pre-wrap overflow-x-auto text-neutral-800 dark:text-neutral-200 max-h-36">
                {JSON.stringify(selectedNodeData.data, null, 2)}
              </pre>
            </div>
          </div>

          {/* Drawer Footer Actions */}
          <div className="pt-4 border-t border-neutral-200 dark:border-neutral-800 space-y-2">
            <button
              onClick={() => {
                const label = String(selectedNodeData.data?.label || selectedNodeData.id);
                const desc = String(
                  selectedNodeData.data?.description ||
                  `${type.toUpperCase()} LLD component specification: ${label}`
                );
                openExplain(
                  selectedNodeData.id,
                  `${label} — ${type.toUpperCase()} Component Specification`,
                  desc
                );
              }}
              className="flex w-full items-center justify-center gap-1.5 rounded-xl bg-black py-2.5 text-xs font-semibold text-white transition-all hover:bg-neutral-800 dark:bg-white dark:text-black dark:hover:bg-neutral-200 cursor-pointer shadow-sm"
            >
              <span>View Full Component Specification</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
