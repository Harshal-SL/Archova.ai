"use client";

import { X, Cpu } from "lucide-react";
import { useAppStore } from "@/lib/store";
import { explanations } from "@/lib/mock-data";
import { motion, AnimatePresence } from "framer-motion";

export default function ExplainModal() {
  const { explainOpen, explainNode, closeExplain, sessions, activeSessionId } = useAppStore();

  const activeSession = sessions.find((s) => s.id === activeSessionId);
  const archData = activeSession?.architectureData;

  // Try to find node details from AI-returned LLD data
  let aiDetails: string | null = null;
  if (explainNode && archData?.lldMap) {
    for (const lldEntry of Object.values(archData.lldMap)) {
      const found = lldEntry.nodes.find((n) => n.id === explainNode);
      if (found) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        aiDetails = (found.data as any)?.details ?? null;
        break;
      }
    }
    // Also check HLD nodes
    if (!aiDetails) {
      const hldFound = archData.hldNodes.find((n) => n.id === explainNode);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      if (hldFound) aiDetails = (hldFound.data as any)?.description ?? null;
    }
  }

  const explanation =
    aiDetails ??
    (explainNode && explanations[explainNode]) ??
    "No explanation available for this component.";

  const label = explainNode
    ? explainNode.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
    : "";

  return (
    <AnimatePresence>
      {explainOpen && explainNode && (
        <div className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center bg-black/80 backdrop-blur-sm font-sans p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", stiffness: 400, damping: 30 }}
            className="relative w-full max-w-lg rounded-2xl border border-[#333333] bg-[#0A0A0A] overflow-hidden"
          >
            <button
              onClick={closeExplain}
              className="absolute right-4 top-4 rounded-full p-2 border border-[#2A2A2A] bg-[#111111] text-white transition-colors hover:bg-white hover:text-black z-10"
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </button>

            {/* Header */}
            <div className="border-b border-[#2A2A2A] p-6 pb-4">
              <div className="flex items-center gap-4 pr-10">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white text-black font-bold text-xl">
                  {label[0] ?? <Cpu className="h-5 w-5" />}
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white tracking-tight">{label}</h3>
                  <p className="text-xs font-mono text-[#555555] mt-0.5">Component Details</p>
                </div>
              </div>
            </div>

            {/* Body */}
            <div className="p-6">
              <p className="leading-relaxed text-[15px] text-[#CCCCCC]">{explanation}</p>
            </div>

            {/* Footer */}
            <div className="border-t border-[#2A2A2A] bg-[#050505] px-6 py-4 flex justify-end">
              <button
                onClick={closeExplain}
                className="rounded-lg bg-white px-6 py-2.5 text-sm font-bold text-black transition-transform hover:scale-105 active:scale-95"
              >
                Got it
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
