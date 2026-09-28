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
} from "lucide-react";

// ── 1. Layer Group Node (Container / Bounding Box) ──
export const LayerGroupNode = memo(({ data }: NodeProps) => {
  const label = String(data?.label || "Architecture Layer");
  const count = typeof data?.count === "number" ? data.count : undefined;

  return (
    <div className="relative h-full w-full rounded-2xl border-2 border-dashed border-neutral-300 bg-neutral-500/[0.02] p-4 backdrop-blur-xs transition-all duration-300 dark:border-neutral-700 dark:bg-neutral-500/[0.02]">
      {/* Top Layer Header */}
      <div className="flex items-center justify-between pb-3">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-black dark:text-white" />
          <span className="font-heading text-xs font-bold uppercase tracking-wider text-black dark:text-white">
            {label}
          </span>
        </div>
        {count !== undefined && (
          <span className="rounded-md border border-neutral-300 bg-neutral-100 px-2.5 py-0.5 text-[10px] font-bold text-black dark:border-neutral-700 dark:bg-neutral-800 dark:text-white shadow-2xs">
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
      className={`group relative flex items-center gap-2.5 rounded-full border px-4 py-2 text-xs font-semibold shadow-xs backdrop-blur-md transition-all duration-150 ${
        selected
          ? "border-black bg-white text-black ring-2 ring-black/40 shadow-md dark:border-white dark:bg-black dark:text-white dark:ring-white/40"
          : "border-neutral-300 bg-white text-black hover:border-black dark:border-neutral-700 dark:bg-black dark:text-white dark:hover:border-white"
      }`}
      style={{ minWidth: 140 }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
      />
      <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-neutral-300 bg-neutral-100 text-black dark:border-neutral-700 dark:bg-neutral-800 dark:text-white">
        <Users className="h-3.5 w-3.5" />
      </div>
      <div className="flex flex-col text-left">
        <span className="font-heading font-bold leading-tight text-black dark:text-white">{label}</span>
        {role && role !== "Stakeholder" && (
          <span className="text-[10px] font-normal text-neutral-500 dark:text-neutral-400">{role}</span>
        )}
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
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
      className={`group relative flex flex-col justify-center rounded-xl border border-neutral-300 bg-white p-3.5 shadow-xs backdrop-blur-md transition-all duration-150 hover:border-black dark:border-neutral-800 dark:bg-neutral-900 dark:hover:border-white ${
        selected ? "ring-2 ring-black/40 border-black dark:ring-white/40 dark:border-white" : ""
      }`}
      style={{ minWidth: 200, minHeight: 70 }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
      />
      <div className="flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-neutral-300 bg-neutral-100 text-black dark:border-neutral-700 dark:bg-neutral-800 dark:text-white">
          <Globe className="h-4 w-4" />
        </div>
        <div className="flex flex-col text-left">
          <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
            Frontend Layer
          </span>
          <span className="font-heading text-xs font-bold text-black dark:text-white">{label}</span>
          <span className="text-[10px] text-neutral-500 dark:text-neutral-400">{tech}</span>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
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
      className={`group relative flex flex-col justify-center rounded-xl border border-neutral-300 bg-white p-3.5 shadow-xs backdrop-blur-md transition-all duration-150 hover:border-black dark:border-neutral-800 dark:bg-neutral-900 dark:hover:border-white ${
        selected ? "ring-2 ring-black/40 border-black dark:ring-white/40 dark:border-white" : ""
      }`}
      style={{ minWidth: 240, minHeight: 75 }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
      />
      <Handle
        type="target"
        position={Position.Left}
        id="gw-left"
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
      />
      <div className="flex items-center gap-2.5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-neutral-300 bg-neutral-100 text-black dark:border-neutral-700 dark:bg-neutral-800 dark:text-white">
          <ShieldCheck className="h-5 w-5" />
        </div>
        <div className="flex flex-col text-left">
          <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
            API & Security Layer
          </span>
          <span className="font-heading text-xs font-bold text-black dark:text-white">{label}</span>
          <span className="text-[10px] text-neutral-500 dark:text-neutral-400">{tech}</span>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
      />
      <Handle
        type="source"
        position={Position.Right}
        id="gw-right"
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
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
      className={`group relative flex flex-col justify-between rounded-xl border border-neutral-300 bg-white p-3.5 shadow-xs backdrop-blur-md transition-all duration-150 hover:border-black dark:border-neutral-800 dark:bg-neutral-900 dark:hover:border-white ${
        selected ? "ring-2 ring-black/40 border-black dark:ring-white/40 dark:border-white" : ""
      }`}
      style={{ minWidth: 190, minHeight: 80 }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
      />
      <Handle
        type="target"
        position={Position.Left}
        id="svc-left"
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
      />

      {/* Header with Service Code Badge */}
      <div className="flex items-center justify-between pb-1.5">
        <span className="rounded-md border border-neutral-300 bg-neutral-100 px-1.5 py-0.5 text-[10px] font-bold text-black dark:border-neutral-700 dark:bg-neutral-800 dark:text-white">
          {code}
        </span>
        <span className="text-[9px] font-semibold text-neutral-500 dark:text-neutral-400">{protocol}</span>
      </div>

      {/* Title */}
      <div className="flex items-start gap-1.5">
        <Server className="mt-0.5 h-3.5 w-3.5 shrink-0 text-black dark:text-white" />
        <span className="font-heading text-xs font-bold leading-tight text-black dark:text-white">{label}</span>
      </div>

      {/* Subtitle / Responsibilities */}
      {tech && (
        <span className="mt-1 line-clamp-1 text-[10px] text-neutral-500 dark:text-neutral-400">{tech}</span>
      )}

      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
      />
      <Handle
        type="source"
        position={Position.Right}
        id="svc-right"
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
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
      className={`group relative flex flex-col justify-center rounded-xl border border-neutral-300 bg-white p-3.5 shadow-xs backdrop-blur-md transition-all duration-150 hover:border-black dark:border-neutral-800 dark:bg-neutral-900 dark:hover:border-white ${
        selected ? "ring-2 ring-black/40 border-black dark:ring-white/40 dark:border-white" : ""
      }`}
      style={{ minWidth: 200, minHeight: 70 }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
      />
      <div className="flex items-center gap-2.5">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-neutral-300 bg-neutral-100 text-black dark:border-neutral-700 dark:bg-neutral-800 dark:text-white">
          <Database className="h-4 w-4" />
        </div>
        <div className="flex flex-col text-left">
          <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
            {engine}
          </span>
          <span className="font-heading text-xs font-bold text-black dark:text-white leading-tight">{label}</span>
          {schema && (
            <span className="font-mono text-[9px] text-neutral-500 dark:text-neutral-400 truncate max-w-[170px]">
              {schema}
            </span>
          )}
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
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
      className={`group relative flex flex-col justify-center rounded-xl border border-neutral-300 bg-white p-3.5 shadow-xs backdrop-blur-md transition-all duration-150 hover:border-black dark:border-neutral-800 dark:bg-neutral-900 dark:hover:border-white ${
        selected ? "ring-2 ring-black/40 border-black dark:ring-white/40 dark:border-white" : ""
      }`}
      style={{ minWidth: 180, minHeight: 70 }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
      />
      <Handle
        type="target"
        position={Position.Left}
        id="cache-left"
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
      />
      <div className="flex items-center gap-2">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-neutral-300 bg-neutral-100 text-black dark:border-neutral-700 dark:bg-neutral-800 dark:text-white">
          <Cpu className="h-4 w-4" />
        </div>
        <div className="flex flex-col text-left">
          <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
            In-Memory Cache
          </span>
          <span className="font-heading text-xs font-bold text-black dark:text-white leading-tight">{label}</span>
          <span className="text-[10px] text-neutral-500 dark:text-neutral-400">{subtitle}</span>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
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
      className={`group relative flex flex-col justify-center rounded-xl border border-neutral-300 bg-white p-3.5 shadow-xs backdrop-blur-md transition-all duration-150 hover:border-black dark:border-neutral-800 dark:bg-neutral-900 dark:hover:border-white ${
        selected ? "ring-2 ring-black/40 border-black dark:ring-white/40 dark:border-white" : ""
      }`}
      style={{ minWidth: 200, minHeight: 75 }}
    >
      <Handle
        type="target"
        position={Position.Left}
        id="q-left"
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
      />
      <div className="flex items-center gap-2.5">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-neutral-300 bg-neutral-100 text-black dark:border-neutral-700 dark:bg-neutral-800 dark:text-white">
          <Radio className="h-4 w-4" />
        </div>
        <div className="flex flex-col text-left">
          <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
            Event Broker
          </span>
          <span className="font-heading text-xs font-bold text-black dark:text-white">{label}</span>
          <span className="text-[10px] text-neutral-500 dark:text-neutral-400">{subtitle}</span>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Right}
        id="q-right"
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
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

  return (
    <div
      className={`group relative flex flex-col justify-center rounded-xl border border-neutral-300 bg-white p-3.5 shadow-xs backdrop-blur-md transition-all duration-150 hover:border-black dark:border-neutral-800 dark:bg-neutral-900 dark:hover:border-white ${
        selected ? "ring-2 ring-black/40 border-black dark:ring-white/40 dark:border-white" : ""
      }`}
      style={{ minWidth: 175, minHeight: 70 }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
      />
      <Handle
        type="target"
        position={Position.Left}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
      />
      <div className="flex items-center gap-2">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-neutral-300 bg-neutral-100 text-black dark:border-neutral-700 dark:bg-neutral-800 dark:text-white">
          <IconComponent className="h-4 w-4" />
        </div>
        <div className="flex flex-col text-left">
          <span className="font-heading text-xs font-bold text-black dark:text-white leading-tight">{label}</span>
          {role && <span className="text-[10px] text-neutral-500 dark:text-neutral-400">{role}</span>}
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-black dark:!border-black dark:!bg-white"
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
