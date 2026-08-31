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
  X,
  Maximize2,
  Minimize2,
  Server,
  Database,
  ShieldCheck,
  Globe,
  Radio,
  ExternalLink,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import { parseLldToReactFlow } from "@/lib/graph-parser";
import { architectureNodeTypes } from "./flow/ArchitectureNodes";
import { architectureEdgeTypes } from "./flow/AnimatedFlowEdge";

interface Props {
  customLldType?: string;
  customLldData?: Record<string, unknown> | null;
}

export default function LLDGraph({ customLldType, customLldData }: Props) {
  const { activeLldType, lldData, openExplain } = useAppStore();

  const type = customLldType || activeLldType || "backend";
  const data = customLldData || lldData[activeLldType as keyof typeof lldData] || null;

  // Parse nodes and edges from custom LLD data or empty
  const parsed = data ? parseLldToReactFlow(type, data) : { nodes: [], edges: [] };

  const [nodes, setNodes, onNodesChange] = useNodesState(parsed.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(parsed.edges);

  // Inspector Drawer state
  const [selectedNodeData, setSelectedNodeData] = useState<Node | null>(null);
  const [inspectorOpen, setInspectorOpen] = useState(false);

  // Search & Filter & Controls
  const [searchQuery, setSearchQuery] = useState("");
  const [animationsEnabled, setAnimationsEnabled] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);

  useEffect(() => {
    const updated = data ? parseLldToReactFlow(type, data) : { nodes: [], edges: [] };
    setNodes(updated.nodes);
    setEdges(updated.edges);
  }, [type, data, setNodes, setEdges]);

  // Click to open inspector
  const onNodeClick: NodeMouseHandler = useCallback((_event, node) => {
    if (node.type === "layerGroup") return;
    setSelectedNodeData(node);
    setInspectorOpen(true);
  }, []);

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

  // Display nodes with search & hover dimming
  const displayNodes = useMemo(() => {
    return nodes.map((n) => {
      if (n.type === "layerGroup") return n;

      let opacity = 1;
      if (hoveredNodeId && connectedNodesSet && !connectedNodesSet.has(n.id)) {
        opacity = 0.25;
      }

      if (searchQuery.trim()) {
        const str = `${n.data?.label || ""} ${n.data?.code || ""} ${n.data?.description || ""} ${n.data?.tech || ""}`.toLowerCase();
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
  }, [nodes, hoveredNodeId, connectedNodesSet, searchQuery]);

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

  return (
    <div className={`relative h-full w-full bg-[#0a0b10] text-white ${isFullscreen ? "fixed inset-0 z-50" : ""}`}>
      {/* ── Top Floating Control Panel ── */}
      <div className="absolute top-4 left-4 z-20 flex flex-wrap items-center gap-2">
        {/* Search Input */}
        <div className="relative flex items-center">
          <Search className="absolute left-2.5 h-3.5 w-3.5 text-zinc-400" />
          <input
            type="text"
            placeholder={`Filter ${type.toUpperCase()} components...`}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-8 w-48 rounded-xl border border-zinc-800 bg-zinc-950/80 pl-8 pr-3 text-xs text-zinc-200 placeholder-zinc-500 backdrop-blur-md focus:border-indigo-500 focus:outline-none"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery("")} className="absolute right-2 text-zinc-400 hover:text-white">
              <X className="h-3 w-3" />
            </button>
          )}
        </div>

        {/* Animation Toggle */}
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

      {/* ── React Flow Canvas or Empty State ── */}
      {nodes.length === 0 ? (
        <div className="flex h-full w-full flex-col items-center justify-center p-8 text-center bg-[#0a0b10]">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl border border-zinc-800 bg-zinc-900/60 text-zinc-500 shadow-xl">
            <Server className="h-8 w-8 text-indigo-400/60" />
          </div>
          <h3 className="text-base font-bold text-white">No {type.toUpperCase()} LLD Generated Yet</h3>
          <p className="mt-1.5 max-w-md text-xs text-zinc-400 leading-relaxed">
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
          <Background gap={22} size={1.2} color="#27272a" />
          <Controls className="!border-zinc-800 !bg-zinc-950/90 !text-white [&>button]:!border-zinc-800 [&>button]:!bg-zinc-900 [&>button]:!text-zinc-200" />
        </ReactFlow>
      )}

      {/* ── Interactive Component Inspector Drawer (Slide-over) ── */}
      {inspectorOpen && selectedNodeData && (
        <div className="absolute top-0 right-0 z-30 flex h-full w-96 flex-col border-l border-zinc-800 bg-zinc-950/95 p-6 backdrop-blur-xl shadow-2xl animate-in slide-in-from-right duration-200">
          {/* Header */}
          <div className="flex items-center justify-between pb-4 border-b border-zinc-800">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/20 text-indigo-400">
                {selectedNodeData.type === "database" ? (
                  <Database className="h-5 w-5" />
                ) : selectedNodeData.type === "gateway" ? (
                  <ShieldCheck className="h-5 w-5" />
                ) : selectedNodeData.type === "frontend" ? (
                  <Globe className="h-5 w-5" />
                ) : (
                  <Server className="h-5 w-5" />
                )}
              </div>
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400">
                  {String(selectedNodeData.data?.code || selectedNodeData.type || type.toUpperCase())}
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

          {/* Body */}
          <div className="flex-1 overflow-y-auto py-4 space-y-4 text-xs">
            <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/60 p-3.5">
              <span className="text-[11px] font-semibold text-zinc-400">Architecture Specification</span>
              <p className="mt-1 text-zinc-200 leading-relaxed">
                {String(
                  selectedNodeData.data?.description ||
                    `${selectedNodeData.data?.label} specification in ${type.toUpperCase()} LLD.`
                )}
              </p>
            </div>

            <div className="space-y-2">
              <span className="text-[11px] font-semibold text-zinc-400">Technical Details</span>
              <div className="grid grid-cols-2 gap-2">
                <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-2.5">
                  <span className="text-[10px] text-zinc-500">Framework / Tech</span>
                  <p className="font-semibold text-zinc-200 truncate">
                    {String(selectedNodeData.data?.tech || selectedNodeData.data?.engine || "Standard")}
                  </p>
                </div>
                <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-2.5">
                  <span className="text-[10px] text-zinc-500">Protocol / Schema</span>
                  <p className="font-semibold text-zinc-200 truncate">
                    {String(selectedNodeData.data?.protocol || selectedNodeData.data?.schema || type.toUpperCase())}
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <span className="text-[11px] font-semibold text-zinc-400">Connected Ingress & Egress</span>
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
                        <span className="text-zinc-400">{isSource ? "Outflow ➔" : "Inflow ⬅"}</span>
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
        </div>
      )}
    </div>
  );
}
