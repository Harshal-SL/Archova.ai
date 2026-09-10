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
          className="fixed left-2 top-16 z-40 rounded-xl border border-neutral-300 bg-white/90 p-2 text-black shadow-md backdrop-blur-md transition-all hover:border-black dark:border-neutral-700 dark:bg-black/90 dark:text-white dark:hover:border-white"
        >
          <PanelLeft className="h-5 w-5" />
        </button>
      )}

      <aside
        className={clsx(
          "flex h-full flex-col border-r border-neutral-200 bg-white transition-all duration-300 dark:border-neutral-800 dark:bg-black",
          sidebarOpen ? "w-72 lg:w-80" : "w-0 overflow-hidden"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-3 border-b border-neutral-200 dark:border-neutral-800 shrink-0">
          <button
            onClick={() => createSession()}
            className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-black text-white dark:bg-white dark:text-black px-3 py-2 text-xs font-bold shadow-sm transition-all hover:bg-neutral-800 dark:hover:bg-neutral-200 active:scale-[0.99]"
          >
            <Plus className="h-4 w-4" />
            New Architecture
          </button>
          <button
            onClick={toggleSidebar}
            title="Collapse sidebar"
            className="ml-2 rounded-xl p-2 text-neutral-500 transition-colors hover:bg-neutral-100 hover:text-black dark:text-neutral-400 dark:hover:bg-neutral-900 dark:hover:text-white"
          >
            <PanelLeftClose className="h-4 w-4" />
          </button>
        </div>

        {/* Sessions list */}
        <div className="flex-1 overflow-y-auto px-2 py-3 space-y-1.5 min-h-[120px]">
          {sessions.length === 0 && (
            <div className="px-3 py-6 text-center">
              <MessageSquare className="mx-auto h-7 w-7 text-neutral-300 dark:text-neutral-700 mb-1.5" />
              <p className="text-xs font-semibold text-neutral-600 dark:text-neutral-400">No architecture sessions yet</p>
              <p className="text-[11px] text-neutral-400 dark:text-neutral-500 mt-0.5">Start a prompt to generate diagrams</p>
            </div>
          )}
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => setActiveSession(s.id)}
              className={clsx(
                "group flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-xs transition-all",
                s.id === activeSessionId
                  ? "border-l-4 border-l-black dark:border-l-white border border-neutral-300 dark:border-neutral-700 bg-neutral-100 dark:bg-neutral-900 font-bold text-black dark:text-white shadow-xs"
                  : "border border-transparent text-neutral-700 hover:border-neutral-200 hover:bg-neutral-50 dark:text-neutral-300 dark:hover:border-neutral-800 dark:hover:bg-neutral-900"
              )}
            >
              <MessageSquare
                className={clsx(
                  "h-4 w-4 shrink-0 transition-colors",
                  s.id === activeSessionId ? "text-black dark:text-white" : "text-neutral-400 group-hover:text-black dark:group-hover:text-white"
                )}
              />
              <span className="truncate flex-1">{s.title}</span>
            </button>
          ))}
        </div>

        {/* User Account footer */}
        <div className="border-t border-neutral-200 p-3 dark:border-neutral-800 shrink-0">
          {user ? (
            <div className="flex items-center justify-between rounded-xl border border-neutral-200 bg-neutral-50 p-2.5 dark:border-neutral-800 dark:bg-neutral-900 shadow-xs">
              <div className="flex min-w-0 items-center gap-2.5">
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-black text-white dark:bg-white dark:text-black text-xs font-bold shadow-sm">
                  {userInitial}
                </div>
                <div className="min-w-0">
                  <p className="truncate text-xs font-bold text-black dark:text-white">
                    {displayName}
                  </p>
                  <p className="truncate text-[10px] text-neutral-500 dark:text-neutral-400">
                    {emailDisplay}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={handleSignOut}
                title="Sign Out"
                aria-label="Sign Out"
                className="rounded-lg p-1.5 text-neutral-400 transition-colors hover:bg-red-500/10 hover:text-red-600 dark:text-neutral-500 dark:hover:text-red-400"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              <Link
                href="/signin"
                className="flex items-center justify-center gap-2 rounded-xl border border-neutral-300 bg-white px-3 py-2 text-xs font-bold text-black transition-all hover:border-black hover:shadow-xs dark:border-neutral-700 dark:bg-black dark:text-white dark:hover:border-white"
              >
                <UserIcon className="h-3.5 w-3.5 text-black dark:text-white" />
                Sign In to Save History
              </Link>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
