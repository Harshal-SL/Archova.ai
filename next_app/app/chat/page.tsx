"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  PanelLeft,
  ArrowUpRight,
  Sun,
  Moon,
  ChevronDown,
  SquarePen,
  Layers,
  Plus,
  Trash2,
  Cpu,
} from "lucide-react";
import Sidebar from "@/components/Sidebar";
import ChatWindow from "@/components/ChatWindow";
import dynamic from "next/dynamic";
import BubbleBg from "@/components/BubbleBg";

const HldWorkspace = dynamic(() => import("@/components/HldWorkspace"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center bg-white/50 dark:bg-black/50">
      <div className="flex items-center gap-2 text-xs font-semibold text-neutral-500">
        <Cpu className="h-4 w-4 animate-spin text-[#005dff]" />
        <span>Loading Studio Topology...</span>
      </div>
    </div>
  ),
});

const ExplainModal = dynamic(() => import("@/components/ExplainModal"), {
  ssr: false,
});
import { ShimmerButton } from "@/components/ui/shimmer-button";
import { useAppStore } from "@/lib/store";
import { cn } from "@/lib/utils";

export default function ChatPage() {
  const router = useRouter();
  const {
    user,
    authLoading,
    sidebarOpen,
    toggleSidebar,
    activeView,
    sessions,
    activeSessionId,
    createSession,
    deleteSession,
    initAuth,
    theme,
    toggleTheme,
  } = useAppStore();

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  useEffect(() => {
    if (!authLoading && !user) {
      router.replace("/signin?redirect=/chat");
    }
  }, [authLoading, user, router]);

  const activeSession = sessions.find((s) => s.id === activeSessionId);
  const sessionTitle = activeSession?.title || "New Architecture";
  const isEmpty = !activeSessionId || (activeSession?.messages?.length ?? 0) === 0;

  if (authLoading) {
    return (
      <div className="relative flex h-screen w-full items-center justify-center bg-white dark:bg-black text-neutral-900 dark:text-white transition-colors">
        <BubbleBg opacity="opacity-40" />
        <div className="relative z-10 flex flex-col items-center gap-4 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-black text-white dark:bg-white dark:text-black shadow-lg animate-pulse">
            <Cpu className="h-6 w-6" />
          </div>
          <div className="space-y-1">
            <div className="font-heading font-extrabold text-base tracking-tight">
              Archova<span className="text-[#005dff] dark:text-[#3b82f6]">.ai</span>
            </div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">
              Verifying studio authorization...
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

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
            "flex h-14 w-full items-center justify-between px-2.5 sm:px-4 shrink-0 z-20 transition-all select-none gap-2",
            isEmpty
              ? "bg-transparent border-b border-transparent"
              : "border-b border-neutral-200/70 bg-white/70 backdrop-blur-2xl backdrop-saturate-150 dark:border-white/10 dark:bg-black/60 shadow-xs"
          )}
        >
          {/* Left: Sidebar Toggle & ChatGPT Model Selector */}
          <div className="flex items-center gap-1.5 sm:gap-2 min-w-0">
            {!sidebarOpen && (
              <button
                type="button"
                onClick={toggleSidebar}
                title="Open sidebar"
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-neutral-200/80 bg-white/70 text-neutral-700 hover:bg-white hover:text-black dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-200 dark:hover:bg-[#161619] dark:hover:border-white/20 cursor-pointer backdrop-blur-md transition-colors shadow-2xs"
              >
                <PanelLeft className="h-4 w-4" />
              </button>
            )}

            <div className="flex items-center gap-1 rounded-xl border border-transparent hover:border-neutral-200/80 hover:bg-white/70 dark:hover:border-[#262626] dark:hover:bg-[#0D0D0F] px-2 sm:px-2.5 py-1 text-xs sm:text-sm font-bold text-neutral-800 dark:text-neutral-200 transition-all cursor-pointer backdrop-blur-md shrink-0">
              <span>Archova.ai 4o</span>
              <ChevronDown className="h-3.5 w-3.5 text-neutral-400" />
            </div>

            {!isEmpty && (
              <span className="truncate text-xs font-medium text-neutral-400/70 dark:text-neutral-500/70 opacity-60 ml-1 hidden md:inline max-w-[200px] lg:max-w-[320px]">
                / {sessionTitle}
              </span>
            )}
          </div>

          {/* Right: Delete Session, New Session, Theme */}
          <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
            {activeSessionId && (
              <button
                type="button"
                onClick={() => deleteSession(activeSessionId)}
                title="Delete this architecture chat"
                className="flex h-8 w-8 items-center justify-center rounded-xl border border-neutral-200/80 bg-white/70 text-neutral-500 hover:text-red-600 hover:bg-red-50 hover:border-red-500/30 dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-400 dark:hover:text-red-400 dark:hover:bg-red-950/40 dark:hover:border-red-500/30 transition-all cursor-pointer shadow-2xs"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            )}

            <ShimmerButton
              onClick={() => createSession()}
              borderRadius="12px"
              shimmerColor="#005dff"
              shimmerDuration="2.5s"
              shimmerSize="1.5px"
              background="#0D0D0F"
              className="px-2.5 sm:px-3 py-1.5 text-xs font-bold text-white border border-[#262626] hover:border-[#005dff]/50 transition-all cursor-pointer shadow-xs"
            >
              <div className="flex items-center gap-1.5 text-white font-bold">
                <Plus className="h-3.5 w-3.5 text-[#005dff]" />
                <span className="hidden sm:inline">New Architecture</span>
              </div>
            </ShimmerButton>

            <button
              type="button"
              onClick={toggleTheme}
              title="Toggle theme"
              className="flex h-8 w-8 items-center justify-center rounded-xl border border-neutral-200/80 bg-white/70 text-neutral-700 hover:bg-white hover:text-black dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-200 dark:hover:bg-[#161619] dark:hover:border-white/20 cursor-pointer transition-colors backdrop-blur-md shadow-2xs"
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
            <div className="grid h-full w-full grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-neutral-200 dark:divide-neutral-800 overflow-hidden bg-transparent">
              <div className="h-1/2 md:h-full overflow-hidden bg-transparent">
                <ChatWindow />
              </div>
              <div className="h-1/2 md:h-full overflow-hidden bg-transparent">
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
