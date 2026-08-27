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
import { hldNodes as fallbackHldNodes, hldEdges as fallbackHldEdges } from "@/lib/mock-data";

export default function HLDGraph() {
  const {
    hldNodes: dynamicNodes,
    hldEdges: dynamicEdges,
    setSelectedNode,
    setActivePipelineStep,
    setActiveLldType,
    openExplain,
  } = useAppStore();

  const initialNodes = dynamicNodes && dynamicNodes.length > 0 ? dynamicNodes : fallbackHldNodes;
  const initialEdges = dynamicEdges && dynamicEdges.length > 0 ? dynamicEdges : fallbackHldEdges;

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Sync state when dynamic nodes/edges from backend are updated
  useEffect(() => {
    if (dynamicNodes && dynamicNodes.length > 0) {
      setNodes(dynamicNodes);
      setEdges(dynamicEdges || []);
    }
  }, [dynamicNodes, dynamicEdges, setNodes, setEdges]);

  const onNodeClick: NodeMouseHandler = useCallback(
    (_event, node) => {
      setSelectedNode(node.id);
      const label = String(node.data?.label || node.id);
      const description = String(node.data?.description || "");

      // Open component explanation / LLD
      openExplain(
        node.id,
        label,
        description || `${label} architecture component in High-Level Design.`
      );

      // If matches one of the 5 LLD types, auto switch tab
      const str = label.toLowerCase();
      if (str.includes("back") || str.includes("api") || str.includes("service")) {
        setActiveLldType("backend");
      } else if (str.includes("front") || str.includes("client") || str.includes("ui")) {
        setActiveLldType("frontend");
      } else if (str.includes("data") || str.includes("db") || str.includes("sql") || str.includes("redis")) {
        setActiveLldType("database");
      } else if (str.includes("sec") || str.includes("auth") || str.includes("jwt")) {
        setActiveLldType("security");
      } else if (str.includes("cloud") || str.includes("aws") || str.includes("infra") || str.includes("k8s")) {
        setActiveLldType("cloud");
      }
    },
    [setSelectedNode, openExplain, setActiveLldType]
  );

  return (
    <div className="h-full w-full bg-white dark:bg-gray-950">
      <ReactFlow
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
