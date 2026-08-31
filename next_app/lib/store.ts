import { create } from "zustand";
import type { User, Session } from "@supabase/supabase-js";
import type { Node, Edge } from "@xyflow/react";
import { supabase } from "./supabaseClient";
import {
  aiEngineApi,
  type LldType,
  type LldStatusType,
  type InterviewQuestion,
  type LogEntry,
} from "./ai-engine-client";

export interface ChatMessage {
  id: string;
  role: "user" | "ai" | "system";
  content: string;
}

export interface ChatSession {
  id: string;
  title: string;
  generationId?: string;
  messages: ChatMessage[];
  hasArchitecture: boolean;
}

export type PipelineStep = 1 | 2 | 3 | 4;
// 1: Prompt & Interview
// 2: ARSRS Document
// 3: High-Level Design (HLD)
// 4: Low-Level Designs (5 LLDs: Backend, Frontend, Database, Security, Cloud)

interface AppState {
  // ── Auth ──
  user: User | null;
  session: Session | null;
  authLoading: boolean;
  setUser: (u: User | null) => void;
  setSession: (s: Session | null) => void;
  initAuth: () => Promise<void>;
  signOut: () => Promise<void>;

  // ── Theme ──
  theme: "light" | "dark";
  toggleTheme: () => void;
  setTheme: (t: "light" | "dark") => void;

  // ── Sidebar ──
  sidebarOpen: boolean;
  toggleSidebar: () => void;

  // ── API & Engine Status ──
  apiConnected: boolean;
  apiVersion: string;
  checkApiHealth: () => Promise<boolean>;

  // ── Step-by-Step / Slider Pipeline Navigation ──
  activePipelineStep: PipelineStep;
  setActivePipelineStep: (step: PipelineStep) => void;
  goToNextStep: () => void;
  goToPrevStep: () => void;

  // ── Active Generation Pipeline ──
  generationId: string | null;
  generationStatus: "IDLE" | "INTERVIEW_IN_PROGRESS" | "INTERVIEW_COMPLETED" | "GENERATING_ARCH" | "COMPLETED" | "ERROR" | string;
  currentQuestion: InterviewQuestion | null;
  interviewCompleted: boolean;
  activeProcess: {
    process?: string;
    stage?: string;
    message?: string;
    status?: string;
  } | null;

  // ── Specifications & Diagrams ──
  arsrsData: Record<string, unknown> | null;
  hldData: Record<string, unknown> | null;
  hldNodes: Node[];
  hldEdges: Edge[];
  selectedNode: string | null;
  setSelectedNode: (id: string | null) => void;

  // ── 5 LLDs Concurrency ──
  lldStatus: Record<LldType, LldStatusType>;
  lldData: Record<LldType, Record<string, unknown> | null>;
  lldMessages: Record<LldType, string | null>;
  activeLldType: LldType;
  setActiveLldType: (type: LldType) => void;

  // ── Real-time Terminal Logs ──
  logs: LogEntry[];
  autoScrollLogs: boolean;
  toggleAutoScrollLogs: () => void;
  addLogEntry: (entry: LogEntry) => void;
  setLogs: (logs: LogEntry[]) => void;
  clearLogs: () => void;

  // ── Chat & Persistence ──
  sessions: ChatSession[];
  activeSessionId: string | null;
  createSession: (title?: string) => Promise<string>;
  setActiveSession: (id: string) => Promise<void>;
  addMessage: (sessionId: string, msg: ChatMessage) => Promise<void>;
  loadSessionsFromSupabase: () => Promise<void>;
  resetGenerationSession: () => void;

  // ── Demo & Offline Testing ──
  loadDemoData: () => void;

  // ── Explanations Modal ──
  explainOpen: boolean;
  explainNode: string | null;
  explainTitle?: string;
  explainContent?: string;
  openExplain: (nodeId: string, title?: string, content?: string) => void;
  closeExplain: () => void;
}

import { hldNodes as initialHldNodes, hldEdges as initialHldEdges, dummyHldData, dummyAllLldData } from "./mock-data";

const initialLldStatus: Record<LldType, LldStatusType> = {
  backend: "NOT_STARTED",
  frontend: "NOT_STARTED",
  database: "NOT_STARTED",
  security: "NOT_STARTED",
  cloud: "NOT_STARTED",
};

const initialLldData: Record<LldType, Record<string, unknown> | null> = {
  backend: null,
  frontend: null,
  database: null,
  security: null,
  cloud: null,
};

const initialLldMessages: Record<LldType, string | null> = {
  backend: null,
  frontend: null,
  database: null,
  security: null,
  cloud: null,
};

let sessionCounter = 0;
let msgCounter = 0;

export function generateMsgId() {
  msgCounter++;
  return `msg-${Date.now()}-${msgCounter}`;
}

