"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import {
  PanelLeft,
  MessageSquare,
  Network,
  Columns2,
  Cpu,
  Plus,
  ArrowUpRight,
  Sun,
  Moon,
  ChevronDown,
  SquarePen,
} from "lucide-react";
import Sidebar from "@/components/Sidebar";
import ChatWindow from "@/components/ChatWindow";
import HldWorkspace from "@/components/HldWorkspace";
import ExplainModal from "@/components/ExplainModal";
import { useAppStore } from "@/lib/store";
import { cn } from "@/lib/utils";

export default function ChatPage() {
  const {
    sidebarOpen,
    toggleSidebar,
    activeView,
    setActiveView,
    sessions,
    activeSessionId,
    createSession,
    initAuth,
    theme,
    toggleTheme,
    hldData,
  } = useAppStore();

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  const activeSession = sessions.find((s) => s.id === activeSessionId);
  const sessionTitle = activeSession?.title || "New Architecture";
  const isEmpty = !activeSessionId || (activeSession?.messages?.length ?? 0) === 0;

  return (
    <div className="flex h-screen w-full overflow-hidden bg-white text-neutral-900 dark:bg-black dark:text-white transition-colors select-none">
      {/* ── Left Collapsible Sidebar ── */}
      <Sidebar />

      {/* ── Main ChatGPT Style Workspace Column ── */}
      <div className="flex flex-1 flex-col overflow-hidden min-w-0 bg-white dark:bg-black">
        {/* Top Minimal Workspace Header */}
        <header
          className={cn(
            "flex h-14 w-full items-center justify-between px-4 shrink-0 z-20 transition-all select-none",
            isEmpty
              ? "bg-transparent border-b border-transparent"
              : "border-b border-neutral-200/80 bg-white/90 backdrop-blur-xl dark:border-neutral-800/80 dark:bg-black/90"
          )}
        >
          {/* Left: Sidebar Toggle & ChatGPT Model Selector */}
          <div className="flex items-center gap-2 min-w-0">
            {!sidebarOpen && (
              <button
                type="button"
                onClick={toggleSidebar}
                title="Open sidebar"
                className="flex h-8 w-8 items-center justify-center rounded-xl border border-neutral-200 bg-neutral-100 text-neutral-700 hover:bg-neutral-200 dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-300 dark:hover:bg-neutral-800 cursor-pointer"
              >
                <PanelLeft className="h-4 w-4" />
              </button>
            )}

            <div className="flex items-center gap-1.5 rounded-xl px-2.5 py-1 text-sm font-bold text-neutral-800 dark:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-800/70 transition-colors cursor-pointer">
              <span>ArchAI 4o</span>
              <ChevronDown className="h-3.5 w-3.5 text-neutral-400" />
            </div>

            {!isEmpty && (
              <span className="truncate text-xs font-semibold text-neutral-500 dark:text-neutral-400 ml-1 hidden sm:inline">
                / {sessionTitle}
              </span>
            )}
          </div>

          {/* Center: View Switcher (Only visible during active conversation or when HLD ready) */}
          {!isEmpty && (
            <div className="flex items-center rounded-2xl border border-neutral-200 bg-neutral-100/90 p-1 dark:border-neutral-800 dark:bg-neutral-900/90 shadow-2xs">
              {/* Tab 1: Chat & AI Interview */}
              <button
                type="button"
                onClick={() => setActiveView("chat")}
                className={cn(
                  "flex items-center gap-1.5 rounded-xl px-3 py-1 text-xs font-semibold transition-all cursor-pointer",
                  activeView === "chat"
                    ? "bg-white text-black shadow-xs dark:bg-black dark:text-white font-bold"
                    : "text-neutral-600 hover:text-black dark:text-neutral-400 dark:hover:text-white"
                )}
              >
                <MessageSquare className="h-3.5 w-3.5" />
                <span>Chat</span>
              </button>

              {/* Tab 2: HLD Architecture Only */}
              <button
                type="button"
                onClick={() => setActiveView("hld")}
                className={cn(
                  "flex items-center gap-1.5 rounded-xl px-3 py-1 text-xs font-semibold transition-all cursor-pointer",
                  activeView === "hld"
                    ? "bg-white text-black shadow-xs dark:bg-black dark:text-white font-bold"
                    : "text-neutral-600 hover:text-black dark:text-neutral-400 dark:hover:text-white"
                )}
              >
                <Network className="h-3.5 w-3.5" />
                <span>HLD Diagram</span>
                {Boolean(hldData) && (
                  <span className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-pulse" />
                )}
              </button>

              {/* Tab 3: Split View (Side-by-Side on desktop) */}
              <button
                type="button"
                onClick={() => setActiveView("split")}
                className={cn(
                  "hidden xl:flex items-center gap-1.5 rounded-xl px-3 py-1 text-xs font-semibold transition-all cursor-pointer",
                  activeView === "split"
                    ? "bg-white text-black shadow-xs dark:bg-black dark:text-white font-bold"
                    : "text-neutral-600 hover:text-black dark:text-neutral-400 dark:hover:text-white"
                )}
                title="View Chat and HLD side-by-side"
              >
                <Columns2 className="h-3.5 w-3.5" />
                <span>Split</span>
              </button>
            </div>
          )}

          {/* Right: Quick actions & Theme */}
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={() => createSession()}
              title="New Architecture"
              className="flex h-8 w-8 items-center justify-center rounded-xl border border-neutral-200 bg-white text-neutral-700 hover:bg-neutral-100 dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-300 dark:hover:bg-neutral-800 cursor-pointer transition-colors shadow-2xs"
            >
              <SquarePen className="h-4 w-4" />
            </button>

            <button
              type="button"
              onClick={toggleTheme}
              title="Toggle theme"
              className="flex h-8 w-8 items-center justify-center rounded-xl border border-neutral-200 bg-white text-neutral-700 hover:bg-neutral-100 dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-300 dark:hover:bg-neutral-800 cursor-pointer transition-colors"
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
        <main className="relative flex-1 overflow-hidden min-h-0 bg-white dark:bg-black">
          {activeView === "chat" && <ChatWindow />}
          {activeView === "hld" && <HldWorkspace />}
          {activeView === "split" && (
            <div className="grid h-full w-full grid-cols-2 divide-x divide-neutral-200 dark:divide-neutral-800 overflow-hidden">
              <div className="h-full overflow-hidden">
                <ChatWindow />
              </div>
              <div className="h-full overflow-hidden">
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
