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
        return "bg-neutral-100 text-black border-neutral-300 dark:bg-neutral-800 dark:text-white dark:border-neutral-700";
      case "GENERATING":
        return "bg-black text-white border-black dark:bg-white dark:text-black dark:border-white animate-pulse";
      case "FAILED":
        return "bg-neutral-200 text-neutral-800 border-neutral-400 dark:bg-neutral-800 dark:text-neutral-300 dark:border-neutral-600";
      default:
        return "bg-neutral-100 text-neutral-500 border-neutral-200 dark:bg-neutral-900 dark:text-neutral-500 dark:border-neutral-800";
    }
  };

  const currentStatus = lldStatus[activeLldType] || "NOT_STARTED";
  const currentData = lldData[activeLldType];
  const currentMessage = lldMessages[activeLldType];

  return (
    <div className="flex h-full flex-col bg-white text-black dark:bg-black dark:text-white transition-colors">
      {/* Top Concurrency Summary Grid */}
      <div className="border-b border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-black">
        <div className="mb-2.5 flex items-center justify-between">
          <span className="font-heading text-[11px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
            Background Parallel Concurrency Status
          </span>
          <div className="flex items-center gap-1.5 text-xs text-black dark:text-white font-semibold">
            <span className="h-2 w-2 rounded-full bg-black dark:bg-white animate-pulse" />
            <span className="font-heading text-xs">Multi-Agent Synthesis</span>
          </div>
        </div>

        {/* 5 LLDs Status Grid */}
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
          {LLD_TABS.map(({ type, icon: Icon }) => {
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
                  "flex flex-col items-start gap-1 rounded-lg border p-2.5 text-left transition-all",
                  isActive
                    ? "border-black bg-neutral-100 dark:border-white dark:bg-neutral-900"
                    : "border-neutral-200 bg-white hover:border-black dark:border-neutral-800 dark:bg-black dark:hover:border-white"
                )}
              >
                <div className="flex w-full items-center justify-between">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-black dark:text-white font-heading">
                    <Icon className="h-3.5 w-3.5" />
                    <span className="tracking-tight">{type.toUpperCase()}</span>
                  </div>
                  <span
                    className={clsx(
                      "rounded-md border px-1.5 py-0.5 text-[9px] font-bold uppercase",
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
        <div className="flex items-center justify-between border-b border-neutral-200 bg-neutral-100 px-6 py-2 text-xs text-black dark:border-neutral-800 dark:bg-neutral-900 dark:text-white">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-black dark:bg-white animate-ping" />
            <span className="font-bold">{activeProcess.process || activeProcess.stage}:</span>
            <span className="truncate max-w-md">{activeProcess.message}</span>
          </div>
          <span className="rounded-md border border-neutral-300 bg-white px-2 py-0.5 text-[10px] font-bold uppercase text-black dark:border-neutral-700 dark:bg-neutral-800 dark:text-white">
            {activeProcess.status || "IN PROGRESS"}
          </span>
        </div>
      )}

      {/* LLD Tab Selector & Controls */}
      <div className="flex items-center justify-between border-b border-neutral-200 px-6 py-2.5 dark:border-neutral-800 bg-white dark:bg-black">
        <div className="flex items-center gap-1.5">
          {LLD_TABS.map(({ type, label }) => (
            <button
              key={type}
              onClick={() => {
                setActiveLldType(type);
                fetchSpecificLld(type);
              }}
              className={clsx(
                "font-heading rounded-md px-3 py-1.5 text-xs font-semibold tracking-tight transition-all",
                activeLldType === type
                  ? "bg-black text-white dark:bg-white dark:text-black"
                  : "text-neutral-700 hover:text-black hover:bg-neutral-100 dark:text-neutral-300 dark:hover:text-white dark:hover:bg-neutral-800"
              )}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          {/* View mode toggle: Diagram vs JSON */}
          <div className="flex items-center rounded-lg border border-neutral-300 bg-white p-0.5 dark:border-neutral-700 dark:bg-neutral-900">
            <button
              onClick={() => setViewMode("diagram")}
              className={clsx(
                "flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-semibold transition-colors",
                viewMode === "diagram"
                  ? "bg-black text-white dark:bg-white dark:text-black"
                  : "text-neutral-600 hover:text-black dark:text-neutral-400 dark:hover:text-white"
              )}
            >
              <Network className="h-3 w-3" />
              <span>Diagram</span>
            </button>
            <button
              onClick={() => setViewMode("json")}
              className={clsx(
                "flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-semibold transition-colors",
                viewMode === "json"
                  ? "bg-black text-white dark:bg-white dark:text-black"
                  : "text-neutral-600 hover:text-black dark:text-neutral-400 dark:hover:text-white"
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
            className="rounded-lg border border-neutral-300 p-1.5 text-neutral-700 hover:border-black hover:text-black dark:border-neutral-700 dark:text-neutral-300 dark:hover:border-white dark:hover:text-white shadow-xs transition-colors"
          >
            <RefreshCw className={clsx("h-3.5 w-3.5", loadingLld && "animate-spin")} />
          </button>

          {currentData && (
            <button
              onClick={handleCopyJson}
              className="flex items-center gap-1 rounded-lg border border-neutral-300 bg-white px-3 py-1.5 text-xs font-medium text-neutral-700 hover:border-black hover:text-black dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-300 dark:hover:border-white dark:hover:text-white shadow-xs transition-colors"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-black dark:text-white" /> : <Copy className="h-3.5 w-3.5" />}
              <span>{copied ? "Copied" : "Copy"}</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="relative flex-1 overflow-hidden bg-neutral-50 text-black dark:bg-black dark:text-white">
        {currentStatus === "GENERATING" && (
          <div className="flex h-full flex-col items-center justify-center p-6 text-center">
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-neutral-200 text-black dark:bg-neutral-800 dark:text-white">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
            <h4 className="text-sm font-bold text-black dark:text-white">
              Generating {activeLldType.toUpperCase()} LLD...
            </h4>
            <p className="mt-1 max-w-sm text-xs text-neutral-500 dark:text-neutral-400">
              {currentMessage || "Multi-agent engine is synthesizing the low-level modules and schemas."}
            </p>
          </div>
        )}

        {currentStatus === "FAILED" && (
          <div className="flex h-full flex-col items-center justify-center p-6 text-center">
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-neutral-200 text-black dark:bg-neutral-800 dark:text-white">
              <AlertCircle className="h-6 w-6" />
            </div>
            <h4 className="text-sm font-bold text-black dark:text-white">
              {activeLldType.toUpperCase()} LLD Generation Failed
            </h4>
            <p className="mt-1 max-w-sm text-xs text-neutral-500 dark:text-neutral-400">
              {currentMessage || "An error occurred during multi-agent synthesis."}
            </p>
          </div>
        )}

        {currentStatus === "NOT_STARTED" && (
          <div className="flex h-full flex-col items-center justify-center p-6 text-center">
            <Server className="mb-2 h-10 w-10 text-neutral-400 dark:text-neutral-600" />
            <p className="text-xs text-neutral-500 dark:text-neutral-400">
              {activeLldType.toUpperCase()} LLD has not started yet. Complete the interview to generate.
            </p>
          </div>
        )}

        {currentStatus === "READY" && currentData && (
          <>
            {viewMode === "diagram" ? (
              <LLDGraph customLldType={activeLldType} customLldData={currentData} />
            ) : (
              <div className="h-full overflow-y-auto p-6 font-mono text-xs text-black dark:text-white">
                <pre className="rounded-xl border border-neutral-300 bg-white p-6 shadow-xs dark:border-neutral-800 dark:bg-neutral-900">
                  {JSON.stringify(currentData, null, 2)}
                </pre>
              </div>
            )}
          </>
        )}
      </div>

      {/* Bottom Slider Footer */}
      <div className="flex items-center justify-between border-t border-neutral-200 bg-white px-6 py-3 dark:border-neutral-800 dark:bg-black">
        <button
          onClick={() => setActivePipelineStep(3)}
          className="flex items-center gap-1.5 rounded-lg border border-neutral-300 bg-white px-4 py-2 text-xs font-semibold text-neutral-700 transition-colors hover:border-black hover:text-black dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-300 dark:hover:border-white dark:hover:text-white"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Visual HLD</span>
        </button>

        <span className="text-xs text-neutral-500 dark:text-neutral-400">
          Step 4 of 4 • Low-Level Designs
        </span>
      </div>
    </div>
  );
}
