"use client";

import { ChevronDown, PanelLeft, MoreHorizontal } from "lucide-react";
import { useAppStore } from "@/lib/store";
import ThemeToggle from "./ThemeToggle";

export default function ChatTopBar() {
  const { sessions, activeSessionId, toggleSidebar } = useAppStore();

  const activeSession = sessions.find((s) => s.id === activeSessionId);
  const title = activeSession?.title ?? "Assistant";

  return (
    <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center justify-between border-b border-white/10 bg-[#070C1A]/72 px-3 backdrop-blur-xl sm:px-4">
      <div className="flex min-w-0 items-center gap-2">
        <button
          onClick={toggleSidebar}
          aria-label="Toggle sidebar"
          title="Toggle sidebar"
          className="inline-flex h-9 w-9 items-center justify-center rounded-xl text-gray-300 transition-colors hover:bg-white/10 hover:text-white"
        >
          <PanelLeft className="h-4 w-4" />
        </button>

        <button
          className="group inline-flex min-w-0 items-center gap-1 rounded-xl px-2 py-1.5 transition-colors hover:bg-white/10"
          title={title}
          aria-label="Current chat"
        >
          <span className="truncate text-sm font-semibold tracking-tight text-gray-100 sm:text-[15px]">
            {title}
          </span>
          <ChevronDown className="h-4 w-4 shrink-0 text-gray-400 transition-colors group-hover:text-gray-200" />
        </button>
      </div>

      <div className="flex items-center gap-2">
        <ThemeToggle />
        <button
          aria-label="More options"
          title="More options"
          className="inline-flex h-9 w-9 items-center justify-center rounded-xl text-gray-300 transition-colors hover:bg-white/10 hover:text-white"
        >
          <MoreHorizontal className="h-4 w-4" />
        </button>
      </div>
    </header>
  );
}
