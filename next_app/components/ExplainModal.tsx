"use client";

import { X } from "lucide-react";
import { useAppStore } from "@/lib/store";
import { explanations } from "@/lib/mock-data";

export default function ExplainModal() {
  const { explainOpen, explainNode, closeExplain } = useAppStore();

  if (!explainOpen || !explainNode) return null;

  const explanation =
    explanations[explainNode] ?? "No explanation available for this component.";
  const label = explainNode.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-[#0F172A]/40 backdrop-blur-sm dark:bg-black/60">
      <div className="relative mx-4 w-full max-w-lg rounded-2xl border border-[#E2E8F0] bg-[#FFFFFF] p-6 shadow-2xl dark:border-gray-700 dark:bg-gray-900">
        {/* Close */}
        <button
          onClick={closeExplain}
          aria-label="Close explanation"
          title="Close"
          className="absolute right-3 top-3 rounded-lg p-1 transition-colors hover:bg-slate-100 dark:hover:bg-gray-800"
        >
          <X className="h-5 w-5 text-[#64748B] dark:text-gray-400" />
        </button>

        {/* Header */}
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#10B981]">
            <span className="text-lg font-bold text-white">
              {label[0]}
            </span>
          </div>
          <div>
            <h3 className="text-lg font-bold text-[#0F172A] dark:text-white">{label}</h3>
            <p className="text-xs text-[#64748B] dark:text-gray-400">Component Explanation</p>
          </div>
        </div>

        {/* Body */}
        <p className="leading-relaxed text-sm text-[#64748B] dark:text-gray-300">
          {explanation}
        </p>

        {/* Footer */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={closeExplain}
            className="rounded-lg bg-[#2563EB] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[#1D4ED8]"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );
}
