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
  const { activeLldType, lldData, theme } = useAppStore();
  const isDark = theme === "dark";

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

  const displayNodes = useMemo(() => {
    return nodes.map((n) => {
      if (n.type === "layerGroup") return n;

      let opacity = 1;
      if (hoveredNodeId && connectedNodesSet && !connectedNodesSet.has(n.id)) {
        opacity = 0.25;
      }

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
          transition: "opacity 0.2s ease",
        },
      };
    });
  }, [nodes, hoveredNodeId, connectedNodesSet, searchQuery]);

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

  return (
    <div className={`relative h-full w-full bg-white text-black dark:bg-black dark:text-white ${isFullscreen ? "fixed inset-0 z-50" : ""}`}>
      {/* ── Top Floating Control Panel ── */}
      <div className="absolute top-4 left-4 z-20 flex flex-wrap items-center gap-2">
        {/* Search Input */}
        <div className="relative flex items-center">
          <Search className="absolute left-2.5 h-3.5 w-3.5 text-neutral-500 dark:text-neutral-400" />
          <input
            type="text"
            placeholder={`Filter ${type.toUpperCase()} components...`}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-8 w-48 rounded-lg border border-neutral-300 bg-white/95 pl-8 pr-3 text-xs text-black placeholder:text-neutral-400 backdrop-blur-md focus:border-black focus:outline-none dark:border-neutral-700 dark:bg-neutral-900/95 dark:text-white dark:placeholder:text-neutral-500 dark:focus:border-white shadow-xs"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery("")} className="absolute right-2 text-neutral-400 hover:text-black dark:hover:text-white">
              <X className="h-3 w-3" />
            </button>
          )}
        </div>

        {/* Animation Toggle */}
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
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-neutral-300 bg-white text-neutral-700 backdrop-blur-md hover:border-black hover:text-black dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-300 dark:hover:border-white dark:hover:text-white shadow-xs"
          title="Toggle Fullscreen"
        >
          {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
        </button>
      </div>

      {/* ── React Flow Canvas or Empty State ── */}
      {nodes.length === 0 ? (
        <div className="flex h-full w-full flex-col items-center justify-center p-8 text-center bg-white text-black dark:bg-black dark:text-white">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-xl border border-neutral-300 bg-neutral-100 text-black dark:border-neutral-700 dark:bg-neutral-900 dark:text-white">
            <Server className="h-8 w-8" />
          </div>
          <h3 className="font-heading text-lg font-bold text-black dark:text-white">No {type.toUpperCase()} LLD Generated Yet</h3>
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
          <Background gap={24} size={1} color={isDark ? "rgba(255, 255, 255, 0.08)" : "rgba(0, 0, 0, 0.06)"} />
          <Controls className="!border-neutral-300 !bg-white !text-black [&>button]:!border-neutral-200 [&>button]:!bg-white [&>button]:!text-neutral-800 [&>button:hover]:!bg-neutral-100 [&>button:hover]:!text-black dark:!border-neutral-700 dark:!bg-neutral-900 dark:!text-white dark:[&>button]:!border-neutral-800 dark:[&>button]:!bg-neutral-900 dark:[&>button]:!text-neutral-200 dark:[&>button:hover]:!bg-neutral-800 dark:[&>button:hover]:!text-white" />
        </ReactFlow>
      )}

      {/* ── Interactive Component Inspector Drawer ── */}
      {inspectorOpen && selectedNodeData && (
        <div className="absolute top-0 right-0 z-30 flex h-full w-96 flex-col border-l border-neutral-300 bg-white/98 p-6 backdrop-blur-xl shadow-2xl animate-in slide-in-from-right duration-200 dark:border-neutral-800 dark:bg-black/98">
          <div className="flex items-center justify-between pb-4 border-b border-neutral-200 dark:border-neutral-800">
            <div className="flex items-center gap-2.5">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-black text-white dark:bg-white dark:text-black">
                {type === "database" ? (
                  <Database className="h-5 w-5" />
                ) : type === "security" ? (
                  <ShieldCheck className="h-5 w-5" />
                ) : type === "frontend" ? (
                  <Globe className="h-5 w-5" />
                ) : (
                  <Server className="h-5 w-5" />
                )}
              </div>
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                  {type.toUpperCase()} LLD
                </span>
                <h3 className="font-heading text-sm font-bold text-black dark:text-white leading-tight">
                  {String(selectedNodeData.data?.label || selectedNodeData.id)}
                </h3>
              </div>
            </div>

            <button
              onClick={() => setInspectorOpen(false)}
              className="rounded-lg p-1 text-neutral-400 hover:bg-neutral-100 hover:text-black dark:hover:bg-neutral-900 dark:hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto py-4 space-y-4 text-xs">
            <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3.5 dark:border-neutral-800 dark:bg-neutral-900">
              <span className="text-[11px] font-bold text-black dark:text-white">LLD Specification</span>
              <p className="mt-1 text-neutral-700 dark:text-neutral-300 leading-relaxed font-normal">
                {String(
                  selectedNodeData.data?.description ||
                    `${selectedNodeData.data?.label} detailed architectural component in ${type.toUpperCase()} LLD.`
                )}
              </p>
            </div>

            <div className="rounded-lg border border-neutral-200 bg-white p-3.5 dark:border-neutral-800 dark:bg-neutral-900 font-mono text-[11px]">
              <span className="text-neutral-500 block mb-1 font-sans font-semibold text-[10px] uppercase tracking-wider">
                Raw Component Node
              </span>
              <pre className="whitespace-pre-wrap overflow-x-auto text-neutral-800 dark:text-neutral-200">
                {JSON.stringify(selectedNodeData.data, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
