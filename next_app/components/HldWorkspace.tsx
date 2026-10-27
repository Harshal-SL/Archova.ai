"use client";

import React, { useState } from "react";
import { useAppStore } from "@/lib/store";
import HLDGraph from "./HLDGraph";
import LldsView from "./LldsView";
import ValidationView from "./ValidationView";
import JsonViewer from "./JsonViewer";
import ComparisonView from "./ComparisonView";
import TubelightChatBar from "./TubelightChatBar";
import VersionDiffDrawer from "./VersionDiffDrawer";
import {
  Network,
  Layers,
  ShieldCheck,
  RefreshCw,
  Code2,
  ChevronDown,
  Sparkles,
  Cpu,
  ArrowRight,
  ArrowLeft,
} from "lucide-react";
import clsx from "clsx";
import { ShimmerButton } from "@/components/ui/shimmer-button";
import Select, { type TSelectData } from "@/components/ui/select";

export default function HldWorkspace() {
  const {
    setActiveView,
    hldWorkspaceTab,
    setHldWorkspaceTab,
    jumpToLld,
    validationData,
    isValidating,
    activeVersionTag,
    availableVersions,
    activeDiff,
    selectVersion,
    activeModelId,
    selectModel,
    benchmarkResults,
    benchmarkModelsConfig,
    isBenchmarking,
  } = useAppStore();

  const [showDiffDrawer, setShowDiffDrawer] = useState(false);

  const versionsList =
    availableVersions.length > 0
      ? availableVersions
      : [{ id: "curr", version_tag: activeVersionTag || "v1.0", is_latest: true }];

  const scorePercent = validationData
    ? Math.round(
        (validationData.validation?.summary?.overall_score ??
          validationData.validation?.scorecard?.overall_composite_score ??
          0) * 100
      )
    : null;

  const verdict = validationData?.validation?.summary?.verdict;
  const isFullyValidated = validationData?.is_fully_validated;

  // Active model display name
  const activeModelDisplayName =
    activeModelId === "archova"
      ? "Archova AI Engine"
      : benchmarkResults[activeModelId]?.model_name ||
        benchmarkModelsConfig.find((m) => m.id === activeModelId)?.name ||
        activeModelId;

  return (
    <div className="relative flex h-full w-full flex-col overflow-hidden bg-transparent text-black dark:text-white transition-colors">
      {/* ── Top Workspace Navigation Header ── */}
      <div className="relative z-40 flex flex-wrap items-center justify-between gap-2 border-b border-neutral-200/80 bg-white/80 px-2 sm:px-4 py-1.5 sm:py-2 backdrop-blur-md dark:border-neutral-800/80 dark:bg-neutral-950/80 shrink-0">
        <div className="flex items-center gap-1 sm:gap-1.5 flex-wrap">
          {/* Back to Chat button */}
          <button
            onClick={() => setActiveView("chat")}
            className="flex items-center gap-1 sm:gap-1.5 rounded-lg px-2 sm:px-2.5 py-1 text-xs font-semibold text-neutral-600 hover:bg-neutral-100 hover:text-black dark:text-neutral-400 dark:hover:bg-[#161619] dark:hover:text-white transition-all cursor-pointer mr-0.5 sm:mr-1 border border-neutral-200/80 dark:border-[#262626]"
            title="Return to Chat Conversation"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Chat</span>
          </button>

          {/* Tab 1: Validator Report & Quality Scorecard */}
          <button
            onClick={() => setHldWorkspaceTab("validation")}
            className={clsx(
              "flex items-center gap-1 sm:gap-1.5 rounded-lg px-2 sm:px-2.5 py-1 text-xs font-semibold transition-all cursor-pointer",
              hldWorkspaceTab === "validation"
                ? "bg-neutral-900 text-white dark:bg-white dark:text-black shadow-xs"
                : "text-neutral-600 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:bg-neutral-900"
            )}
          >
            <ShieldCheck className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Validation </span><span>Audit</span>
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

          {/* Tab 4: Raw JSON Inspector for HLD & 5 LLDs */}
          <button
            onClick={() => setHldWorkspaceTab("json")}
            className={clsx(
              "flex items-center gap-1 sm:gap-1.5 rounded-lg px-2 sm:px-2.5 py-1 text-xs font-semibold transition-all cursor-pointer",
              hldWorkspaceTab === "json"
                ? "bg-neutral-900 text-white dark:bg-white dark:text-black shadow-xs"
                : "text-neutral-600 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:bg-[#161619]"
            )}
          >
            <Code2 className="h-3.5 w-3.5 text-emerald-500" />
            <span className="hidden sm:inline">Raw </span><span>JSON</span>
          </button>
        </div>

        {/* ── Right Section: Version Dropdown, Changelog, and HLD/LLD Toggle Switch ── */}
        <div className="relative z-50 flex items-center gap-1.5 sm:gap-2.5 text-xs shrink-0 flex-wrap">
          {/* Version Switcher Dropdown */}
          <div className="relative z-50">
            <Select
              id="workspace-version-select"
              title="Architecture Version"
              value={activeVersionTag || "v1.0"}
              onChange={(ver) => selectVersion(ver)}
              data={versionsList.map((ver, idx) => ({
                id: ver.id || `ver-${ver.version_tag}-${idx}`,
                label: `${ver.version_tag}${idx === 0 || ver.is_latest ? " (Latest)" : ""}`,
                value: ver.version_tag,
                description: ver.is_latest ? "Active production architecture" : "Historical iteration snapshot",
                icon: "🏷️",
              }))}
            />
          </div>

          {/* Evolution Changelog / Diff Button */}
          {activeDiff && (
            <ShimmerButton
              type="button"
              onClick={() => setShowDiffDrawer(true)}
              borderRadius="10px"
              shimmerColor="rgba(16, 185, 129, 0.75)"
              shimmerDuration="2.5s"
              background="rgba(16, 185, 129, 0.12)"
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400 border border-emerald-500/40 shadow-xs hover:shadow-md transition-all cursor-pointer"
            >
              <div className="flex items-center gap-1.5">
                <Sparkles className="h-3 w-3" />
                <span>Changelog</span>
              </div>
            </ShimmerButton>
          )}

          {/* ── HLD / LLD Toggle Switch (In place of Approved button on right corner) ── */}
          <div
            className="relative inline-flex items-center rounded-full border border-neutral-200/80 bg-white/70 p-0.5 dark:border-[#262626] dark:bg-[#0D0D0F] shadow-2xs backdrop-blur-md select-none"
            role="group"
            aria-label="HLD and LLD Toggle Switch"
          >
            {/* HLD Option Button */}
            <button
              type="button"
              onClick={() => setHldWorkspaceTab("hld")}
              className={clsx(
                "relative z-10 flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-bold transition-all duration-200 cursor-pointer",
                hldWorkspaceTab === "hld"
                  ? "bg-black text-white shadow-xs dark:bg-white dark:text-black"
                  : "text-neutral-500 hover:text-black dark:text-neutral-400 dark:hover:text-white"
              )}
              title="Switch to High-Level Design (HLD)"
            >
              <Network className="h-3.5 w-3.5" />
              <span>HLD</span>
            </button>

            {/* Sliding Switch Track */}
            <button
              type="button"
              onClick={() => setHldWorkspaceTab(hldWorkspaceTab === "lld" ? "hld" : "lld")}
              className="mx-1 relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full bg-neutral-300 p-0.5 transition-colors duration-200 dark:bg-[#161619] dark:border dark:border-[#262626] focus:outline-hidden"
              title="Toggle between HLD and LLD"
              aria-label="Toggle between HLD and LLD"
            >
              <span
                className={clsx(
                  "inline-block h-4 w-4 transform rounded-full bg-white shadow-md transition-transform duration-200 ease-in-out dark:bg-neutral-100",
                  hldWorkspaceTab === "lld" ? "translate-x-4 bg-indigo-600 dark:bg-indigo-400" : "translate-x-0"
                )}
              />
            </button>

            {/* LLD Option Button */}
            <button
              type="button"
              onClick={() => setHldWorkspaceTab("lld")}
              className={clsx(
                "relative z-10 flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-bold transition-all duration-200 cursor-pointer",
                hldWorkspaceTab === "lld"
                  ? "bg-black text-white shadow-xs dark:bg-white dark:text-black"
                  : "text-neutral-500 hover:text-black dark:text-neutral-400 dark:hover:text-white"
              )}
              title="Switch to Low-Level Designs (LLD)"
            >
              <Layers className="h-3.5 w-3.5" />
              <span>LLD</span>
            </button>
          </div>
        </div>
      </div>

      {/* ── Active External Model Alert Banner ── */}
      {activeModelId !== "archova" && (
        <div className="flex items-center justify-between bg-amber-500/10 px-4 py-1.5 text-xs text-amber-800 dark:text-amber-300 border-b border-amber-500/25 shrink-0 z-10">
          <div className="flex items-center gap-2">
            <Cpu className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
            <span>
              Viewing direct 1-shot architecture generated by{" "}
              <strong className="underline">{activeModelDisplayName}</strong>{" "}
              (Validator Score: {scorePercent || 74}%)
            </span>
          </div>
          <button
            onClick={() => selectModel("archova")}
            className="flex items-center gap-1 font-bold underline hover:text-black dark:hover:text-white transition-colors cursor-pointer text-[11px]"
          >
            <span>Switch back to Archova AI Engine</span>
            <ArrowRight className="h-3 w-3" />
          </button>
        </div>
      )}

      {/* Main Content Area */}
      <div className="relative flex-1 bg-transparent min-h-0 overflow-hidden">
        <div key={`${hldWorkspaceTab}-${activeModelId}`} className="h-full w-full animate-in fade-in duration-300">
          {hldWorkspaceTab === "comparison" ? (
            <ComparisonView />
          ) : hldWorkspaceTab === "hld" ? (
            <HLDGraph onSelectLld={(lldType) => jumpToLld(lldType)} />
          ) : hldWorkspaceTab === "validation" ? (
            <ValidationView />
          ) : hldWorkspaceTab === "json" ? (
            <JsonViewer />
          ) : (
            <LldsView onBackToHld={() => setHldWorkspaceTab("hld")} />
          )}
        </div>
      </div>

      {/* ── Version Diff Changelog Drawer ── */}
      <VersionDiffDrawer
        open={showDiffDrawer}
        onClose={() => setShowDiffDrawer(false)}
        versionTag={activeVersionTag || "v1.0"}
        diff={activeDiff}
      />

      {/* ── Tubelight Chat Bar & Floating Moveable/Resizable Chat Window ── */}
      <TubelightChatBar />
    </div>
  );
}
