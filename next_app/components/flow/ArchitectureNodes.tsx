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
  Lock,
  Layers,
  Cloud,
  CheckCircle2,
  HardDrive,
  Cpu,
} from "lucide-react";

// ── 1. Layer Group Node (Container / Bounding Box) ──
export const LayerGroupNode = memo(({ data }: NodeProps) => {
  const label = String(data?.label || "Architecture Layer");
  const count = typeof data?.count === "number" ? data.count : undefined;

  return (
    <div className="relative h-full w-full rounded-2xl border border-zinc-700/50 bg-zinc-950/40 p-4 backdrop-blur-xs transition-all duration-300 hover:border-zinc-500/60 dark:border-zinc-800/80 dark:bg-zinc-950/60">
      {/* Top Layer Header */}
      <div className="flex items-center justify-between pb-3">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-zinc-400" />
          <span className="text-xs font-bold uppercase tracking-wider text-zinc-300 dark:text-zinc-200">
            {label}
          </span>
        </div>
        {count !== undefined && (
          <span className="rounded-full bg-zinc-800/80 px-2 py-0.5 text-[10px] font-semibold text-zinc-400">
            {count} Components
          </span>
        )}
      </div>
    </div>
  );
});
LayerGroupNode.displayName = "LayerGroupNode";

