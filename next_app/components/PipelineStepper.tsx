"use client";

import { MessageSquare, FileText, Network, Boxes, Check, ArrowRight } from "lucide-react";
import { useAppStore, type PipelineStep } from "@/lib/store";
import clsx from "clsx";

export default function PipelineStepper() {
  const {
    activePipelineStep,
    setActivePipelineStep,
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
    <div className="shrink-0 flex items-center justify-between border-b border-neutral-200/70 bg-white/70 px-4 py-2 backdrop-blur-2xl backdrop-saturate-150 shadow-xs dark:border-white/10 dark:bg-black/60">
      <div className="flex items-center gap-1.5 sm:gap-2 overflow-x-auto py-0.5">
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
                    ? "bg-black text-white dark:bg-white dark:text-black shadow-xs"
                    : isAvailable
                    ? "text-neutral-700 hover:bg-black/5 hover:text-black dark:text-neutral-300 dark:hover:bg-white/10 dark:hover:text-white"
                    : "cursor-not-allowed text-neutral-400 opacity-40 dark:text-neutral-600"
                )}
              >
                <div
                  className={clsx(
                    "flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px]",
                    isActive
                      ? "bg-neutral-800 text-white dark:bg-neutral-200 dark:text-black"
                      : isCompleted
                      ? "border border-neutral-400 bg-neutral-200 text-neutral-900 dark:border-neutral-600 dark:bg-neutral-800 dark:text-neutral-100 font-bold"
                      : "bg-neutral-200 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400"
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
                <ArrowRight className="mx-1 h-3 w-3 text-neutral-300 dark:text-neutral-700 shrink-0" />
              )}
            </div>
          );
        })}
      </div>

      {/* Right side pipeline status */}
      <div className="hidden lg:flex items-center gap-2 text-xs font-semibold text-neutral-500 dark:text-neutral-400">
        <span className="flex items-center gap-1.5">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-black dark:bg-white opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-black dark:bg-white" />
          </span>
          <span className="text-black dark:text-white font-bold">Multi-Agent SAE Pipeline</span>
        </span>
      </div>
    </div>
  );
}
