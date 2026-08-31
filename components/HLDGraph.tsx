"use client";

import { useCallback, useEffect, useState, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  Panel,
  MarkerType,
  useNodesState,
  useEdgesState,
  type NodeMouseHandler,
  type Node,
  type Edge,
} from "@xyflow/react";
import {
  Search,
  Zap,
  Layers,
  X,
  ArrowRight,
  Maximize2,
  Minimize2,
  Activity,
  Server,
  Database,
  ShieldCheck,
  Globe,
  Radio,
  ExternalLink,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import { architectureNodeTypes } from "./flow/ArchitectureNodes";
import { architectureEdgeTypes } from "./flow/AnimatedFlowEdge";

export default function HLDGraph() {
  const {
    hldNodes: dynamicNodes,
    hldEdges: dynamicEdges,
    setSelectedNode,
    setActivePipelineStep,
    setActiveLldType,
  } = useAppStore();

  const initialNodes = dynamicNodes || [];
  const initialEdges = dynamicEdges || [];

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Inspector Drawer state
  const [selectedNodeData, setSelectedNodeData] = useState<Node | null>(null);
  const [inspectorOpen, setInspectorOpen] = useState(false);

  // Search & Filter
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedLayer, setSelectedLayer] = useState<string>("all");
  const [animationsEnabled, setAnimationsEnabled] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Sync state when dynamic nodes/edges from backend are updated
  useEffect(() => {
    setNodes(dynamicNodes || []);
    setEdges(dynamicEdges || []);
  }, [dynamicNodes, dynamicEdges, setNodes, setEdges]);

  // Node Click: Open rich inspector drawer
  const onNodeClick: NodeMouseHandler = useCallback(
    (_event, node) => {
      // Don't open drawer on layer group backgrounds
      if (node.type === "layerGroup") return;

      setSelectedNode(node.id);
      setSelectedNodeData(node);
      setInspectorOpen(true);
    },
    [setSelectedNode]
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

      // Filter by layer category
      if (selectedLayer !== "all") {
        if (selectedLayer === "frontend" && !["actor", "frontend"].includes(n.type || "")) opacity = 0.15;
        if (selectedLayer === "gateway" && n.type !== "gateway") opacity = 0.15;
        if (selectedLayer === "services" && n.type !== "service") opacity = 0.15;
        if (selectedLayer === "data" && !["database", "cache"].includes(n.type || "")) opacity = 0.15;
        if (selectedLayer === "queue" && n.type !== "queue") opacity = 0.15;
        if (selectedLayer === "devops" && n.type !== "devops") opacity = 0.15;
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
      const strokeColor = isConnected && hoveredNodeId !== null ? "#818cf8" : (e.style?.stroke as string) || "#6366f1";

      return {
        ...e,
        animated: animationsEnabled,
        selected: isConnected && hoveredNodeId !== null,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 18,
          height: 18,
          color: strokeColor,
        },
        style: {
          ...e.style,
          opacity: isDimmed ? 0.15 : 1,
          stroke: strokeColor,
          strokeWidth: isConnected && hoveredNodeId !== null ? 3 : 1.75,
          transition: "opacity 0.2s ease, stroke 0.2s ease",
        },
      };
    });
  }, [edges, connectedEdgesSet, hoveredNodeId, animationsEnabled]);

  // Jump to corresponding LLD tab from drawer
  const handleJumpToLld = (type: "backend" | "frontend" | "database" | "security" | "cloud") => {
    setActiveLldType(type);
    setActivePipelineStep(4);
  };

  return (
    <div className={`relative h-full w-full bg-[#0a0b10] text-white ${isFullscreen ? "fixed inset-0 z-50" : ""}`}>
      {/* ── Top Floating Control Panel ── */}
      <div className="absolute top-4 left-4 z-20 flex flex-wrap items-center gap-2">
        {/* Layer Filters */}
        <div className="flex items-center gap-1 rounded-xl border border-zinc-800 bg-zinc-950/80 p-1 backdrop-blur-md shadow-xl">
          {[
            { id: "all", label: "All Layers" },
            { id: "frontend", label: "Frontend" },
            { id: "gateway", label: "Gateway" },
            { id: "services", label: "Microservices" },
            { id: "data", label: "Data & Cache" },
            { id: "queue", label: "Async Queue" },
            { id: "devops", label: "DevOps & Obs" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedLayer(tab.id)}
              className={`rounded-lg px-2.5 py-1 text-[11px] font-semibold transition-all ${
                selectedLayer === tab.id
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-zinc-400 hover:bg-zinc-800 hover:text-white"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search / Filter Input */}
        <div className="relative flex items-center">
          <Search className="absolute left-2.5 h-3.5 w-3.5 text-zinc-400" />
          <input
            type="text"
            placeholder="Filter components..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-8 w-44 rounded-xl border border-zinc-800 bg-zinc-950/80 pl-8 pr-3 text-xs text-zinc-200 placeholder-zinc-500 backdrop-blur-md focus:border-indigo-500 focus:outline-none"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-2 text-zinc-400 hover:text-white"
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>

        {/* Flow Animation Toggle */}
        <button
          onClick={() => setAnimationsEnabled(!animationsEnabled)}
          className={`flex items-center gap-1.5 rounded-xl border px-3 py-1.5 text-xs font-semibold backdrop-blur-md transition-all ${
            animationsEnabled
              ? "border-emerald-500/50 bg-emerald-950/40 text-emerald-300"
              : "border-zinc-800 bg-zinc-950/80 text-zinc-400 hover:text-white"
          }`}
          title="Toggle data flow animation"
        >
          <Zap className={`h-3.5 w-3.5 ${animationsEnabled ? "text-emerald-400 animate-pulse" : ""}`} />
          <span>{animationsEnabled ? "Flow: Active" : "Flow: Paused"}</span>
        </button>

        {/* Fullscreen Toggle */}
        <button
          onClick={() => setIsFullscreen(!isFullscreen)}
          className="flex h-8 w-8 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-950/80 text-zinc-400 backdrop-blur-md hover:text-white"
          title="Toggle Fullscreen"
        >
          {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
        </button>
      </div>

      {/* ── React Flow Interactive Canvas or Empty State ── */}
      {nodes.length === 0 ? (
        <div className="flex h-full w-full flex-col items-center justify-center p-8 text-center bg-[#0a0b10]">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl border border-zinc-800 bg-zinc-900/60 text-zinc-500 shadow-xl">
            <Layers className="h-8 w-8 text-indigo-400/60" />
          </div>
          <h3 className="text-base font-bold text-white">No High-Level Design (HLD) Generated Yet</h3>
          <p className="mt-1.5 max-w-md text-xs text-zinc-400 leading-relaxed">
            Enter your project requirements in Step 1 and complete the stakeholder clarification questions to synthesize the interactive visual topology.
          </p>
        </div>
      ) : (
        <ReactFlow
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
          <Background gap={22} size={1.2} color="#27272a" />
          <Controls className="!border-zinc-800 !bg-zinc-950/90 !text-white [&>button]:!border-zinc-800 [&>button]:!bg-zinc-900 [&>button]:!text-zinc-200" />
        </ReactFlow>
      )}

      {/* ── Interactive Component Inspector Drawer (Slide-over) ── */}
      {inspectorOpen && selectedNodeData && (
        <div className="absolute top-0 right-0 z-30 flex h-full w-96 flex-col border-l border-zinc-800 bg-zinc-950/95 p-6 backdrop-blur-xl shadow-2xl animate-in slide-in-from-right duration-200">
          {/* Drawer Header */}
          <div className="flex items-center justify-between pb-4 border-b border-zinc-800">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/20 text-indigo-400">
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
                <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400">
                  {String(selectedNodeData.data?.code || selectedNodeData.type || "Component")}
                </span>
                <h3 className="text-sm font-bold text-white leading-tight">
                  {String(selectedNodeData.data?.label || selectedNodeData.id)}
                </h3>
              </div>
            </div>

            <button
              onClick={() => setInspectorOpen(false)}
              className="rounded-lg p-1 text-zinc-400 hover:bg-zinc-850 hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Drawer Body Specs */}
          <div className="flex-1 overflow-y-auto py-4 space-y-4 text-xs">
            {/* Description */}
            <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/60 p-3.5">
              <span className="text-[11px] font-semibold text-zinc-400">Architecture Role</span>
              <p className="mt-1 text-zinc-200 leading-relaxed">
                {String(
                  selectedNodeData.data?.description ||
                    `${selectedNodeData.data?.label} architectural component in High-Level Design.`
                )}
              </p>
            </div>

            {/* Tech Stack & Protocol */}
            <div className="space-y-2">
              <span className="text-[11px] font-semibold text-zinc-400">Technical Specifications</span>
              <div className="grid grid-cols-2 gap-2">
                <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-2.5">
                  <span className="text-[10px] text-zinc-500">Technology</span>
                  <p className="font-semibold text-zinc-200 truncate">
                    {String(selectedNodeData.data?.tech || selectedNodeData.data?.engine || "Standard Microservice")}
                  </p>
                </div>
                <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-2.5">
                  <span className="text-[10px] text-zinc-500">Protocol / Engine</span>
                  <p className="font-semibold text-zinc-200 truncate">
                    {String(selectedNodeData.data?.protocol || selectedNodeData.data?.schema || "gRPC / HTTPS")}
                  </p>
                </div>
              </div>
            </div>

            {/* Ingress / Egress Topology Connections */}
            <div className="space-y-2">
              <span className="text-[11px] font-semibold text-zinc-400">Topology Connections</span>
              <div className="space-y-1.5">
                {edges
                  .filter((e) => e.source === selectedNodeData.id || e.target === selectedNodeData.id)
                  .map((e) => {
                    const isSource = e.source === selectedNodeData.id;
                    const otherNodeId = isSource ? e.target : e.source;
                    const otherNode = nodes.find((n) => n.id === otherNodeId);
                    return (
                      <div
                        key={e.id}
                        className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900/40 px-3 py-2 text-[11px]"
                      >
                        <span className="text-zinc-400">
                          {isSource ? "Outflow ➔" : "Inflow ⬅"}
                        </span>
                        <span className="font-semibold text-zinc-200">
                          {String(otherNode?.data?.label || otherNodeId)}
                        </span>
                        {Boolean((e.data as Record<string, unknown> | undefined)?.label) ? (
                          <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-[9px] font-mono text-zinc-400">
                            {String((e.data as Record<string, unknown>).label)}
                          </span>
                        ) : null}
                      </div>
                    );
                  })}
              </div>
            </div>
          </div>

          {/* Drawer Footer Actions: Jump to LLD */}
          <div className="pt-4 border-t border-zinc-800 space-y-2">
            <span className="text-[11px] font-semibold text-zinc-400">Inspect Domain LLD</span>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => handleJumpToLld("backend")}
                className="flex items-center justify-center gap-1 rounded-xl border border-zinc-800 bg-zinc-900 py-2 text-xs font-semibold text-zinc-200 hover:border-indigo-500 hover:text-white"
              >
                <span>Backend LLD</span>
                <ArrowRight className="h-3 w-3" />
              </button>
              <button
                onClick={() => handleJumpToLld("database")}
                className="flex items-center justify-center gap-1 rounded-xl border border-zinc-800 bg-zinc-900 py-2 text-xs font-semibold text-zinc-200 hover:border-emerald-500 hover:text-white"
              >
                <span>Database LLD</span>
                <ArrowRight className="h-3 w-3" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
