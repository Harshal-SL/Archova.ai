"use client";

import { useCallback, useEffect, useState, useMemo } from "react";
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
    theme,
  } = useAppStore();

  const isDark = theme === "dark";

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
      const strokeColor = isDark
        ? (isConnected && hoveredNodeId !== null ? "#ffffff" : "#737373")
        : (isConnected && hoveredNodeId !== null ? "#000000" : "#525252");

      return {
        ...e,
        animated: animationsEnabled,
        selected: isConnected && hoveredNodeId !== null,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 16,
          height: 16,
          color: strokeColor,
        },
        style: {
          ...e.style,
          opacity: isDimmed ? 0.15 : 1,
          stroke: strokeColor,
          strokeWidth: isConnected && hoveredNodeId !== null ? 2.5 : 1.5,
          transition: "opacity 0.2s ease, stroke 0.2s ease",
        },
      };
    });
  }, [edges, connectedEdgesSet, hoveredNodeId, animationsEnabled, isDark]);

  // Jump to corresponding LLD tab from drawer
  const handleJumpToLld = (type: "backend" | "frontend" | "database" | "security" | "cloud") => {
    setActiveLldType(type);
    setActivePipelineStep(4);
  };

  return (
    <div className={`relative h-full w-full bg-white text-black dark:bg-black dark:text-white ${isFullscreen ? "fixed inset-0 z-50" : ""}`}>
      {/* ── Top Floating Control Panel Monochrome ── */}
      <div className="absolute top-4 left-4 z-20 flex flex-wrap items-center gap-2">
        {/* Layer Filters */}
        <div className="flex items-center gap-1 rounded-lg border border-neutral-200 bg-white/95 p-1 shadow-sm backdrop-blur-md dark:border-neutral-800 dark:bg-neutral-900/95">
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
              className={`rounded-md px-2.5 py-1 text-[11px] font-semibold transition-all duration-150 ${
                selectedLayer === tab.id
                  ? "bg-black text-white dark:bg-white dark:text-black"
                  : "text-neutral-600 hover:text-black hover:bg-neutral-100 dark:text-neutral-400 dark:hover:text-white dark:hover:bg-neutral-800"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search / Filter Input */}
        <div className="relative flex items-center">
          <Search className="absolute left-2.5 h-3.5 w-3.5 text-neutral-500 dark:text-neutral-400" />
          <input
            type="text"
            placeholder="Filter components..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-8 w-44 rounded-lg border border-neutral-300 bg-white/95 pl-8 pr-3 text-xs text-black placeholder:text-neutral-400 backdrop-blur-md focus:border-black focus:outline-none dark:border-neutral-700 dark:bg-neutral-900/95 dark:text-white dark:placeholder:text-neutral-500 dark:focus:border-white"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-2 text-neutral-400 hover:text-black dark:hover:text-white"
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>

        {/* Flow Animation Toggle */}
        <button
          onClick={() => setAnimationsEnabled(!animationsEnabled)}
          className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold backdrop-blur-md transition-all duration-150 ${
            animationsEnabled
              ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black"
              : "border-neutral-300 bg-white text-neutral-700 hover:border-black hover:text-black dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-300 dark:hover:border-white dark:hover:text-white"
          }`}
          title="Toggle data flow animation"
        >
          <Zap className="h-3.5 w-3.5" />
          <span>{animationsEnabled ? "Flow: Active" : "Flow: Paused"}</span>
        </button>

        {/* Fullscreen Toggle */}
        <button
          onClick={() => setIsFullscreen(!isFullscreen)}
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-neutral-300 bg-white text-neutral-700 backdrop-blur-md hover:border-black hover:text-black dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-300 dark:hover:border-white dark:hover:text-white"
          title="Toggle Fullscreen"
        >
          {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
        </button>
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
          <Background gap={24} size={1} color={isDark ? "rgba(255, 255, 255, 0.08)" : "rgba(0, 0, 0, 0.06)"} />
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
                ) : (
                  <Server className="h-5 w-5" />
                )}
              </div>
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                  {String(selectedNodeData.data?.code || selectedNodeData.type || "Component")}
                </span>
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
                    return (
                      <div
                        key={e.id}
                        className="flex items-center justify-between rounded-lg border border-neutral-200 bg-white px-3 py-2 text-[11px] dark:border-neutral-800 dark:bg-neutral-900"
                      >
                        <span className="font-bold text-black dark:text-white">
                          {isSource ? "Outflow ➔" : "Inflow ⬅"}
                        </span>
                        <span className="font-medium text-neutral-800 dark:text-neutral-200">
                          {String(otherNode?.data?.label || otherNodeId)}
                        </span>
                        {Boolean((e.data as Record<string, unknown> | undefined)?.label) ? (
                          <span className="rounded border border-neutral-300 bg-neutral-100 px-1.5 py-0.5 text-[9px] font-mono text-neutral-700 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">
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
          <div className="pt-4 border-t border-neutral-200 dark:border-neutral-800 space-y-2">
            <span className="text-[11px] font-bold text-black dark:text-white uppercase tracking-wider">Inspect Domain LLD</span>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => handleJumpToLld("backend")}
                className="flex items-center justify-center gap-1 rounded-lg bg-black py-2 text-xs font-semibold text-white transition-all hover:bg-neutral-800 dark:bg-white dark:text-black dark:hover:bg-neutral-200"
              >
                <span>Backend LLD</span>
                <ArrowRight className="h-3 w-3" />
              </button>
              <button
                onClick={() => handleJumpToLld("database")}
                className="flex items-center justify-center gap-1 rounded-lg border border-neutral-300 bg-white py-2 text-xs font-semibold text-neutral-800 shadow-xs transition-colors hover:border-black hover:text-black dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-300 dark:hover:border-white dark:hover:text-white"
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
