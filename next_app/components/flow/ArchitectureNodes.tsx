"use client";

import React, { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import {
  Users,
  Globe,
  ShieldCheck,
  Server,
  Database,
  Radio,
  GitBranch,
  Activity,
  Boxes,
  Layers,
  Cloud,
  Cpu,
  ArrowRight,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import { getComponentTheme, getLayerGroupTheme } from "@/lib/flow-colors";

// Helper for card background in both light & dark themes
const getCardBg = (isDark: boolean, bgDark: string, bgLight: string) =>
  isDark
    ? `linear-gradient(135deg, rgba(18, 18, 24, 0.96), ${bgDark})`
    : `linear-gradient(135deg, #ffffff 42%, ${bgLight})`;

// Helper for card elevation shadow with rich colored glow
const getCardShadow = (
  isDark: boolean,
  selected: boolean | undefined,
  glow: string,
  lightColor: string
) =>
  selected
    ? isDark
      ? `0 0 24px -2px ${glow}`
      : `0 0 0 2.5px ${lightColor}, 0 8px 24px -4px ${glow}`
    : isDark
    ? `0 4px 16px -4px ${glow}`
    : `0 4px 16px -2px rgba(15, 23, 42, 0.12), 0 0 0 1px ${lightColor}45`;

// ── 1. Layer Group Node (Container / Bounding Box) ──
export const LayerGroupNode = memo(({ id, data }: NodeProps) => {
  const { theme: appTheme, jumpToLld } = useAppStore();
  const isDark = appTheme !== "light";
  const label = String(data?.label || "Architecture Layer");
  const count = typeof data?.count === "number" ? data.count : undefined;

  const groupTheme = getLayerGroupTheme(label, id);
  const accentColor = isDark ? groupTheme.darkColor : groupTheme.lightColor;

  const lowerLabel = `${label} ${id}`.toLowerCase();
  const IconComponent =
    lowerLabel.includes("frontend")
      ? Globe
      : lowerLabel.includes("backend") || lowerLabel.includes("service")
      ? Server
      : lowerLabel.includes("database") || lowerLabel.includes("persistence") || lowerLabel.includes("cache")
      ? Database
      : lowerLabel.includes("deployment") || lowerLabel.includes("devops") || lowerLabel.includes("observability") || lowerLabel.includes("cloud")
      ? Cloud
      : Layers;

  const isLldInternalGroup =
    id.startsWith("bgroup-") ||
    id.startsWith("fgroup-") ||
    id.startsWith("dbgroup-") ||
    id.startsWith("cgroup-") ||
    id.startsWith("secgroup-") ||
    Boolean(data?.hideExplore);

  const divisionLld = isLldInternalGroup
    ? null
    : lowerLabel.includes("frontend")
    ? "frontend"
    : lowerLabel.includes("backend") || lowerLabel.includes("service")
    ? "backend"
    : lowerLabel.includes("database") || lowerLabel.includes("persistence")
    ? "database"
    : lowerLabel.includes("deployment") || lowerLabel.includes("cloud") || lowerLabel.includes("devops")
    ? "cloud"
    : lowerLabel.includes("security")
    ? "security"
    : null;

  return (
    <div
      className="relative h-full w-full rounded-2xl border-2 border-dashed p-4 backdrop-blur-xs transition-all duration-300"
      style={{
        borderColor: isDark ? `${groupTheme.darkColor}44` : `${groupTheme.lightColor}99`,
        backgroundColor: isDark ? `${groupTheme.primary}08` : `${groupTheme.lightColor}12`,
        boxShadow: isDark ? "none" : `0 4px 20px -4px ${groupTheme.lightColor}20`,
      }}
    >
      {/* Top Layer Header */}
      <div className="flex items-center justify-between pb-3">
        <div className="flex items-center gap-2">
          <div
            className="flex h-7 w-7 items-center justify-center rounded-lg border shadow-xs"
            style={{
              backgroundColor: isDark ? groupTheme.badgeBgDark : groupTheme.badgeBgLight,
              borderColor: isDark ? groupTheme.badgeBorderDark : groupTheme.badgeBorderLight,
              color: isDark ? accentColor : groupTheme.badgeTextLight,
            }}
          >
            <IconComponent className="h-4 w-4" />
          </div>
          <span
            className="font-heading text-xs font-black uppercase tracking-wider"
            style={{ color: accentColor }}
          >
            {label}
          </span>
          {Boolean(data?.subtitle) && (
            <span className="hidden md:inline-block text-[10px] font-semibold text-neutral-600 dark:text-neutral-400">
              · {String(data.subtitle)}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {count !== undefined && (
            <span
              className="rounded-md border px-2.5 py-0.5 text-[10px] font-extrabold shadow-xs"
              style={{
                backgroundColor: isDark ? groupTheme.badgeBgDark : "#ffffff",
                borderColor: isDark ? groupTheme.badgeBorderDark : groupTheme.lightColor,
                color: accentColor,
              }}
            >
              {count} Components
            </span>
          )}
          {divisionLld && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                jumpToLld(divisionLld as any);
              }}
              className="pointer-events-auto flex items-center gap-1 rounded-md border px-2.5 py-0.5 text-[10px] font-extrabold shadow-xs transition-all hover:scale-105 cursor-pointer"
              style={{
                backgroundColor: isDark ? groupTheme.badgeBgDark : groupTheme.lightColor,
                borderColor: isDark ? groupTheme.badgeBorderDark : groupTheme.lightColor,
                color: isDark ? accentColor : "#ffffff",
              }}
              title={`Display ${divisionLld.toUpperCase()} LLD Design`}
            >
              <span>Explore {divisionLld.toUpperCase()} LLD</span>
              <ArrowRight className="h-3 w-3" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
});
LayerGroupNode.displayName = "LayerGroupNode";

// ── 2. User / Actor Node ──
export const ActorNode = memo(({ id, data, selected }: NodeProps) => {
  const { theme: appTheme } = useAppStore();
  const isDark = appTheme !== "light";
  const label = String(data?.label || "User Actor");
  const role = String(data?.role || data?.description || "Stakeholder");

  const theme = getComponentTheme(id, label, "actor", data?.color as string);
  const accentColor = isDark ? theme.darkColor : theme.lightColor;
  const borderColor = selected ? theme.primary : isDark ? theme.borderDark : theme.borderLight;
  const bgColor = isDark
    ? `linear-gradient(135deg, rgba(20, 20, 26, 0.95), ${theme.bgDark})`
    : `linear-gradient(135deg, #ffffff 40%, ${theme.bgLight})`;

  return (
    <div
      className={`group relative flex items-center gap-2.5 rounded-full border-2 px-4 py-2 text-xs font-semibold backdrop-blur-md transition-all duration-200 cursor-pointer hover:scale-[1.02] ${
        selected ? "ring-2 ring-offset-1" : ""
      }`}
      style={{
        minWidth: 150,
        borderColor,
        background: bgColor,
        boxShadow: selected
          ? isDark
            ? `0 0 20px -2px ${theme.glow}`
            : `0 0 0 2px ${theme.lightColor}, 0 6px 18px -2px ${theme.glow}`
          : isDark
          ? `0 4px 14px -4px ${theme.glow}`
          : `0 3px 12px -2px rgba(15, 23, 42, 0.12), 0 0 0 1px ${theme.lightColor}45`,
      }}
    >
      <Handle
        type="target"
        position={Position.Top}
        id="act-top"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
      <div
        className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border shadow-xs transition-all"
        style={{
          backgroundColor: isDark ? theme.badgeBgDark : theme.badgeBgLight,
          borderColor: isDark ? theme.badgeBorderDark : theme.badgeBorderLight,
          color: isDark ? accentColor : theme.badgeTextLight,
          boxShadow: isDark ? `0 0 8px -2px ${theme.glow}` : `0 2px 6px -1px ${theme.lightColor}55`,
        }}
      >
        <Users className="h-3.5 w-3.5" />
      </div>
      <div className="flex flex-col text-left">
        <span className="font-heading font-extrabold leading-tight text-slate-900 dark:text-neutral-50">{label}</span>
        {role && role !== "Stakeholder" && (
          <span className="text-[10px] font-semibold text-neutral-600 dark:text-neutral-400">{role}</span>
        )}
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        id="act-bottom"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
    </div>
  );
});
ActorNode.displayName = "ActorNode";

// ── 3. Frontend Client Node ──
export const FrontendNode = memo(({ id, data, selected }: NodeProps) => {
  const { theme: appTheme } = useAppStore();
  const isDark = appTheme !== "light";
  const label = String(data?.label || "Web Application");
  const tech = String(data?.tech || data?.description || "React / Next.js");

  const theme = getComponentTheme(id, label, "frontend", data?.color as string);
  const accentColor = isDark ? theme.darkColor : theme.lightColor;
  const borderColor = selected ? theme.primary : isDark ? theme.borderDark : theme.borderLight;
  const bgColor = getCardBg(isDark, theme.bgDark, theme.bgLight);

  return (
    <div
      className={`group relative flex flex-col justify-center rounded-xl border-2 p-3.5 backdrop-blur-md transition-all duration-200 cursor-pointer hover:scale-[1.02] overflow-hidden ${
        selected ? "ring-2 ring-offset-1" : ""
      }`}
      style={{
        minWidth: 280,
        minHeight: 84,
        borderColor,
        background: bgColor,
        boxShadow: getCardShadow(isDark, selected, theme.glow, theme.lightColor),
      }}
    >
      {/* Heavy Colored Top Accent Strip */}
      <div
        className="absolute top-0 left-0 right-0 h-1.5 rounded-t-[10px]"
        style={{ backgroundColor: accentColor }}
      />

      <Handle
        type="target"
        position={Position.Top}
        id="fe-top"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
      <Handle
        type="target"
        position={Position.Left}
        id="fe-left"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
      <div className="flex items-center gap-2.5">
        <div
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border shadow-xs transition-all"
          style={{
            backgroundColor: isDark ? theme.badgeBgDark : theme.badgeBgLight,
            borderColor: isDark ? theme.badgeBorderDark : theme.badgeBorderLight,
            color: isDark ? accentColor : theme.badgeTextLight,
            boxShadow: isDark ? `0 0 10px -2px ${theme.glow}` : `0 2px 8px -1px ${theme.lightColor}55`,
          }}
        >
          <Globe className="h-4 w-4" />
        </div>
        <div className="flex flex-col text-left">
          <span
            className="text-[9.5px] font-black uppercase tracking-wider"
            style={{ color: accentColor }}
          >
            Frontend Layer
          </span>
          <span className="font-heading text-xs font-bold text-slate-900 dark:text-neutral-50">{label}</span>
          <span className="text-[10px] text-neutral-600 dark:text-neutral-400 truncate max-w-[220px] font-medium">{tech}</span>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        id="fe-bottom"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
      <Handle
        type="source"
        position={Position.Right}
        id="fe-right"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
    </div>
  );
});
FrontendNode.displayName = "FrontendNode";

// ── 4. API Gateway / Ingress Node ──
export const GatewayNode = memo(({ id, data, selected }: NodeProps) => {
  const { theme: appTheme } = useAppStore();
  const isDark = appTheme !== "light";
  const label = String(data?.label || "API Gateway / Ingress");
  const tech = String(data?.tech || "NGINX · TLS 1.3 · Rate Limiting · RBAC");

  const theme = getComponentTheme(id, label, "gateway", data?.color as string);
  const accentColor = isDark ? theme.darkColor : theme.lightColor;
  const borderColor = selected ? theme.primary : isDark ? theme.borderDark : theme.borderLight;
  const bgColor = getCardBg(isDark, theme.bgDark, theme.bgLight);

  return (
    <div
      className={`group relative flex flex-col justify-center rounded-xl border-2 p-3.5 backdrop-blur-md transition-all duration-200 cursor-pointer hover:scale-[1.02] overflow-hidden ${
        selected ? "ring-2 ring-offset-1" : ""
      }`}
      style={{
        minWidth: 280,
        minHeight: 80,
        borderColor,
        background: bgColor,
        boxShadow: getCardShadow(isDark, selected, theme.glow, theme.lightColor),
      }}
    >
      {/* Heavy Colored Top Accent Strip */}
      <div
        className="absolute top-0 left-0 right-0 h-1.5 rounded-t-[10px]"
        style={{ backgroundColor: accentColor }}
      />

      <Handle
        type="target"
        position={Position.Top}
        id="gw-top"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
      <Handle
        type="target"
        position={Position.Left}
        id="gw-left"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
      <div className="flex items-center gap-2.5">
        <div
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border shadow-xs transition-all"
          style={{
            backgroundColor: isDark ? theme.badgeBgDark : theme.badgeBgLight,
            borderColor: isDark ? theme.badgeBorderDark : theme.badgeBorderLight,
            color: isDark ? accentColor : theme.badgeTextLight,
            boxShadow: isDark ? `0 0 10px -2px ${theme.glow}` : `0 2px 8px -1px ${theme.lightColor}55`,
          }}
        >
          <ShieldCheck className="h-5 w-5" />
        </div>
        <div className="flex flex-col text-left">
          <span
            className="text-[9.5px] font-black uppercase tracking-wider"
            style={{ color: accentColor }}
          >
            API & Security Layer
          </span>
          <span className="font-heading text-xs font-bold text-slate-900 dark:text-neutral-50">{label}</span>
          <span className="text-[10px] text-neutral-600 dark:text-neutral-400 truncate max-w-[240px] font-medium">{tech}</span>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        id="gw-bottom"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
      <Handle
        type="source"
        position={Position.Right}
        id="gw-right"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
    </div>
  );
});
GatewayNode.displayName = "GatewayNode";

// ── 5. Modular Microservice Node ──
export const ServiceNode = memo(({ id, data, selected }: NodeProps) => {
  const { theme: appTheme } = useAppStore();
  const isDark = appTheme !== "light";
  const label = String(data?.label || "Service");
  const code = String(data?.code || "SVC");
  const tech = String(data?.tech || data?.description || "");
  const protocol = String(data?.protocol || "REST / gRPC");

  const theme = getComponentTheme(id, label, "service", data?.color as string);
  const accentColor = isDark ? theme.darkColor : theme.lightColor;
  const borderColor = selected ? theme.primary : isDark ? theme.borderDark : theme.borderLight;
  const bgColor = getCardBg(isDark, theme.bgDark, theme.bgLight);

  return (
    <div
      className={`group relative flex flex-col justify-between rounded-xl border-2 p-3.5 backdrop-blur-md transition-all duration-200 cursor-pointer hover:scale-[1.02] overflow-hidden ${
        selected ? "ring-2 ring-offset-1" : ""
      }`}
      style={{
        minWidth: 280,
        minHeight: 88,
        borderColor,
        background: bgColor,
        boxShadow: getCardShadow(isDark, selected, theme.glow, theme.lightColor),
      }}
    >
      {/* Heavy Colored Top Accent Strip */}
      <div
        className="absolute top-0 left-0 right-0 h-1.5 rounded-t-[10px]"
        style={{ backgroundColor: accentColor }}
      />

      <Handle
        type="target"
        position={Position.Top}
        id="svc-top"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
      <Handle
        type="target"
        position={Position.Left}
        id="svc-left"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />

      {/* Header with Service Code Badge */}
      <div className="flex items-center justify-between pb-1.5 pt-0.5">
        <span
          className="rounded-md border px-2 py-0.5 text-[10px] font-black tracking-tight shadow-xs"
          style={{
            backgroundColor: isDark ? theme.badgeBgDark : theme.badgeBgLight,
            borderColor: isDark ? theme.badgeBorderDark : theme.badgeBorderLight,
            color: isDark ? accentColor : theme.badgeTextLight,
          }}
        >
          {code}
        </span>
        <span
          className="text-[9px] font-extrabold uppercase tracking-wide"
          style={{ color: accentColor }}
        >
          {protocol}
        </span>
      </div>

      {/* Title */}
      <div className="flex items-start gap-1.5">
        <div
          className="flex h-5 w-5 shrink-0 items-center justify-center rounded-md border shadow-2xs mt-0.5"
          style={{
            backgroundColor: isDark ? theme.badgeBgDark : theme.badgeBgLight,
            borderColor: isDark ? theme.badgeBorderDark : theme.badgeBorderLight,
            color: isDark ? accentColor : theme.badgeTextLight,
          }}
        >
          <Server className="h-3 w-3" />
        </div>
        <span className="font-heading text-xs font-bold leading-tight text-slate-900 dark:text-neutral-50">{label}</span>
      </div>

      {/* Subtitle / Responsibilities */}
      {tech && (
        <span className="mt-1 line-clamp-1 text-[10px] text-neutral-600 dark:text-neutral-400 font-medium">{tech}</span>
      )}

      <Handle
        type="source"
        position={Position.Bottom}
        id="svc-bottom"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
      <Handle
        type="source"
        position={Position.Right}
        id="svc-right"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
    </div>
  );
});
ServiceNode.displayName = "ServiceNode";

// ── 6. Database / Storage Node ──
export const DatabaseNode = memo(({ id, data, selected }: NodeProps) => {
  const { theme: appTheme } = useAppStore();
  const isDark = appTheme !== "light";
  const label = String(data?.label || "Database");
  const engine = String(data?.engine || "PostgreSQL");
  const schema = String(data?.schema || data?.description || "");

  const theme = getComponentTheme(id, label, "database", data?.color as string);
  const accentColor = isDark ? theme.darkColor : theme.lightColor;
  const borderColor = selected ? theme.primary : isDark ? theme.borderDark : theme.borderLight;
  const bgColor = getCardBg(isDark, theme.bgDark, theme.bgLight);

  return (
    <div
      className={`group relative flex flex-col justify-center rounded-xl border-2 p-3.5 backdrop-blur-md transition-all duration-200 cursor-pointer hover:scale-[1.02] overflow-hidden ${
        selected ? "ring-2 ring-offset-1" : ""
      }`}
      style={{
        minWidth: 280,
        minHeight: 84,
        borderColor,
        background: bgColor,
        boxShadow: getCardShadow(isDark, selected, theme.glow, theme.lightColor),
      }}
    >
      {/* Heavy Colored Top Accent Strip */}
      <div
        className="absolute top-0 left-0 right-0 h-1.5 rounded-t-[10px]"
        style={{ backgroundColor: accentColor }}
      />

      <Handle
        type="target"
        position={Position.Top}
        id="db-top"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
      <Handle
        type="target"
        position={Position.Left}
        id="db-left"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
      <div className="flex items-center gap-2.5">
        <div
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border shadow-xs transition-all"
          style={{
            backgroundColor: isDark ? theme.badgeBgDark : theme.badgeBgLight,
            borderColor: isDark ? theme.badgeBorderDark : theme.badgeBorderLight,
            color: isDark ? accentColor : theme.badgeTextLight,
            boxShadow: isDark ? `0 0 10px -2px ${theme.glow}` : `0 2px 8px -1px ${theme.lightColor}55`,
          }}
        >
          <Database className="h-4 w-4" />
        </div>
        <div className="flex flex-col text-left">
          <span
            className="text-[9.5px] font-black uppercase tracking-wider"
            style={{ color: accentColor }}
          >
            {engine}
          </span>
          <span className="font-heading text-xs font-bold text-slate-900 dark:text-neutral-50 leading-tight">{label}</span>
          {schema && (
            <span className="font-mono text-[9px] text-neutral-600 dark:text-neutral-400 truncate max-w-[210px] font-semibold">
              {schema}
            </span>
          )}
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        id="db-bottom"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
      <Handle
        type="source"
        position={Position.Right}
        id="db-right"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
    </div>
  );
});
DatabaseNode.displayName = "DatabaseNode";

// ── 7. Cache & Redis Node ──
export const CacheNode = memo(({ id, data, selected }: NodeProps) => {
  const { theme: appTheme } = useAppStore();
  const isDark = appTheme !== "light";
  const label = String(data?.label || "Redis Cluster");
  const subtitle = String(data?.subtitle || data?.description || "Cache · Tokens · PubSub");

  const theme = getComponentTheme(id, label, "cache", data?.color as string);
  const accentColor = isDark ? theme.darkColor : theme.lightColor;
  const borderColor = selected ? theme.primary : isDark ? theme.borderDark : theme.borderLight;
  const bgColor = getCardBg(isDark, theme.bgDark, theme.bgLight);

  return (
    <div
      className={`group relative flex flex-col justify-center rounded-xl border-2 p-3.5 backdrop-blur-md transition-all duration-200 cursor-pointer hover:scale-[1.02] overflow-hidden ${
        selected ? "ring-2 ring-offset-1" : ""
      }`}
      style={{
        minWidth: 230,
        minHeight: 78,
        borderColor,
        background: bgColor,
        boxShadow: getCardShadow(isDark, selected, theme.glow, theme.lightColor),
      }}
    >
      {/* Heavy Colored Top Accent Strip */}
      <div
        className="absolute top-0 left-0 right-0 h-1.5 rounded-t-[10px]"
        style={{ backgroundColor: accentColor }}
      />

      <Handle
        type="target"
        position={Position.Top}
        id="cache-top"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
      <Handle
        type="target"
        position={Position.Left}
        id="cache-left"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
      <div className="flex items-center gap-2">
        <div
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border shadow-xs transition-all"
          style={{
            backgroundColor: isDark ? theme.badgeBgDark : theme.badgeBgLight,
            borderColor: isDark ? theme.badgeBorderDark : theme.badgeBorderLight,
            color: isDark ? accentColor : theme.badgeTextLight,
            boxShadow: isDark ? `0 0 10px -2px ${theme.glow}` : `0 2px 8px -1px ${theme.lightColor}55`,
          }}
        >
          <Cpu className="h-4 w-4" />
        </div>
        <div className="flex flex-col text-left">
          <span
            className="text-[9.5px] font-black uppercase tracking-wider"
            style={{ color: accentColor }}
          >
            In-Memory Cache
          </span>
          <span className="font-heading text-xs font-bold text-slate-900 dark:text-neutral-50 leading-tight">{label}</span>
          <span className="text-[10px] text-neutral-600 dark:text-neutral-400 truncate max-w-[190px] font-medium">{subtitle}</span>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        id="cache-bottom"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
      <Handle
        type="source"
        position={Position.Right}
        id="cache-right"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
    </div>
  );
});
CacheNode.displayName = "CacheNode";

// ── 8. Message Queue / Event Bus Node ──
export const QueueNode = memo(({ id, data, selected }: NodeProps) => {
  const { theme: appTheme } = useAppStore();
  const isDark = appTheme !== "light";
  const label = String(data?.label || "RabbitMQ");
  const subtitle = String(data?.subtitle || data?.description || "Event Messaging · DLQ · Retry x3");

  const theme = getComponentTheme(id, label, "queue", data?.color as string);
  const accentColor = isDark ? theme.darkColor : theme.lightColor;
  const borderColor = selected ? theme.primary : isDark ? theme.borderDark : theme.borderLight;
  const bgColor = getCardBg(isDark, theme.bgDark, theme.bgLight);

  return (
    <div
      className={`group relative flex flex-col justify-center rounded-xl border-2 p-3.5 backdrop-blur-md transition-all duration-200 cursor-pointer hover:scale-[1.02] overflow-hidden ${
        selected ? "ring-2 ring-offset-1" : ""
      }`}
      style={{
        minWidth: 240,
        minHeight: 80,
        borderColor,
        background: bgColor,
        boxShadow: getCardShadow(isDark, selected, theme.glow, theme.lightColor),
      }}
    >
      {/* Heavy Colored Top Accent Strip */}
      <div
        className="absolute top-0 left-0 right-0 h-1.5 rounded-t-[10px]"
        style={{ backgroundColor: accentColor }}
      />

      <Handle
        type="target"
        position={Position.Top}
        id="q-top"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
      <Handle
        type="target"
        position={Position.Left}
        id="q-left"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
      <div className="flex items-center gap-2.5">
        <div
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border shadow-xs transition-all"
          style={{
            backgroundColor: isDark ? theme.badgeBgDark : theme.badgeBgLight,
            borderColor: isDark ? theme.badgeBorderDark : theme.badgeBorderLight,
            color: isDark ? accentColor : theme.badgeTextLight,
            boxShadow: isDark ? `0 0 10px -2px ${theme.glow}` : `0 2px 8px -1px ${theme.lightColor}55`,
          }}
        >
          <Radio className="h-4 w-4" />
        </div>
        <div className="flex flex-col text-left">
          <span
            className="text-[9.5px] font-black uppercase tracking-wider"
            style={{ color: accentColor }}
          >
            Event Broker
          </span>
          <span className="font-heading text-xs font-bold text-slate-900 dark:text-neutral-50 leading-tight">{label}</span>
          <span className="text-[10px] text-neutral-600 dark:text-neutral-400 truncate max-w-[200px] font-medium">{subtitle}</span>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Right}
        id="q-right"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="q-bottom"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
    </div>
  );
});
QueueNode.displayName = "QueueNode";

// ── 9. DevOps & Observability Node ──
export const DevOpsNode = memo(({ id, data, selected }: NodeProps) => {
  const { theme: appTheme } = useAppStore();
  const isDark = appTheme !== "light";
  const label = String(data?.label || "DevOps Tool");
  const role = String(data?.role || data?.description || "");
  const category = String(data?.category || "devops");

  const IconComponent =
    category === "cicd"
      ? GitBranch
      : category === "k8s"
      ? Cloud
      : category === "monitoring"
      ? Activity
      : Boxes;

  const theme = getComponentTheme(id, label, category, data?.color as string);
  const accentColor = isDark ? theme.darkColor : theme.lightColor;
  const borderColor = selected ? theme.primary : isDark ? theme.borderDark : theme.borderLight;
  const bgColor = getCardBg(isDark, theme.bgDark, theme.bgLight);

  return (
    <div
      className={`group relative flex flex-col justify-center rounded-xl border-2 p-3.5 backdrop-blur-md transition-all duration-200 cursor-pointer hover:scale-[1.02] overflow-hidden ${
        selected ? "ring-2 ring-offset-1" : ""
      }`}
      style={{
        minWidth: 245,
        minHeight: 78,
        borderColor,
        background: bgColor,
        boxShadow: getCardShadow(isDark, selected, theme.glow, theme.lightColor),
      }}
    >
      {/* Heavy Colored Top Accent Strip */}
      <div
        className="absolute top-0 left-0 right-0 h-1.5 rounded-t-[10px]"
        style={{ backgroundColor: accentColor }}
      />

      <Handle
        type="target"
        position={Position.Top}
        id="dev-top"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
      <Handle
        type="target"
        position={Position.Left}
        id="dev-left"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
      <div className="flex items-center gap-2">
        <div
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border shadow-xs transition-all"
          style={{
            backgroundColor: isDark ? theme.badgeBgDark : theme.badgeBgLight,
            borderColor: isDark ? theme.badgeBorderDark : theme.badgeBorderLight,
            color: isDark ? accentColor : theme.badgeTextLight,
            boxShadow: isDark ? `0 0 10px -2px ${theme.glow}` : `0 2px 8px -1px ${theme.lightColor}55`,
          }}
        >
          <IconComponent className="h-4 w-4" />
        </div>
        <div className="flex flex-col text-left">
          <span
            className="text-[9.5px] font-black uppercase tracking-wider"
            style={{ color: accentColor }}
          >
            {category.toUpperCase()}
          </span>
          <span className="font-heading text-xs font-bold leading-tight text-slate-900 dark:text-neutral-50">{label}</span>
          {role && (
            <span className="text-[10px] text-neutral-600 dark:text-neutral-400 truncate max-w-[195px] font-medium">{role}</span>
          )}
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        id="dev-bottom"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
      <Handle
        type="source"
        position={Position.Right}
        id="dev-right"
        className="!h-2.5 !w-2.5 !border-2 transition-transform duration-150 hover:scale-125"
        style={{
          backgroundColor: accentColor,
          borderColor: isDark ? "#000000" : "#ffffff",
          boxShadow: `0 0 6px ${accentColor}`,
        }}
      />
    </div>
  );
});
DevOpsNode.displayName = "DevOpsNode";

// Export nodeTypes map for ReactFlow
export const architectureNodeTypes = {
  layerGroup: LayerGroupNode,
  actor: ActorNode,
  frontend: FrontendNode,
  gateway: GatewayNode,
  service: ServiceNode,
  database: DatabaseNode,
  cache: CacheNode,
  queue: QueueNode,
  devops: DevOpsNode,
};
