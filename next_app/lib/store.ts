import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Node, Edge } from "@xyflow/react";

// ─── Types ──────────────────────────────────────────────────────────
export interface ChatMessage {
  id: string;
  role: "user" | "ai";
  content: string;
}

export interface HLDNode {
  id: string;
  label: string;
  description?: string;
  children?: LLDComponent[];
}

export interface LLDComponent {
  id: string;
  label: string;
  details?: string;
}

export interface ArchitectureData {
  hldNodes: Node[];
  hldEdges: Edge[];
  lldMap: Record<string, { nodes: Node[]; edges: Edge[] }>;
  summaryText: string;
}

export interface ChatSession {
  id: string;           // supabase session id (UUID) or local fallback
  title: string;
  messages: ChatMessage[];
  hasArchitecture: boolean;
  architectureData?: ArchitectureData;
}

export type ArchView = "hld" | "lld";

export interface AuthUser {
  id: string;
  email: string;
  name: string;
}

// ─── State Interface ──────────────────────────────────────────────────
interface AppState {
  // Auth
  user: AuthUser | null;
  authLoading: boolean;
  setUser: (u: AuthUser | null) => void;
  setAuthLoading: (v: boolean) => void;

  // Sidebar
  sidebarOpen: boolean;
  toggleSidebar: () => void;

  // Chat sessions
  sessions: ChatSession[];
  activeSessionId: string | null;
  createSession: (id?: string, title?: string) => string;
  setActiveSession: (id: string) => void;
  addMessage: (sessionId: string, msg: ChatMessage) => void;
  updateSessionTitle: (sessionId: string, title: string) => void;
  setArchitectureReady: (sessionId: string, data?: ArchitectureData) => void;
  setSessions: (sessions: ChatSession[]) => void;

  // Streaming / loading
  isGenerating: boolean;
  streamingContent: string;
  setIsGenerating: (v: boolean) => void;
  setStreamingContent: (v: string) => void;
  appendStreamingContent: (chunk: string) => void;

  // Architecture panel
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

// ─── Counters ────────────────────────────────────────────────────────
let sessionCounter = 0;
let msgCounter = 0;
export function generateMsgId() {
  msgCounter++;
  return `msg-${msgCounter}`;
}

// ─── Store ────────────────────────────────────────────────────────────
export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Auth
      user: null,
      authLoading: false,
      setUser: (u) => set({ user: u }),
      setAuthLoading: (v) => set({ authLoading: v }),

      // Sidebar
      sidebarOpen: true,
      toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

      // Sessions
      sessions: [],
      activeSessionId: null,

      createSession: (id?: string, title?: string) => {
        sessionCounter++;
        const newId = id ?? `session-${Date.now()}-${sessionCounter}`;
        const newSession: ChatSession = {
          id: newId,
          title: title ?? `New Design ${sessionCounter}`,
          messages: [],
          hasArchitecture: false,
        };
        set((s) => ({
          sessions: [newSession, ...s.sessions],
          activeSessionId: newId,
          archVisible: false,
          selectedNode: null,
          archView: "hld",
          streamingContent: "",
        }));
        return newId;
      },

      setActiveSession: (id) => {
        const session = get().sessions.find((s) => s.id === id);
        set({
          activeSessionId: id,
          archVisible: session?.hasArchitecture ?? false,
          selectedNode: null,
          archView: "hld",
          streamingContent: "",
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

      updateSessionTitle: (sessionId, title) => {
        set((s) => ({
          sessions: s.sessions.map((ses) =>
            ses.id === sessionId ? { ...ses, title } : ses
          ),
        }));
      },

      setArchitectureReady: (sessionId, data) => {
        set((s) => ({
          sessions: s.sessions.map((ses) =>
            ses.id === sessionId
              ? { ...ses, hasArchitecture: true, architectureData: data }
              : ses
          ),
          archVisible: true,
        }));
      },

      setSessions: (sessions) => set({ sessions }),

      // Streaming
      isGenerating: false,
      streamingContent: "",
      setIsGenerating: (v) => set({ isGenerating: v }),
      setStreamingContent: (v) => set({ streamingContent: v }),
      appendStreamingContent: (chunk) =>
        set((s) => ({ streamingContent: s.streamingContent + chunk })),

      // Architecture
      archVisible: false,
      archView: "hld",
      setArchView: (v) => set({ archView: v }),
      selectedNode: null,
      setSelectedNode: (id) => set({ selectedNode: id }),

      // Explain
      explainOpen: false,
      explainNode: null,
      openExplain: (nodeId) => set({ explainOpen: true, explainNode: nodeId }),
      closeExplain: () => set({ explainOpen: false, explainNode: null }),
    }),
    {
      name: "architectai-store",
      // Only persist auth + sessions, not transient UI state
      partialize: (state) => ({
        user: state.user,
        sessions: state.sessions,
        activeSessionId: state.activeSessionId,
        sidebarOpen: state.sidebarOpen,
      }),
    }
  )
);
