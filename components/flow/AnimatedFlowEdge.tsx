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
    const strokeColor = (style.stroke as string) || (selected ? "#000000" : "#737373");

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
            markerWidth="5"
            markerHeight="5"
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

        {/* Base Stroke Layer */}
        <BaseEdge
          id={id}
          path={edgePath}
          markerEnd={effectiveMarkerEnd}
          style={{
            ...style,
            stroke: strokeColor,
            strokeWidth: selected ? 2.5 : 1.5,
            strokeDasharray: isAnimated ? "6 6" : undefined,
            animation: isAnimated ? "dashFlow 20s linear infinite" : undefined,
          }}
        />

        {/* Interactive Protocol / Event Label in Pure Monochrome */}
        {label && (
          <EdgeLabelRenderer>
            <div
              style={{
                position: "absolute",
                transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
                pointerEvents: "all",
              }}
              className={`nodrag nopan flex items-center gap-1 rounded-md border border-neutral-300 bg-white px-2 py-0.5 text-[9.5px] font-mono font-bold text-black shadow-xs backdrop-blur-md dark:border-neutral-700 dark:bg-neutral-900 dark:text-white transition-all duration-200 ${
                selected ? "ring-2 ring-black dark:ring-white" : ""
              }`}
            >
              <span className="h-1.5 w-1.5 rounded-full bg-black dark:bg-white" />
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
