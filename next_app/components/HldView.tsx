"use client";

import { useState } from "react";
import {
  Network,
  Copy,
  Check,
  ArrowLeft,
  ArrowRight,
  Info,
  GitBranch,
  Sparkles,
  ChevronDown,
  Code2,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import HLDGraph from "./HLDGraph";
import VersionDiffDrawer from "./VersionDiffDrawer";
import JsonViewer from "./JsonViewer";
import clsx from "clsx";
import Select, { type TSelectData } from "./ui/select";

export default function HldView() {
  const {
    hldData,
    setActivePipelineStep,
    openExplain,
    activeVersionTag,
    availableVersions,
    activeDiff,
    selectVersion,
    jumpToLld,
  } = useAppStore();
  const [copied, setCopied] = useState(false);
  const [showDiffDrawer, setShowDiffDrawer] = useState(false);
  const [viewMode, setViewMode] = useState<"visual" | "json">("visual");

  const handleCopy = () => {
    if (!hldData) return;
    navigator.clipboard.writeText(JSON.stringify(hldData, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const versionsList =
    availableVersions.length > 0
      ? availableVersions
      : [{ id: "curr", version_tag: activeVersionTag || "v1.0", is_latest: true }];

  return (
    <div className="flex h-full flex-col bg-white text-black dark:bg-black dark:text-white transition-colors">
      {/* Top action header */}
      <div className="relative z-40 flex items-center justify-between border-b border-neutral-200 bg-white px-6 py-3.5 dark:border-neutral-800 dark:bg-black">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-black text-white dark:bg-white dark:text-black shadow-xs">
            <Network className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-heading text-sm font-bold tracking-tight text-black dark:text-white">
                High-Level Design (HLD) Architecture
              </h2>

              {/* Version Switcher Dropdown */}
              <div className="relative z-50">
                <Select
                  id="hld-view-version-select"
                  title="Architecture Version"
                  value={activeVersionTag || "v1.0"}
                  onChange={(ver) => selectVersion(ver)}
                  data={versionsList.map((ver, idx) => ({
                    id: ver.id || `hld-ver-${ver.version_tag}-${idx}`,
                    label: `${ver.version_tag}${idx === 0 || ver.is_latest ? " (Latest)" : ""}`,
                    value: ver.version_tag,
                    description: ver.is_latest ? "Active production design" : "Historical snapshot",
                    icon: "🏷️",
                  }))}
                />
              </div>

              {/* Evolution Changelog / Diff Button */}
              {activeDiff && (
                <button
                  type="button"
                  onClick={() => setShowDiffDrawer(true)}
                  className="flex items-center gap-1.5 rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-700 dark:text-emerald-400 hover:bg-emerald-500/20 transition-all cursor-pointer shadow-2xs"
                >
                  <Sparkles className="h-3 w-3" />
                  <span>Changelog</span>
                </button>
              )}
            </div>
            <p className="text-[11px] text-neutral-500 dark:text-neutral-400">
              Interactive system topology dynamically managed with non-destructive delta versioning
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          {/* View Mode Toggle: Topology vs JSON */}
          <div className="flex items-center rounded-lg border border-neutral-200/80 bg-white/70 p-0.5 backdrop-blur-md dark:border-[#262626] dark:bg-[#0D0D0F]">
            <button
              type="button"
              onClick={() => setViewMode("visual")}
              className={clsx(
                "flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-semibold transition-all cursor-pointer",
                viewMode === "visual"
                  ? "bg-white text-black shadow-2xs dark:bg-[#161619] dark:text-white dark:border dark:border-[#262626]"
                  : "text-neutral-500 hover:text-black dark:text-neutral-400 dark:hover:text-white"
              )}
            >
              <Network className="h-3.5 w-3.5" />
              <span>Diagram</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode("json")}
              className={clsx(
                "flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-semibold transition-all cursor-pointer",
                viewMode === "json"
                  ? "bg-white text-black shadow-2xs dark:bg-[#161619] dark:text-white dark:border dark:border-[#262626]"
                  : "text-neutral-500 hover:text-black dark:text-neutral-400 dark:hover:text-white"
              )}
            >
              <Code2 className="h-3.5 w-3.5 text-emerald-500" />
              <span>Raw JSON</span>
            </button>
          </div>

          {activeDiff && (
            <button
              onClick={() => setShowDiffDrawer(true)}
              className="flex items-center gap-1.5 rounded-lg border border-neutral-200/80 bg-white/70 backdrop-blur-md px-3 py-1.5 text-xs font-semibold text-neutral-800 shadow-xs hover:border-black hover:text-black dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-200 dark:hover:bg-[#161619] dark:hover:border-white/20 dark:hover:text-white"
            >
              <GitBranch className="h-3.5 w-3.5 text-emerald-500" />
              <span>Inspect Diff</span>
            </button>
          )}

          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 rounded-lg border border-neutral-200/80 bg-white/70 backdrop-blur-md px-3 py-1.5 text-xs font-semibold text-neutral-800 shadow-xs transition-all hover:border-black hover:text-black dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-200 dark:hover:bg-[#161619] dark:hover:border-white/20 dark:hover:text-white"
          >
            {copied ? (
              <Check className="h-3.5 w-3.5 text-black dark:text-white" />
            ) : (
              <Copy className="h-3.5 w-3.5" />
            )}
            <span>{copied ? "Copied" : "Copy JSON"}</span>
          </button>

          <button
            onClick={() =>
              openExplain(
                "hld-overview",
                `High-Level Design Architecture (${activeVersionTag || "v1.0"})`,
                hldData
                  ? JSON.stringify(hldData, null, 2)
                  : "High-Level Design diagram generated by the SAE engine."
              )
            }
            className="flex items-center gap-1 rounded-lg border border-neutral-200/80 bg-white/70 backdrop-blur-md px-3 py-1.5 text-xs font-semibold text-neutral-800 shadow-xs hover:border-black hover:text-black dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-200 dark:hover:bg-[#161619] dark:hover:border-white/20 dark:hover:text-white"
          >
            <Info className="h-3.5 w-3.5" />
            <span>Details</span>
          </button>

          <button
            onClick={() => setActivePipelineStep(4)}
            className="flex items-center gap-1.5 rounded-lg bg-black px-4 py-1.5 text-xs font-semibold text-white transition-all hover:bg-neutral-800 dark:bg-white dark:text-black dark:hover:bg-neutral-200"
          >
            <span>Explore 5 LLDs</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Version Diff Drawer */}
      <VersionDiffDrawer
        open={showDiffDrawer}
        onClose={() => setShowDiffDrawer(false)}
        versionTag={activeVersionTag || "v1.1"}
        diff={activeDiff}
      />

      {/* Main Content Area: Visual Canvas or Raw JSON */}
      {viewMode === "visual" ? (
        <div key="visual" className="relative flex-1 bg-neutral-50 dark:bg-black animate-in fade-in duration-300">
          <div className="absolute left-4 top-4 z-10 flex items-center gap-2 rounded-lg border border-neutral-200/80 bg-white/80 px-3.5 py-1.5 text-xs font-medium text-black shadow-xs backdrop-blur-md dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-200">
            <span className="h-2 w-2 rounded-full bg-black dark:bg-white" />
            <span>Click any component node to inspect details and jump to its LLD</span>
          </div>

          <HLDGraph onSelectLld={(lldType) => jumpToLld(lldType)} />
        </div>
      ) : (
        <div className="relative flex-1 overflow-hidden">
          <JsonViewer defaultTab="hld" />
        </div>
      )}

      {/* Bottom Slider Footer */}
      <div className="flex items-center justify-between border-t border-neutral-200/70 bg-white/70 px-6 py-3 backdrop-blur-2xl backdrop-saturate-150 dark:border-white/10 dark:bg-black/60 shadow-lg">
        <button
          onClick={() => setActivePipelineStep(2)}
          className="flex items-center gap-1.5 rounded-lg border border-neutral-200/80 bg-white/80 px-4 py-2 text-xs font-semibold text-neutral-700 backdrop-blur-md transition-colors hover:border-black hover:text-black dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-200 dark:hover:bg-[#161619] dark:hover:border-white/20 dark:hover:text-white cursor-pointer"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to ARSRS Document</span>
        </button>

        <button
          onClick={() => setActivePipelineStep(4)}
          className="flex items-center gap-1.5 rounded-lg bg-black px-5 py-2 text-xs font-semibold text-white transition-all hover:bg-neutral-800 dark:bg-white dark:text-black dark:hover:bg-neutral-200"
        >
          <span>Explore Low-Level Designs (5 LLDs)</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
