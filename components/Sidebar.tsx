"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Plus,
  MessageSquare,
  PanelLeftClose,
  PanelLeft,
  LogOut,
  User as UserIcon,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import TerminalConsole from "./TerminalConsole";
import clsx from "clsx";

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

  const handleSignOut = async () => {
    await signOut();
    router.push("/signin");
  };

  const displayName =
    user?.user_metadata?.name ||
    user?.user_metadata?.full_name ||
    user?.email?.split("@")[0] ||
    "Guest User";

  const emailDisplay = user?.email || "Not signed in";
  const userInitial = displayName.charAt(0).toUpperCase();

  return (
    <>
      {/* Collapse/Expand button when closed */}
      {!sidebarOpen && (
        <button
          onClick={toggleSidebar}
          aria-label="Open sidebar"
          title="Open sidebar"
          className="fixed left-2 top-16 z-40 rounded-lg bg-gray-100 p-2 shadow-md transition-colors hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700"
        >
          <PanelLeft className="h-5 w-5 text-gray-600 dark:text-gray-400" />
        </button>
      )}

      <aside
        className={clsx(
          "flex h-full flex-col border-r border-gray-200 bg-gray-50 transition-all duration-300 dark:border-gray-800 dark:bg-[#0d1117]",
          sidebarOpen ? "w-72 lg:w-80" : "w-0 overflow-hidden"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-3 border-b border-gray-200 dark:border-gray-800 shrink-0">
          <button
            onClick={() => createSession()}
            className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 px-3 py-2 text-sm font-medium text-white shadow-sm transition-opacity hover:opacity-90"
          >
            <Plus className="h-4 w-4" />
            New Architecture
          </button>
          <button
            onClick={toggleSidebar}
            title="Collapse sidebar"
            className="ml-2 rounded-lg p-2 transition-colors hover:bg-gray-200 dark:hover:bg-gray-800"
          >
            <PanelLeftClose className="h-4 w-4 text-gray-500" />
          </button>
        </div>

        {/* Sessions list */}
        <div className="flex-1 overflow-y-auto px-2 py-3 space-y-1 min-h-[120px]">
          {sessions.length === 0 && (
            <div className="px-3 py-6 text-center">
              <MessageSquare className="mx-auto h-7 w-7 text-gray-300 dark:text-gray-700 mb-1.5" />
              <p className="text-xs text-gray-400">No architecture sessions yet</p>
              <p className="text-[11px] text-gray-400 mt-0.5">Start a prompt to generate diagrams</p>
            </div>
          )}
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => setActiveSession(s.id)}
              className={clsx(
                "group flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-sm transition-all",
                s.id === activeSessionId
                  ? "bg-white font-medium text-indigo-600 shadow-sm dark:bg-gray-800 dark:text-indigo-400"
                  : "text-gray-600 hover:bg-gray-200/70 dark:text-gray-400 dark:hover:bg-gray-800/50"
              )}
            >
              <MessageSquare
                className={clsx(
                  "h-4 w-4 shrink-0 transition-colors",
                  s.id === activeSessionId ? "text-indigo-500" : "text-gray-400"
                )}
              />
              <span className="truncate flex-1">{s.title}</span>
            </button>
          ))}
        </div>

        {/* Cleanly Merged AI Architecture Pipeline Logs */}
        <div className="shrink-0">
          <TerminalConsole />
        </div>

        {/* User Account footer */}
        <div className="border-t border-gray-200 p-3 dark:border-gray-800 shrink-0">
          {user ? (
            <div className="flex items-center justify-between rounded-xl border border-gray-200 bg-white p-2.5 dark:border-gray-800 dark:bg-gray-900 shadow-sm">
              <div className="flex min-w-0 items-center gap-2.5">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-xs font-bold text-white shadow-sm">
                  {userInitial}
                </div>
                <div className="min-w-0">
                  <p className="truncate text-xs font-semibold text-gray-900 dark:text-gray-100">
                    {displayName}
                  </p>
                  <p className="truncate text-[11px] text-gray-500 dark:text-gray-400">
                    {emailDisplay}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={handleSignOut}
                title="Sign Out"
                aria-label="Sign Out"
                className="rounded-lg p-1.5 text-gray-400 transition-colors hover:bg-gray-100 hover:text-red-500 dark:hover:bg-gray-800"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              <Link
                href="/signin"
                className="flex items-center justify-center gap-2 rounded-xl border border-gray-300 bg-white px-3 py-2 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200 dark:hover:bg-gray-800"
              >
                <UserIcon className="h-3.5 w-3.5" />
                Sign In to Save History
              </Link>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
