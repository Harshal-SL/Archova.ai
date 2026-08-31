"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Cpu,
  LogOut,
  Radio,
  RotateCcw,
  RefreshCw,
  Zap,
} from "lucide-react";
import ThemeToggle from "./ThemeToggle";
import { useAppStore } from "@/lib/store";
import clsx from "clsx";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const isChat = pathname === "/chat";

  const {
    user,
    initAuth,
    signOut,
    apiConnected,
    apiVersion,
    checkApiHealth,
    generationId,
    resetGenerationSession,
  } = useAppStore();

  useEffect(() => {
    initAuth();
    checkApiHealth();
  }, [initAuth, checkApiHealth]);

  const handleSignOut = async () => {
    await signOut();
    router.push("/signin");
  };

  const displayName =
    user?.user_metadata?.name ||
    user?.user_metadata?.full_name ||
    user?.email?.split("@")[0] ||
    "User";

  const userInitial = displayName.charAt(0).toUpperCase();

  return (
    <nav className="fixed top-0 z-50 flex h-14 w-full items-center justify-between border-b border-gray-200 bg-white/80 px-4 backdrop-blur-md dark:border-gray-800 dark:bg-gray-950/80 md:px-6">
      {/* Brand logo */}
      <div className="flex items-center gap-3">
        <Link href="/" className="flex items-center gap-2 font-bold text-lg">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-md shadow-indigo-500/20">
            <Cpu className="h-4 w-4 text-white" />
          </div>
          <span className="bg-gradient-to-r from-indigo-500 to-purple-500 bg-clip-text text-transparent">
            ArchAI
          </span>
        </Link>

        {/* API Connection Health Badge */}
        <div className="hidden sm:flex items-center gap-2">
          <button
            onClick={() => checkApiHealth()}
            title="Click to recheck API health"
            className={clsx(
              "flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold transition-all",
              apiConnected
                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                : "border-amber-500/30 bg-amber-500/10 text-amber-600 dark:text-amber-400 hover:bg-amber-500/20"
            )}
          >
            <span
              className={clsx(
                "h-1.5 w-1.5 rounded-full",
                apiConnected ? "bg-emerald-500 animate-pulse" : "bg-amber-500"
              )}
            />
            <span>{apiConnected ? `Engine: Ready (v${apiVersion})` : "Engine: Initializing..."}</span>
          </button>

          {/* Active Generation ID badge */}
          {generationId && (
            <span className="rounded-full border border-indigo-500/30 bg-indigo-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-indigo-600 dark:text-indigo-400 font-mono">
              ID: {generationId.slice(0, 12)}...
            </span>
          )}
        </div>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-2.5">
        {/* Load Demo Graphics / Test Button */}
        {isChat && (
          <button
            onClick={() => {
              useAppStore.getState().loadDemoData();
            }}
            title="Load Sample Outputs & Test Graphics"
            className="flex items-center gap-1.5 rounded-xl border border-indigo-500/40 bg-indigo-500/10 px-3 py-1.5 text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:bg-indigo-500/20 transition-all shadow-sm"
          >
            <Zap className="h-3.5 w-3.5 text-indigo-500 animate-pulse" />
            <span>Load Demo Outputs</span>
          </button>
        )}

        {/* Reset / New Session */}
        {isChat && generationId && (
          <button
            onClick={resetGenerationSession}
            title="Reset Architecture Session"
            className="flex items-center gap-1 rounded-lg border border-gray-200 bg-gray-50 px-2.5 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-100 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-800"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">New Session</span>
          </button>
        )}

        <ThemeToggle />

        {user ? (
          <div className="flex items-center gap-2">
            <Link
              href="/chat"
              className="flex items-center gap-2 rounded-xl bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
            >
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-xs font-bold text-white shadow-sm">
                {userInitial}
              </div>
              <span className="hidden sm:inline max-w-[120px] truncate">{displayName}</span>
            </Link>
            <button
              onClick={handleSignOut}
              title="Sign Out"
              aria-label="Sign Out"
              className="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-red-500 dark:hover:bg-gray-800"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Link
              href="/signin"
              className="rounded-lg px-3 py-1.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
            >
              Sign In
            </Link>
            <Link
              href="/signup"
              className="rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 px-3.5 py-1.5 text-sm font-medium text-white shadow-sm transition-opacity hover:opacity-90"
            >
              Sign Up
            </Link>
          </div>
        )}
      </div>
    </nav>
  );
}
