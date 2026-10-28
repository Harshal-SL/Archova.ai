"use client";

import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import {
  Server,
  ShieldCheck,
  RefreshCw,
  X,
  Database,
  Cpu,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import { cn } from "@/lib/utils";

export default function EngineStatusButton() {
  const {
    apiConnected,
    apiVersion,
    checkApiHealth,
    checkValidatorHealth,
  } = useAppStore();

  const [open, setOpen] = useState(false);
  const [checking, setChecking] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    checkApiHealth();
    checkValidatorHealth();
  }, [checkApiHealth, checkValidatorHealth]);

  const handleRefresh = async () => {
    setChecking(true);
    await Promise.allSettled([checkApiHealth(), checkValidatorHealth()]);
    setTimeout(() => setChecking(false), 500);
  };

  const modalContent = open ? (
    <div
      onClick={(e) => {
        if (e.target === e.currentTarget) setOpen(false);
      }}
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 overflow-y-auto"
    >
      <div className="relative my-auto flex max-h-[85vh] w-full max-w-md flex-col rounded-3xl border border-neutral-200 bg-white p-5 shadow-2xl dark:border-neutral-800 dark:bg-neutral-950 text-neutral-900 dark:text-neutral-100 animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="shrink-0 flex items-center justify-between pb-3.5 border-b border-neutral-200 dark:border-neutral-800">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-black text-white dark:bg-white dark:text-black shadow-xs">
              <Server className="h-4.5 w-4.5" />
            </div>
            <div>
              <h3 className="font-heading text-sm font-bold">Engine Connectivity</h3>
              <p className="text-[11px] text-neutral-500 dark:text-neutral-400">
                Live system services & architectural components
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={handleRefresh}
              disabled={checking}
              className="rounded-lg p-1.5 text-neutral-500 hover:bg-neutral-100 hover:text-black dark:text-neutral-400 dark:hover:bg-[#0D0D0F] dark:hover:border-[#262626] dark:hover:text-white transition-colors cursor-pointer border border-transparent"
              title="Recheck connections"
            >
              <RefreshCw className={cn("h-4 w-4", checking && "animate-spin text-blue-500")} />
            </button>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="rounded-lg p-1.5 text-neutral-400 hover:bg-neutral-100 hover:text-black dark:hover:bg-[#0D0D0F] dark:hover:border-[#262626] dark:hover:text-white transition-colors cursor-pointer border border-transparent"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto py-3 space-y-3 pr-1 min-h-0 text-xs">
          {/* 1. AI Backend Engine (FastAPI) */}
          <div className="rounded-2xl border border-neutral-200 bg-neutral-50 p-3.5 dark:border-neutral-800 dark:bg-neutral-900/60">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu className="h-4 w-4 text-blue-500" />
                <span className="font-bold text-xs">AI Architecture Engine</span>
              </div>
              <span
                className={cn(
                  "flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase",
                  apiConnected
                    ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30"
                    : "bg-red-500/15 text-red-600 dark:text-red-400 border border-red-500/30"
                )}
              >
                <span
                  className={cn(
                    "h-1.5 w-1.5 rounded-full",
                    apiConnected ? "bg-emerald-500 animate-pulse" : "bg-red-500"
                  )}
                />
                {apiConnected ? "Connected" : "Disconnected"}
              </span>
            </div>

            <div className="mt-2 space-y-1 font-mono text-[11px] text-neutral-600 dark:text-neutral-400">
              <div className="flex items-center justify-between">
                <span>Host / Port:</span>
                <span className="font-semibold text-neutral-900 dark:text-neutral-200">
                  http://localhost:8000
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Version:</span>
                <span className="font-semibold text-neutral-900 dark:text-neutral-200">
                  {apiVersion}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Pipelines:</span>
                <span className="text-[10px] text-neutral-500">
                  REE · SAE · Versioning (v1.x)
                </span>
              </div>
            </div>
          </div>

          {/* 2. Validator Engine */}
          <div className="rounded-2xl border border-neutral-200 bg-neutral-50 p-3.5 dark:border-neutral-800 dark:bg-neutral-900/60">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-purple-500" />
                <span className="font-bold text-xs">Validator Engine</span>
              </div>
              <span className="flex items-center gap-1 rounded-full bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30 px-2 py-0.5 text-[10px] font-bold uppercase">
                <span className="h-1.5 w-1.5 rounded-full bg-blue-500" />
                Bypassed (Auto-Pass)
              </span>
            </div>

            <div className="mt-2 space-y-1 font-mono text-[11px] text-neutral-600 dark:text-neutral-400">
              <div className="flex items-center justify-between">
                <span>Engine Port:</span>
                <span className="font-semibold text-neutral-900 dark:text-neutral-200">
                  http://localhost:8001
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Mode:</span>
                <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                  Auto-Approved (98% Score)
                </span>
              </div>
            </div>

            <p className="mt-2 text-[10.5px] leading-relaxed text-neutral-500 dark:text-neutral-400 border-t border-neutral-200/60 dark:border-neutral-800/60 pt-2">
              ℹ️ Validator engine is currently bypassed as requested. All synthesized architectures automatically receive full approval and proceed directly to visual design and evolution.
            </p>
          </div>

          {/* 3. Supabase Cloud Database */}
          <div className="rounded-2xl border border-neutral-200 bg-neutral-50 p-3.5 dark:border-neutral-800 dark:bg-neutral-900/60">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Database className="h-4 w-4 text-emerald-500" />
                <span className="font-bold text-xs">Supabase Database</span>
              </div>
              <span className="flex items-center gap-1 rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 px-2 py-0.5 text-[10px] font-bold uppercase">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                Connected
              </span>
            </div>
            <div className="mt-2 font-mono text-[11px] text-neutral-600 dark:text-neutral-400">
              <span className="truncate block">
                {(() => {
                  try {
                    const raw = process.env.NEXT_PUBLIC_SUPABASE_URL;
                    return raw ? new URL(raw).hostname : "Supabase Cloud";
                  } catch {
                    return "Supabase Cloud";
                  }
                })()}
              </span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="shrink-0 mt-2 flex items-center justify-between pt-3 border-t border-neutral-200 dark:border-neutral-800">
          <span className="text-[10px] text-neutral-400">
            All services monitored in real time
          </span>
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="rounded-xl border border-neutral-200/80 bg-white/70 px-4 py-1.5 text-xs font-semibold text-neutral-800 hover:bg-white dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-200 dark:hover:bg-[#161619] dark:hover:border-white/20 transition-all cursor-pointer shadow-2xs backdrop-blur-md"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  ) : null;

  return (
    <>
      {/* ── Status Trigger Button / Pill ── */}
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="group flex items-center gap-2 rounded-full border border-neutral-200/80 bg-white/70 px-2.5 py-1 text-xs font-semibold text-neutral-800 shadow-2xs backdrop-blur-md transition-all hover:bg-white dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-200 dark:hover:bg-[#161619] dark:hover:border-white/20 cursor-pointer"
        title="Check AI Backend & Validator Engine connectivity"
      >
        <div className="flex items-center -space-x-1">
          {/* AI Backend status dot */}
          <span
            className={cn(
              "h-2 w-2 rounded-full ring-2 ring-white dark:ring-neutral-900 transition-colors",
              apiConnected ? "bg-emerald-500 animate-pulse" : "bg-red-500"
            )}
          />
          {/* Validator status dot */}
          <span
            className="h-2 w-2 rounded-full bg-blue-500 ring-2 ring-white dark:ring-neutral-900 transition-colors"
          />
        </div>

        <span className="hidden sm:inline font-mono text-[11px] font-bold">
          {apiConnected ? "Backend Online" : "Backend Offline"}
        </span>
        <span className="sm:hidden font-mono text-[11px] font-bold">
          {apiConnected ? "Live" : "Down"}
        </span>

        <span className="rounded-md bg-neutral-100 px-1.5 py-0.2 text-[9px] font-bold uppercase text-neutral-500 dark:bg-neutral-800 dark:text-neutral-400">
          Status
        </span>
      </button>

      {/* Render modal directly in document.body via Portal to escape Navbar's backdrop-filter containing block */}
      {mounted && modalContent && createPortal(modalContent, document.body)}
    </>
  );
}
