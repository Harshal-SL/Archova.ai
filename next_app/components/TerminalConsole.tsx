"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import {
  Terminal,
  Trash2,
  ScrollText,
  Radio,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import { aiEngineApi, type LogEntry } from "@/lib/ai-engine-client";
import clsx from "clsx";

interface Props {
  initialCollapsed?: boolean;
  filterStage?: "all" | "validator" | "errors";
  title?: string;
  maxHeightClass?: string;
  className?: string;
  showFilters?: boolean;
}

export default function TerminalConsole({
  initialCollapsed = false,
  filterStage = "all",
  title = "Pipeline Stream",
  maxHeightClass = "h-44",
  className,
  showFilters = true,
}: Props) {
  const {
    generationId,
    logs,
    autoScrollLogs,
    toggleAutoScrollLogs,
    addLogEntry,
    setLogs,
    clearLogs,
  } = useAppStore();

  const [collapsed, setCollapsed] = useState(initialCollapsed);
  const [activeFilter, setActiveFilter] = useState<"all" | "validator" | "errors">(filterStage);
  const terminalBodyRef = useRef<HTMLDivElement>(null);
  const sseRef = useRef<EventSource | null>(null);

  // Auto-scroll logic
  useEffect(() => {
    if (autoScrollLogs && terminalBodyRef.current && !collapsed) {
      terminalBodyRef.current.scrollTop = terminalBodyRef.current.scrollHeight;
    }
  }, [logs.length, autoScrollLogs, collapsed, activeFilter]);

  // Connect SSE Stream when generationId changes
  useEffect(() => {
    if (!generationId) {
      if (sseRef.current) {
        sseRef.current.close();
        sseRef.current = null;
      }
      return;
    }

    aiEngineApi
      .getLogs(generationId)
      .then((res) => {
        if (res.logs && res.logs.length > 0) {
          setLogs(res.logs);
        }
      })
      .catch(() => {});

    const sseUrl = aiEngineApi.getLogsStreamUrl(generationId);
    const eventSource = new EventSource(sseUrl);
    sseRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const entry: LogEntry = JSON.parse(event.data);
        addLogEntry(entry);
      } catch (err) {
        console.warn("Failed to parse SSE log:", err);
      }
    };

    eventSource.onerror = () => {
      if (eventSource.readyState === EventSource.CLOSED) {
        eventSource.close();
      }
    };

    return () => {
      eventSource.close();
      sseRef.current = null;
    };
  }, [generationId, addLogEntry, setLogs]);

  const validatorCount = useMemo(() => {
    return logs.filter((l) => {
      const s = (l?.stage || "").toUpperCase();
      const m = (l?.message || "").toLowerCase();
      const p = (l?.process || "").toLowerCase();
      return (
        s.includes("VALIDAT") ||
        s.includes("REVALIDAT") ||
        s.includes("CORRECTION") ||
        m.includes("validat") ||
        m.includes("rubric") ||
        m.includes("benchmark") ||
        p.includes("validat")
      );
    }).length;
  }, [logs]);

  const errorCount = useMemo(() => {
    return logs.filter((l) => l?.level === "ERROR" || l?.level === "WARNING").length;
  }, [logs]);

  const displayedLogs = useMemo(() => {
    if (activeFilter === "validator") {
      return logs.filter((l) => {
        const s = (l?.stage || "").toUpperCase();
        const m = (l?.message || "").toLowerCase();
        const p = (l?.process || "").toLowerCase();
        return (
          s.includes("VALIDAT") ||
          s.includes("REVALIDAT") ||
          s.includes("CORRECTION") ||
          m.includes("validat") ||
          m.includes("rubric") ||
          m.includes("benchmark") ||
          p.includes("validat")
        );
      });
    }
    if (activeFilter === "errors") {
      return logs.filter((l) => l?.level === "ERROR" || l?.level === "WARNING");
    }
    return logs;
  }, [logs, activeFilter]);

  const getStageBadgeClass = (stage: string) => {
    const s = (stage || "").toUpperCase();
    if (s.includes("VALIDAT") || s.includes("REVALIDAT")) {
      return "bg-indigo-500/15 text-indigo-600 border-indigo-500/30 dark:text-indigo-400";
    }
    if (s.includes("ERROR") || s.includes("FAIL")) {
      return "bg-rose-500/15 text-rose-600 border-rose-500/30 dark:text-rose-400";
    }
    if (s.includes("HLD") || s.includes("LLD")) {
      return "bg-teal-500/15 text-teal-600 border-teal-500/30 dark:text-teal-400";
    }
    return "bg-neutral-200 text-neutral-800 border-neutral-300 dark:bg-neutral-800 dark:text-neutral-200 dark:border-neutral-700";
  };

  return (
    <div
      className={clsx(
        "flex flex-col bg-white text-black font-mono text-xs overflow-hidden dark:bg-[#0a0a0c] dark:text-white rounded-2xl border border-neutral-200 dark:border-neutral-800 shadow-sm",
        className
      )}
    >
      {/* Terminal Header */}
      <div className="flex flex-wrap items-center justify-between border-b border-neutral-200 bg-neutral-100/80 px-3 py-2 dark:border-neutral-800 dark:bg-neutral-900/90 gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <div className="flex items-center gap-1 shrink-0">
            <span className="h-2 w-2 rounded-full bg-rose-500/80" />
            <span className="h-2 w-2 rounded-full bg-amber-500/80" />
            <span className="h-2 w-2 rounded-full bg-emerald-500/80" />
          </div>
          <div className="flex items-center gap-1.5 font-bold truncate text-black dark:text-white">
            <Terminal className="h-3.5 w-3.5 text-indigo-500 shrink-0" />
            <span className="font-heading text-[11px] font-bold tracking-tight truncate">
              {title}
            </span>
          </div>

          {/* Quick Filter Pills */}
          {showFilters && (
            <div className="hidden sm:flex items-center gap-1 ml-2 border border-neutral-300 dark:border-neutral-700/80 rounded-lg p-0.5 bg-neutral-200/50 dark:bg-neutral-950 text-[10px]">
              <button
                type="button"
                onClick={() => setActiveFilter("all")}
                className={clsx(
                  "px-2 py-0.5 rounded-md transition-colors cursor-pointer",
                  activeFilter === "all"
                    ? "bg-black text-white dark:bg-white dark:text-black font-bold shadow-2xs"
                    : "text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white"
                )}
              >
                All ({logs.length})
              </button>
              <button
                type="button"
                onClick={() => setActiveFilter("validator")}
                className={clsx(
                  "px-2 py-0.5 rounded-md transition-colors cursor-pointer",
                  activeFilter === "validator"
                    ? "bg-indigo-600 text-white font-bold shadow-2xs"
                    : "text-neutral-600 dark:text-neutral-400 hover:text-indigo-600 dark:hover:text-indigo-400"
                )}
              >
                Validator ({validatorCount})
              </button>
              <button
                type="button"
                onClick={() => setActiveFilter("errors")}
                className={clsx(
                  "px-2 py-0.5 rounded-md transition-colors cursor-pointer",
                  activeFilter === "errors"
                    ? "bg-rose-600 text-white font-bold shadow-2xs"
                    : "text-neutral-600 dark:text-neutral-400 hover:text-rose-600 dark:hover:text-rose-400"
                )}
              >
                Issues ({errorCount})
              </button>
            </div>
          )}
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          {generationId && (
            <span className="flex items-center gap-1 text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold mr-1">
              <Radio className="h-2.5 w-2.5 animate-pulse" />
              <span>LIVE</span>
            </span>
          )}

          <button
            onClick={toggleAutoScrollLogs}
            title="Toggle Auto-Scroll"
            className={clsx(
              "rounded px-2 py-0.5 text-[9px] font-semibold transition-all cursor-pointer",
              autoScrollLogs
                ? "bg-black text-white dark:bg-white dark:text-black shadow-xs"
                : "border border-neutral-300 bg-white/70 text-neutral-600 hover:text-black dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300"
            )}
          >
            {autoScrollLogs ? "Scroll: ON" : "Scroll: OFF"}
          </button>

          <button
            onClick={clearLogs}
            title="Clear logs"
            className="rounded p-1 text-neutral-500 transition-colors hover:bg-neutral-200 hover:text-black dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-white cursor-pointer"
          >
            <Trash2 className="h-3 w-3" />
          </button>

          <button
            onClick={() => setCollapsed(!collapsed)}
            title={collapsed ? "Expand logs" : "Collapse logs"}
            className="rounded p-1 text-neutral-500 hover:bg-neutral-200 hover:text-black dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-white cursor-pointer"
          >
            {collapsed ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronUp className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>

      {/* Terminal Output Body */}
      {!collapsed && (
        <div
          ref={terminalBodyRef}
          className={clsx(
            "overflow-y-auto p-3 space-y-1.5 bg-neutral-950 text-neutral-200 selection:bg-indigo-500/30",
            maxHeightClass
          )}
        >
          {displayedLogs.length === 0 ? (
            <div className="py-6 text-center text-neutral-500 italic text-[11px]">
              <ScrollText className="mx-auto h-5 w-5 mb-1.5 text-neutral-600" />
              <span>
                {activeFilter === "validator"
                  ? "No validation engine logs yet. Run the validator audit to stream logs in real time."
                  : activeFilter === "errors"
                  ? "No warnings or errors detected."
                  : "Real-time engine and validator logs will stream here."}
              </span>
            </div>
          ) : (
            displayedLogs.map((entry, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2 font-mono text-[10.5px] leading-relaxed break-words hover:bg-white/5 rounded px-1 -mx-1"
              >
                <span className="shrink-0 text-neutral-500 select-none">[{entry.timestamp}]</span>
                <span
                  className={clsx(
                    "shrink-0 rounded border px-1.5 py-0.2 text-[8.5px] font-bold uppercase",
                    getStageBadgeClass(entry.stage)
                  )}
                >
                  {entry.stage || "INFO"}
                </span>
                <span
                  className={clsx(
                    "flex-1",
                    entry.level === "ERROR"
                      ? "font-semibold text-rose-400"
                      : entry.level === "WARNING"
                      ? "font-semibold text-amber-300"
                      : "text-neutral-200"
                  )}
                >
                  {entry.message}
                </span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
