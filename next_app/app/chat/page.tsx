"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import {
  PanelLeft,
  ArrowUpRight,
  Sun,
  Moon,
  ChevronDown,
  SquarePen,
  Layers,
} from "lucide-react";
import Sidebar from "@/components/Sidebar";
import ChatWindow from "@/components/ChatWindow";
import HldWorkspace from "@/components/HldWorkspace";
import ExplainModal from "@/components/ExplainModal";
import BubbleBg from "@/components/BubbleBg";
import { useAppStore } from "@/lib/store";
import { cn } from "@/lib/utils";

export default function ChatPage() {
  const {
    sidebarOpen,
    toggleSidebar,
    activeView,
    sessions,
    activeSessionId,
    createSession,
    initAuth,
    theme,
    toggleTheme,
    loadDemoData,
  } = useAppStore();

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  const activeSession = sessions.find((s) => s.id === activeSessionId);
  const sessionTitle = activeSession?.title || "New Architecture";
  const isEmpty = !activeSessionId || (activeSession?.messages?.length ?? 0) === 0;

  return (
    <div className="relative flex h-screen w-full overflow-hidden bg-white text-neutral-900 dark:bg-black dark:text-white transition-colors select-none">
      {/* ── Background with Increased Opacity in Light Mode ── */}
      <BubbleBg opacity="opacity-65 dark:opacity-30" speed="slow" starCount={34} shootingStarCount={4} />

      {/* ── Left Collapsible Sidebar ── */}
      <Sidebar />

      {/* ── Main ChatGPT Style Workspace Column ── */}
      <div className="relative z-10 flex flex-1 flex-col overflow-hidden min-w-0 bg-transparent">
        {/* Top Minimal Workspace Header */}
        <header
          className={cn(
            "flex h-14 w-full items-center justify-between px-4 shrink-0 z-20 transition-all select-none",
            isEmpty
              ? "bg-transparent border-b border-transparent"
              : "border-b border-neutral-200/70 bg-white/70 backdrop-blur-2xl backdrop-saturate-150 dark:border-white/10 dark:bg-black/60 shadow-xs"
          )}
        >
          {/* Left: Sidebar Toggle & ChatGPT Model Selector */}
          <div className="flex items-center gap-2 min-w-0">
            {!sidebarOpen && (
              <button
                type="button"
                onClick={toggleSidebar}
                title="Open sidebar"
                className="flex h-8 w-8 items-center justify-center rounded-xl border border-neutral-200/80 bg-white/70 text-neutral-700 hover:bg-white hover:text-black dark:border-white/10 dark:bg-white/[0.06] dark:text-neutral-300 dark:hover:bg-white/10 cursor-pointer backdrop-blur-md transition-colors"
              >
                <PanelLeft className="h-4 w-4" />
              </button>
            )}

            <div className="flex items-center gap-1.5 rounded-xl px-2.5 py-1 text-sm font-bold text-neutral-800 dark:text-neutral-200 hover:bg-black/5 dark:hover:bg-white/10 transition-colors cursor-pointer">
              <span>ArchAI 4o</span>
              <ChevronDown className="h-3.5 w-3.5 text-neutral-400" />
            </div>

            {!isEmpty && (
              <span className="truncate text-xs font-semibold text-neutral-500 dark:text-neutral-400 ml-1 hidden sm:inline">
                / {sessionTitle}
              </span>
            )}
          </div>




          {/* Right: Load Template, New Session, Theme */}
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={() => {
                loadDemoData();
              }}
              title="Load Basic HLD & LLD Architecture Template"
              className="flex items-center gap-1.5 rounded-xl border border-blue-500/30 bg-blue-500/10 px-3 py-1.5 text-xs font-bold text-blue-600 hover:bg-blue-500/20 dark:border-blue-400/30 dark:bg-blue-950/40 dark:text-blue-300 dark:hover:bg-blue-900/50 backdrop-blur-md transition-all cursor-pointer shadow-2xs"
            >
              <Layers className="h-3.5 w-3.5 text-blue-500" />
              <span className="hidden sm:inline">Load Basic Template</span>
              <span className="sm:hidden">Template</span>
            </button>

            <button
              type="button"
              onClick={() => createSession()}
              title="New Architecture"
              className="flex h-8 w-8 items-center justify-center rounded-xl border border-neutral-200/80 bg-white/70 text-neutral-700 hover:bg-white hover:text-black dark:border-white/10 dark:bg-white/[0.06] dark:text-neutral-300 dark:hover:bg-white/10 cursor-pointer transition-colors shadow-2xs backdrop-blur-md"
            >
              <SquarePen className="h-4 w-4" />
            </button>

            <button
              type="button"
              onClick={toggleTheme}
              title="Toggle theme"
              className="flex h-8 w-8 items-center justify-center rounded-xl border border-neutral-200/80 bg-white/70 text-neutral-700 hover:bg-white hover:text-black dark:border-white/10 dark:bg-white/[0.06] dark:text-neutral-300 dark:hover:bg-white/10 cursor-pointer transition-colors backdrop-blur-md"
            >
              {theme === "dark" ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
            </button>

            <Link
              href="/"
              title="Back to Landing Page"
              className="hidden md:flex items-center gap-1 text-xs font-semibold text-neutral-500 hover:text-black dark:text-neutral-400 dark:hover:text-white transition-colors ml-1 px-2 py-1"
            >
              <span>Home</span>
              <ArrowUpRight className="h-3 w-3" />
            </Link>
          </div>
        </header>

        {/* ── Main Body View Content ── */}
        <main className="relative flex-1 overflow-hidden min-h-0 bg-transparent">
          {activeView === "chat" && <ChatWindow />}
          {activeView === "hld" && <HldWorkspace />}
          {activeView === "split" && (
            <div className="grid h-full w-full grid-cols-2 divide-x divide-neutral-200 dark:divide-neutral-800 overflow-hidden bg-transparent">
              <div className="h-full overflow-hidden bg-transparent">
                <ChatWindow />
              </div>
              <div className="h-full overflow-hidden bg-transparent">
                <HldWorkspace />
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Component Specification Inspector Modal */}
      <ExplainModal />
    </div>
  );
}
