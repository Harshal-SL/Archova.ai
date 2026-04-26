"use client";

import { Plus, MessageSquare, PanelLeftClose, PanelLeft } from "lucide-react";
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

  return (
    <>
      {/* Collapse/Expand button when closed */}
      {!sidebarOpen && (
        <button
          onClick={toggleSidebar}
          className="fixed left-2 top-16 z-40 rounded-lg bg-gray-100 p-2 shadow-md transition-colors hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700"
        >
          <PanelLeft className="h-5 w-5 text-gray-600 dark:text-gray-400" />
        </button>
      )}

      <aside
        className={clsx(
          "flex h-full flex-col border-r border-gray-200 bg-gray-50 transition-all duration-300 dark:border-gray-800 dark:bg-gray-900",
          sidebarOpen ? "w-64" : "w-0 overflow-hidden"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-3">
          <button
            onClick={() => createSession()}
            className="flex flex-1 items-center gap-2 rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium transition-colors hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-800"
          >
            <Plus className="h-4 w-4" />
            New Chat
          </button>
          <button
            onClick={toggleSidebar}
            className="ml-2 rounded-lg p-2 transition-colors hover:bg-gray-200 dark:hover:bg-gray-800"
          >
            <PanelLeftClose className="h-4 w-4 text-gray-500" />
          </button>
        </div>

        {/* Chat list */}
        <div className="flex-1 overflow-y-auto px-2 py-1">
          {sessions.length === 0 && (
            <p className="px-3 py-6 text-center text-xs text-gray-400">
              No conversations yet
            </p>
          )}
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => setActiveSession(s.id)}
              className={clsx(
                "mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors",
                s.id === activeSessionId
                  ? "bg-gray-200 font-medium dark:bg-gray-800"
                  : "hover:bg-gray-100 dark:hover:bg-gray-800/50"
              )}
            >
              <MessageSquare className="h-4 w-4 shrink-0 text-gray-400" />
              <span className="truncate">{s.title}</span>
            </button>
          ))}
        </div>
      </aside>
    </>
  );
}