export const useAppStore = create<AppState>((set, get) => ({
  // Auth
  user: null,
  session: null,
  authLoading: true,

  setUser: (user) => set({ user }),
  setSession: (session) => set({ session, user: session?.user ?? null }),

  initAuth: async () => {
    try {
      const { data } = await supabase.auth.getSession();
      if (data?.session) {
        set({
          session: data.session,
          user: data.session.user,
          authLoading: false,
        });
        await get().loadSessionsFromSupabase();
      } else {
        set({ session: null, user: null, authLoading: false });
      }

      supabase.auth.onAuthStateChange(async (_event, session) => {
        set({
          session,
          user: session?.user ?? null,
          authLoading: false,
        });
        if (session?.user) {
          await get().loadSessionsFromSupabase();
        }
      });
    } catch {
      set({ authLoading: false });
    }
  },

  signOut: async () => {
    try {
      await supabase.auth.signOut({ scope: "local" });
    } catch (err) {
      console.warn("Sign out notice:", err);
    } finally {
      set({
        user: null,
        session: null,
        sessions: [],
        activeSessionId: null,
      });

      if (typeof window !== "undefined") {
        // Clear any leftover supabase auth tokens in localStorage
        try {
          Object.keys(localStorage).forEach((key) => {
            if (key.startsWith("sb-") || key.includes("supabase.auth")) {
              localStorage.removeItem(key);
            }
          });
        } catch {
          // ignore
        }
        window.location.href = "/signin";
      }
    }
  },

  // Theme
  theme: "dark",
  toggleTheme: () => {
    const next = get().theme === "dark" ? "light" : "dark";
    set({ theme: next });
    if (typeof window !== "undefined") {
      localStorage.setItem("theme", next);
      if (next === "dark") {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
    }
  },
  setTheme: (t) => {
    set({ theme: t });
    if (typeof window !== "undefined") {
      localStorage.setItem("theme", t);
      if (t === "dark") {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
    }
  },

  // Sidebar
  sidebarOpen: true,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  // API Health
  apiConnected: false,
  apiVersion: "2.0.0",
  checkApiHealth: async () => {
    const res = await aiEngineApi.checkHealth();
    set({ apiConnected: res.ok, apiVersion: res.version || "2.0.0" });
    return res.ok;
  },

  // Step-by-Step / Slider Pipeline Navigation
  activePipelineStep: 1,
  setActivePipelineStep: (step) => set({ activePipelineStep: step }),
  goToNextStep: () => {
    const current = get().activePipelineStep;
    if (current < 4) {
      set({ activePipelineStep: (current + 1) as PipelineStep });
    }
  },
  goToPrevStep: () => {
    const current = get().activePipelineStep;
    if (current > 1) {
      set({ activePipelineStep: (current - 1) as PipelineStep });
    }
  },

  // Generation Pipeline
  generationId: null,
  generationStatus: "IDLE",
  currentQuestion: null,
  interviewCompleted: false,
  activeProcess: null,

  // Specs & Diagrams
  arsrsData: null,
  hldData: null,
  hldNodes: [],
  hldEdges: [],
  selectedNode: null,
  setSelectedNode: (id) => set({ selectedNode: id }),

  // LLDs
  lldStatus: initialLldStatus,
  lldData: initialLldData,
  lldMessages: initialLldMessages,
  activeLldType: "backend",
  setActiveLldType: (type) => set({ activeLldType: type }),

  // Logs
  logs: [],
  autoScrollLogs: true,
  toggleAutoScrollLogs: () => set((s) => ({ autoScrollLogs: !s.autoScrollLogs })),
  addLogEntry: (entry) => {
    set((s) => {
      const exists = s.logs.some(
        (l) => l.timestamp === entry.timestamp && l.message === entry.message
      );
      if (exists) return s;

      const newLogs = [...s.logs, entry];

      const newProcess =
        entry.process || entry.stage
          ? {
              process: entry.process || entry.stage,
              stage: entry.stage,
              message: entry.message,
              status: entry.process_status || (entry.level === "ERROR" ? "FAILED" : "IN_PROGRESS"),
            }
          : s.activeProcess;

      const newLldStatus = entry.lld_status
        ? { ...s.lldStatus, ...entry.lld_status }
        : s.lldStatus;

      return {
        logs: newLogs,
        activeProcess: newProcess,
        lldStatus: newLldStatus,
      };
    });
  },
  setLogs: (logs) => set({ logs }),
  clearLogs: () => set({ logs: [] }),

  // Reset Session
  resetGenerationSession: () => {
    set({
      activePipelineStep: 1,
      generationId: null,
      generationStatus: "IDLE",
      currentQuestion: null,
      interviewCompleted: false,
      activeProcess: null,
      arsrsData: null,
      hldData: null,
      hldNodes: [],
      hldEdges: [],
      selectedNode: null,
      lldStatus: initialLldStatus,
      lldData: initialLldData,
      lldMessages: initialLldMessages,
      logs: [],
    });
  },

  // Chat sessions
  sessions: [],
  activeSessionId: null,

  loadSessionsFromSupabase: async () => {
    const currentUser = get().user;
    if (!currentUser) return;

    try {
      const { data: dbSessions } = await supabase
        .from("chat_sessions")
        .select("id, title, created_at")
        .eq("user_id", currentUser.id)
        .order("created_at", { ascending: false });

      if (!dbSessions) return;

      const loadedSessions: ChatSession[] = dbSessions.map((s) => ({
        id: s.id,
        title: s.title || "Architecture Session",
        messages: [],
        hasArchitecture: false,
      }));

      set({ sessions: loadedSessions });

      if (loadedSessions.length > 0 && !get().activeSessionId) {
        await get().setActiveSession(loadedSessions[0].id);
      }
    } catch {
      // Fallback
    }
  },

  createSession: async (title?: string) => {
    sessionCounter++;
    const defaultTitle = title || `Architecture ${sessionCounter}`;
    const currentUser = get().user;

    let newId = `session-${Date.now()}`;

    if (currentUser) {
      try {
        const { data } = await supabase
          .from("chat_sessions")
          .insert([
            {
              user_id: currentUser.id,
              title: defaultTitle,
            },
          ])
          .select()
          .single();

        if (data?.id) {
          newId = data.id;
        }
      } catch (err) {
        console.warn("Could not persist session to Supabase:", err);
      }
    }

    const newSession: ChatSession = {
      id: newId,
      title: defaultTitle,
      messages: [],
      hasArchitecture: false,
    };

    set((s) => ({
      sessions: [newSession, ...s.sessions.filter((ses) => ses.id !== newId)],
      activeSessionId: newId,
      activePipelineStep: 1,
      generationId: null,
      generationStatus: "IDLE",
      currentQuestion: null,
      interviewCompleted: false,
      activeProcess: null,
      arsrsData: null,
      hldData: null,
      hldNodes: [],
      hldEdges: [],
      selectedNode: null,
      lldStatus: initialLldStatus,
      lldData: initialLldData,
      logs: [],
    }));

    return newId;
  },

  setActiveSession: async (id: string) => {
    set({
      activeSessionId: id,
    });

    const session = get().sessions.find((s) => s.id === id);
    if (session && session.messages.length === 0 && id.includes("-")) {
      try {
        const { data: dbMessages } = await supabase
          .from("messages")
          .select("*")
          .eq("session_id", id)
          .order("created_at", { ascending: true });

        if (dbMessages && dbMessages.length > 0) {
          const mappedMsgs: ChatMessage[] = dbMessages.map((m) => ({
            id: m.id,
            role: m.role === "assistant" ? "ai" : "user",
            content: m.content,
          }));

          set((s) => ({
            sessions: s.sessions.map((ses) =>
              ses.id === id
                ? {
                    ...ses,
                    messages: mappedMsgs,
                    hasArchitecture: mappedMsgs.some((m) => m.role === "ai"),
                  }
                : ses
            ),
          }));
        }
      } catch {
        // Continue
      }
    }
  },

  addMessage: async (sessionId: string, msg: ChatMessage) => {
    set((s) => ({
      sessions: s.sessions.map((ses) =>
        ses.id === sessionId
          ? {
              ...ses,
              messages: [...ses.messages, msg],
              hasArchitecture: ses.hasArchitecture || msg.role === "ai",
            }
          : ses
      ),
    }));

    try {
      await supabase.from("messages").insert([
        {
          session_id: sessionId,
          role: msg.role === "ai" ? "assistant" : "user",
          content: msg.content,
        },
      ]);
    } catch {
      // Continue
    }
  },

  // Demo & Offline Testing
  loadDemoData: () => {
    set({
      hldData: dummyHldData as Record<string, unknown>,
      hldNodes: initialHldNodes,
      hldEdges: initialHldEdges,
      lldData: dummyAllLldData as Record<LldType, Record<string, unknown> | null>,
      lldStatus: {
        backend: "READY",
        frontend: "READY",
        database: "READY",
        security: "READY",
        cloud: "READY",
      },
      generationStatus: "COMPLETED",
      activePipelineStep: 3,
    });
  },

  // Modal Explanations
  explainOpen: false,
  explainNode: null,
  explainTitle: undefined,
  explainContent: undefined,
  openExplain: (nodeId, title, content) =>
    set({
      explainOpen: true,
      explainNode: nodeId,
      explainTitle: title,
      explainContent: content,
    }),
  closeExplain: () =>
    set({
      explainOpen: false,
      explainNode: null,
      explainTitle: undefined,
      explainContent: undefined,
    }),
}));

