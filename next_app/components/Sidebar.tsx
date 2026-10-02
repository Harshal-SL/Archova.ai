"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Plus,
  MessageSquare,
  PanelLeftClose,
  PanelLeft,
  LogOut,
  User as UserIcon,
  Trash2,
  Cpu,
  Moon,
  Sun,
  Search,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import { cn } from "@/lib/utils";

export default function Sidebar() {
  const router = useRouter();
  const {
    sidebarOpen,
    toggleSidebar,
    sessions,
    activeSessionId,
    createSession,
    setActiveSession,
    user,
    signOut,
    theme,
    toggleTheme,
  } = useAppStore();

  const [searchFilter, setSearchFilter] = useState("");

  const handleSignOut = async () => {
    await signOut();
    router.push("/signin");
  };

  const displayName =
    user?.user_metadata?.name ||
    user?.user_metadata?.full_name ||
    user?.email?.split("@")[0] ||
    "Harshal";

  const emailDisplay = user?.email || "Guest Architecture Mode";
  const userInitial = displayName.charAt(0).toUpperCase();

  const filteredSessions = sessions.filter((s) =>
    s.title.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <>
      {/* Floating Toggle button when sidebar is collapsed */}
      {!sidebarOpen && (
        <button
          type="button"
          onClick={toggleSidebar}
          aria-label="Open sidebar"
          title="Open sidebar"
          className="fixed left-3 top-3 z-40 flex h-9 w-9 items-center justify-center rounded-xl border border-neutral-200/80 bg-white/70 text-neutral-800 shadow-md backdrop-blur-2xl backdrop-saturate-150 transition-all hover:bg-white hover:text-black dark:border-white/10 dark:bg-black/60 dark:text-neutral-200 dark:hover:bg-neutral-900 dark:hover:text-white cursor-pointer"
        >
          <PanelLeft className="h-4 w-4" />
        </button>
      )}

      {/* Main Sidebar Aside with Glassmorphism */}
      <aside
        className={cn(
          "flex h-full flex-col border-r border-neutral-200/70 bg-white/70 backdrop-blur-2xl backdrop-saturate-150 transition-all duration-300 ease-in-out dark:border-white/10 dark:bg-[#0a0a0a]/65 shadow-[4px_0_24px_-2px_rgba(0,0,0,0.03)] dark:shadow-[4px_0_32px_rgba(0,0,0,0.4)] z-30 shrink-0 select-none",
          sidebarOpen ? "w-72 lg:w-80" : "w-0 -translate-x-full overflow-hidden border-r-0"
        )}
      >
        {/* Top Header & Brand */}
        <div className="flex items-center justify-between p-3.5 border-b border-neutral-200/60 dark:border-white/10 shrink-0 bg-white/40 dark:bg-white/[0.02] backdrop-blur-md">
          <Link
            href="/"
            className="flex items-center gap-2.5 rounded-xl px-2 py-1 text-sm font-bold text-neutral-900 transition-colors hover:opacity-80 dark:text-white"
          >
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-black text-white dark:bg-white dark:text-black shadow-xs">
              <Cpu className="h-4 w-4" />
            </div>
            <span className="tracking-tight font-extrabold text-base">ArchAI</span>
            <span className="rounded-md bg-neutral-200/80 px-1.5 py-0.5 text-[10px] font-mono text-neutral-700 dark:bg-white/10 dark:text-neutral-300">
              v2.5
            </span>
          </Link>

          <button
            type="button"
            onClick={toggleSidebar}
            title="Collapse sidebar"
            className="rounded-lg p-1.5 text-neutral-500 transition-colors hover:bg-black/5 hover:text-black dark:text-neutral-400 dark:hover:bg-white/10 dark:hover:text-white cursor-pointer"
          >
            <PanelLeftClose className="h-4 w-4" />
          </button>
        </div>

        {/* New Architecture Button */}
        <div className="p-3 shrink-0">
          <button
            type="button"
            onClick={() => createSession()}
            className="flex w-full items-center justify-center gap-2 rounded-2xl border border-neutral-300/80 bg-white/80 py-2.5 px-4 text-xs sm:text-sm font-bold text-neutral-900 shadow-xs backdrop-blur-md transition-all duration-200 hover:border-black/40 hover:bg-white hover:shadow-sm dark:border-white/15 dark:bg-white/[0.08] dark:text-white dark:hover:border-white/30 dark:hover:bg-white/[0.14] cursor-pointer active:scale-[0.99]"
          >
            <Plus className="h-4 w-4" />
            <span>New Architecture</span>
          </button>
        </div>

        {/* Search Filter when sessions exist */}
        {sessions.length > 3 && (
          <div className="px-3 pb-2 shrink-0">
            <div className="flex items-center gap-2 rounded-xl border border-neutral-200/80 bg-white/60 px-2.5 py-1.5 text-xs backdrop-blur-md shadow-2xs dark:border-white/10 dark:bg-white/[0.04]">
              <Search className="h-3.5 w-3.5 text-neutral-400" />
              <input
                type="text"
                placeholder="Search architectures..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="w-full bg-transparent text-xs text-neutral-800 placeholder:text-neutral-400 outline-none dark:text-neutral-200"
              />
            </div>
          </div>
        )}

        {/* History / Sessions List */}
        <div className="flex-1 overflow-y-auto px-2.5 py-2 space-y-1 min-h-[140px]">
          <div className="px-2 py-1 text-[11px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
            Recent Architectures
          </div>

          {sessions.length === 0 ? (
            <div className="px-3 py-10 text-center">
              <MessageSquare className="mx-auto h-7 w-7 text-neutral-300 dark:text-neutral-700 mb-2" />
              <p className="text-xs font-semibold text-neutral-700 dark:text-neutral-300">
                No architecture sessions yet
              </p>
              <p className="text-[11px] text-neutral-500 dark:text-neutral-400 mt-1">
                Enter your requirements prompt to synthesize HLD diagrams
              </p>
            </div>
          ) : (
            filteredSessions.map((s) => {
              const isActive = s.id === activeSessionId;
              return (
                <div
                  key={s.id}
                  onClick={() => setActiveSession(s.id)}
                  className={cn(
                    "group relative flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-left text-xs transition-all cursor-pointer",
                    isActive
                      ? "bg-black/[0.08] font-bold text-black backdrop-blur-md dark:bg-white/15 dark:text-white shadow-2xs border-l-2 border-l-black dark:border-l-white"
                      : "text-neutral-700 hover:bg-black/[0.04] hover:text-black dark:text-neutral-400 dark:hover:bg-white/[0.06] dark:hover:text-white"
                  )}
                >
                  <MessageSquare
                    className={cn(
                      "h-3.5 w-3.5 shrink-0 transition-colors",
                      isActive
                        ? "text-black dark:text-white"
                        : "text-neutral-400 group-hover:text-neutral-700 dark:group-hover:text-neutral-300"
                    )}
                  />
                  <span className="truncate flex-1">{s.title}</span>
                </div>
              );
            })
          )}
        </div>

        {/* Docked User Profile below the sidebar */}
        <div className="border-t border-neutral-200/60 p-3 dark:border-white/10 shrink-0 bg-white/40 dark:bg-white/[0.02] backdrop-blur-xl">
          {user ? (
            <div className="flex items-center justify-between rounded-2xl border border-neutral-200/80 bg-white/75 p-2.5 shadow-xs backdrop-blur-md dark:border-white/10 dark:bg-white/[0.06]">
              <div className="flex min-w-0 items-center gap-2.5">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-black text-white text-xs font-bold dark:bg-white dark:text-black shadow-xs">
                  {userInitial}
                </div>
                <div className="min-w-0">
                  <p className="truncate text-xs font-bold text-neutral-900 dark:text-white leading-tight">
                    {displayName}
                  </p>
                  <p className="truncate text-[10px] text-neutral-500 dark:text-neutral-400">
                    {emailDisplay}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={toggleTheme}
                  title="Toggle theme"
                  className="rounded-lg p-1.5 text-neutral-500 transition-colors hover:bg-black/5 hover:text-black dark:text-neutral-400 dark:hover:bg-white/10 dark:hover:text-white cursor-pointer"
                >
                  {theme === "dark" ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
                </button>

                <button
                  type="button"
                  onClick={handleSignOut}
                  title="Sign out"
                  className="rounded-lg p-1.5 text-neutral-500 transition-colors hover:bg-red-50 hover:text-red-600 dark:text-neutral-400 dark:hover:bg-red-950/40 dark:hover:text-red-400 cursor-pointer"
                >
                  <LogOut className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between rounded-2xl border border-neutral-200/80 bg-white/75 p-2.5 shadow-xs backdrop-blur-md dark:border-white/10 dark:bg-white/[0.06]">
              <Link
                href="/signin"
                className="flex min-w-0 items-center gap-2.5 flex-1 hover:opacity-80 transition-opacity"
              >
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-black text-white text-xs font-bold dark:bg-white dark:text-black shadow-xs">
                  {userInitial}
                </div>
                <div className="min-w-0">
                  <p className="truncate text-xs font-bold text-neutral-900 dark:text-white leading-tight">
                    {displayName}
                  </p>
                  <p className="truncate text-[10px] text-blue-500 dark:text-blue-400 font-medium">
                    Sign in to save history
                  </p>
                </div>
              </Link>

              <button
                type="button"
                onClick={toggleTheme}
                title="Toggle theme"
                className="rounded-lg p-1.5 text-neutral-500 transition-colors hover:bg-black/5 hover:text-black dark:text-neutral-400 dark:hover:bg-white/10 dark:hover:text-white cursor-pointer"
              >
                {theme === "dark" ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
              </button>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
