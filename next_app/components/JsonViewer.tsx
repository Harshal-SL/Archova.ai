"use client";

import React, { useState, useMemo } from "react";
import {
  Code2,
  Copy,
  Check,
  Download,
  Search,
  Server,
  Layout,
  Database,
  ShieldCheck,
  Cloud,
  Network,
  Layers,
  FileJson,
  X,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import type { LldType } from "@/lib/ai-engine-client";
import clsx from "clsx";

export type JsonViewerTab = "hld" | LldType | "all";

interface JsonViewerProps {
  defaultTab?: JsonViewerTab;
  showTabs?: boolean;
  customData?: Record<string, unknown> | null;
  title?: string;
}

const TABS: Array<{
  id: JsonViewerTab;
  label: string;
  icon: typeof Server;
  badge?: string;
}> = [
  { id: "hld", label: "High-Level Design (HLD)", icon: Network, badge: "HLD" },
  { id: "backend", label: "Backend LLD", icon: Server, badge: "API & Svc" },
  { id: "database", label: "Database LLD", icon: Database, badge: "Schemas" },
  { id: "security", label: "Security LLD", icon: ShieldCheck, badge: "Auth & RBAC" },
  { id: "frontend", label: "Frontend LLD", icon: Layout, badge: "UI & State" },
  { id: "cloud", label: "Cloud LLD", icon: Cloud, badge: "Infra & Fargate" },
  { id: "all", label: "Combined Package", icon: Layers, badge: "Complete" },
];

export default function JsonViewer({
  defaultTab = "hld",
  showTabs = true,
  customData,
  title,
}: JsonViewerProps) {
  const { hldData, lldData, generationId, activeVersionTag } = useAppStore();
  const [activeTab, setActiveTab] = useState<JsonViewerTab>(defaultTab);
  const [copied, setCopied] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Determine current active payload
  const activePayload = useMemo(() => {
    if (customData) return customData;

    if (activeTab === "hld") {
      return hldData;
    }
    if (activeTab === "all") {
      return {
        generation_id: generationId,
        version: activeVersionTag || "v1.0",
        high_level_design: hldData,
        low_level_designs: lldData,
      };
    }
    return lldData[activeTab as LldType] || null;
  }, [customData, activeTab, hldData, lldData, generationId, activeVersionTag]);

  const jsonString = useMemo(() => {
    if (!activePayload) return "";
    try {
      return JSON.stringify(activePayload, null, 2);
    } catch {
      return String(activePayload);
    }
  }, [activePayload]);

  const stats = useMemo(() => {
    if (!activePayload) return { keys: 0, bytes: 0, lines: 0 };
    const bytes = new Blob([jsonString]).size;
    const lines = jsonString ? jsonString.split("\n").length : 0;
    const keys = typeof activePayload === "object" ? Object.keys(activePayload).length : 0;
    return { keys, bytes, lines };
  }, [activePayload, jsonString]);

  const handleCopy = () => {
    if (!jsonString) return;
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!jsonString) return;
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${activeTab}_architecture_${generationId || "export"}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Syntax highlighting line-by-line with simple regex
  const highlightedLines = useMemo(() => {
    if (!jsonString) return [];
    const lines = jsonString.split("\n");

    return lines.map((line, idx) => {
      const isSearchMatch =
        searchQuery.trim().length > 0 &&
        line.toLowerCase().includes(searchQuery.toLowerCase());

      return {
        num: idx + 1,
        raw: line,
        isSearchMatch,
      };
    });
  }, [jsonString, searchQuery]);

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="flex h-full w-full flex-col overflow-hidden bg-neutral-950 text-neutral-100 font-sans">
      {/* ── Subheader with Tabs & Controls ── */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-neutral-800 bg-neutral-900/90 px-4 py-2.5 backdrop-blur-md shrink-0">
        <div className="flex items-center gap-2 overflow-x-auto py-0.5 no-scrollbar">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shrink-0">
            <FileJson className="h-4 w-4" />
          </div>

          {title ? (
            <span className="text-xs font-bold text-white tracking-wide shrink-0">
              {title}
            </span>
          ) : showTabs ? (
            <div className="flex items-center gap-1 bg-[#0D0D0F] p-1 rounded-lg border border-[#262626]">
              {TABS.map((tab) => {
                const TabIcon = tab.icon;
                const isActive = activeTab === tab.id;
                const hasData =
                  tab.id === "hld"
                    ? Boolean(hldData)
                    : tab.id === "all"
                    ? Boolean(hldData)
                    : Boolean(lldData[tab.id as LldType]);

                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={clsx(
                      "flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-all cursor-pointer whitespace-nowrap",
                      isActive
                        ? "bg-[#161619] text-white font-semibold shadow-xs border border-[#262626]"
                        : "text-neutral-400 hover:bg-[#161619]/60 hover:text-neutral-200"
                    )}
                  >
                    <TabIcon className={clsx("h-3 w-3", isActive ? "text-emerald-400" : "text-neutral-500")} />
                    <span>{tab.badge}</span>
                    {hasData ? (
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shrink-0" />
                    ) : (
                      <span className="h-1.5 w-1.5 rounded-full bg-neutral-600 shrink-0" />
                    )}
                  </button>
                );
              })}
            </div>
          ) : null}
        </div>

        {/* Right Action Tools: Search, Copy, Download, Stats */}
        <div className="flex items-center gap-2">
          {/* Search within JSON */}
          <div className="relative flex items-center">
            <Search className="pointer-events-none absolute left-2.5 h-3.5 w-3.5 text-neutral-500" />
            <input
              type="text"
              placeholder="Filter keys or values..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-7 w-36 sm:w-48 rounded-lg border border-[#262626] bg-[#0D0D0F] pl-8 pr-7 text-xs text-white placeholder-neutral-500 focus:border-white/20 focus:outline-hidden"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="absolute right-2 text-neutral-400 hover:text-white"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </div>

          {/* Stats Badge */}
          {activePayload && (
            <div className="hidden lg:flex items-center gap-1.5 rounded-md bg-[#0D0D0F] border border-[#262626] px-2 py-1 text-[11px] font-mono text-neutral-400">
              <span className="text-emerald-400">{formatSize(stats.bytes)}</span>
              <span>•</span>
              <span>{stats.lines} lines</span>
              <span>•</span>
              <span>{stats.keys} keys</span>
            </div>
          )}

          {/* Copy Button */}
          <button
            type="button"
            onClick={handleCopy}
            disabled={!activePayload}
            className="flex items-center gap-1 rounded-lg border border-[#262626] bg-[#0D0D0F] px-2.5 py-1 text-xs font-semibold text-neutral-200 hover:border-white/20 hover:text-white hover:bg-[#161619] transition-colors cursor-pointer disabled:opacity-40"
            title="Copy formatted JSON to clipboard"
          >
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5 text-emerald-400" />
                <span className="text-emerald-400">Copied</span>
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5 text-neutral-400" />
                <span>Copy JSON</span>
              </>
            )}
          </button>

          {/* Download Button */}
          <button
            type="button"
            onClick={handleDownload}
            disabled={!activePayload}
            className="flex items-center gap-1 rounded-lg border border-[#262626] bg-[#0D0D0F] px-2.5 py-1 text-xs font-semibold text-neutral-200 hover:border-white/20 hover:text-white hover:bg-[#161619] transition-colors cursor-pointer disabled:opacity-40"
            title="Download JSON artifact file"
          >
            <Download className="h-3.5 w-3.5 text-neutral-400" />
            <span className="hidden sm:inline">Export</span>
          </button>
        </div>
      </div>

      {/* ── JSON Code Output Canvas ── */}
      <div className="relative flex-1 overflow-auto bg-[#0d1117] p-4 font-mono text-xs leading-relaxed selection:bg-emerald-950 selection:text-emerald-200">
        {!activePayload ? (
          <div className="flex h-full flex-col items-center justify-center p-8 text-center font-sans">
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-neutral-900 text-neutral-500 border border-neutral-800">
              <Code2 className="h-6 w-6" />
            </div>
            <h4 className="text-sm font-bold text-white">
              No JSON Artifact Available for {activeTab.toUpperCase()}
            </h4>
            <p className="mt-1 max-w-md text-xs text-neutral-400">
              This design artifact has not been generated by the AI Engine yet. Complete the
              interview stage or run the generation pipeline to produce the structured design payload.
            </p>
          </div>
        ) : (
          <div className="min-w-max">
            {highlightedLines.map((line) => (
              <div
                key={line.num}
                className={clsx(
                  "flex items-start hover:bg-neutral-800/40 rounded-xs px-1 py-0.2 transition-colors",
                  line.isSearchMatch && "bg-amber-500/20 border-l-2 border-amber-400 pl-1"
                )}
              >
                {/* Gutter Line Number */}
                <span className="w-10 shrink-0 select-none text-right pr-4 text-neutral-600 text-[11px]">
                  {line.num}
                </span>

                {/* Line text with color formatting */}
                <span className="text-neutral-200 whitespace-pre">
                  {formatJsonLine(line.raw)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Bottom Information Strip ── */}
      <div className="flex items-center justify-between border-t border-neutral-800 bg-neutral-900 px-4 py-1.5 text-[11px] text-neutral-500 font-mono shrink-0">
        <div className="flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          <span>Source: AI Engine API (FastAPI Port 8000)</span>
          {generationId && <span>• Run: {generationId}</span>}
        </div>
        <div className="flex items-center gap-3">
          <span>Active Artifact: {activeTab.toUpperCase()}</span>
          <span>Format: RFC 8259 JSON</span>
        </div>
      </div>
    </div>
  );
}

/**
 * Basic syntax colorizer for JSON lines
 */
function formatJsonLine(line: string): React.ReactNode {
  // Key match: "key":
  const keyMatch = line.match(/^(\s*)(".*?")\s*:(.*)$/);
  if (keyMatch) {
    const [, indent, key, rest] = keyMatch;
    return (
      <>
        <span>{indent}</span>
        <span className="text-sky-300 font-medium">{key}</span>
        <span className="text-neutral-400">:</span>
        {formatJsonValue(rest)}
      </>
    );
  }

  return formatJsonValue(line);
}

function formatJsonValue(val: string): React.ReactNode {
  // String value
  if (val.includes('"')) {
    const parts = val.split(/(".*?")/g);
    return parts.map((part, i) => {
      if (part.startsWith('"') && part.endsWith('"')) {
        return (
          <span key={i} className="text-emerald-300">
            {part}
          </span>
        );
      }
      return <span key={i}>{formatPrimitive(part)}</span>;
    });
  }

  return formatPrimitive(val);
}

function formatPrimitive(text: string): React.ReactNode {
  // Numbers, booleans, null
  return (
    <span
      dangerouslySetInnerHTML={{
        __html: text
          .replace(/\b(true|false)\b/g, '<span class="text-amber-400 font-semibold">$1</span>')
          .replace(/\b(null)\b/g, '<span class="text-rose-400 font-semibold">$1</span>')
          .replace(/\b(-?\d+(\.\d+)?)\b/g, '<span class="text-indigo-300 font-semibold">$1</span>'),
      }}
    />
  );
}
