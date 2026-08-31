"use client";

import React, { memo } from "react";
import {
  BaseEdge,
  EdgeLabelRenderer,
  getSmoothStepPath,
  type EdgeProps,
} from "@xyflow/react";

export interface CustomEdgeData {
  label?: string;
  protocol?: string;
  particleColor?: string;
  strokeColor?: string;
  animated?: boolean;
}

export const AnimatedFlowEdge = memo(
  ({
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    style = {},
    markerEnd,
    data,
    selected,
  }: EdgeProps) => {
    const [edgePath, labelX, labelY] = getSmoothStepPath({
      sourceX,
      sourceY,
      sourcePosition,
      targetX,
      targetY,
      targetPosition,
      borderRadius: 12,
    });

    const edgeData = (data || {}) as CustomEdgeData;
    const label = edgeData.label || "";
    const isAnimated = edgeData.animated !== false;
    const strokeColor = selected
      ? "#818cf8"
      : (style.stroke as string) || "#4f46e5";

    const customMarkerId = `arrowhead-${id}`;
    const effectiveMarkerEnd = markerEnd || `url(#${customMarkerId})`;

    return (
      <>
        <defs>
          <marker
            id={customMarkerId}
            viewBox="0 0 10 10"
            refX="6"
            refY="5"
            markerUnits="strokeWidth"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path
              d="M 0 1.5 L 8 5 L 0 8.5 z"
              fill={strokeColor}
              stroke={strokeColor}
              strokeWidth="0.5"
            />
          </marker>
        </defs>

        {/* Base Glow Layer */}
        <BaseEdge
          id={`${id}-glow`}
          path={edgePath}
          style={{
            ...style,
            stroke: strokeColor,
            strokeWidth: selected ? 4 : 2,
            opacity: selected ? 0.8 : 0.35,
            filter: "drop-shadow(0 0 4px rgba(99, 102, 241, 0.4))",
          }}
        />

        {/* Main Edge Path with Directional Arrow */}
        <BaseEdge
          id={id}
          path={edgePath}
          markerEnd={effectiveMarkerEnd}
          style={{
            ...style,
            stroke: strokeColor,
            strokeWidth: selected ? 2.5 : 1.75,
            strokeDasharray: isAnimated ? "6 6" : undefined,
            animation: isAnimated ? "dashFlow 20s linear infinite" : undefined,
          }}
        />

        {/* Optional Interactive Protocol / Event Label */}
        {label && (
          <EdgeLabelRenderer>
            <div
              style={{
                position: "absolute",
                transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
                pointerEvents: "all",
              }}
              className={`nodrag nopan flex items-center gap-1 rounded-md border px-2 py-0.5 text-[9.5px] font-mono font-medium shadow-md backdrop-blur-md transition-all duration-200 ${
                selected
                  ? "border-indigo-400 bg-zinc-950 text-indigo-300 ring-1 ring-indigo-400"
                  : "border-zinc-700/80 bg-zinc-950/90 text-zinc-300 hover:border-zinc-500 hover:text-white"
              }`}
            >
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>{label}</span>
            </div>
          </EdgeLabelRenderer>
        )}
      </>
    );
  }
);

AnimatedFlowEdge.displayName = "AnimatedFlowEdge";

export const architectureEdgeTypes = {
  animatedFlow: AnimatedFlowEdge,
};
