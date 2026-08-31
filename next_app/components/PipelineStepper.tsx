"use client";

import { MessageSquare, FileText, Network, Boxes, Check, ArrowRight, Zap } from "lucide-react";
import { useAppStore, type PipelineStep } from "@/lib/store";
import clsx from "clsx";

export default function PipelineStepper() {
  const {
    activePipelineStep,
    setActivePipelineStep,
    generationId,
    interviewCompleted,
    arsrsData,
    hldData,
    lldStatus,
  } = useAppStore();

  const isStep2Available = Boolean(arsrsData || hldData);
  const isStep3Available = Boolean(hldData);
  const isStep4Available = Boolean(
    Object.values(lldStatus).some((s) => s === "READY" || s === "GENERATING") || hldData
  );

  const steps: Array<{
    step: PipelineStep;
    title: string;
    icon: typeof MessageSquare;
    isAvailable: boolean;
    isCompleted: boolean;
  }> = [
    {
      step: 1,
      title: "1. Prompt & Interview",
      icon: MessageSquare,
      isAvailable: true,
      isCompleted: interviewCompleted || isStep2Available,
    },
    {
      step: 2,
      title: "2. ARSRS Document",
      icon: FileText,
      isAvailable: isStep2Available,
      isCompleted: Boolean(arsrsData),
    },
    {
      step: 3,
      title: "3. Visual HLD",
      icon: Network,
      isAvailable: isStep3Available,
      isCompleted: Boolean(hldData),
    },
    {
      step: 4,
      title: "4. Low-Level Designs",
      icon: Boxes,
      isAvailable: isStep4Available,
      isCompleted: Object.values(lldStatus).some((s) => s === "READY"),
    },
  ];

  return (
    <div className="shrink-0 flex items-center justify-between border-b border-gray-200/80 bg-white/90 px-4 py-2 backdrop-blur-md dark:border-gray-800/80 dark:bg-black/90">
      <div className="flex items-center gap-1 sm:gap-2 overflow-x-auto py-0.5">
        {steps.map(({ step, title, icon: Icon, isAvailable, isCompleted }, idx) => {
          const isActive = activePipelineStep === step;
          return (
            <div key={step} className="flex items-center">
              <button
                onClick={() => {
                  if (isAvailable) {
                    setActivePipelineStep(step);
                  }
                }}
                disabled={!isAvailable}
                className={clsx(
                  "group flex items-center gap-2 rounded-xl px-3 py-1.5 text-xs font-semibold transition-all whitespace-nowrap",
                  isActive
                    ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-md shadow-indigo-500/20"
                    : isAvailable
                    ? "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800/60"
                    : "cursor-not-allowed text-gray-400 opacity-40 dark:text-gray-600"
                )}
              >
                <div
                  className={clsx(
                    "flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px]",
                    isActive
                      ? "bg-white/20 text-white"
                      : isCompleted
                      ? "bg-emerald-500/20 text-emerald-500 dark:text-emerald-400"
                      : "bg-gray-200 dark:bg-gray-800"
                  )}
                >
                  {isCompleted && !isActive ? (
                    <Check className="h-2.5 w-2.5" />
                  ) : (
                    <Icon className="h-2.5 w-2.5" />
                  )}
                </div>
                <span>{title}</span>
              </button>

              {idx < steps.length - 1 && (
                <ArrowRight className="mx-1 h-3 w-3 text-gray-300 dark:text-gray-700 shrink-0" />
              )}
            </div>
          );
        })}
      </div>

      {/* Right side pipeline status */}
      <div className="hidden lg:flex items-center gap-2 text-[11px] text-gray-500 dark:text-gray-400">
        <span className="flex items-center gap-1 font-medium">
          <Zap className="h-3 w-3 text-indigo-500" />
          <span>Multi-Agent SAE Pipeline</span>
        </span>
      </div>
    </div>
  );
}
