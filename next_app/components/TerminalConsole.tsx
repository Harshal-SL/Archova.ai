"use client";

import { useEffect, useRef, useState } from "react";
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
}

export default function TerminalConsole({ initialCollapsed = false }: Props) {
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
  const terminalBodyRef = useRef<HTMLDivElement>(null);
  const sseRef = useRef<EventSource | null>(null);

  // Auto-scroll logic
  useEffect(() => {
    if (autoScrollLogs && terminalBodyRef.current) {
      terminalBodyRef.current.scrollTop = terminalBodyRef.current.scrollHeight;
    }
  }, [logs.length, autoScrollLogs]);

  // Connect SSE Stream when generationId changes
  useEffect(() => {
    if (!generationId) {
      if (sseRef.current) {
        sseRef.current.close();
        sseRef.current = null;
      }
      return;
    }

    // 1. Initial historical logs fetch
    aiEngineApi
      .getLogs(generationId)
      .then((res) => {
        if (res.logs && res.logs.length > 0) {
          setLogs(res.logs);
        }
      })
      .catch(() => {});

    // 2. Connect to EventSource (SSE)
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

  const getStageBadgeClass = (stage: string) => {
    const s = stage.toLowerCase().replace(/_/g, "-");
    switch (s) {
      case "ree":
        return "bg-blue-500/20 text-blue-400 border-blue-500/30";
      case "sae":
        return "bg-purple-500/20 text-purple-400 border-purple-500/30";
      case "interview":
        return "bg-amber-500/20 text-amber-400 border-amber-500/30";
      case "lld-backend":
        return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
      case "lld-frontend":
        return "bg-pink-500/20 text-pink-400 border-pink-500/30";
      case "lld-database":
        return "bg-sky-500/20 text-sky-400 border-sky-500/30";
      case "lld-security":
        return "bg-rose-500/20 text-rose-400 border-rose-500/30";
      case "lld-cloud":
        return "bg-teal-500/20 text-teal-400 border-teal-500/30";
      case "client":
        return "bg-gray-500/20 text-gray-300 border-gray-500/30";
      default:
        return "bg-indigo-500/20 text-indigo-400 border-indigo-500/30";
    }
  };

  return (
    <div className="flex flex-col border-t border-gray-200 bg-[#090d16] text-gray-200 dark:border-gray-800 font-mono text-xs overflow-hidden">
      {/* Terminal Header */}
      <div className="flex items-center justify-between bg-[#060911] px-3 py-2 border-b border-gray-800/80">
        <div className="flex items-center gap-1.5 min-w-0">
          <div className="flex items-center gap-1 shrink-0">
            <span className="h-2 w-2 rounded-full bg-red-500/80" />
            <span className="h-2 w-2 rounded-full bg-amber-500/80" />
            <span className="h-2 w-2 rounded-full bg-emerald-500/80" />
          </div>
          <div className="flex items-center gap-1 font-semibold text-gray-300 truncate">
            <Terminal className="h-3 w-3 text-indigo-400 shrink-0" />
            <span className="text-[11px] truncate">Pipeline Logs</span>
          </div>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          {generationId && (
            <span className="flex items-center gap-1 text-[10px] text-emerald-400">
              <Radio className="h-2.5 w-2.5 animate-pulse" />
              <span className="hidden sm:inline">SSE</span>
            </span>
          )}

          <span className="rounded bg-gray-800 px-1.5 py-0.5 text-[9px] font-bold text-gray-400">
            {logs.length}
          </span>

          <button
            onClick={toggleAutoScrollLogs}
            title="Toggle Auto-Scroll"
            className={clsx(
              "rounded px-1.5 py-0.5 text-[9px] font-semibold transition-colors",
              autoScrollLogs
                ? "bg-indigo-500/20 text-indigo-300"
                : "bg-gray-800 text-gray-400 hover:text-white"
            )}
          >
            {autoScrollLogs ? "Scroll:ON" : "OFF"}
          </button>

          <button
            onClick={clearLogs}
            title="Clear logs"
            className="rounded p-1 text-gray-400 transition-colors hover:bg-gray-800 hover:text-white"
          >
            <Trash2 className="h-3 w-3" />
          </button>

          <button
            onClick={() => setCollapsed(!collapsed)}
            title={collapsed ? "Expand logs" : "Collapse logs"}
            className="rounded p-1 text-gray-400 hover:bg-gray-800 hover:text-white"
          >
            {collapsed ? (
              <ChevronUp className="h-3 w-3" />
            ) : (
              <ChevronDown className="h-3 w-3" />
            )}
          </button>
        </div>
      </div>

      {/* Terminal Output Body */}
      {!collapsed && (
        <div
          ref={terminalBodyRef}
          className="h-44 overflow-y-auto p-2.5 space-y-1 bg-[#060911]/90"
        >
          {logs.length === 0 ? (
            <div className="py-4 text-center text-gray-500 italic text-[11px]">
              <ScrollText className="mx-auto h-5 w-5 mb-1 text-gray-600" />
              <span>Real-time pipeline logs will stream here.</span>
            </div>
          ) : (
            logs.map((entry, idx) => (
              <div
                key={idx}
                className="flex items-baseline gap-1.5 font-mono text-[10px] leading-relaxed break-words"
              >
                <span className="shrink-0 text-gray-500">[{entry.timestamp}]</span>
                <span
                  className={clsx(
                    "shrink-0 rounded border px-1 py-0.2 text-[8px] font-bold uppercase",
                    getStageBadgeClass(entry.stage)
                  )}
                >
                  [{entry.stage || "INFO"}]
                </span>
                <span
                  className={clsx(
                    "flex-1",
                    entry.level === "ERROR"
                      ? "font-semibold text-red-400"
                      : entry.level === "WARNING"
                      ? "text-amber-300"
                      : "text-gray-200"
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
