"use client";

import { useEffect } from "react";
import { Plus, PanelLeftClose, PanelLeft, LogOut, Loader2 } from "lucide-react";
import { useAppStore } from "@/lib/store";
import { apiCreateSession, apiGetSessions } from "@/lib/api";
import clsx from "clsx";
import { useRouter } from "next/navigation";

export default function Sidebar() {
  const {
    sidebarOpen,
    toggleSidebar,
    sessions,
    activeSessionId,
    createSession,
    setSessions,
    setActiveSession,
    user,
    setUser,
  } = useAppStore();
  const router = useRouter();

  // Load sessions from Supabase when user is available
  useEffect(() => {
    if (!user) return;
    apiGetSessions(user.id).then((dbSessions) => {
      if (dbSessions.length === 0) return;
      const mapped = dbSessions.map((s) => ({
        id: s.id,
        title: s.title,
        messages: [],
        hasArchitecture: false,
      }));
      // Merge: keep local sessions that aren't from DB yet
      setSessions(mapped);
    });
  }, [user, setSessions]);

  const handleNewDesign = async () => {
    if (user) {
      // Create in Supabase
      const dbSession = await apiCreateSession(user.id, "New Design");
      if (dbSession) {
        createSession(dbSession.id, dbSession.title);
        return;
      }
    }
    // Fallback: local session
    createSession();
  };

  const handleLogout = () => {
    setUser(null);
    router.push("/");
  };

  const displayName = user?.name ?? user?.email?.split("@")[0] ?? "Guest";
  const initials = displayName.slice(0, 2).toUpperCase();

  return (
    <>
      {!sidebarOpen && (
        <button
          onClick={toggleSidebar}
          className="fixed left-4 top-4 z-40 rounded-lg p-2 transition-colors hover:bg-[#1F1F1F] text-[#AAAAAA] hover:text-white"
          aria-label="Open sidebar"
        >
          <PanelLeft className="h-5 w-5" />
        </button>
      )}

      <aside
        className={clsx(
          "flex h-full flex-col border-r border-[#2A2A2A] bg-[#111111] transition-all duration-300 shrink-0",
          sidebarOpen ? "w-[260px]" : "w-0 overflow-hidden border-none"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4">
          <button
            id="new-design-btn"
            onClick={handleNewDesign}
            className="flex flex-1 items-center gap-2 rounded-full border border-white px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-white hover:text-black"
          >
            <Plus className="h-4 w-4" />
            New Design
          </button>
          <button
            onClick={toggleSidebar}
            className="ml-3 rounded-lg p-2 transition-colors hover:bg-[#1F1F1F] text-[#AAAAAA] hover:text-white"
            aria-label="Close sidebar"
          >
            <PanelLeftClose className="h-4 w-4" />
          </button>
        </div>

        {/* Sessions list */}
        <div className="flex-1 overflow-y-auto px-3 py-2">
          {sessions.length === 0 && (
            <p className="px-3 py-8 text-center text-xs text-[#555555]">
              No past designs yet.
              <br />
              Click &quot;New Design&quot; to begin.
            </p>
          )}
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => setActiveSession(s.id)}
              className={clsx(
                "mb-1 w-full rounded-lg px-3 py-2.5 text-left text-sm transition-all",
                s.id === activeSessionId
                  ? "bg-[#1F1F1F] border-l-[3px] border-white text-white pl-2"
                  : "hover:bg-[#1A1A1A] text-[#AAAAAA] border-l-[3px] border-transparent hover:text-white"
              )}
            >
              <div className="truncate font-medium">{s.title}</div>
            </button>
          ))}
        </div>

        {/* User footer */}
        <div className="border-t border-[#2A2A2A] p-4 flex items-center justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-white bg-black text-xs font-bold text-white">
              {initials}
            </div>
            <span className="truncate text-sm font-semibold text-white">
              {displayName}
            </span>
          </div>
          <button
            onClick={handleLogout}
            className="ml-2 shrink-0 text-[#555555] hover:text-white transition-colors"
            aria-label="Logout"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </aside>
    </>
  );
}
