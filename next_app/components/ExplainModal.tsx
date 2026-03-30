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
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="relative mx-4 w-full max-w-lg rounded-2xl border border-gray-200 bg-white p-6 shadow-2xl dark:border-gray-700 dark:bg-gray-900">
        {/* Close */}
        <button
          onClick={closeExplain}
          className="absolute right-3 top-3 rounded-lg p-1 transition-colors hover:bg-gray-100 dark:hover:bg-gray-800"
        >
          <X className="h-5 w-5 text-gray-400" />
        </button>

        {/* Header */}
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600">
            <span className="text-lg font-bold text-white">
              {label[0]}
            </span>
          </div>
          <div>
            <h3 className="text-lg font-bold">{label}</h3>
            <p className="text-xs text-gray-500">Component Explanation</p>
          </div>
        </div>

        {/* Body */}
        <p className="leading-relaxed text-sm text-gray-600 dark:text-gray-300">
          {explanation}
        </p>

        {/* Footer */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={closeExplain}
            className="rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );
}
