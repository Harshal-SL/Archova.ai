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

  const getStageBadgeClass = (stage: string) => {
    return "bg-neutral-100 text-black border-neutral-300 dark:bg-neutral-900 dark:text-white dark:border-neutral-700";
  };

  return (
    <div className="flex flex-col border-t-2 border-t-black dark:border-t-white bg-white text-black font-mono text-xs overflow-hidden dark:bg-black dark:text-white">
      {/* Terminal Header */}
      <div className="flex items-center justify-between border-b border-neutral-200 bg-neutral-100/80 px-3 py-2 dark:border-neutral-800 dark:bg-neutral-900">
        <div className="flex items-center gap-1.5 min-w-0">
          <div className="flex items-center gap-1 shrink-0">
            <span className="h-2 w-2 rounded-full bg-neutral-400 dark:bg-neutral-600" />
            <span className="h-2 w-2 rounded-full bg-neutral-400 dark:bg-neutral-600" />
            <span className="h-2 w-2 rounded-full bg-neutral-400 dark:bg-neutral-600" />
          </div>
          <div className="flex items-center gap-1 font-bold truncate text-black dark:text-white">
            <Terminal className="h-3.5 w-3.5 text-black dark:text-white shrink-0" />
            <span className="font-heading text-[11px] font-bold tracking-tight truncate">Pipeline Stream</span>
          </div>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          {generationId && (
            <span className="flex items-center gap-1 text-[10px] text-black dark:text-white font-semibold">
              <Radio className="h-2.5 w-2.5 animate-pulse" />
              <span className="hidden sm:inline">LIVE</span>
            </span>
          )}

          <span className="rounded border border-neutral-300 bg-neutral-200 px-1.5 py-0.5 text-[9px] font-bold text-black dark:border-neutral-700 dark:bg-neutral-800 dark:text-white">
            {logs.length}
          </span>

          <button
            onClick={toggleAutoScrollLogs}
            title="Toggle Auto-Scroll"
            className={clsx(
              "rounded px-1.5 py-0.5 text-[9px] font-semibold transition-all",
              autoScrollLogs
                ? "bg-black text-white dark:bg-white dark:text-black shadow-xs"
                : "border border-neutral-300 bg-white text-neutral-600 hover:text-black dark:border-neutral-700 dark:bg-black dark:text-neutral-400 dark:hover:text-white"
            )}
          >
            {autoScrollLogs ? "Scroll:ON" : "OFF"}
          </button>

          <button
            onClick={clearLogs}
            title="Clear logs"
            className="rounded p-1 text-neutral-500 transition-colors hover:bg-neutral-200 hover:text-black dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-white"
          >
            <Trash2 className="h-3 w-3" />
          </button>

          <button
            onClick={() => setCollapsed(!collapsed)}
            title={collapsed ? "Expand logs" : "Collapse logs"}
            className="rounded p-1 text-neutral-500 hover:bg-neutral-200 hover:text-black dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-white"
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
          className="h-44 overflow-y-auto p-2.5 space-y-1 bg-white text-black dark:bg-black dark:text-white"
        >
          {logs.length === 0 ? (
            <div className="py-4 text-center text-neutral-400 dark:text-neutral-600 italic text-[11px]">
              <ScrollText className="mx-auto h-5 w-5 mb-1 text-neutral-400" />
              <span>Real-time pipeline logs will stream here.</span>
            </div>
          ) : (
            logs.map((entry, idx) => (
              <div
                key={idx}
                className="flex items-baseline gap-1.5 font-mono text-[10px] leading-relaxed break-words"
              >
                <span className="shrink-0 text-neutral-400 dark:text-neutral-600">[{entry.timestamp}]</span>
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
                      ? "font-bold text-red-600 dark:text-red-400"
                      : entry.level === "WARNING"
                      ? "font-bold text-amber-600 dark:text-amber-400"
                      : "text-black dark:text-white"
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
