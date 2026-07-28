import { create } from "zustand";

export interface ChatMessage {
  id: string;
  role: "user" | "ai";
  content: string;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  hasArchitecture: boolean;
}

export type ArchView = "hld" | "lld";

interface AppState {
  // Theme
  theme: "light" | "dark";
  toggleTheme: () => void;
  setTheme: (t: "light" | "dark") => void;

  // Sidebar
  sidebarOpen: boolean;
  toggleSidebar: () => void;

  // Chat sessions
  sessions: ChatSession[];
  activeSessionId: string | null;
  createSession: () => string;
  setActiveSession: (id: string) => void;
  addMessage: (sessionId: string, msg: ChatMessage) => void;
  setArchitectureReady: (sessionId: string) => void;

  // Architecture
  archVisible: boolean;
  archView: ArchView;
  setArchView: (v: ArchView) => void;
  selectedNode: string | null;
  setSelectedNode: (id: string | null) => void;

  // Explain modal
  explainOpen: boolean;
  explainNode: string | null;
  openExplain: (nodeId: string) => void;
  closeExplain: () => void;
}

let sessionCounter = 0;
let msgCounter = 0;

export const useAppStore = create<AppState>((set, get) => ({
  // Theme
  theme: "dark",
  toggleTheme: () => {
    const next = get().theme === "dark" ? "light" : "dark";
    set({ theme: next });
    if (typeof window !== "undefined") localStorage.setItem("theme", next);
  },
  setTheme: (t) => set({ theme: t }),

  // Sidebar
  sidebarOpen: true,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  // Sessions
  sessions: [],
  activeSessionId: null,

  createSession: () => {
    sessionCounter++;
    const id = `session-${sessionCounter}`;
    const newSession: ChatSession = {
      id,
      title: `New Chat ${sessionCounter}`,
      messages: [],
      hasArchitecture: false,
    };
    set((s) => ({
      sessions: [newSession, ...s.sessions],
      activeSessionId: id,
      archVisible: false,
      selectedNode: null,
    }));
    return id;
  },

  setActiveSession: (id) => {
    const session = get().sessions.find((s) => s.id === id);
    set({
      activeSessionId: id,
      archVisible: session?.hasArchitecture ?? false,
      selectedNode: null,
    });
  },

  addMessage: (sessionId, msg) => {
    set((s) => ({
      sessions: s.sessions.map((ses) =>
        ses.id === sessionId
          ? { ...ses, messages: [...ses.messages, msg] }
          : ses
      ),
    }));
  },

  setArchitectureReady: (sessionId) => {
    set((s) => ({
      sessions: s.sessions.map((ses) =>
        ses.id === sessionId ? { ...ses, hasArchitecture: true } : ses
      ),
      archVisible: true,
    }));
  },

  // Architecture
  archVisible: false,
  archView: "hld",
  setArchView: (v) => set({ archView: v, selectedNode: null }),
  selectedNode: null,
  setSelectedNode: (id) => set({ selectedNode: id }),

  // Explain
  explainOpen: false,
  explainNode: null,
  openExplain: (nodeId) => set({ explainOpen: true, explainNode: nodeId }),
  closeExplain: () => set({ explainOpen: false, explainNode: null }),
}));

export function generateMsgId() {
  msgCounter++;
  return `msg-${msgCounter}`;
}
