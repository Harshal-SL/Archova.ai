"use client";

import { useState } from "react";
import {
  FileText,
  Copy,
  Check,
  ArrowLeft,
  ArrowRight,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
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
    <div className="flex h-full flex-col bg-white dark:bg-black">
      {/* Top action header */}
      <div className="flex items-center justify-between border-b border-gray-200 bg-white/80 px-6 py-3.5 backdrop-blur-md dark:border-gray-800 dark:bg-black/80">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-sm">
            <FileText className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-gray-900 dark:text-white">
              Architecture-Ready Structured Requirements (ARSRS)
            </h2>
            <p className="text-[11px] text-gray-500">
              Formally synthesized requirements specification from REE engine
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 rounded-xl border border-gray-200 bg-white px-3 py-1.5 text-xs font-semibold text-gray-700 shadow-sm transition-all hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200 dark:hover:bg-gray-800"
          >
            {copied ? (
              <Check className="h-3.5 w-3.5 text-emerald-500" />
            ) : (
              <Copy className="h-3.5 w-3.5" />
            )}
            <span>{copied ? "Copied" : "Copy JSON"}</span>
          </button>

          <button
            onClick={() => setActivePipelineStep(3)}
            className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 px-4 py-1.5 text-xs font-semibold text-white shadow-md shadow-indigo-500/20 transition-all hover:opacity-95"
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
            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900/60 font-mono text-xs leading-relaxed text-gray-800 dark:text-gray-200">
              <pre className="overflow-x-auto whitespace-pre-wrap">
                {JSON.stringify(arsrsData, null, 2)}
              </pre>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <FileText className="h-12 w-12 text-gray-300 dark:text-gray-700 mb-3" />
              <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                No ARSRS Document Generated Yet
              </p>
              <p className="text-xs text-gray-500 mt-1 max-w-sm">
                Submit a problem statement in Step 1 and complete the stakeholder interview
                to generate the ARSRS document.
              </p>
              <button
                onClick={() => setActivePipelineStep(1)}
                className="mt-4 flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white transition-opacity hover:opacity-90"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                <span>Go to Step 1: Prompt & Interview</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Slider Footer */}
      <div className="flex items-center justify-between border-t border-gray-200 bg-white/80 px-6 py-3 backdrop-blur-md dark:border-gray-800 dark:bg-black/80">
        <button
          onClick={() => setActivePipelineStep(1)}
          className="flex items-center gap-1.5 rounded-xl border border-gray-200 bg-white px-4 py-2 text-xs font-semibold text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200 dark:hover:bg-gray-800"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Prompt & Interview</span>
        </button>

        <button
          onClick={() => setActivePipelineStep(3)}
          className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 px-5 py-2 text-xs font-semibold text-white shadow-md shadow-indigo-500/20 transition-all hover:opacity-95"
        >
          <span>Proceed to Visual HLD</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
