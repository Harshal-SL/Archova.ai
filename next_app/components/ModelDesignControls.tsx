"use client";

import { useAppStore } from "@/lib/store";
import { Scale, RefreshCw, Cpu, Sparkles } from "lucide-react";
import { ShimmerButton } from "./ui/shimmer-button";
import Select, { type TSelectData } from "./ui/select";

export default function ModelDesignControls() {
  const {
    activeModelId,
    selectModel,
    benchmarkResults,
    benchmarkModelsConfig,
    isBenchmarking,
    setHldWorkspaceTab,
  } = useAppStore();

  const modelOptions: TSelectData[] = [
    {
      id: "archova",
      label: "Archova AI Engine",
      value: "archova",
      description: "Multi-Agent REE + SAE Engine (with In-Detail Rationale)",
      icon: <Sparkles className="h-3.5 w-3.5 text-[#005dff]" />,
    },
    ...Object.values(benchmarkResults)
      .filter((m) => m.model_id !== "archova")
      .map((m) => ({
        id: m.model_id,
        label: m.model_name,
        value: m.model_id,
        description: "Direct 1-Shot Baseline Model",
        icon: <Cpu className="h-3.5 w-3.5 text-neutral-500" />,
      })),
    ...(Object.keys(benchmarkResults).length === 0
      ? benchmarkModelsConfig.map((m) => ({
          id: m.id,
          label: m.name,
          value: m.id,
          description: "Direct 1-Shot Baseline Model",
          icon: <Cpu className="h-3.5 w-3.5 text-neutral-500" />,
        }))
      : []),
  ];

  return (
    <div className="flex items-center gap-2 pointer-events-auto">
      {/* 1. Animated Models Dropdown Menu (First) */}
      <Select
        id="model-selector-dropdown"
        data={modelOptions}
        value={activeModelId}
        onChange={(val) => selectModel(val)}
        title="Choose Architecture Model"
      />

      {isBenchmarking && (
        <RefreshCw className="h-3.5 w-3.5 animate-spin text-[#005dff]" />
      )}

      {/* 2. Compare Models Button (Grey with white animation) */}
      <ShimmerButton
        type="button"
        onClick={() => setHldWorkspaceTab("comparison")}
        borderRadius="14px"
        shimmerColor="#ffffff"
        shimmerDuration="2.5s"
        background="#0D0D0F"
        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-white border border-[#262626] hover:border-white/20 shadow-2xs hover:shadow-md transition-all cursor-pointer pointer-events-auto"
        title="Compare Archova AI Engine with baseline LLM models"
      >
        <div className="flex items-center gap-1.5 text-white">
          <Scale className="h-3.5 w-3.5 text-white" />
          <span>Compare Models</span>
        </div>
      </ShimmerButton>
    </div>
  );
}

