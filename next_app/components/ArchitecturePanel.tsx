"use client";

import { ArrowLeft, Info, HelpCircle } from "lucide-react";
import { useAppStore } from "@/lib/store";
import { motion, AnimatePresence } from "framer-motion";
import HLDGraph from "./HLDGraph";
import LLDGraph from "./LLDGraph";

export default function ArchitecturePanel() {
  const { archVisible, archView, setArchView, selectedNode, setSelectedNode, openExplain } =
    useAppStore();

  const selectedLabel = selectedNode
    ?.replace(/-/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <AnimatePresence>
      {archVisible && (
        <motion.div
          initial={{ x: "100%", opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: "100%", opacity: 0 }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className="flex h-full w-full flex-col border-l border-[#2A2A2A] bg-[#0F0F0F] font-sans lg:w-[600px] z-10 shadow-[-10px_0_30px_rgba(0,0,0,0.5)]"
        >
          {/* Header bar */}
          <div className="flex items-center justify-between border-b border-[#2A2A2A] px-4 py-3 bg-[#0A0A0A]">
            <div className="flex items-center gap-4">
              <div className="flex space-x-1">
                <button
                  onClick={() => {
                    setArchView("hld");
                    setSelectedNode(null);
                  }}
                  className={`px-3 py-1.5 text-sm font-semibold transition-all border-b-2 ${
                    archView === "hld"
                      ? "border-white text-white"
                      : "border-transparent text-[#555] hover:text-[#AAAAAA]"
                  }`}
                >
                  HLD
                </button>
                <div
                  className={`px-3 py-1.5 text-sm font-semibold transition-all border-b-2 ${
                    archView === "lld"
                      ? "border-white text-white"
                      : "border-transparent text-[#555]"
                  } ${archView !== "lld" && !selectedNode ? "opacity-50 cursor-not-allowed" : ""}`}
                >
                  LLD
                </div>
              </div>
            </div>

            {archView === "lld" && (
              <div className="flex items-center gap-3">
                <button
                  onClick={() => {
                    setArchView("hld");
                    setSelectedNode(null);
                  }}
                  className="flex items-center gap-1 rounded-lg border border-white bg-transparent px-3 py-1.5 text-xs font-semibold text-white transition-opacity hover:opacity-80"
                >
                  <ArrowLeft className="h-3 w-3" />
                  Back to HLD
                </button>
              </div>
            )}
          </div>

          {/* Breadcrumb Info Strip */}
          <div className="border-b border-[#2A2A2A] bg-[#111111] px-4 py-2 text-xs font-mono text-[#AAAAAA] flex justify-between items-center">
             <span>
               {archView === "hld" 
                 ? "HLD › Overview" 
                 : `HLD › ${selectedLabel ?? "Component Details"}`}
             </span>
             {selectedNode && (
               <button
                 onClick={() => openExplain(selectedNode)}
                 className="flex items-center gap-1 text-white hover:underline transition-all"
               >
                 <HelpCircle className="h-3 w-3" /> Explain Node
               </button>
             )}
          </div>

          {/* Graph Layout Container */}
          <div className="flex-1 relative overflow-hidden bg-[#0F0F0F]">
            <AnimatePresence mode="wait">
              {archView === "hld" ? (
                <motion.div
                  key="hld"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.2 }}
                  className="absolute inset-0"
                >
                  <HLDGraph />
                </motion.div>
              ) : (
                <motion.div
                  key="lld"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                  className="absolute inset-0"
                >
                  <LLDGraph />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
