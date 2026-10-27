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
  type Edge,
  type ReactFlowInstance,
} from "@xyflow/react";
import {
  Search,
  Zap,
  Layers,
  X,
  ArrowRight,
  Maximize2,
  Minimize2,
  Server,
  Database,
  ShieldCheck,
  Globe,
  Radio,
  ChevronDown,
  Sparkles,
  ArrowDownUp,
  GitFork,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/lib/store";
import Select, { type TSelectData } from "@/components/ui/select";
import { architectureNodeTypes } from "./flow/ArchitectureNodes";
import { architectureEdgeTypes } from "./flow/AnimatedFlowEdge";
import { getEdgeTheme, getComponentTheme } from "@/lib/flow-colors";
import { parseHldToReactFlow, layoutHldLeftToRight, layoutHldTopDown } from "@/lib/graph-parser";
import ModelDesignControls from "./ModelDesignControls";

export function getComponentLldType(
  node: Node | null | undefined
): "backend" | "frontend" | "database" | "security" | "cloud" {
  if (!node) return "backend";
  const division = (node.data?.division as string)?.toLowerCase();
  const type = (node.type || "").toLowerCase();
  const id = (node.id || "").toLowerCase();
  const label = String(node.data?.label || "").toLowerCase();
  const role = String(node.data?.role || "").toLowerCase();

  // 1. Frontend Division (Actors, Web App, Gateway)
  if (
    division === "frontend" ||
    type === "frontend" ||
    type === "actor" ||
    id.includes("front") ||
    id.includes("actor") ||
    id.includes("gateway") ||
    label.includes("web app") ||
    label.includes("next.js") ||
    label.includes("react") ||
    label.includes("user") ||
    label.includes("client") ||
    label.includes("admin") ||
    label.includes("gateway")
  ) {
    return "frontend";
  }

  // 2. Database Division (Postgres, Cache, Storage)
  if (
    division === "database" ||
    type === "database" ||
    type === "cache" ||
    id.includes("db") ||
    id.includes("database") ||
    id.includes("cache") ||
    id.includes("redis") ||
    id.includes("postgres") ||
    label.includes("database") ||
    label.includes("postgres") ||
    label.includes("cache") ||
    label.includes("redis")
  ) {
    return "database";
  }

  // 3. Deployment / Cloud Division (Kubernetes, CI/CD, Observability)
  if (
    division === "deployment" ||
    type === "devops" ||
    id.includes("k8s") ||
    id.includes("cicd") ||
    id.includes("cloud") ||
    id.includes("deploy") ||
    id.includes("monitor") ||
    label.includes("kubernetes") ||
    label.includes("docker") ||
    label.includes("aws") ||
    label.includes("prometheus") ||
    label.includes("ci/cd") ||
    role.includes("pipeline")
  ) {
    return "cloud";
  }

  // 4. Security Division
  if (
    division === "security" ||
    type === "security" ||
    id.includes("waf") ||
    id.includes("security") ||
    id.includes("guard") ||
    label.includes("waf") ||
    label.includes("security")
  ) {
    return "security";
  }

  // 5. Backend Division (Microservices, Domain Services, Event Bus Queue)
  return "backend";
}

interface HLDGraphProps {
  onSelectLld?: (type: "backend" | "frontend" | "database" | "security" | "cloud") => void;
}

export default function HLDGraph({ onSelectLld }: HLDGraphProps = {}) {
  const {
    hldData,
    hldNodes: dynamicNodes,
    hldEdges: dynamicEdges,
    setSelectedNode,
    setActivePipelineStep,
    setActiveLldType,
    jumpToLld,
    openExplain,
    openTechRationale,
    theme,
    layoutDirection,
    setLayoutDirection,
    activeModelId,
  } = useAppStore();

  const isArchova = !activeModelId || activeModelId === "archova";
  const isDark = theme === "dark";
  const rfInstanceRef = useRef<any>(null);

  // Defensive sanitizer: guarantees React Flow nodes always have valid position: { x, y }
  const sanitizeNodes = useCallback((nodeList: Node[]): Node[] => {
    if (!Array.isArray(nodeList)) return [];
    return nodeList.map((n, idx) => {
      const raw = n as any;
      const posX = typeof n?.position?.x === "number" ? n.position.x : (typeof raw.x === "number" ? raw.x : 200 + (idx % 4) * 360);
      const posY = typeof n?.position?.y === "number" ? n.position.y : (typeof raw.y === "number" ? raw.y : 120 + Math.floor(idx / 4) * 220);
      return {
        ...n,
        id: String(n.id || `node-${idx}`),
        position: { x: posX, y: posY },
        data: n.data || { label: raw.label || raw.name || n.id || `Component ${idx + 1}` },
      };
    });
  }, []);

  // Use dynamicNodes or empty graph
  const initialData = useMemo(() => {
    if (dynamicNodes && dynamicNodes.length > 0) {
      return { nodes: sanitizeNodes(dynamicNodes), edges: dynamicEdges || [] };
    }
    return { nodes: [], edges: [] };
  }, [dynamicNodes, dynamicEdges, sanitizeNodes]);

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

  const divisionSelectData: TSelectData[] = useMemo(
    () => [
      { id: "all", label: "All Divisions (16)", value: "all", description: "Show complete multi-tier system topology", icon: "🌐" },
      { id: "frontend", label: "Frontend (4)", value: "frontend", description: "Client interfaces, mobile, and API gateway", icon: "💻" },
      { id: "backend", label: "Backend (7)", value: "backend", description: "Microservices, async workers, and message buses", icon: "⚙️" },
      { id: "database", label: "Database (2)", value: "database", description: "Primary datastores, replicas, and caching layers", icon: "🗄️" },
      { id: "deployment", label: "Deployment (3)", value: "deployment", description: "Cloud infrastructure, CDN, and telemetry", icon: "🚀" },
    ],
    []
  );

  // Sync state when dynamic nodes/edges from backend or layoutDirection are updated
  useEffect(() => {
    if (hldData) {
      const parsed = parseHldToReactFlow(hldData, undefined, layoutDirection);
      setNodes(sanitizeNodes(parsed.nodes));
      setEdges(parsed.edges || []);
    } else if (dynamicNodes && dynamicNodes.length > 0) {
      const parsed =
        layoutDirection === "LR"
          ? layoutHldLeftToRight(dynamicNodes as any, dynamicEdges as any)
          : layoutHldTopDown(dynamicNodes as any, dynamicEdges as any);
      setNodes(sanitizeNodes(parsed.nodes));
      setEdges(parsed.edges || []);
    } else {
      setNodes([]);
      setEdges([]);
    }
  }, [hldData, dynamicNodes, dynamicEdges, layoutDirection, setNodes, setEdges, sanitizeNodes]);

  const handleLayoutDirectionChange = useCallback(
    (dir: "TB" | "LR") => {
      setLayoutDirection(dir);
      if (hldData) {
        const parsed = parseHldToReactFlow(hldData, undefined, dir);
        setNodes(sanitizeNodes(parsed.nodes));
        setEdges(parsed.edges);
      } else if (dynamicNodes && dynamicNodes.length > 0) {
        const parsed =
          dir === "LR"
            ? layoutHldLeftToRight(dynamicNodes as any, dynamicEdges as any)
            : layoutHldTopDown(dynamicNodes as any, dynamicEdges as any);
        setNodes(sanitizeNodes(parsed.nodes));
        setEdges(parsed.edges);
      }
      setTimeout(() => {
        rfInstanceRef.current?.fitView({ duration: 500, padding: 0.18 });
      }, 50);
    },
    [hldData, dynamicNodes, dynamicEdges, setLayoutDirection, setNodes, setEdges, sanitizeNodes]
  );

  // Jump to corresponding LLD tab
  const handleJumpToLld = useCallback(
    (type: "backend" | "frontend" | "database" | "security" | "cloud") => {
      setActiveLldType(type);
      jumpToLld(type);
      if (onSelectLld) {
        onSelectLld(type);
      }
    },
    [setActiveLldType, jumpToLld, onSelectLld]
  );

  // Node Click: On clicking specific component, navigate directly to corresponding LLD design
  const onNodeClick: NodeMouseHandler = useCallback(
    (_event, node) => {
      setSelectedNode(node.id);
      setSelectedNodeData(node);
      const targetLld = getComponentLldType(node);
      handleJumpToLld(targetLld);
    },
    [setSelectedNode, handleJumpToLld]
  );

  // Hover highlighting for interactive connection tracking
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);

  const onNodeMouseEnter: NodeMouseHandler = useCallback((_event, node) => {
    if (node.type !== "layerGroup") {
      setHoveredNodeId(node.id);
    }
  }, []);

  const onNodeMouseLeave: NodeMouseHandler = useCallback(() => {
    setHoveredNodeId(null);
  }, []);

  // Compute connected nodes & edges during hover
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

  // Apply visual styling for hover dimming and animations
  const displayNodes = useMemo(() => {
    return nodes.map((n) => {
      if (n.type === "layerGroup") return n;

      let opacity = 1;
      if (hoveredNodeId && connectedNodesSet && !connectedNodesSet.has(n.id)) {
        opacity = 0.25;
      }

      // Filter by architecture division (Frontend, Backend, Database, Deployment)
      if (selectedLayer !== "all") {
        if (n.type === "layerGroup") {
          const groupId = n.id.toLowerCase();
          const isTargetGroup = groupId.includes(selectedLayer);
          if (!isTargetGroup) {
            opacity = 0.2;
          }
        } else {
          const nodeDivision = (n.data?.division as string) || (
            ["actor", "frontend", "gateway"].includes(n.type || "") ? "frontend" :
              ["service", "queue"].includes(n.type || "") ? "backend" :
                ["database", "cache"].includes(n.type || "") ? "database" :
                  n.type === "devops" ? "deployment" : ""
          );

          if (nodeDivision !== selectedLayer) {
            opacity = 0.12;
          }
        }
      }

      // Filter by search query
      if (searchQuery.trim()) {
        const str = `${n.data?.label || ""} ${n.data?.code || ""} ${n.data?.description || ""}`.toLowerCase();
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
  }, [nodes, hoveredNodeId, connectedNodesSet, selectedLayer, searchQuery]);

  const displayEdges = useMemo(() => {
    return edges.map((e) => {
      const isConnected = connectedEdgesSet ? connectedEdgesSet.has(e.id) : true;
      const isDimmed = connectedEdgesSet && !isConnected;

      // Check division filtering for edges
      let divisionDimmed = false;
      if (selectedLayer !== "all") {
        const sNode = nodes.find((n) => n.id === e.source);
        const tNode = nodes.find((n) => n.id === e.target);
        const sDiv = (sNode?.data?.division as string) || (
          ["actor", "frontend", "gateway"].includes(sNode?.type || "") ? "frontend" :
            ["service", "queue"].includes(sNode?.type || "") ? "backend" :
              ["database", "cache"].includes(sNode?.type || "") ? "database" :
                sNode?.type === "devops" ? "deployment" : ""
        );
        const tDiv = (tNode?.data?.division as string) || (
          ["actor", "frontend", "gateway"].includes(tNode?.type || "") ? "frontend" :
            ["service", "queue"].includes(tNode?.type || "") ? "backend" :
              ["database", "cache"].includes(tNode?.type || "") ? "database" :
                tNode?.type === "devops" ? "deployment" : ""
        );
        if (sDiv !== selectedLayer && tDiv !== selectedLayer) {
          divisionDimmed = true;
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
          animated: animationsEnabled,
        },
        style: {
          ...e.style,
          opacity: isDimmed ? 0.12 : divisionDimmed ? 0.08 : 1,
          stroke: strokeColor,
          strokeWidth: isHovered ? 3.4 : (isDark ? 2.0 : 2.4),
          filter: isHovered
            ? (isDark ? `drop-shadow(0 0 8px ${strokeColor})` : `drop-shadow(0 0 6px ${strokeColor}aa)`)
            : undefined,
          transition: "opacity 0.2s ease, stroke 0.2s ease, stroke-width 0.2s ease",
        },
      };
    });
  }, [edges, nodes, connectedEdgesSet, hoveredNodeId, selectedLayer, animationsEnabled, isDark]);

  return (
    <div className={`relative h-full w-full text-slate-900 dark:text-white ${isFullscreen ? "fixed inset-0 z-50 bg-white dark:bg-black" : "bg-transparent"}`}>
      {/* ── Top Floating Control Panel Monochrome ── */}
      {/* ── Top-Right Floating Controls (Positioned Below Home Button) ── */}
      <div className="absolute top-3.5 right-4 z-20 flex flex-col items-end gap-2 pointer-events-none">
        <div className="flex items-center gap-2">
          {/* Architecture Division Dropdown */}
          <div className="pointer-events-auto">
            <Select
              id="hld-division-select"
              title="Filter Architecture Division"
              value={selectedLayer}
              onChange={(val) => setSelectedLayer(val)}
              data={divisionSelectData}
            />
          </div>

          {/* Search / Filter Input */}
          <div className="relative flex items-center pointer-events-auto">
            <Search className="absolute left-2.5 h-3.5 w-3.5 text-neutral-500 dark:text-neutral-400" />
            <input
              type="text"
              placeholder="Filter components..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-8 w-44 rounded-xl border border-neutral-300 bg-white/95 pl-8 pr-3 text-xs text-black placeholder:text-neutral-400 backdrop-blur-md focus:border-black focus:outline-none dark:border-neutral-700 dark:bg-neutral-900/95 dark:text-white dark:placeholder:text-neutral-500 dark:focus:border-white shadow-2xs"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-2 text-neutral-400 hover:text-black dark:hover:text-white cursor-pointer"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </div>

          {/* Flow Animation Toggle */}
          <button
            onClick={() => setAnimationsEnabled(!animationsEnabled)}
            className={`pointer-events-auto flex items-center gap-1.5 rounded-xl border px-3 py-1.5 text-xs font-semibold backdrop-blur-md transition-all duration-150 cursor-pointer shadow-2xs ${animationsEnabled
              ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black"
              : "border-neutral-200/80 bg-white/70 text-neutral-700 hover:border-black hover:text-black dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-300 dark:hover:bg-[#161619] dark:hover:border-white/20 dark:hover:text-white"
              }`}
            title="Toggle data flow animation"
          >
            <Zap className="h-3.5 w-3.5" />
            <span>{animationsEnabled ? "Flow: Active" : "Flow: Paused"}</span>
          </button>

          {/* Fullscreen Toggle */}
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="pointer-events-auto flex h-8 w-8 items-center justify-center rounded-xl border border-neutral-200/80 bg-white/70 text-neutral-700 backdrop-blur-md hover:border-black hover:text-black dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-300 dark:hover:bg-[#161619] dark:hover:border-white/20 dark:hover:text-white shadow-2xs cursor-pointer transition-colors"
            title="Toggle Fullscreen"
          >
            {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </button>
        </div>

        {/* ── Right-Top Controls Directly Below Flow: Active Button (Requirement 2 & 3) ── */}
        <div className="flex items-center gap-2 pointer-events-auto">
          <ModelDesignControls />
        </div>
      </div>

      {/* ── React Flow Interactive Canvas or Empty State ── */}
      {nodes.length === 0 ? (
        <div className="flex h-full w-full flex-col items-center justify-center p-8 text-center bg-white text-black dark:bg-black dark:text-white">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-xl border border-neutral-300 bg-neutral-100 text-black dark:border-neutral-700 dark:bg-neutral-900 dark:text-white">
            <Layers className="h-8 w-8" />
          </div>
          <h3 className="font-heading text-lg font-bold text-black dark:text-white">No High-Level Design (HLD) Generated Yet</h3>
          <p className="mt-1.5 max-w-md text-xs text-neutral-500 dark:text-neutral-400 leading-relaxed">
            Enter your project requirements in Step 1 and complete the stakeholder interview questions to synthesize the interactive visual topology.
          </p>
        </div>
      ) : (
        <ReactFlow
          onInit={(inst) => {
            rfInstanceRef.current = inst;
          }}
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
          <Controls className="!border-neutral-200/80 !bg-white/70 !text-black [&>button]:!border-neutral-200 [&>button]:!bg-white [&>button]:!text-neutral-800 [&>button:hover]:!bg-neutral-100 [&>button:hover]:!text-black dark:!border-[#262626] dark:!bg-[#0D0D0F] dark:!text-white dark:[&>button]:!border-[#262626] dark:[&>button]:!bg-[#0D0D0F] dark:[&>button]:!text-neutral-200 dark:[&>button:hover]:!bg-[#161619] dark:[&>button:hover]:!text-white" />
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
                ) : (
                  <Server className="h-5 w-5" />
                )}
              </div>
              <div>
                <div className="flex items-center gap-1.5 mb-0.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                    {String(selectedNodeData.data?.code || selectedNodeData.type || "Component")}
                  </span>
                  {Boolean(selectedNodeData.data?.division) && (
                    <span className="rounded-sm border border-neutral-300 bg-neutral-100 px-1.5 py-0.2 text-[9px] font-bold uppercase tracking-wider text-neutral-700 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">
                      {String(selectedNodeData.data?.division)} Division
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
            {/* Description */}
            <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3.5 dark:border-neutral-800 dark:bg-neutral-900">
              <span className="text-[11px] font-bold text-black dark:text-white">Architecture Role</span>
              <p className="mt-1 text-neutral-700 dark:text-neutral-300 leading-relaxed font-normal">
                {String(
                  selectedNodeData.data?.description ||
                  `${selectedNodeData.data?.label} architectural component in High-Level Design.`
                )}
              </p>
            </div>

            {/* Tech Stack & Protocol */}
            <div className="space-y-2">
              <span className="text-[11px] font-bold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">Technical Specifications</span>
              <div className="grid grid-cols-2 gap-2">
                <div className="rounded-lg border border-neutral-200 bg-white p-2.5 dark:border-neutral-800 dark:bg-neutral-900">
                  <span className="text-[10px] text-neutral-500 font-semibold">Technology</span>
                  <p className="font-bold text-black dark:text-white truncate">
                    {String(selectedNodeData.data?.tech || selectedNodeData.data?.engine || "Standard Microservice")}
                  </p>
                </div>
                <div className="rounded-lg border border-neutral-200 bg-white p-2.5 dark:border-neutral-800 dark:bg-neutral-900">
                  <span className="text-[10px] text-neutral-500 font-semibold">Protocol / Engine</span>
                  <p className="font-bold text-black dark:text-white truncate">
                    {String(selectedNodeData.data?.protocol || selectedNodeData.data?.schema || "gRPC / HTTPS")}
                  </p>
                </div>
              </div>
            </div>

            {/* Ingress / Egress Topology Connections */}
            <div className="space-y-2">
              <span className="text-[11px] font-bold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">Topology Connections</span>
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
          </div>

          {/* Drawer Footer Actions */}
          <div className="pt-4 border-t border-neutral-200 dark:border-neutral-800 space-y-2">
            {/* Action 1: Why This Tech? (In-detail Rationale & Alternatives) — ONLY visible for AI_engine */}
            {isArchova ? (
              <button
                onClick={() => {
                  openTechRationale({
                    id: selectedNodeData.id,
                    type: selectedNodeData.type,
                    ...((selectedNodeData.data || {}) as Record<string, unknown>),
                  });
                }}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 py-2.5 text-xs font-bold text-white transition-all hover:from-blue-500 hover:to-indigo-500 cursor-pointer shadow-md hover:shadow-lg hover:scale-[1.01] active:scale-[0.99]"
              >
                <Sparkles className="h-3.5 w-3.5 text-amber-300 animate-pulse" />
                <span>Why This Tech? (In-detail & Alternatives)</span>
              </button>
            ) : (
              <div className="flex items-center gap-2 rounded-xl border border-amber-500/20 bg-amber-50/70 p-2.5 text-[11px] text-amber-900 dark:border-amber-500/20 dark:bg-amber-950/25 dark:text-amber-200">
                <Sparkles className="h-3.5 w-3.5 text-amber-500 shrink-0" />
                <span>
                  <strong>Note:</strong> In-detail rationale & trade-offs are available exclusively for <strong>Archova AI Engine</strong> designs.
                </span>
              </div>
            )}

            <button
              onClick={() => {
                const targetLld = getComponentLldType(selectedNodeData);
                handleJumpToLld(targetLld);
              }}
              className="flex w-full items-center justify-center gap-1.5 rounded-xl bg-black py-2 text-xs font-semibold text-white transition-all hover:bg-neutral-800 dark:bg-white dark:text-black dark:hover:bg-neutral-200 cursor-pointer shadow-sm"
            >
              <span>Explore {getComponentLldType(selectedNodeData).toUpperCase()} LLD Blueprint</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>

            <button
              onClick={() => {
                const label = String(selectedNodeData.data?.label || selectedNodeData.id);
                const desc = String(selectedNodeData.data?.description || `High-Level Design component: ${label}`);
                openExplain(selectedNodeData.id, `${label} — Architecture Specification`, desc);
              }}
              className="flex w-full items-center justify-center gap-1.5 rounded-xl border border-neutral-200/80 bg-white/70 backdrop-blur-md py-2 text-xs font-semibold text-neutral-800 transition-all hover:border-black hover:text-black dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-300 dark:hover:bg-[#161619] dark:hover:border-white/20 dark:hover:text-white cursor-pointer shadow-2xs"
            >
              <span>View Full Component Specification</span>
            </button>
          </div>
        </div>
      )}

      {/* Floating Guidance Banner */}
      <div className="absolute bottom-4 left-4 z-20 hidden md:flex items-center gap-2 rounded-xl border border-neutral-200/80 bg-white/70 px-3.5 py-1.5 text-xs text-neutral-800 shadow-sm backdrop-blur-md dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-200 pointer-events-none">
        <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
        <span>Click any component (Frontend, Backend, Database, Cloud) to display its LLD design</span>
      </div>
    </div>
  );
}
