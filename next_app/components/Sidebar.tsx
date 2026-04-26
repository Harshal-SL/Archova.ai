"use client";

import { useMemo, useState } from "react";
import { Plus, MessageSquare, PanelLeftClose, Search, User } from "lucide-react";
import { useAppStore } from "@/lib/store";
import clsx from "clsx";

export default function Sidebar() {
  const {
    sidebarOpen,
    toggleSidebar,
    sessions,
    activeSessionId,
    createSession,
    setActiveSession,
  } = useAppStore();
  const [search, setSearch] = useState("");

  const filteredSessions = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return sessions;
    return sessions.filter((s) => s.title.toLowerCase().includes(q));
  }, [sessions, search]);

  return (
    <>
      {sidebarOpen && (
        <button
          aria-label="Close sidebar overlay"
          onClick={toggleSidebar}
          className="fixed inset-0 z-20 bg-black/35 md:hidden"
        />
      )}

      <aside
        className={clsx(
          "fixed inset-y-0 left-0 z-30 flex w-[280px] flex-col border-r border-slate-200 bg-background backdrop-blur-xl transition-all duration-300 dark:border-white/10 dark:bg-background md:relative md:inset-auto",
          sidebarOpen
            ? "translate-x-0 opacity-100"
            : "-translate-x-full opacity-0 md:w-0 md:overflow-hidden md:opacity-100"
        )}
      >
        <div className="flex items-center justify-between px-3 py-3">
          <button
            onClick={() => createSession()}
            className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#2563EB] to-[#1D4ED8] px-3 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-500/25 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-blue-500/30"
          >
            <Plus className="h-4 w-4" />
            New Chat
          </button>
          <button
            onClick={toggleSidebar}
            aria-label="Collapse sidebar"
            title="Collapse sidebar"
            className="ml-2 rounded-xl p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900 dark:text-gray-300 dark:hover:bg-white/10 dark:hover:text-white"
          >
            <PanelLeftClose className="h-4 w-4" />
          </button>
        </div>

        <div className="px-3 pb-2">
          <label className="relative block">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 dark:text-gray-500" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search chats"
              className="h-10 w-full rounded-xl border border-slate-200 bg-white pl-9 pr-3 text-sm text-slate-900 outline-none transition-colors placeholder:text-slate-400 focus:border-blue-400/70 focus:bg-white dark:border-white/10 dark:bg-white/5 dark:text-gray-200 dark:placeholder:text-gray-500 dark:focus:bg-white/10"
            />
          </label>
        </div>

        <div className="flex-1 overflow-y-auto px-2 pb-3">
          {filteredSessions.length === 0 && (
            <p className="px-3 py-6 text-center text-xs text-slate-400 dark:text-gray-400">
              No conversations yet
            </p>
          )}
          {filteredSessions.map((s) => (
            <button
              key={s.id}
              onClick={() => setActiveSession(s.id)}
              className={clsx(
                "mb-1.5 flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-left text-sm transition-all duration-200",
                s.id === activeSessionId
                  ? "bg-slate-100 font-medium text-slate-900 dark:bg-white/12 dark:text-white"
                  : "text-slate-700 hover:bg-slate-100 hover:text-slate-900 dark:text-gray-300 dark:hover:bg-white/8 dark:hover:text-white"
              )}
            >
              <MessageSquare className="h-4 w-4 shrink-0" />
              <span className="truncate">{s.title}</span>
            </button>
          ))}
        </div>

        <div className="border-t border-slate-200 p-3 dark:border-white/10">
          <button
            aria-label="Open account profile"
            title="My profile"
            className="flex w-full items-center gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-left text-slate-900 transition-all duration-200 hover:bg-slate-50 dark:border-white/10 dark:bg-white/5 dark:text-gray-200 dark:hover:bg-white/10"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-[#2563EB] to-[#1E40AF] text-xs font-semibold text-white">
              MP
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-slate-900 dark:text-white">My Account</p>
              <p className="truncate text-xs text-slate-500 dark:text-gray-400">manu@example.com</p>
            </div>
            <User className="h-4 w-4 text-slate-400 dark:text-gray-400" />
          </button>
        </div>
      </aside>
    </>
  );
}
