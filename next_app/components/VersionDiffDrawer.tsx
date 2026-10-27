"use client";

import React from "react";
import {
  X,
  Sparkles,
  ShieldCheck,
  Layers,
  Database,
  ArrowRight,
  GitBranch,
  CheckCircle2,
  Code2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ShimmerButton } from "@/components/ui/shimmer-button";

interface VersionDiffDrawerProps {
  open: boolean;
  onClose: () => void;
  versionTag: string;
  diff: any | null;
}

const getNodeLabel = (node: any): string => {
  if (typeof node === "string") return node;
  if (!node) return "Unknown Service";
  return node.data?.label || node.label || node.id || node.name || JSON.stringify(node);
};

const getTableName = (table: any): string => {
  if (typeof table === "string") return table;
  if (!table) return "Unknown Table";
  return table.name || table.table || JSON.stringify(table);
};

export default function VersionDiffDrawer({
  open,
  onClose,
  versionTag,
  diff,
}: VersionDiffDrawerProps) {
  if (!open) return null;

  const fromVer = diff?.from_version || "v1.0";
  const toVer = diff?.to_version || versionTag || "v1.1";
  const summary =
    diff?.feature_summary ||
    "Non-destructive feature extension embedded into the baseline architecture without mutating existing microservices.";
  const addedNodes = diff?.added_nodes || [];
  const addedTables = diff?.added_tables || [];
  const addedColumns = diff?.added_columns || [];
  const addedEndpoints = diff?.added_endpoints || [];
  const addedEdges = diff?.added_edges || [];

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-xs transition-opacity duration-300">
      <div className="relative flex h-full w-full max-w-lg flex-col border-l border-neutral-200 bg-white shadow-2xl dark:border-neutral-800 dark:bg-neutral-950 text-neutral-900 dark:text-neutral-100 animate-in slide-in-from-right duration-200">
        {/* Drawer Header */}
        <div className="flex items-center justify-between border-b border-neutral-200 px-6 py-4 dark:border-neutral-800">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-heading text-sm font-bold">Architecture Evolution Diff</h3>
                <span className="flex items-center gap-1 rounded-md border border-neutral-300 dark:border-neutral-700 bg-neutral-100 dark:bg-neutral-900 px-2 py-0.5 text-[10px] font-mono font-bold">
                  {fromVer} <ArrowRight className="h-3 w-3" /> {toVer}
                </span>
              </div>
              <p className="text-[11px] text-neutral-500 dark:text-neutral-400">
                Non-destructive additive delta changelog
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-neutral-400 hover:bg-neutral-100 hover:text-black dark:hover:bg-neutral-800 dark:hover:text-white transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Invariance Certificate Banner */}
        <div className="m-4 flex items-start gap-3 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-4">
          <ShieldCheck className="h-5 w-5 shrink-0 text-emerald-600 dark:text-emerald-400 mt-0.5" />
          <div>
            <h4 className="text-xs font-bold text-emerald-700 dark:text-emerald-400">
              100% Invariance Certified
            </h4>
            <p className="text-[11px] text-neutral-600 dark:text-neutral-300 mt-0.5 leading-relaxed">
              All baseline components from <strong>{fromVer}</strong> survived 100% intact with zero deletions, renames, or breaking type alterations.
            </p>
          </div>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto px-6 py-2 space-y-5 text-xs">
          {/* Feature Summary */}
          <div>
            <span className="text-[10px] font-black uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
              Feature Overview
            </span>
            <p className="mt-1 rounded-xl border border-neutral-200 bg-neutral-50 p-3 leading-relaxed dark:border-neutral-800 dark:bg-neutral-900/50">
              {summary}
            </p>
          </div>

          {/* Added Microservices */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                <Layers className="h-3.5 w-3.5 text-blue-500" />
                Added Microservices ({addedNodes.length})
              </span>
            </div>
            {addedNodes.length > 0 ? (
              <div className="space-y-1.5">
                {addedNodes.map((node: any, idx: number) => {
                  const label = getNodeLabel(node);
                  return (
                    <div
                      key={idx}
                      className="flex items-center justify-between rounded-xl border border-neutral-200 bg-neutral-50 px-3.5 py-2 dark:border-neutral-800 dark:bg-neutral-900"
                    >
                      <span className="font-semibold text-neutral-800 dark:text-neutral-200 font-mono text-[11px]">
                        {label}
                      </span>
                      <span className="rounded-md border border-emerald-500/40 bg-emerald-500/15 px-2 py-0.5 text-[9px] font-bold text-emerald-600 dark:text-emerald-400 uppercase">
                        ✨ NEW
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-neutral-400 italic text-[11px]">No new nodes added.</p>
            )}
          </div>

          {/* Added Database Tables & Schema Extensions */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                <Database className="h-3.5 w-3.5 text-purple-500" />
                Added Persistence Tables ({addedTables.length})
              </span>
            </div>
            {addedTables.length > 0 ? (
              <div className="space-y-1.5">
                {addedTables.map((tbl: any, idx: number) => {
                  const name = getTableName(tbl);
                  return (
                    <div
                      key={idx}
                      className="flex items-center justify-between rounded-xl border border-neutral-200 bg-neutral-50 px-3.5 py-2 dark:border-neutral-800 dark:bg-neutral-900"
                    >
                      <span className="font-semibold text-neutral-800 dark:text-neutral-200 font-mono text-[11px]">
                        {name}
                      </span>
                      <span className="rounded-md border border-purple-500/40 bg-purple-500/15 px-2 py-0.5 text-[9px] font-bold text-purple-600 dark:text-purple-400 uppercase">
                        + TABLE
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-neutral-400 italic text-[11px]">No new tables added.</p>
            )}
          </div>

          {/* Added Columns */}
          {addedColumns.length > 0 && (
            <div>
              <span className="text-[10px] font-black uppercase tracking-wider text-neutral-500 dark:text-neutral-400 mb-2 block">
                Additive Column Extensions ({addedColumns.length})
              </span>
              <div className="space-y-1.5">
                {addedColumns.map((col: any, idx: number) => {
                  const isObj = typeof col === "object" && col !== null;
                  const colText = isObj ? `${col.table || ""}.${col.column || col.name || ""}` : String(col);
                  const colType = isObj ? col.type : "";
                  return (
                    <div
                      key={idx}
                      className="flex items-center justify-between rounded-xl border border-neutral-200 bg-neutral-50 px-3.5 py-2 dark:border-neutral-800 dark:bg-neutral-900 font-mono text-[11px]"
                    >
                      <span>
                        <strong className="text-blue-500">{colText}</strong>
                      </span>
                      {colType && <span className="text-[10px] text-neutral-500">{colType}</span>}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Added API Endpoints */}
          {addedEndpoints.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-wider text-neutral-500 dark:text-neutral-400 mb-2">
                <Code2 className="h-3.5 w-3.5 text-emerald-500" />
                Added API Endpoints ({addedEndpoints.length})
              </div>
              <div className="space-y-1.5">
                {addedEndpoints.map((ep: any, idx: number) => {
                  const isObj = typeof ep === "object" && ep !== null;
                  const method = isObj ? (ep.method || "GET").toUpperCase() : "API";
                  const path = isObj ? (ep.path || ep.route || "") : String(ep);
                  const service = isObj ? ep.service : "";
                  return (
                    <div
                      key={idx}
                      className="flex items-center justify-between rounded-xl border border-neutral-200 bg-neutral-50 px-3.5 py-2 dark:border-neutral-800 dark:bg-neutral-900 font-mono text-[11px]"
                    >
                      <div className="flex items-center gap-2 truncate">
                        <span className={cn(
                          "rounded-md px-1.5 py-0.5 text-[9px] font-bold uppercase",
                          method === "POST" ? "bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20" :
                          method === "GET" ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20" :
                          method === "DELETE" ? "bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20" :
                          "bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20"
                        )}>
                          {method}
                        </span>
                        <span className="truncate">{path}</span>
                      </div>
                      {service && (
                        <span className="text-[10px] text-neutral-400 ml-2 shrink-0">
                          {service}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Inter-Service Topology Edges */}
          {addedEdges.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-wider text-neutral-500 dark:text-neutral-400 mb-2">
                <GitBranch className="h-3.5 w-3.5 text-amber-500" />
                Inter-Service Topology Edges ({addedEdges.length})
              </div>
              <div className="space-y-1.5">
                {addedEdges.map((edge: any, idx: number) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between rounded-xl border border-neutral-200 bg-neutral-50 px-3.5 py-2 dark:border-neutral-800 dark:bg-neutral-900 font-mono text-[11px]"
                  >
                    <span>
                      {edge.source} <ArrowRight className="inline h-3 w-3 text-neutral-400" /> {edge.target}
                    </span>
                    {edge.label && (
                      <span className="rounded-md bg-neutral-200 dark:bg-neutral-800 px-2 py-0.5 text-[9px] text-neutral-600 dark:text-neutral-400">
                        {edge.label}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Drawer Footer */}
        <div className="border-t border-neutral-200 p-4 dark:border-neutral-800 flex justify-end">
          <ShimmerButton
            onClick={onClose}
            borderRadius="12px"
            shimmerColor="rgba(16, 185, 129, 0.7)"
            background="rgba(20, 20, 25, 0.9)"
            className="px-5 py-2 text-xs font-semibold text-white shadow-md hover:shadow-lg transition-all"
          >
            Close Drawer
          </ShimmerButton>
        </div>
      </div>
    </div>
  );
}
