"use client";

import { ArrowLeft, Info } from "lucide-react";
import { useAppStore } from "@/lib/store";
import HLDGraph from "./HLDGraph";
import LLDGraph from "./LLDGraph";

export default function ArchitecturePanel() {
  const { archVisible, archView, setArchView, selectedNode, setSelectedNode, openExplain } =
    useAppStore();

  if (!archVisible) return null;

  const selectedLabel = selectedNode
    ?.replace(/-/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div className="flex h-full w-full flex-col border-l border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-950 lg:w-[480px]">
      {/* Header bar */}
      <div className="flex items-center justify-between border-b border-gray-200 px-3 py-2 dark:border-gray-800">
        <div className="flex items-center gap-2">
          {archView === "lld" && (
            <button
              onClick={() => {
                setArchView("hld");
                setSelectedNode(null);
              }}
              className="flex items-center gap-1 rounded-lg px-2 py-1 text-xs text-gray-500 transition-colors hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              <ArrowLeft className="h-3 w-3" />
              Back to HLD
            </button>
          )}
          <span className="text-xs font-semibold text-gray-400">
            {archView === "hld" ? "High Level Design" : `LLD — ${selectedLabel ?? "Overview"}`}
          </span>
        </div>

        {archView === "lld" && selectedNode && (
          <button
            onClick={() => openExplain(selectedNode)}
            className="flex items-center gap-1 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 px-2.5 py-1 text-xs font-medium text-white transition-opacity hover:opacity-90"
          >
            <Info className="h-3 w-3" />
            Explain
          </button>
        )}
      </div>

      {/* Info strip */}
      <div className="border-b border-gray-200 bg-gray-50 px-3 py-1.5 text-xs text-gray-400 dark:border-gray-800 dark:bg-gray-900">
        {archView === "hld"
          ? "Click any node to explore its Low Level Design"
          : "Click a node to get an AI explanation"}
      </div>

      {/* Graph */}
      <div className="flex-1">
        {archView === "hld" ? <HLDGraph /> : <LLDGraph />}
      </div>
    </div>
  );
}
