"use client";

import React from "react";
import { useAppStore } from "@/lib/store";
import HLDGraph from "./HLDGraph";
import LldsView from "./LldsView";
import ValidationView from "./ValidationView";
import TubelightChatBar from "./TubelightChatBar";

export default function HldWorkspace() {
  const {
    hldWorkspaceTab,
    setHldWorkspaceTab,
    jumpToLld,
  } = useAppStore();

  return (
    <div className="relative flex h-full w-full flex-col overflow-hidden bg-transparent text-black dark:text-white transition-colors">
      {/* Main Content: HLD Diagram Canvas, 5 LLDs Concurrency View, or Validation View */}
      <div className="relative flex-1 bg-transparent min-h-0 overflow-hidden">
        {hldWorkspaceTab === "hld" ? (
          <HLDGraph onSelectLld={(lldType) => jumpToLld(lldType)} />
        ) : hldWorkspaceTab === "validation" ? (
          <ValidationView />
        ) : (
          <LldsView onBackToHld={() => setHldWorkspaceTab("hld")} />
        )}
      </div>

      {/* ── Tubelight Chat Bar & Floating Moveable/Resizable Chat Window ── */}
      <TubelightChatBar />
    </div>
  );
}
