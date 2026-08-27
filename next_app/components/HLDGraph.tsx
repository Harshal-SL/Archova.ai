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
import { hldNodes as mockHldNodes, hldEdges as mockHldEdges } from "@/lib/mock-data";

// ─── Custom Monochrome Node ──────────────────────────────────────────
const MonochromeNode = memo(({ data, selected }: NodeProps) => (
  <div
    className={`px-4 py-3 rounded-xl border font-semibold text-sm transition-all flex flex-col items-center justify-center min-w-[130px] max-w-[200px] text-center cursor-pointer ${
      selected
        ? "bg-white text-black border-white scale-[1.04]"
        : "bg-black text-white border-[#555555] hover:bg-white hover:text-black hover:border-white"
    }`}
  >
    <Handle type="target" position={Position.Top} className="!opacity-0 !bg-transparent !border-none" />
    <span className="font-bold">{data.label as string}</span>
    {data.description ? (
      <span className={`mt-1 text-[11px] font-normal leading-tight ${selected ? "text-black/60" : "text-white/40"}`}>
        {data.description as string}
      </span>
    ) : null}
    <Handle type="source" position={Position.Bottom} className="!opacity-0 !bg-transparent !border-none" />
  </div>
));
MonochromeNode.displayName = "MonochromeNode";

const nodeTypes = { default: MonochromeNode };

// ─── Skeleton Loader ────────────────────────────────────────────────
function SkeletonLoader() {
  return (
    <div className="h-full w-full bg-[#0F0F0F] flex items-center justify-center">
      <div className="flex flex-col items-center gap-4 animate-pulse">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-12 rounded-xl bg-[#1A1A1A] border border-[#2A2A2A]"
            style={{ width: `${180 - i * 20}px` }}
          />
        ))}
      </div>
    </div>
  );
}

// ─── HLD Graph ──────────────────────────────────────────────────────
export default function HLDGraph() {
  const { setSelectedNode, setArchView, sessions, activeSessionId, isGenerating } = useAppStore();

  const activeSession = sessions.find((s) => s.id === activeSessionId);
  const archData = activeSession?.architectureData;

  // Use AI-returned data or fall back to cleaned mock
  const rawNodes = archData?.hldNodes ?? mockHldNodes.map((n) => ({ ...n, style: {}, type: "default" as const }));
  const rawEdges = (archData?.hldEdges ?? mockHldEdges).map((e) => ({
    ...e,
    style: { stroke: "#AAAAAA", strokeWidth: 1.5, strokeDasharray: "6,4" },
    animated: true,
  }));

  const cleanNodes = rawNodes.map((n) => ({ ...n, style: {}, type: "default" as const }));

  const [nodes, , onNodesChange] = useNodesState(cleanNodes);
  const [edges, , onEdgesChange] = useEdgesState(rawEdges);

  const onNodeClick: NodeMouseHandler = useCallback(
    (_event, node) => {
      setSelectedNode(node.id);
      setArchView("lld");
    },
    [setSelectedNode, setArchView]
  );

  if (isGenerating && !archData) return <SkeletonLoader />;

  if (!archData && (!rawNodes || rawNodes.length === 0)) {
    return (
      <div className="h-full flex items-center justify-center text-[#555555] text-sm font-mono">
        Your design will appear here…
      </div>
    );
  }

  return (
    <div className="h-full w-full bg-[#0F0F0F]">
      <ReactFlow
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
