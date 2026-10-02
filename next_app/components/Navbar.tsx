"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Cpu,
  LogOut,
  RotateCcw,
  Zap,
  ArrowUpRight,
  Layers,
} from "lucide-react";
import ThemeToggle from "./ThemeToggle";
import { useAppStore, type PipelineStep } from "@/lib/store";
import clsx from "clsx";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const isChat = pathname === "/chat";
  const isLanding = pathname === "/";

  const {
    user,
    initAuth,
    signOut,
    generationId,
    resetGenerationSession,
    activePipelineStep,
    setActivePipelineStep,
  } = useAppStore();

  useEffect(() => {
    initAuth();
  }, [initAuth]);

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

  const navLinks = [
    { label: "Home", href: isLanding ? "#home" : "/#home" },
    { label: "About", href: isLanding ? "#about" : "/#about" },
    { label: "Services", href: isLanding ? "#services" : "/#services" },
  ];

  return (
    <nav className="fixed top-0 z-50 flex h-14 w-full items-center justify-between border-b border-neutral-200 bg-white/90 px-4 backdrop-blur-xl transition-colors dark:border-neutral-800 dark:bg-black/90 md:px-8">
      {/* Brand logo & Nav links */}
      <div className="flex items-center gap-6 lg:gap-8">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-black text-white dark:bg-white dark:text-black shadow-sm transition-transform duration-200 group-hover:scale-105">
            <Cpu className="h-4 w-4" />
          </div>
          <span className="font-heading font-extrabold text-lg tracking-tight text-black dark:text-white">
            Arch<span className="text-neutral-500 dark:text-neutral-400">AI</span>
          </span>
        </Link>

        {/* Section Links for Landing Page */}
        {!isChat && (
          <div className="hidden md:flex items-center gap-6 text-xs font-semibold text-neutral-600 dark:text-neutral-400">
            {navLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="transition-colors hover:text-black dark:hover:text-white"
              >
                {link.label}
              </a>
            ))}
          </div>
        )}

        {/* View Switcher for Chat Studio */}
        {isChat && (
          <div className="hidden md:flex items-center rounded-lg border border-neutral-300 bg-neutral-100 p-0.5 dark:border-neutral-800 dark:bg-neutral-900">
            {[
              { step: 1, label: "1. Interview" },
              { step: 2, label: "2. ARSRS Spec" },
              { step: 3, label: "3. Visual HLD" },
              { step: 4, label: "4. Low-Level Designs" },
            ].map(({ step, label }) => (
              <button
                key={step}
                onClick={() => setActivePipelineStep(step as PipelineStep)}
                className={clsx(
                  "rounded-md px-3 py-1 text-xs font-semibold transition-all",
                  activePipelineStep === step
                    ? "bg-black text-white shadow-xs dark:bg-white dark:text-black"
                    : "text-neutral-600 hover:text-black dark:text-neutral-400 dark:hover:text-white"
                )}
              >
                {label}
              </button>
            ))}
          </div>
        )}

        {/* Frontend Standalone Sample Mode Badge */}
        <div className="hidden sm:flex items-center gap-2">
          <span className="flex items-center gap-1.5 rounded-full border border-neutral-300 bg-neutral-100 px-2.5 py-0.5 text-[11px] font-semibold text-black dark:border-neutral-700 dark:bg-neutral-900 dark:text-white">
            <span className="h-1.5 w-1.5 rounded-full bg-black dark:bg-white animate-pulse" />
            <span>Sample Mode</span>
          </span>

          {/* Active Generation ID badge */}
          {generationId && isChat && (
            <span className="rounded-full border border-neutral-300 bg-neutral-100 px-2.5 py-0.5 text-[11px] font-semibold text-neutral-800 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-200 font-mono">
              ID: {generationId.slice(0, 8)}...
            </span>
          )}
        </div>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-3">
        {/* Load Basic HLD & LLD Template Button on Chat */}
        {isChat && (
          <button
            onClick={() => {
              useAppStore.getState().loadDemoData();
            }}
            title="Load Basic HLD & LLD Architecture Template"
            className="flex items-center gap-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 px-3 py-1.5 text-xs font-bold text-blue-600 hover:bg-blue-500/20 dark:border-blue-400/30 dark:bg-blue-950/40 dark:text-blue-300 dark:hover:bg-blue-900/50 transition-all shadow-xs cursor-pointer"
          >
            <Layers className="h-3.5 w-3.5 text-blue-500" />
            <span>Load Basic Template</span>
          </button>
        )}

        {/* Reset / New Session */}
        {isChat && generationId && (
          <button
            onClick={resetGenerationSession}
            title="Reset Architecture Session"
            className="flex items-center gap-1 rounded-full border border-neutral-300 bg-white px-2.5 py-1.5 text-xs font-semibold text-neutral-700 hover:border-black hover:text-black dark:border-neutral-700 dark:bg-black dark:text-neutral-300 dark:hover:border-white dark:hover:text-white transition-colors cursor-pointer"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">New Session</span>
          </button>
        )}

        {/* Fast links from outside Chat */}
        {!isChat && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                useAppStore.getState().loadDemoData();
                router.push("/chat");
              }}
              title="Load Basic HLD & LLD Architecture Template"
              className="hidden sm:inline-flex items-center gap-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 px-3 py-1.5 text-xs font-bold text-blue-600 hover:bg-blue-500/20 dark:border-blue-400/30 dark:bg-blue-950/40 dark:text-blue-300 dark:hover:bg-blue-900/50 transition-all cursor-pointer shadow-xs"
            >
              <Layers className="h-3.5 w-3.5 text-blue-500" />
              <span>Load Template</span>
            </button>
            <Link
              href="/chat"
              className="hidden sm:inline-flex items-center gap-1 rounded-full border border-neutral-300 bg-neutral-100 px-3 py-1 text-xs font-semibold text-neutral-900 hover:bg-neutral-200 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100 dark:hover:bg-neutral-800 transition-all"
            >
              <span>Studio</span>
              <ArrowUpRight className="h-3 w-3" />
            </Link>
          </div>
        )}

        <ThemeToggle />

        {user ? (
          <div className="flex items-center gap-2">
            <Link
              href="/chat"
              className="flex items-center gap-2 rounded-full border border-neutral-300 bg-white px-3 py-1 text-xs font-medium text-black transition-colors hover:border-black dark:border-neutral-700 dark:bg-black dark:text-white dark:hover:border-white"
            >
              <div className="flex h-5 w-5 items-center justify-center rounded-full bg-black text-white dark:bg-white dark:text-black text-[10px] font-bold shadow-sm">
                {userInitial}
              </div>
              <span className="hidden sm:inline max-w-[120px] truncate">{displayName}</span>
            </Link>
            <button
              onClick={handleSignOut}
              title="Sign Out"
              aria-label="Sign Out"
              className="rounded-full p-1.5 text-neutral-500 transition-colors hover:bg-neutral-100 hover:text-black dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-white"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Link
              href="/signin"
              className="rounded-full px-3 py-1.5 text-xs font-semibold text-neutral-700 transition-colors hover:text-black dark:text-neutral-300 dark:hover:text-white"
            >
              Sign In
            </Link>
            <Link
              href="/signup"
              className="rounded-full bg-black px-4 py-1.5 text-xs font-bold text-white shadow-sm transition-all hover:bg-neutral-800 dark:bg-white dark:text-black dark:hover:bg-neutral-200 hover:-translate-y-0.5 active:translate-y-0"
            >
              Get Started
            </Link>
          </div>
        )}
      </div>
    </nav>
  );
}