// ── 2. User / Actor Node ──
export const ActorNode = memo(({ data, selected }: NodeProps) => {
  const label = String(data?.label || "User Actor");
  const role = String(data?.role || data?.description || "Stakeholder");

  return (
    <div
      className={`group relative flex items-center gap-2.5 rounded-full border px-4 py-2 text-xs font-semibold shadow-lg backdrop-blur-md transition-all duration-200 ${
        selected
          ? "border-indigo-400 bg-indigo-950/90 text-white shadow-indigo-500/25 ring-2 ring-indigo-400/50"
          : "border-zinc-700/80 bg-zinc-900/90 text-zinc-100 hover:border-zinc-500 hover:bg-zinc-850"
      }`}
      style={{ minWidth: 140 }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2 !w-2 !border-zinc-900 !bg-indigo-400"
      />
      <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-zinc-800 text-indigo-400">
        <Users className="h-3.5 w-3.5" />
      </div>
      <div className="flex flex-col text-left">
        <span className="font-semibold leading-tight text-white">{label}</span>
        {role && role !== "Stakeholder" && (
          <span className="text-[10px] font-normal text-zinc-400">{role}</span>
        )}
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2 !w-2 !border-zinc-900 !bg-indigo-400"
      />
    </div>
  );
});
ActorNode.displayName = "ActorNode";

// ── 3. Frontend Client Node ──
export const FrontendNode = memo(({ data, selected }: NodeProps) => {
  const label = String(data?.label || "Web Application");
  const tech = String(data?.tech || data?.description || "React / Next.js");

  return (
    <div
      className={`group relative flex flex-col justify-center rounded-xl border p-3.5 shadow-xl backdrop-blur-md transition-all duration-200 ${
        selected
          ? "border-pink-500 bg-zinc-900/95 shadow-pink-500/20 ring-2 ring-pink-500/40"
          : "border-zinc-700/80 bg-zinc-900/90 hover:border-zinc-500 hover:shadow-zinc-700/20"
      }`}
      style={{ minWidth: 200, minHeight: 70 }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2 !w-2 !border-zinc-900 !bg-pink-400"
      />
      <div className="flex items-center gap-2">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-pink-500/20 text-pink-400">
          <Globe className="h-4 w-4" />
        </div>
        <div className="flex flex-col text-left">
          <span className="text-[11px] font-bold uppercase tracking-wider text-pink-400">
            Frontend Layer
          </span>
          <span className="text-xs font-bold text-white">{label}</span>
          <span className="text-[10px] text-zinc-400">{tech}</span>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2 !w-2 !border-zinc-900 !bg-pink-400"
      />
    </div>
  );
});
FrontendNode.displayName = "FrontendNode";

// ── 4. API Gateway / Ingress Node ──
export const GatewayNode = memo(({ data, selected }: NodeProps) => {
  const label = String(data?.label || "API Gateway / Ingress");
  const tech = String(data?.tech || "NGINX · TLS 1.3 · Rate Limiting · RBAC");

  return (
    <div
      className={`group relative flex flex-col justify-center rounded-xl border p-3.5 shadow-xl backdrop-blur-md transition-all duration-200 ${
        selected
          ? "border-blue-400 bg-zinc-900/95 shadow-blue-500/20 ring-2 ring-blue-400/40"
          : "border-zinc-700/80 bg-zinc-900/90 hover:border-blue-500/60"
      }`}
      style={{ minWidth: 240, minHeight: 75 }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2 !w-2 !border-zinc-900 !bg-blue-400"
      />
      <Handle
        type="target"
        position={Position.Left}
        id="gw-left"
        className="!h-2 !w-2 !border-zinc-900 !bg-blue-400"
      />
      <div className="flex items-center gap-2.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/20 text-blue-400">
          <ShieldCheck className="h-5 w-5" />
        </div>
        <div className="flex flex-col text-left">
          <span className="text-[10px] font-bold uppercase tracking-wider text-blue-400">
            API & Security Layer
          </span>
          <span className="text-xs font-bold text-white">{label}</span>
          <span className="text-[10px] text-zinc-400">{tech}</span>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2 !w-2 !border-zinc-900 !bg-blue-400"
      />
      <Handle
        type="source"
        position={Position.Right}
        id="gw-right"
        className="!h-2 !w-2 !border-zinc-900 !bg-blue-400"
      />
    </div>
  );
});
GatewayNode.displayName = "GatewayNode";

// ── 5. Modular Microservice Node ──
export const ServiceNode = memo(({ data, selected }: NodeProps) => {
  const label = String(data?.label || "Service");
  const code = String(data?.code || "SVC");
  const tech = String(data?.tech || data?.description || "");
  const protocol = String(data?.protocol || "REST / gRPC");

  return (
    <div
      className={`group relative flex flex-col justify-between rounded-xl border p-3 shadow-lg backdrop-blur-md transition-all duration-200 ${
        selected
          ? "border-indigo-400 bg-zinc-900/95 shadow-indigo-500/25 ring-2 ring-indigo-400/40"
          : "border-zinc-700/80 bg-zinc-900/90 hover:border-indigo-500/70 hover:shadow-indigo-500/10"
      }`}
      style={{ minWidth: 190, minHeight: 80 }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2 !w-2 !border-zinc-900 !bg-indigo-400"
      />
      <Handle
        type="target"
        position={Position.Left}
        id="svc-left"
        className="!h-2 !w-2 !border-zinc-900 !bg-indigo-400"
      />

      {/* Header with Service Code Badge */}
      <div className="flex items-center justify-between pb-1.5">
        <span className="rounded bg-indigo-500/20 px-1.5 py-0.5 text-[10px] font-bold text-indigo-400">
          {code}
        </span>
        <span className="text-[9px] font-medium text-zinc-500">{protocol}</span>
      </div>

      {/* Title */}
      <div className="flex items-start gap-1.5">
        <Server className="mt-0.5 h-3.5 w-3.5 shrink-0 text-indigo-400" />
        <span className="text-xs font-bold leading-tight text-white">{label}</span>
      </div>

      {/* Subtitle / Responsibilities */}
      {tech && (
        <span className="mt-1 line-clamp-1 text-[10px] text-zinc-400">{tech}</span>
      )}

      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2 !w-2 !border-zinc-900 !bg-indigo-400"
      />
      <Handle
        type="source"
        position={Position.Right}
        id="svc-right"
        className="!h-2 !w-2 !border-zinc-900 !bg-indigo-400"
      />
    </div>
  );
});
ServiceNode.displayName = "ServiceNode";

// ── 6. Database / Storage Node ──
export const DatabaseNode = memo(({ data, selected }: NodeProps) => {
  const label = String(data?.label || "Database");
  const engine = String(data?.engine || "PostgreSQL");
  const schema = String(data?.schema || data?.description || "");

  return (
    <div
      className={`group relative flex flex-col justify-center rounded-xl border p-3 shadow-lg backdrop-blur-md transition-all duration-200 ${
        selected
          ? "border-emerald-400 bg-zinc-900/95 shadow-emerald-500/20 ring-2 ring-emerald-400/40"
          : "border-zinc-700/80 bg-zinc-900/90 hover:border-emerald-500/70"
      }`}
      style={{ minWidth: 200, minHeight: 70 }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2 !w-2 !border-zinc-900 !bg-emerald-400"
      />
      <div className="flex items-center gap-2.5">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400">
          <Database className="h-4 w-4" />
        </div>
        <div className="flex flex-col text-left">
          <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">
            {engine}
          </span>
          <span className="text-xs font-bold text-white leading-tight">{label}</span>
          {schema && (
            <span className="font-mono text-[9px] text-zinc-400 truncate max-w-[170px]">
              {schema}
            </span>
          )}
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2 !w-2 !border-zinc-900 !bg-emerald-400"
      />
    </div>
  );
});
DatabaseNode.displayName = "DatabaseNode";

// ── 7. Cache & Redis Node ──
export const CacheNode = memo(({ data, selected }: NodeProps) => {
  const label = String(data?.label || "Redis Cluster");
  const subtitle = String(data?.subtitle || data?.description || "Cache · Tokens · PubSub");

  return (
    <div
      className={`group relative flex flex-col justify-center rounded-xl border p-3 shadow-lg backdrop-blur-md transition-all duration-200 ${
        selected
          ? "border-amber-400 bg-zinc-900/95 shadow-amber-500/20 ring-2 ring-amber-400/40"
          : "border-zinc-700/80 bg-zinc-900/90 hover:border-amber-500/70"
      }`}
      style={{ minWidth: 180, minHeight: 70 }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2 !w-2 !border-zinc-900 !bg-amber-400"
      />
      <Handle
        type="target"
        position={Position.Left}
        id="cache-left"
        className="!h-2 !w-2 !border-zinc-900 !bg-amber-400"
      />
      <div className="flex items-center gap-2">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-amber-500/20 text-amber-400">
          <Cpu className="h-4 w-4" />
        </div>
        <div className="flex flex-col text-left">
          <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400">
            In-Memory Cache
          </span>
          <span className="text-xs font-bold text-white leading-tight">{label}</span>
          <span className="text-[10px] text-zinc-400">{subtitle}</span>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2 !w-2 !border-zinc-900 !bg-amber-400"
      />
    </div>
  );
});
CacheNode.displayName = "CacheNode";

// ── 8. Message Queue / Event Bus Node ──
export const QueueNode = memo(({ data, selected }: NodeProps) => {
  const label = String(data?.label || "RabbitMQ");
  const subtitle = String(data?.subtitle || data?.description || "Event Messaging · DLQ · Retry x3");

  return (
    <div
      className={`group relative flex flex-col justify-center rounded-xl border p-3.5 shadow-lg backdrop-blur-md transition-all duration-200 ${
        selected
          ? "border-yellow-400 bg-zinc-900/95 shadow-yellow-500/20 ring-2 ring-yellow-400/40"
          : "border-zinc-700/80 bg-zinc-900/90 hover:border-yellow-500/70"
      }`}
      style={{ minWidth: 200, minHeight: 75 }}
    >
      <Handle
        type="target"
        position={Position.Left}
        id="q-left"
        className="!h-2 !w-2 !border-zinc-900 !bg-yellow-400"
      />
      <div className="flex items-center gap-2.5">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-yellow-500/20 text-yellow-400">
          <Radio className="h-4 w-4" />
        </div>
        <div className="flex flex-col text-left">
          <span className="text-[10px] font-bold uppercase tracking-wider text-yellow-400">
            Event Broker
          </span>
          <span className="text-xs font-bold text-white">{label}</span>
          <span className="text-[10px] text-zinc-400">{subtitle}</span>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Right}
        id="q-right"
        className="!h-2 !w-2 !border-zinc-900 !bg-yellow-400"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2 !w-2 !border-zinc-900 !bg-yellow-400"
      />
    </div>
  );
});
QueueNode.displayName = "QueueNode";

// ── 9. DevOps & Observability Node ──
export const DevOpsNode = memo(({ data, selected }: NodeProps) => {
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

  const accentColor =
    category === "cicd"
      ? "text-cyan-400 bg-cyan-500/20 border-cyan-400"
      : category === "k8s"
      ? "text-blue-400 bg-blue-500/20 border-blue-400"
      : "text-purple-400 bg-purple-500/20 border-purple-400";

  return (
    <div
      className={`group relative flex flex-col justify-center rounded-xl border p-3 shadow-lg backdrop-blur-md transition-all duration-200 ${
        selected
          ? `border-cyan-400 bg-zinc-900/95 ring-2 ring-cyan-400/40`
          : "border-zinc-700/80 bg-zinc-900/90 hover:border-zinc-500"
      }`}
      style={{ minWidth: 175, minHeight: 70 }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2 !w-2 !border-zinc-900 !bg-cyan-400"
      />
      <Handle
        type="target"
        position={Position.Left}
        className="!h-2 !w-2 !border-zinc-900 !bg-cyan-400"
      />
      <div className="flex items-center gap-2">
        <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${accentColor}`}>
          <IconComponent className="h-4 w-4" />
        </div>
        <div className="flex flex-col text-left">
          <span className="text-xs font-bold text-white leading-tight">{label}</span>
          {role && <span className="text-[10px] text-zinc-400">{role}</span>}
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2 !w-2 !border-zinc-900 !bg-cyan-400"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!h-2 !w-2 !border-zinc-900 !bg-cyan-400"
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
