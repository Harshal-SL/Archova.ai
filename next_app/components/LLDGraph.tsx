"use client";

import { useCallback, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MarkerType,
  useNodesState,
  useEdgesState,
  type NodeMouseHandler,
} from "@xyflow/react";
import { useAppStore } from "@/lib/store";
import { lldData } from "@/lib/mock-data";

const DEFAULT_NODE = "frontend";

export default function LLDGraph() {
  const { selectedNode, openExplain } = useAppStore();
  const activeNode = selectedNode ?? DEFAULT_NODE;
  const data = lldData[activeNode] ?? lldData[DEFAULT_NODE];
  const normalizedEdges = useMemo(
    () =>
      data.edges.map((edge) => ({
        ...edge,
        animated: false,
        type: "straight",
        markerEnd: { type: MarkerType.ArrowClosed },
        style: {
          ...edge.style,
          strokeWidth: 2,
        },
      })),
    [data.edges]
  );

  const [nodes, , onNodesChange] = useNodesState(data.nodes);
  const [edges, , onEdgesChange] = useEdgesState(normalizedEdges);

  const onNodeClick: NodeMouseHandler = useCallback(
    (_event, node) => {
      openExplain(node.id);
    },
    [openExplain]
  );

  return (
    <div className="h-full w-full">
      <ReactFlow
        key={activeNode}
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={20} size={1} />
        <Controls />
      </ReactFlow>
    </div>
  );
}
