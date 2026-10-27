"use client";

import React, { memo } from "react";
import {
  BaseEdge,
  EdgeLabelRenderer,
  getSmoothStepPath,
  type EdgeProps,
} from "@xyflow/react";
import { getEdgeTheme } from "@/lib/flow-colors";

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
    source,
    target,
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
    animated,
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
    const isAnimated = typeof animated === "boolean" ? animated : edgeData.animated !== false;

    // Resolve the connection color - identical to the originating component!
    const theme = getEdgeTheme(source, target, edgeData.strokeColor || (style.stroke as string));
    const strokeColor = (style.stroke as string) || edgeData.strokeColor || theme.primary;

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

        {/* Base Stroke Layer with component-matching color */}
        <BaseEdge
          id={id}
          path={edgePath}
          markerEnd={effectiveMarkerEnd}
          style={{
            ...style,
            stroke: strokeColor,
            strokeWidth: selected ? 3.4 : (style.strokeWidth || 2.4),
            strokeDasharray: isAnimated ? "6 6" : "none",
            animation: isAnimated ? "dashFlow 1.8s linear infinite" : "none",
            filter: selected ? `drop-shadow(0 0 6px ${strokeColor})` : undefined,
          }}
        />

        {/* Interactive Protocol / Event Label colored with component theme */}
        {label && (
          <EdgeLabelRenderer>
            <div
              style={{
                position: "absolute",
                transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
                pointerEvents: "all",
                borderColor: strokeColor,
                borderWidth: 1.2,
                boxShadow: `0 2px 8px -2px ${strokeColor}44`,
                zIndex: 20,
              }}
              className={`nodrag nopan flex items-center gap-1.5 rounded-md border bg-white/95 px-2 py-0.5 text-[9px] font-mono font-bold shadow-xs backdrop-blur-md dark:bg-neutral-950/95 transition-all duration-150 select-none ${
                selected ? "ring-2 ring-offset-1 scale-105" : ""
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full shrink-0 ${isAnimated ? "animate-pulse" : "opacity-40"}`}
                style={{
                  backgroundColor: strokeColor,
                  boxShadow: isAnimated ? `0 0 5px ${strokeColor}` : "none",
                }}
              />
              <span className="truncate max-w-[160px] font-bold tracking-tight" style={{ color: strokeColor }}>
                {label}
              </span>
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
