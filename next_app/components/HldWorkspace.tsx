"use client";

import React from "react";
import { useAppStore } from "@/lib/store";
import HLDGraph from "./HLDGraph";
import LldsView from "./LldsView";
import ValidationView from "./ValidationView";
import TubelightChatBar from "./TubelightChatBar";
import { Network, Layers, ShieldCheck, RefreshCw } from "lucide-react";
import clsx from "clsx";

export default function HldWorkspace() {
  const {
    hldWorkspaceTab,
    setHldWorkspaceTab,
    jumpToLld,
    validationData,
    isValidating,
  } = useAppStore();

  const scorePercent = validationData
    ? Math.round(
        (validationData.validation?.summary?.overall_score ??
          validationData.validation?.scorecard?.overall_composite_score ??
          0) * 100
      )
    : null;

  const verdict = validationData?.validation?.summary?.verdict;
  const isFullyValidated = validationData?.is_fully_validated;

  return (
    <div className="relative flex h-full w-full flex-col overflow-hidden bg-transparent text-black dark:text-white transition-colors">
      {/* ── Top Workspace Navigation Header ── */}
      <div className="flex items-center justify-between border-b border-neutral-200/80 bg-white/80 px-4 py-2 backdrop-blur-md dark:border-neutral-800/80 dark:bg-neutral-950/80 z-10 shrink-0">
        <div className="flex items-center gap-1.5">
          {/* Tab 1: HLD Architecture Topology */}
          <button
            onClick={() => setHldWorkspaceTab("hld")}
            className={clsx(
              "flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold transition-all cursor-pointer",
              hldWorkspaceTab === "hld"
                ? "bg-neutral-900 text-white dark:bg-white dark:text-black shadow-xs"
                : "text-neutral-600 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:bg-neutral-900"
            )}
          >
            <Network className="h-3.5 w-3.5" />
            <span>HLD Topology</span>
          </button>

          {/* Tab 2: 5 LLDs Component Blueprints */}
          <button
            onClick={() => setHldWorkspaceTab("lld")}
            className={clsx(
              "flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold transition-all cursor-pointer",
              hldWorkspaceTab === "lld"
                ? "bg-neutral-900 text-white dark:bg-white dark:text-black shadow-xs"
                : "text-neutral-600 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:bg-neutral-900"
            )}
          >
            <Layers className="h-3.5 w-3.5" />
            <span>5 LLD Blueprints</span>
          </button>

          {/* Tab 3: Validator Report & Quality Scorecard */}
          <button
            onClick={() => setHldWorkspaceTab("validation")}
            className={clsx(
              "flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold transition-all cursor-pointer",
              hldWorkspaceTab === "validation"
                ? "bg-neutral-900 text-white dark:bg-white dark:text-black shadow-xs"
                : "text-neutral-600 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:bg-neutral-900"
            )}
          >
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>Validation Audit</span>
            {isValidating && (
              <RefreshCw className="h-3 w-3 animate-spin text-indigo-500" />
            )}
            {scorePercent !== null && !isValidating && (
              <span
                className={clsx(
                  "rounded-full px-1.5 py-0.2 text-[10px] font-bold border",
                  scorePercent >= 80
                    ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/30 dark:text-emerald-400"
                    : "bg-amber-500/10 text-amber-600 border-amber-500/30 dark:text-amber-400"
                )}
              >
                {scorePercent}%
              </span>
            )}
          </button>
        </div>

        {/* Right Status Pill if Validated */}
        {validationData && !isValidating && (
          <div className="hidden sm:flex items-center gap-2 text-xs">
            <span
              className={clsx(
                "rounded-full px-2 py-0.5 text-[10px] font-bold uppercase border",
                isFullyValidated
                  ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/30 dark:text-emerald-400"
                  : "bg-amber-500/10 text-amber-600 border-amber-500/30 dark:text-amber-400"
              )}
            >
              {verdict?.replace(/_/g, " ") || "VALIDATED"}
            </span>
          </div>
        )}
      </div>

      {/* Main Content: HLD Diagram Canvas, 5 LLDs Concurrency View, or Validation View */}
      <div className="relative flex-1 bg-transparent min-h-0 overflow-hidden">
        {hldWorkspaceTab === "hld" ? (
          <HLDGraph onSelectLld={(lldType) => jumpToLld(lldType)} />
        ) : hldWorkspaceTab === "validation" ? (
          <ValidationView />
        ) : (
          <LldsView onBackToHld={() => setHldWorkspaceTab("hld")} />
        )}
      </div>

      {/* ── Tubelight Chat Bar & Floating Moveable/Resizable Chat Window ── */}
      <TubelightChatBar />
    </div>
  );
}
