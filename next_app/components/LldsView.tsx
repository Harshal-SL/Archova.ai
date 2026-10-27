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
  Code2,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import { aiEngineApi, type LldType } from "@/lib/ai-engine-client";
import LLDGraph from "./LLDGraph";
import JsonViewer from "./JsonViewer";
import clsx from "clsx";
import Select, { type TSelectData } from "@/components/ui/select";

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
    setHldWorkspaceTab,
    isValidating,
    runCorrectionWorkflow,
    activeModelId,
  } = useAppStore();

  const isArchova = !activeModelId || activeModelId === "archova";

  const [viewMode, setViewMode] = useState<"visual" | "json">("visual");

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
    if (isArchova && generationId && !lldData[activeLldType]) {
      fetchSpecificLld(activeLldType);
    }
  }, [isArchova, generationId, activeLldType, lldData, fetchSpecificLld]);

  const currentStatus = lldStatus[activeLldType] || "NOT_STARTED";
  const currentData = lldData[activeLldType];
  const currentMessage = lldMessages[activeLldType];
  const activeTabObj = LLD_TABS.find((t) => t.type === activeLldType) || LLD_TABS[0];
  const ActiveIcon = activeTabObj.icon;

  return (
    <div className="flex h-full flex-col bg-transparent text-black dark:text-white transition-colors">
      {/* Main Content Area (Diagram view or Raw JSON) */}
      <div key={`${activeLldType}-${viewMode}`} className="relative flex-1 overflow-hidden bg-transparent text-black dark:text-white animate-in fade-in duration-300">
        {viewMode === "json" ? (
          <JsonViewer
            defaultTab={activeLldType}
            customData={currentData}
            title={`${activeTabObj.label} JSON`}
          />
        ) : (
          <>
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

            {currentStatus === "NOT_STARTED" && !currentData && (
              <div className="flex h-full flex-col items-center justify-center p-6 text-center">
                <Server className="mb-2 h-10 w-10 text-neutral-400 dark:text-neutral-600" />
                <p className="text-xs text-neutral-500 dark:text-neutral-400">
                  {activeTabObj.label} has not been generated yet for this architecture.
                </p>
              </div>
            )}

            {currentData && currentStatus !== "GENERATING" && currentStatus !== "FAILED" && (
              <LLDGraph customLldType={activeLldType} customLldData={currentData} />
            )}
          </>
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
          className="flex items-center gap-1.5 rounded-lg border border-neutral-200/80 bg-white/80 px-4 py-2 text-xs font-semibold text-neutral-700 backdrop-blur-md transition-colors hover:border-black hover:text-black dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-300 dark:hover:bg-[#161619] dark:hover:border-white/20 dark:hover:text-white cursor-pointer"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Visual HLD</span>
        </button>

        {/* Right: Only keep the dropdown menu of selecting the LLD designs */}
        <div className="flex items-center gap-3">
          <Select
            id="lld-view-select"
            title="Switch Low-Level Design"
            value={activeLldType}
            onChange={(type) => {
              setActiveLldType(type as LldType);
              fetchSpecificLld(type as LldType);
            }}
            data={LLD_TABS.map((tab) => ({
              id: tab.type,
              label: tab.label,
              value: tab.type,
              description: tab.description,
              icon:
                tab.type === "backend"
                  ? "⚙️"
                  : tab.type === "frontend"
                  ? "💻"
                  : tab.type === "database"
                  ? "🗄️"
                  : tab.type === "security"
                  ? "🛡️"
                  : "☁️",
            }))}
          />
        </div>
      </div>
    </div>
  );
}
