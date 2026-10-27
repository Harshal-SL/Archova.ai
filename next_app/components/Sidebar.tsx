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
  LogIn,
  User as UserIcon,
  Trash2,
  Cpu,
  Search,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import { cn } from "@/lib/utils";

import ShootingStarsGrid from "@/components/ui/shooting-stars-grid";
import { ShimmerButton } from "@/components/ui/shimmer-button";

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
  } = useAppStore();

  const [mounted, setMounted] = useState(false);
  const [searchFilter, setSearchFilter] = useState("");

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const handleSignOut = async () => {
    await signOut();
  };

  const displayName =
    user?.user_metadata?.name ||
    user?.user_metadata?.full_name ||
    user?.email?.split("@")[0] ||
    (user ? "Architect" : "Guest Mode");

  const emailDisplay = user?.email || (user ? "Guest Architecture Mode" : "Sign in to sync history");
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
          className="fixed left-3 top-3 z-40 flex h-9 w-9 items-center justify-center rounded-xl border border-neutral-200/50 bg-white/40 text-neutral-800 shadow-md backdrop-blur-2xl backdrop-saturate-150 transition-all hover:bg-white/70 hover:text-black dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-200 dark:hover:bg-[#161619] dark:hover:border-white/20 dark:hover:text-white cursor-pointer"
        >
          <PanelLeft className="h-4 w-4" />
        </button>
      )}

      {/* Main Sidebar Aside with Glassmorphism */}
      <aside
        className={cn(
          "relative flex h-full flex-col border-r border-neutral-200/50 bg-white/35 backdrop-blur-2xl backdrop-saturate-150 transition-all duration-300 ease-in-out dark:border-white/[0.08] dark:bg-black/35 shadow-[4px_0_24px_-2px_rgba(0,0,0,0.03)] dark:shadow-[4px_0_32px_rgba(0,0,0,0.4)] z-30 shrink-0 select-none overflow-hidden",
          sidebarOpen ? "w-72 lg:w-80" : "w-0 -translate-x-full overflow-hidden border-r-0"
        )}
      >
        {/* ── Background Animation Layer inside Sidebar ── */}
        <div
          className="pointer-events-none absolute inset-0 z-0 overflow-hidden opacity-45 dark:opacity-35"
          aria-hidden="true"
        >
          {/* Subtle Ambient Glowing Orbs */}
          <div className="absolute -top-16 -left-16 h-48 w-48 rounded-full bg-blue-500/15 dark:bg-blue-600/20 blur-3xl animate-pulse" />
          <div className="absolute top-1/2 -right-16 h-56 w-56 rounded-full bg-indigo-500/10 dark:bg-indigo-600/15 blur-3xl" />
          <div
            className="absolute -bottom-16 left-1/3 h-48 w-48 rounded-full bg-cyan-500/15 dark:bg-cyan-500/15 blur-3xl animate-pulse"
            style={{ animationDuration: "5s" }}
          />

          {/* Shooting Stars Grid Animation */}
          {mounted && (
            <ShootingStarsGrid
              starCount={24}
              shootingStarCount={3}
              gridSize={36}
              speed="slow"
              glow={true}
              interactive={false}
              className="h-full w-full rounded-none border-none shadow-none min-h-0 bg-transparent dark:bg-transparent"
            >
              {null}
            </ShootingStarsGrid>
          )}
        </div>

        {/* Top Header & Brand */}
        <div className="relative z-10 flex items-center justify-between p-3.5 border-b border-neutral-200/40 dark:border-white/[0.06] shrink-0 bg-white/20 dark:bg-white/[0.01] backdrop-blur-md">
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
        <div className="relative z-10 p-3 shrink-0">
          <ShimmerButton
            onClick={() => createSession()}
            borderRadius="16px"
            shimmerColor="#005dff"
            shimmerDuration="2.5s"
            shimmerSize="2px"
            background="#0D0D0F"
            className="w-full py-2.5 px-4 text-xs sm:text-sm font-bold text-white border border-[#262626] hover:border-[#005dff]/50 transition-all cursor-pointer shadow-xs"
          >
            <div className="flex items-center justify-center gap-2 text-white font-bold">
              <Plus className="h-4 w-4 text-[#005dff]" />
              <span>New Architecture</span>
            </div>
          </ShimmerButton>
        </div>

        {/* Search Filter when sessions exist */}
        {sessions.length > 3 && (
          <div className="relative z-10 px-3 pb-2 shrink-0">
            <div className="flex items-center gap-2 rounded-xl border border-neutral-200/50 bg-white/30 px-2.5 py-1.5 text-xs backdrop-blur-md shadow-2xs dark:border-white/[0.06] dark:bg-white/[0.02]">
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
        <div className="relative z-10 flex-1 overflow-y-auto px-2.5 py-2 space-y-1 min-h-[140px]">
          <div className="px-2 py-1 text-[10.5px] font-bold uppercase tracking-wider text-neutral-400/70 dark:text-neutral-500/70 opacity-60">
            Recent Architectures
          </div>

          {sessions.length === 0 ? (
            <div className="px-3 py-10 text-center">
              <MessageSquare className="mx-auto h-7 w-7 text-neutral-300/80 dark:text-neutral-700/80 mb-2" />
              <p className="text-xs font-semibold text-neutral-700/80 dark:text-neutral-300/80">
                No architecture sessions yet
              </p>
              <p className="text-[11px] text-neutral-500/70 dark:text-neutral-400/70 mt-1">
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
                      ? "bg-white/30 font-bold text-black backdrop-blur-md dark:bg-white/[0.02] dark:text-white shadow-2xs border border-neutral-200/50 dark:border-white/[0.06] border-l-2 border-l-black dark:border-l-white"
                      : "text-neutral-700/80 hover:bg-white/20 hover:text-black dark:text-neutral-400/80 dark:hover:bg-white/[0.02] dark:hover:text-white"
                  )}
                >
                  <MessageSquare
                    className={cn(
                      "h-3.5 w-3.5 shrink-0 transition-colors",
                      isActive
                        ? "text-black dark:text-white"
                        : "text-neutral-400/60 group-hover:text-neutral-700 dark:group-hover:text-neutral-300"
                    )}
                  />
                  <span className="truncate flex-1">{s.title}</span>
                </div>
              );
            })
          )}
        </div>

        {/* Docked User Profile below the sidebar */}
        <div className="relative z-10 border-t border-neutral-200/40 p-3 dark:border-white/[0.06] shrink-0 bg-white/15 dark:bg-white/[0.01] backdrop-blur-xl">
          {user ? (
            <div className="flex items-center justify-between rounded-2xl border border-neutral-200/50 bg-white/30 p-2.5 shadow-2xs backdrop-blur-md dark:border-white/[0.06] dark:bg-white/[0.02] opacity-85 hover:opacity-100 transition-all duration-200">
              <div className="flex min-w-0 items-center gap-2.5">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-black/80 text-white text-xs font-bold dark:bg-white/90 dark:text-black shadow-xs">
                  {userInitial}
                </div>
                <div className="min-w-0">
                  <p className="truncate text-xs font-bold text-neutral-900/90 dark:text-white/90 leading-tight">
                    {displayName}
                  </p>
                  <p className="truncate text-[10px] text-neutral-500/80 dark:text-neutral-400/70">
                    {emailDisplay}
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={handleSignOut}
                title="Log out"
                aria-label="Log out"
                className="flex h-8 w-8 items-center justify-center rounded-xl border border-red-500/25 bg-red-500/10 hover:bg-red-500/20 text-red-600 dark:border-red-500/30 dark:bg-red-950/40 dark:hover:bg-red-900/50 dark:text-red-400 transition-all duration-150 cursor-pointer shadow-2xs group shrink-0"
              >
                <LogOut className="h-4 w-4 text-red-600 dark:text-red-400 transition-transform duration-150 group-hover:scale-110" />
              </button>
            </div>
          ) : (
            <div className="flex items-center justify-between rounded-2xl border border-neutral-200/50 bg-white/30 p-2.5 shadow-2xs backdrop-blur-md dark:border-white/[0.06] dark:bg-white/[0.02] opacity-85 hover:opacity-100 transition-all duration-200">
              <Link
                href="/signin"
                className="flex min-w-0 items-center gap-2.5 flex-1 hover:opacity-80 transition-opacity"
              >
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-neutral-200 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-200 text-xs font-bold shadow-xs">
                  <UserIcon className="h-4 w-4" />
                </div>
                <div className="min-w-0">
                  <p className="truncate text-xs font-bold text-neutral-900/90 dark:text-white/90 leading-tight">
                    Guest Mode
                  </p>
                  <p className="truncate text-[10px] text-sky-600 dark:text-sky-400 font-medium">
                    Sign in to save history
                  </p>
                </div>
              </Link>

              <Link
                href="/signin"
                title="Sign in"
                aria-label="Sign in"
                className="flex h-8 w-8 items-center justify-center rounded-xl border border-sky-500/25 bg-sky-500/10 hover:bg-sky-500/20 text-sky-600 dark:border-sky-500/30 dark:bg-sky-950/40 dark:hover:bg-sky-900/50 dark:text-sky-400 transition-all duration-150 cursor-pointer shadow-2xs group shrink-0"
              >
                <LogIn className="h-4 w-4 text-sky-600 dark:text-sky-400 transition-transform duration-150 group-hover:scale-110" />
              </Link>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
