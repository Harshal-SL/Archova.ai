"use client";

import { useCallback } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  type NodeMouseHandler,
} from "@xyflow/react";
import { useAppStore } from "@/lib/store";
import { hldNodes, hldEdges } from "@/lib/mock-data";

export default function HLDGraph() {
  const { setSelectedNode, setArchView, openExplain } = useAppStore();
  const [nodes, , onNodesChange] = useNodesState(hldNodes);
  const [edges, , onEdgesChange] = useEdgesState(hldEdges);

  const onNodeClick: NodeMouseHandler = useCallback(
    (_event, node) => {
      setSelectedNode(node.id);
      setArchView("lld");
    },
    [setSelectedNode, setArchView]
  );

  return (
    <div className="h-full w-full bg-background dark:bg-background">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        style={{ backgroundColor: "var(--background)" }}
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
