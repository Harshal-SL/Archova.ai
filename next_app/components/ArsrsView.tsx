"use client";

import { useState } from "react";
import {
  FileText,
  Copy,
  Check,
  ArrowLeft,
  ArrowRight,
} from "lucide-react";
import { useAppStore } from "@/lib/store";

export default function ArsrsView() {
  const { arsrsData, setActivePipelineStep } = useAppStore();
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!arsrsData) return;
    navigator.clipboard.writeText(JSON.stringify(arsrsData, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex h-full flex-col bg-white text-black dark:bg-black dark:text-white transition-colors">
      {/* Top action header */}
      <div className="flex items-center justify-between border-b border-neutral-200 bg-white/90 px-6 py-3.5 backdrop-blur-md dark:border-neutral-800 dark:bg-black/90">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-black text-white dark:bg-white dark:text-black shadow-sm">
            <FileText className="h-4 w-4" />
          </div>
          <div>
            <h2 className="font-heading text-sm font-bold tracking-tight text-black dark:text-white">
              Architecture-Ready Structured Requirements (ARSRS)
            </h2>
            <p className="text-[11px] text-neutral-500 dark:text-neutral-400">
              Formally synthesized requirements specification from REE engine
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 rounded-full border border-neutral-300 bg-white px-3 py-1.5 text-xs font-semibold text-neutral-800 shadow-xs transition-all hover:border-black hover:text-black dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-200 dark:hover:border-white dark:hover:text-white"
          >
            {copied ? (
              <Check className="h-3.5 w-3.5 text-black dark:text-white" />
            ) : (
              <Copy className="h-3.5 w-3.5" />
            )}
            <span>{copied ? "Copied" : "Copy JSON"}</span>
          </button>

          <button
            onClick={() => setActivePipelineStep(3)}
            className="flex items-center gap-1.5 rounded-full bg-black text-white dark:bg-white dark:text-black px-4 py-1.5 text-xs font-semibold shadow-sm transition-all hover:bg-neutral-800 dark:hover:bg-neutral-200"
          >
            <span>Proceed to Visual HLD</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Main Document Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-4xl space-y-6">
          {arsrsData ? (
            <div className="rounded-3xl border border-neutral-300 border-t-4 border-t-black dark:border-neutral-800 dark:border-t-white bg-white dark:bg-[#0a0a0a] p-6 shadow-xl font-mono text-xs leading-relaxed text-black dark:text-white">
              <div className="mb-4 flex items-center justify-between border-b border-neutral-200 pb-3 dark:border-neutral-800">
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-black dark:bg-white animate-pulse" />
                  <span className="font-heading text-xs font-bold uppercase tracking-wider text-black dark:text-white">
                    Synthesized Specification Document
                  </span>
                </div>
                <span className="rounded-full bg-neutral-100 px-2.5 py-0.5 text-[10px] font-bold text-neutral-800 dark:bg-neutral-900 dark:text-neutral-200 border border-neutral-300 dark:border-neutral-700">
                  READY
                </span>
              </div>
              <pre className="overflow-x-auto whitespace-pre-wrap">
                {JSON.stringify(arsrsData, null, 2)}
              </pre>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-neutral-100 text-black dark:bg-neutral-900 dark:text-white border border-neutral-300 dark:border-neutral-700 shadow-sm">
                <FileText className="h-8 w-8" />
              </div>
              <p className="font-heading text-base font-bold text-black dark:text-white">
                No ARSRS Document Generated Yet
              </p>
              <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1 max-w-sm leading-relaxed">
                Submit a problem statement in Step 1 and complete the stakeholder interview
                to generate the ARSRS document.
              </p>
              <button
                onClick={() => setActivePipelineStep(1)}
                className="mt-5 flex items-center gap-1.5 rounded-full bg-black text-white dark:bg-white dark:text-black px-5 py-2.5 text-xs font-semibold shadow-sm transition-all hover:bg-neutral-800 dark:hover:bg-neutral-200"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                <span>Go to Step 1: Prompt & Interview</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Slider Footer */}
      <div className="flex items-center justify-between border-t border-neutral-200/70 bg-white/70 px-6 py-3 backdrop-blur-2xl backdrop-saturate-150 dark:border-white/10 dark:bg-black/60 shadow-lg">
        <button
          onClick={() => setActivePipelineStep(1)}
          className="flex items-center gap-1.5 rounded-full border border-neutral-200/80 bg-white/80 px-4 py-2 text-xs font-semibold text-neutral-800 backdrop-blur-md transition-colors hover:border-black dark:border-white/10 dark:bg-white/[0.06] dark:text-neutral-200 dark:hover:border-white"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Prompt & Interview</span>
        </button>

        <button
          onClick={() => setActivePipelineStep(3)}
          className="flex items-center gap-1.5 rounded-full bg-black text-white dark:bg-white dark:text-black px-5 py-2 text-xs font-semibold shadow-sm transition-all hover:bg-neutral-800 dark:hover:bg-neutral-200"
        >
          <span>Proceed to Visual HLD</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
