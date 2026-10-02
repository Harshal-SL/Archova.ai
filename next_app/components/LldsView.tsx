"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  Server,
  Layout,
  Database,
  ShieldCheck,
  Cloud,
  Loader2,
  AlertCircle,
  ArrowLeft,
  ChevronUp,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import { aiEngineApi, type LldType } from "@/lib/ai-engine-client";
import LLDGraph from "./LLDGraph";
import clsx from "clsx";

const LLD_TABS: Array<{
  type: LldType;
  label: string;
  shortLabel: string;
  icon: typeof Server;
  description: string;
}> = [
    { type: "backend", label: "Backend LLD", shortLabel: "Backend", icon: Server, description: "FastAPI & Microservices" },
    { type: "frontend", label: "Frontend LLD", shortLabel: "Frontend", icon: Layout, description: "Next.js 16 & UI Components" },
    { type: "database", label: "Database LLD", shortLabel: "Database", icon: Database, description: "PostgreSQL & Schema Tables" },
    { type: "security", label: "Security LLD", shortLabel: "Security", icon: ShieldCheck, description: "Auth, RBAC & WAF Guard" },
    { type: "cloud", label: "Cloud LLD", shortLabel: "Cloud", icon: Cloud, description: "AWS ECS Fargate & Cloud Tier" },
  ];

interface Props {
  onBackToHld?: () => void;
}

export default function LldsView({ onBackToHld }: Props = {}) {
  const {
    generationId,
    lldStatus,
    lldData,
    lldMessages,
    activeLldType,
    setActiveLldType,
    setActivePipelineStep,
  } = useAppStore();

  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as unknown as HTMLElement)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const fetchSpecificLld = useCallback(
    async (type: LldType) => {
      if (!generationId) return;
      try {
        const response = await aiEngineApi.getLLD(generationId, type);
        useAppStore.setState((s) => ({
          lldStatus: { ...s.lldStatus, [type]: response.status },
          lldData: { ...s.lldData, [type]: response.data || null },
          lldMessages: { ...s.lldMessages, [type]: response.message || null },
        }));
      } catch (err) {
        console.error(`Failed to fetch ${type} LLD:`, err);
      }
    },
    [generationId]
  );

  useEffect(() => {
    if (generationId && !lldData[activeLldType]) {
      fetchSpecificLld(activeLldType);
    }
  }, [generationId, activeLldType, lldData, fetchSpecificLld]);

  const currentStatus = lldStatus[activeLldType] || "NOT_STARTED";
  const currentData = lldData[activeLldType];
  const currentMessage = lldMessages[activeLldType];
  const activeTabObj = LLD_TABS.find((t) => t.type === activeLldType) || LLD_TABS[0];
  const ActiveIcon = activeTabObj.icon;

  return (
    <div className="flex h-full flex-col bg-transparent text-black dark:text-white transition-colors">
      {/* Main Content Area (Diagram view) */}
      <div className="relative flex-1 overflow-hidden bg-transparent text-black dark:text-white">
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
          <LLDGraph customLldType={activeLldType} customLldData={currentData} />
        )}
      </div>

      {/* Bottom Slider Footer with Navigation Controls & Bottom-Right LLD Dropdown */}
      <div className="flex items-center justify-between border-t border-neutral-200/70 bg-white/70 px-6 py-3 backdrop-blur-2xl backdrop-saturate-150 dark:border-white/10 dark:bg-black/60 shadow-lg">
        {/* Left: Back to Visual HLD */}
        <button
          onClick={() => {
            if (onBackToHld) {
              onBackToHld();
            } else {
              setActivePipelineStep(3);
            }
          }}
          className="flex items-center gap-1.5 rounded-lg border border-neutral-200/80 bg-white/80 px-4 py-2 text-xs font-semibold text-neutral-700 backdrop-blur-md transition-colors hover:border-black hover:text-black dark:border-white/10 dark:bg-white/[0.06] dark:text-neutral-300 dark:hover:border-white dark:hover:text-white cursor-pointer"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Visual HLD</span>
        </button>

        {/* Right: Step Tracker & Bottom-Right LLD Navigation Dropdown */}
        <div className="flex items-center gap-4">
          <span className="text-xs text-neutral-500 dark:text-neutral-400 hidden sm:inline">
            Step 4 of 4 • Low-Level Designs
          </span>

          {/* Bottom-Right LLD Navigation Dropdown Menu */}
          <div className="relative" ref={dropdownRef}>
            {dropdownOpen && (
              <div className="absolute bottom-full right-0 mb-2 w-64 rounded-xl border border-neutral-200 bg-white/95 p-1.5 shadow-xl backdrop-blur-xl dark:border-neutral-800 dark:bg-neutral-950/95 z-50">
                <div className="px-2 py-1 border-b border-neutral-100 dark:border-neutral-800/80 flex items-center justify-between mb-1">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-neutral-400 dark:text-neutral-500">
                    Switch LLD
                  </span>
                  <span className="text-[9px] font-mono text-neutral-400">
                    5 Topologies
                  </span>
                </div>

                <div className="space-y-0.5">
                  {LLD_TABS.map((item) => {
                    const ItemIcon = item.icon;
                    const isCurrent = activeLldType === item.type;
                    return (
                      <button
                        key={item.type}
                        type="button"
                        onClick={() => {
                          setActiveLldType(item.type);
                          fetchSpecificLld(item.type);
                          setDropdownOpen(false);
                        }}
                        className={clsx(
                          "flex w-full items-center justify-between gap-2 rounded-lg px-2.5 py-1.5 text-left text-xs transition-colors cursor-pointer",
                          isCurrent
                            ? "bg-neutral-900 text-white dark:bg-white dark:text-black font-semibold"
                            : "text-neutral-700 hover:bg-neutral-100 hover:text-black dark:text-neutral-300 dark:hover:bg-neutral-900 dark:hover:text-white"
                        )}
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          <ItemIcon
                            className={clsx(
                              "h-3.5 w-3.5 shrink-0",
                              isCurrent
                                ? "text-white dark:text-black"
                                : "text-neutral-400 dark:text-neutral-500"
                            )}
                          />
                          <span className="truncate">{item.label}</span>
                        </div>
                        {isCurrent && (
                          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shrink-0" />
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Small Dropdown Trigger Button */}
            <button
              type="button"
              onClick={() => setDropdownOpen((prev) => !prev)}
              className="flex items-center gap-1.5 rounded-lg border border-neutral-300 bg-white px-2.5 py-1.5 text-xs font-semibold text-neutral-800 shadow-2xs hover:border-black dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-200 dark:hover:border-neutral-400 cursor-pointer transition-colors"
              title="Navigate between Low-Level Designs"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 shrink-0" />
              <ActiveIcon className="h-3.5 w-3.5 text-neutral-600 dark:text-neutral-400" />
              <span>{activeTabObj.label}</span>
              <ChevronUp
                className={clsx(
                  "h-3 w-3 text-neutral-400 transition-transform duration-200 ml-0.5",
                  dropdownOpen && "rotate-180"
                )}
              />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
