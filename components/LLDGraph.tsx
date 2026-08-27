"use client";

import { useCallback, useEffect } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  type NodeMouseHandler,
} from "@xyflow/react";
import { useAppStore } from "@/lib/store";
import { parseLldToReactFlow } from "@/lib/graph-parser";
import { lldData as fallbackLldData } from "@/lib/mock-data";

interface Props {
  customLldType?: string;
  customLldData?: Record<string, unknown> | null;
}

export default function LLDGraph({ customLldType, customLldData }: Props) {
  const {
    activeLldType,
    lldData,
    openExplain,
  } = useAppStore();

  const type = customLldType || activeLldType || "backend";
  const data = customLldData || lldData[activeLldType as keyof typeof lldData];

  // Parse nodes and edges from custom LLD data or fallback
  const parsed = data
    ? parseLldToReactFlow(type, data)
    : fallbackLldData[type] || fallbackLldData["frontend"] || { nodes: [], edges: [] };

  const [nodes, setNodes, onNodesChange] = useNodesState(parsed.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(parsed.edges);

  useEffect(() => {
    const updated = data
      ? parseLldToReactFlow(type, data)
      : fallbackLldData[type] || fallbackLldData["frontend"] || { nodes: [], edges: [] };
    setNodes(updated.nodes);
    setEdges(updated.edges);
  }, [type, data, setNodes, setEdges]);

  const onNodeClick: NodeMouseHandler = useCallback(
    (_event, node) => {
      const label = String(node.data?.label || node.id);
      const details =
        typeof node.data?.details === "object" && node.data?.details !== null
          ? JSON.stringify(node.data.details, null, 2)
          : String(node.data?.details || `${label} component in ${type.toUpperCase()} LLD`);

      openExplain(node.id, label, details);
    },
    [openExplain, type]
  );

  return (
    <div className="h-full w-full bg-white dark:bg-gray-950">
      <ReactFlow
        key={`${type}-${nodes.length}`}
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        fitView
        fitViewOptions={{ padding: 0.25 }}
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={18} size={1} />
        <Controls />
      </ReactFlow>
    </div>
  );
}
