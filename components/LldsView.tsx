"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Server,
  Layout,
  Database,
  ShieldCheck,
  Cloud,
  Copy,
  Check,
  RefreshCw,
  Loader2,
  AlertCircle,
  Network,
  Code2,
  ArrowLeft,
  Info,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import { aiEngineApi, type LldType, type LldStatusType } from "@/lib/ai-engine-client";
import LLDGraph from "./LLDGraph";
import clsx from "clsx";

const LLD_TABS: Array<{ type: LldType; label: string; icon: typeof Server }> = [
  { type: "backend", label: "Backend LLD", icon: Server },
  { type: "frontend", label: "Frontend LLD", icon: Layout },
  { type: "database", label: "Database LLD", icon: Database },
  { type: "security", label: "Security LLD", icon: ShieldCheck },
  { type: "cloud", label: "Cloud LLD", icon: Cloud },
];

export default function LldsView() {
  const {
    generationId,
    lldStatus,
    lldData,
    lldMessages,
    activeLldType,
    setActiveLldType,
    activeProcess,
    setActivePipelineStep,
    openExplain,
  } = useAppStore();

  const [copied, setCopied] = useState(false);
  const [loadingLld, setLoadingLld] = useState(false);
  const [viewMode, setViewMode] = useState<"diagram" | "json">("diagram");

  const fetchSpecificLld = useCallback(
    async (type: LldType) => {
      if (!generationId) return;
      setLoadingLld(true);
      try {
        const response = await aiEngineApi.getLLD(generationId, type);
        useAppStore.setState((s) => ({
          lldStatus: { ...s.lldStatus, [type]: response.status },
          lldData: { ...s.lldData, [type]: response.data || null },
          lldMessages: { ...s.lldMessages, [type]: response.message || null },
        }));
      } catch (err) {
        console.error(`Failed to fetch ${type} LLD:`, err);
      } finally {
        setLoadingLld(false);
      }
    },
    [generationId]
  );

  useEffect(() => {
    if (generationId && !lldData[activeLldType]) {
      fetchSpecificLld(activeLldType);
    }
  }, [generationId, activeLldType, lldData, fetchSpecificLld]);

  const handleCopyJson = () => {
    const data = lldData[activeLldType];
    if (!data) return;
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getStatusPill = (status: LldStatusType) => {
    switch (status) {
      case "READY":
        return "bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border-emerald-500/40";
      case "GENERATING":
        return "bg-amber-500/20 text-amber-600 dark:text-amber-400 border-amber-500/40 animate-pulse";
      case "FAILED":
        return "bg-red-500/20 text-red-600 dark:text-red-400 border-red-500/40";
      default:
        return "bg-gray-500/10 text-gray-500 border-gray-500/20";
    }
  };

  const currentStatus = lldStatus[activeLldType] || "NOT_STARTED";
  const currentData = lldData[activeLldType];
  const currentMessage = lldMessages[activeLldType];

  return (
    <div className="flex h-full flex-col bg-white dark:bg-black">
      {/* Top Concurrency Summary Grid */}
      <div className="border-b border-gray-200 bg-gray-50/70 p-4 dark:border-gray-800 dark:bg-gray-900/50">
        <div className="mb-2 flex items-center justify-between">
          <span className="text-[11px] font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">
            Background Parallel Concurrency Status
          </span>
          <div className="flex items-center gap-1.5 text-xs text-indigo-500 font-medium">
            <span className="h-2 w-2 rounded-full bg-indigo-500 animate-pulse" />
            <span>Live Server Stream</span>
          </div>
        </div>

        {/* 5 LLDs Status Grid */}
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
          {LLD_TABS.map(({ type, label, icon: Icon }) => {
            const status = lldStatus[type] || "NOT_STARTED";
            const isActive = activeLldType === type;
            return (
              <button
                key={type}
                onClick={() => {
                  setActiveLldType(type);
                  fetchSpecificLld(type);
                }}
                className={clsx(
                  "flex flex-col items-start gap-1 rounded-xl border p-2.5 text-left transition-all",
                  isActive
                    ? "border-indigo-500 bg-white shadow-sm dark:border-indigo-500 dark:bg-gray-800"
                    : "border-gray-200 bg-white/60 hover:border-gray-300 dark:border-gray-800 dark:bg-gray-900/60"
                )}
              >
                <div className="flex w-full items-center justify-between">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-gray-800 dark:text-gray-200">
                    <Icon className="h-3.5 w-3.5 text-indigo-500" />
                    <span>{type.toUpperCase()}</span>
                  </div>
                  <span
                    className={clsx(
                      "rounded-full border px-1.5 py-0.5 text-[9px] font-bold uppercase",
                      getStatusPill(status)
                    )}
                  >
                    {status.replace("_", " ")}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Active Process Banner if running */}
      {activeProcess && (
        <div className="flex items-center justify-between border-b border-indigo-500/20 bg-indigo-500/10 px-6 py-2 text-xs">
          <div className="flex items-center gap-2 text-indigo-900 dark:text-indigo-200">
            <span className="h-2 w-2 rounded-full bg-indigo-500 animate-ping" />
            <span className="font-bold">{activeProcess.process || activeProcess.stage}:</span>
            <span className="truncate max-w-md">{activeProcess.message}</span>
          </div>
          <span className="rounded bg-indigo-500/20 px-2 py-0.5 text-[10px] font-bold uppercase text-indigo-600 dark:text-indigo-400">
            {activeProcess.status || "IN PROGRESS"}
          </span>
        </div>
      )}

      {/* LLD Tab Selector & Controls */}
      <div className="flex items-center justify-between border-b border-gray-200 px-6 py-2.5 dark:border-gray-800">
        <div className="flex items-center gap-1.5">
          {LLD_TABS.map(({ type, label }) => (
            <button
              key={type}
              onClick={() => {
                setActiveLldType(type);
                fetchSpecificLld(type);
              }}
              className={clsx(
                "rounded-xl px-3 py-1.5 text-xs font-semibold transition-all",
                activeLldType === type
                  ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-sm"
                  : "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
              )}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          {/* View mode toggle: Diagram vs JSON */}
          <div className="flex items-center rounded-xl border border-gray-200 bg-gray-100 p-0.5 dark:border-gray-700 dark:bg-gray-800">
            <button
              onClick={() => setViewMode("diagram")}
              className={clsx(
                "flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-medium transition-colors",
                viewMode === "diagram"
                  ? "bg-white text-gray-900 shadow-sm dark:bg-gray-900 dark:text-white"
                  : "text-gray-500 hover:text-gray-900 dark:text-gray-400"
              )}
            >
              <Network className="h-3 w-3" />
              <span>Diagram</span>
            </button>
            <button
              onClick={() => setViewMode("json")}
              className={clsx(
                "flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-medium transition-colors",
                viewMode === "json"
                  ? "bg-white text-gray-900 shadow-sm dark:bg-gray-900 dark:text-white"
                  : "text-gray-500 hover:text-gray-900 dark:text-gray-400"
              )}
            >
              <Code2 className="h-3 w-3" />
              <span>JSON</span>
            </button>
          </div>

          <button
            onClick={() => fetchSpecificLld(activeLldType)}
            disabled={loadingLld}
            title="Refresh LLD"
            className="rounded-xl border border-gray-200 p-1.5 text-gray-500 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800"
          >
            <RefreshCw className={clsx("h-3.5 w-3.5", loadingLld && "animate-spin")} />
          </button>

          {currentData && (
            <button
              onClick={handleCopyJson}
              className="flex items-center gap-1 rounded-xl border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
              <span>{copied ? "Copied" : "Copy"}</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="relative flex-1 overflow-hidden">
        {currentStatus === "GENERATING" && (
          <div className="flex h-full flex-col items-center justify-center p-6 text-center">
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-500/10 text-amber-500">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
            <h4 className="text-sm font-bold text-gray-900 dark:text-white">
              Generating {activeLldType.toUpperCase()} LLD...
            </h4>
            <p className="mt-1 max-w-sm text-xs text-gray-500">
              {currentMessage || "Multi-agent engine is synthesizing the low-level modules and schemas."}
            </p>
          </div>
        )}

        {currentStatus === "FAILED" && (
          <div className="flex h-full flex-col items-center justify-center p-6 text-center">
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-red-500/10 text-red-500">
              <AlertCircle className="h-6 w-6" />
            </div>
            <h4 className="text-sm font-bold text-red-600 dark:text-red-400">
              {activeLldType.toUpperCase()} LLD Generation Failed
            </h4>
            <p className="mt-1 max-w-sm text-xs text-gray-500">
              {currentMessage || "An error occurred during multi-agent synthesis."}
            </p>
          </div>
        )}

        {currentStatus === "NOT_STARTED" && (
          <div className="flex h-full flex-col items-center justify-center p-6 text-center">
            <Server className="mb-2 h-10 w-10 text-gray-300 dark:text-gray-700" />
            <p className="text-xs text-gray-400">
              {activeLldType.toUpperCase()} LLD has not started yet. Complete the interview to generate.
            </p>
          </div>
        )}

        {currentStatus === "READY" && currentData && (
          <>
            {viewMode === "diagram" ? (
              <LLDGraph customLldType={activeLldType} customLldData={currentData} />
            ) : (
              <div className="h-full overflow-y-auto p-6 font-mono text-xs text-gray-800 dark:text-gray-200">
                <pre className="rounded-2xl border border-gray-200 bg-gray-50 p-6 dark:border-gray-800 dark:bg-gray-900">
                  {JSON.stringify(currentData, null, 2)}
                </pre>
              </div>
            )}
          </>
        )}
      </div>

      {/* Bottom Slider Footer */}
      <div className="flex items-center justify-between border-t border-gray-200 bg-white/80 px-6 py-3 backdrop-blur-md dark:border-gray-800 dark:bg-black/80">
        <button
          onClick={() => setActivePipelineStep(3)}
          className="flex items-center gap-1.5 rounded-xl border border-gray-200 bg-white px-4 py-2 text-xs font-semibold text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200 dark:hover:bg-gray-800"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Visual HLD</span>
        </button>

        <span className="text-xs text-gray-400">
          Step 4 of 4 • Low-Level Designs
        </span>
      </div>
    </div>
  );
}
