"use client";

import { memo, useCallback } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
  type NodeMouseHandler,
  type NodeProps,
} from "@xyflow/react";
import { useAppStore } from "@/lib/store";
import { lldData as mockLldData } from "@/lib/mock-data";

const DEFAULT_NODE = "frontend";

// ─── Custom LLD Node ────────────────────────────────────────────────
const MonochromeLLDNode = memo(({ data, selected }: NodeProps) => (
  <div
    className={`px-4 py-3 rounded-lg border font-mono text-xs transition-all flex flex-col min-w-[140px] max-w-[220px] items-start cursor-pointer ${
      selected
        ? "bg-white text-black border-white scale-[1.04]"
        : "bg-[#111111] text-white border-[#333333] hover:bg-white hover:text-black hover:border-white"
    }`}
  >
    <Handle type="target" position={Position.Top} className="!opacity-0 !bg-transparent !border-none" />
    <span className={`mb-1 text-[10px] uppercase tracking-wider ${selected ? "opacity-50" : "opacity-40"}`}>
      component
    </span>
    <span className="font-bold text-sm">{data.label as string}</span>
    {data.details ? (
      <span className={`mt-1.5 text-[11px] leading-tight ${selected ? "text-black/60" : "text-white/40"}`}>
        {data.details as string}
      </span>
    ) : null}
    <Handle type="source" position={Position.Bottom} className="!opacity-0 !bg-transparent !border-none" />
  </div>
));
MonochromeLLDNode.displayName = "MonochromeLLDNode";

const nodeTypes = { default: MonochromeLLDNode };

export default function LLDGraph() {
  const { selectedNode, openExplain, sessions, activeSessionId } = useAppStore();
  const activeNode = selectedNode ?? DEFAULT_NODE;

  const activeSession = sessions.find((s) => s.id === activeSessionId);
  const archData = activeSession?.architectureData;

  // Use AI-returned LLD map or fall back to mock
  const lldEntry =
    archData?.lldMap?.[activeNode] ??
    mockLldData[activeNode] ??
    mockLldData[DEFAULT_NODE];

  const cleanNodes = lldEntry.nodes.map((n) => ({ ...n, style: {}, type: "default" as const }));
  const cleanEdges = lldEntry.edges.map((e) => ({
    ...e,
    style: { stroke: "#AAAAAA", strokeWidth: 1.5, strokeDasharray: "6,4" },
    animated: true,
  }));

  const [nodes, , onNodesChange] = useNodesState(cleanNodes);
  const [edges, , onEdgesChange] = useEdgesState(cleanEdges);

  const onNodeClick: NodeMouseHandler = useCallback(
    (_event, node) => openExplain(node.id),
    [openExplain]
  );

  return (
    <div className="h-full w-full bg-[#0F0F0F]">
      <ReactFlow
        key={activeNode}
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        proOptions={{ hideAttribution: true }}
        colorMode="dark"
      >
        <Background gap={20} size={1} color="#222222" />
        <Controls showInteractive={false} className="opacity-40" />
      </ReactFlow>
    </div>
  );
}
