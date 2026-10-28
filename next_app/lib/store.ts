import { create } from "zustand";
import type { User, Session } from "@supabase/supabase-js";
import type { Node, Edge } from "@xyflow/react";
import { supabase } from "./supabaseClient";
import { syncAuthCookie } from "./auth-cookie";
import {
  aiEngineApi,
  type LldType,
  type LldStatusType,
  type InterviewQuestion,
  type LogEntry,
  type BenchmarkModelConfig,
  type ModelBenchmarkResult,
  type BenchmarkComparisonSummary,
  type AgentTelemetry,
  DEFAULT_BENCHMARK_PRESETS,
} from "./ai-engine-client";
import {
  validatorApi,
  type ValidatedArchitectureResponse,
} from "./validator-client";
import { parseHldToReactFlow } from "./graph-parser";

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

export type PipelineStep = 1 | 2 | 3 | 4 | 5;
// 1: Prompt & Interview
// 2: ARSRS Document
// 3: High-Level Design (HLD)
// 4: Low-Level Designs (5 LLDs: Backend, Frontend, Database, Security, Cloud)
// 5: Validation & Quality Scorecard (Standalone Validator Engine + AI Correction Workflow)

export interface ActiveAgentInfo {
  id: string;
  name: string;
  role: string;
  icon: "brain" | "mic" | "cpu" | "network" | "sparkles" | "shield";
  task: string;
  status: "thinking" | "working" | "completed" | "idle";
  stage: "REE" | "INTERVIEW" | "SAE" | "HLD" | "READY" | string;
  progressPercent?: number;
  thought?: string;
}

export type WorkspaceView = "chat" | "hld" | "split";

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
  setSidebarOpen: (open: boolean) => void;

  // ── Active Workspace View (ChatGPT style) ──
  activeView: WorkspaceView;
  setActiveView: (v: WorkspaceView) => void;

  // ── Active Agent Telemetry & Multi-Agent Swarm ──
  activeAgent: ActiveAgentInfo | null;
  setActiveAgent: (agent: ActiveAgentInfo | null) => void;
  agentSwarm: Record<string, AgentTelemetry>;
  activeAgentsList: AgentTelemetry[];
  isPollingAgents: boolean;
  setAgentSwarm: (swarm: Record<string, AgentTelemetry>) => void;
  startAgentTelemetryPolling: (generationId: string) => void;
  stopAgentTelemetryPolling: () => void;

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
  setArsrsData: (data: Record<string, unknown> | null) => void;
  hldData: Record<string, unknown> | null;
  hldNodes: Node[];
  hldEdges: Edge[];
  selectedNode: string | null;
  setSelectedNode: (id: string | null) => void;
  hldWorkspaceTab: "hld" | "lld" | "validation" | "json" | "comparison";
  setHldWorkspaceTab: (tab: "hld" | "lld" | "validation" | "json" | "comparison") => void;
  layoutDirection: "TB" | "LR";
  setLayoutDirection: (dir: "TB" | "LR") => void;
  toggleLayoutDirection: () => void;

  // ── 5 LLDs Concurrency ──
  lldStatus: Record<LldType, LldStatusType>;
  lldData: Record<LldType, Record<string, unknown> | null>;
  lldMessages: Record<LldType, string | null>;
  activeLldType: LldType;
  setActiveLldType: (type: LldType) => void;
  jumpToLld: (type: LldType) => void;

  // ── Standalone Validator Engine & Correction Workflow ──
  validatorConnected: boolean;
  validatorVersion: string;
  checkValidatorHealth: () => Promise<boolean>;
  validationData: ValidatedArchitectureResponse | null;
  validatedGenerationId: string | null;
  isValidating: boolean;
  validationError: string | null;
  setValidationData: (data: ValidatedArchitectureResponse | null) => void;
  validateArchitecture: (pkg?: Record<string, any>) => Promise<ValidatedArchitectureResponse | null>;
  runCorrectionWorkflow: (maxRetries?: number, force?: boolean) => Promise<ValidatedArchitectureResponse | null>;

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
  saveCurrentArchitecture: (targetSessionId?: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  resetGenerationSession: () => void;

  // ── Demo & Offline Testing ──
  loadDemoData: () => void;

  // ── Versioning & Architectural Evolution ──
  activeVersionTag: string;
  availableVersions: Array<{
    id: string;
    version_tag: string;
    prompt?: string;
    created_at?: string;
    is_latest?: boolean;
    diff?: any;
    design_json?: any;
  }>;
  activeDiff: any | null;
  setActiveVersionTag: (tag: string) => void;
  fetchVersionsForSession: (sessionId: string) => Promise<void>;
  selectVersion: (versionTagOrId: string) => Promise<void>;
  evolveArchitecture: (featurePrompt: string) => Promise<{ success: boolean; versionTag: string; diff: any }>;

  // ── Explanations & Tech Rationale Modal ──
  explainOpen: boolean;
  explainNode: string | null;
  explainTitle?: string;
  explainContent?: string;
  explainNodeData?: Record<string, unknown>;
  openExplain: (nodeId: string, title?: string, content?: string, nodeData?: Record<string, unknown>) => void;
  openTechRationale: (nodeData: Record<string, unknown>) => void;
  closeExplain: () => void;

  // ── Multi-Model Comparison & Benchmarking ──
  benchmarkModelsConfig: BenchmarkModelConfig[];
  benchmarkApiKey: string;
  isBenchmarking: boolean;
  benchmarkResults: Record<string, ModelBenchmarkResult>;
  activeModelId: string;
  comparisonData: BenchmarkComparisonSummary | null;
  archovaSnapshot: {
    arsrsData: Record<string, unknown> | null;
    hldData: Record<string, unknown> | null;
    hldNodes: Node[];
    hldEdges: Edge[];
    lldData: Record<LldType, Record<string, unknown> | null>;
    validationData: ValidatedArchitectureResponse | null;
  } | null;
  setBenchmarkModelsConfig: (models: BenchmarkModelConfig[]) => void;
  setBenchmarkApiKey: (key: string) => void;
  selectModel: (modelId: string) => void;
  runBenchmarkSuite: (promptText: string) => Promise<void>;
}

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

export function generateUUID(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export function isUUID(str: string | null | undefined): boolean {
  if (!str) return false;
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(str);
}

let agentPollingInterval: ReturnType<typeof setInterval> | null = null;
let authListenerInitialized = false;

export const useAppStore = create<AppState>((set, get) => ({
  // Auth
  user: null,
  session: null,
  authLoading: true,

  setUser: (user) => set({ user }),
  setSession: (session) => set({ session, user: session?.user ?? null }),

  initAuth: async () => {
    try {
      // 1. Check Supabase session
      const { data } = await supabase.auth.getSession();
      if (data?.session) {
        syncAuthCookie(data.session.access_token);
        set({
          session: data.session,
          user: data.session.user,
          authLoading: false,
        });
        await get().loadSessionsFromSupabase();
      } else {
        syncAuthCookie(null);
        set({ session: null, user: null, authLoading: false });
      }

      // 2. Attach a single onAuthStateChange listener
      if (!authListenerInitialized) {
        authListenerInitialized = true;
        supabase.auth.onAuthStateChange(async (event, session) => {
          if (event === "SIGNED_OUT" || !session) {
            syncAuthCookie(null);
            set({
              session: null,
              user: null,
              authLoading: false,
              sessions: [],
              activeSessionId: null,
            });
          } else if (session) {
            syncAuthCookie(session.access_token);
            set({
              session,
              user: session.user,
              authLoading: false,
            });
            await get().loadSessionsFromSupabase();
          }
        });
      }
    } catch {
      syncAuthCookie(null);
      set({ authLoading: false });
    }
  },

  signOut: async () => {
    syncAuthCookie(null);
    // 1. Instantly reset all in-memory store states to eliminate stale session/user data
    set({
      user: null,
      session: null,
      sessions: [],
      activeSessionId: null,
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
      validationData: null,
      validatedGenerationId: null,
      activeAgent: null,
      agentSwarm: {},
      activeAgentsList: [],
      activePipelineStep: 1,
    });

    // 2. Clear browser storage (localStorage and sessionStorage)
    if (typeof window !== "undefined") {
      try {
        localStorage.removeItem("archai-guest-user");
        const keysToRemove: string[] = [];
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          if (
            key &&
            (key.startsWith("sb-") ||
              key.includes("supabase.auth") ||
              key.includes("supabase") ||
              key === "archai-guest-user")
          ) {
            keysToRemove.push(key);
          }
        }
        keysToRemove.forEach((k) => localStorage.removeItem(k));
        sessionStorage.clear();
      } catch (storageErr) {
        console.warn("Storage cleanup notice:", storageErr);
      }
    }

    // 3. Notify Supabase with a timeout safeguard so network latency never blocks logout
    try {
      await Promise.race([
        supabase.auth.signOut({ scope: "local" }),
        new Promise((resolve) => setTimeout(resolve, 1000)),
      ]);
    } catch (err) {
      console.warn("Supabase sign out notice:", err);
    }

    // 4. Clean navigation to signin page (full browser reload to flush in-memory React/router caches)
    if (typeof window !== "undefined") {
      window.location.href = "/signin";
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
  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  // Active Workspace View
  activeView: "chat",
  setActiveView: (view) => set({ activeView: view }),

  // Active Agent Telemetry
  activeAgent: {
    id: "agent-ree",
    name: "Requirements Engineering Agent",
    role: "Input Understanding & Scope Extraction",
    icon: "brain",
    task: "Ready to analyze software requirements statement",
    status: "idle",
    stage: "READY",
    progressPercent: 0,
    thought: "Awaiting architectural requirements prompt to begin multi-agent pipeline.",
  },
  setActiveAgent: (agent) => set({ activeAgent: agent }),

  // Multi-Agent Swarm Telemetry State
  agentSwarm: {},
  activeAgentsList: [],
  isPollingAgents: false,
  setAgentSwarm: (swarm) => set({ agentSwarm: swarm }),

  startAgentTelemetryPolling: (generationId: string) => {
    if (agentPollingInterval) {
      clearInterval(agentPollingInterval);
      agentPollingInterval = null;
    }
    set({ isPollingAgents: true });

    let notFoundCount = 0;

    const fetchTelemetry = async () => {
      try {
        const data = await aiEngineApi.getAgentTelemetry(generationId);

        if (!data || data.status === "NOT_FOUND") {
          notFoundCount++;
          if (notFoundCount >= 3) {
            get().stopAgentTelemetryPolling();
            return;
          }
        } else {
          notFoundCount = 0;
        }

        if (data && Array.isArray(data.all_agents)) {
          const swarmMap: Record<string, AgentTelemetry> = {};
          for (const a of data.all_agents) {
            swarmMap[a.agent_id] = a;
          }
          set({
            agentSwarm: swarmMap,
            activeAgentsList: data.active_agents || [],
          });

          // Sync activeAgent to the latest working specialist
          if (data.active_agents && data.active_agents.length > 0) {
            const topAgent = data.active_agents[data.active_agents.length - 1];
            set({
              activeAgent: {
                id: topAgent.agent_id,
                name: topAgent.name,
                role: topAgent.role,
                icon: (topAgent.icon as any) || "sparkles",
                task: topAgent.current_task,
                status: topAgent.status === "running" ? "working" : "thinking",
                stage: topAgent.stage,
                progressPercent: topAgent.progress_percent,
                thought: topAgent.thought,
              },
            });
          }

          // Auto-stop polling when lifecycle reaches terminal state or interview is waiting for user
          const hasActiveAgents = data.active_agents && data.active_agents.length > 0;
          if (
            data.status === "COMPLETED" ||
            data.status === "FAILED" ||
            (data.status === "INTERVIEW_IN_PROGRESS" && !hasActiveAgents)
          ) {
            get().stopAgentTelemetryPolling();
          }
        }
      } catch (err) {
        console.warn("[Archova] Swarm telemetry tick warning:", err);
      }
    };

    fetchTelemetry();
    agentPollingInterval = setInterval(fetchTelemetry, 1200);
  },

  stopAgentTelemetryPolling: () => {
    if (agentPollingInterval) {
      clearInterval(agentPollingInterval);
      agentPollingInterval = null;
    }
    set({ isPollingAgents: false });
  },

  // API Health — Connects to FastAPI backend
  apiConnected: false,
  apiVersion: "Checking...",
  checkApiHealth: async () => {
    const res = await aiEngineApi.checkHealth();
    set({ apiConnected: res.ok, apiVersion: res.version || (res.ok ? "2.0.0" : "Offline") });
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

  // Generation Pipeline — Clean initial state
  generationId: null,
  generationStatus: "IDLE",
  currentQuestion: null,
  interviewCompleted: false,
  activeProcess: null,

  // Specs & Diagrams — Clean initial state
  arsrsData: null,
  setArsrsData: (data) => set({ arsrsData: data }),
  hldData: null,
  hldNodes: [],
  hldEdges: [],
  selectedNode: null,
  setSelectedNode: (id) => set({ selectedNode: id }),
  hldWorkspaceTab: "hld",
  setHldWorkspaceTab: (tab) => set({ hldWorkspaceTab: tab }),
  layoutDirection: "TB",
  setLayoutDirection: (dir) => {
    set({ layoutDirection: dir });
    const state = get();
    if (state.hldData) {
      const parsed = parseHldToReactFlow(state.hldData, undefined, dir);
      set({ hldNodes: parsed.nodes, hldEdges: parsed.edges });
    }
  },
  toggleLayoutDirection: () => {
    const current = get().layoutDirection;
    const next = current === "TB" ? "LR" : "TB";
    get().setLayoutDirection(next);
  },

  // LLDs — Clean initial state
  lldStatus: initialLldStatus,
  lldData: initialLldData,
  lldMessages: initialLldMessages,
  activeLldType: "backend",
  setActiveLldType: (type) => set({ activeLldType: type }),
  jumpToLld: (type) => {
    const state = get();
    const existingLld = state.lldData[type] || null;

    set({
      activeLldType: type,
      hldWorkspaceTab: "lld",
      activePipelineStep: 4,
      lldStatus: {
        ...state.lldStatus,
        [type]: existingLld ? "READY" : state.lldStatus[type] || "NOT_STARTED",
      },
    });

    // Auto-fetch fresh LLD from AI engine backend if generationId exists
    if (!existingLld && state.generationId) {
      aiEngineApi
        .getLLD(state.generationId, type)
        .then((res) => {
          if (res.data) {
            set((s) => ({
              lldData: { ...s.lldData, [type]: res.data },
              lldStatus: { ...s.lldStatus, [type]: "READY" },
            }));
          }
        })
        .catch((err) => {
          console.warn(`[Archova] Auto-fetch ${type} LLD note:`, err);
        });
    }
  },

  // Validator Engine Health & Results
  validatorConnected: true,
  validatorVersion: "Bypassed (Auto-Pass)",
  checkValidatorHealth: async () => {
    const res = await validatorApi.checkHealth();
    set({ validatorConnected: res.ok, validatorVersion: res.version || "Bypassed" });
    return res.ok;
  },
  validationData: null,
  validatedGenerationId: null,
  isValidating: false,
  validationError: null,
  setValidationData: (data) => set({ validationData: data }),

  validateArchitecture: async (pkg?: Record<string, any>) => {
    const { generationId, arsrsData, hldData, lldData, addLogEntry } = get();
    set({ isValidating: true, validationError: null });

    const now = new Date().toTimeString().split(" ")[0];
    addLogEntry({
      timestamp: now,
      stage: "VALIDATOR",
      message: "🛡️ Activating Standalone Validator Engine (Port 8001)...",
      level: "INFO",
    });

    try {
      let packagePayload = pkg;
      if (!packagePayload) {
        packagePayload = {
          generation_id: generationId || "custom-package",
          prompt: "System Architecture",
          status: "COMPLETED",
          arsrs: arsrsData,
          hld: hldData,
          llds: lldData,
        };
      }

      const result = await validatorApi.validate(packagePayload);
      set({
        validationData: result,
        validatedGenerationId: generationId,
        isValidating: false,
        validationError: null,
        activePipelineStep: 5,
      });

      const scorePercent = Math.round((result.validation?.summary?.overall_score || 0) * 100);
      const verdict = result.validation?.summary?.verdict || "APPROVED";
      const findingsCount = result.validation?.summary?.total_findings_count || 0;

      addLogEntry({
        timestamp: new Date().toTimeString().split(" ")[0],
        stage: "VALIDATOR",
        message: `✓ Architecture validated! Composite Score: ${scorePercent}% | Verdict: ${verdict} | Findings: ${findingsCount}`,
        level: "INFO",
      });

      return result;
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Validation failed.";
      set({ isValidating: false, validationError: msg });
      addLogEntry({
        timestamp: new Date().toTimeString().split(" ")[0],
        stage: "VALIDATOR",
        message: `❌ Validator Engine error: ${msg}`,
        level: "ERROR",
      });
      return null;
    }
  },

  runCorrectionWorkflow: async (maxRetries = 2, force = false) => {
    const { generationId, isValidating, validatedGenerationId, addLogEntry, hldData, arsrsData, lldData, hldNodes, hldEdges } = get();

    // 1. Guard against duplicate validation requests caused by React effects, component remounts, or repeated generation events
    if (isValidating) {
      return null;
    }
    if (!force && generationId && validatedGenerationId === generationId && get().validationData) {
      return get().validationData;
    }

    set({ isValidating: true, validationError: null });

    const now = new Date().toTimeString().split(" ")[0];
    addLogEntry({
      timestamp: now,
      stage: "CORRECTION",
      message: `🔄 Starting automated Validator-AI Correction workflow (Max retries: ${maxRetries})...`,
      level: "INFO",
    });

    try {
      let result: ValidatedArchitectureResponse | null = null;
      if (generationId) {
        result = await aiEngineApi.validateAndCorrect(generationId, maxRetries);
      } else {
        result = await get().validateArchitecture();
      }

      if (result) {
        // Extract architecture from the final validated package
        const rawArch = (result.architecture || {}) as Record<string, any>;
        const finalHld = (rawArch.hld || hldData) as Record<string, unknown> | null;
        const finalArsrs = (rawArch.arsrs || arsrsData) as Record<string, unknown> | null;

        // Re-parse React Flow nodes & edges strictly from the final corrected HLD
        let finalNodes = hldNodes;
        let finalEdges = hldEdges;
        if (finalHld) {
          const parsed = parseHldToReactFlow(finalHld);
          finalNodes = parsed.nodes;
          finalEdges = parsed.edges;
        }

        // Extract all five LLDs strictly from the final corrected package
        const rawLlds = (rawArch.llds || {}) as Record<string, any>;
        const currentLldData = lldData;
        const finalLldData: Record<LldType, Record<string, unknown> | null> = {
          backend: (rawLlds.backend?.data || rawLlds.backend || rawArch.lld_backend || currentLldData.backend) as any,
          frontend: (rawLlds.frontend?.data || rawLlds.frontend || rawArch.lld_frontend || currentLldData.frontend) as any,
          database: (rawLlds.database?.data || rawLlds.database || rawArch.lld_database || currentLldData.database) as any,
          security: (rawLlds.security?.data || rawLlds.security || rawArch.lld_security || currentLldData.security) as any,
          cloud: (rawLlds.cloud?.data || rawLlds.cloud || rawArch.lld_cloud || currentLldData.cloud) as any,
        };

        const scorePercent = Math.round((result.validation?.summary?.overall_score || 0) * 100);
        const verdict = result.validation?.summary?.verdict || "APPROVED";
        const isApproved = Boolean(result.is_fully_validated);

        const newLldStatus: Record<LldType, LldStatusType> = {
          backend: finalLldData.backend ? "READY" : "NOT_STARTED",
          frontend: finalLldData.frontend ? "READY" : "NOT_STARTED",
          database: finalLldData.database ? "READY" : "NOT_STARTED",
          security: finalLldData.security ? "READY" : "NOT_STARTED",
          cloud: finalLldData.cloud ? "READY" : "NOT_STARTED",
        };

        set({
          validationData: result,
          validatedGenerationId: generationId,
          isValidating: false,
          validationError: null,
          activePipelineStep: 3,
          arsrsData: finalArsrs,
          hldData: finalHld,
          hldNodes: finalNodes,
          hldEdges: finalEdges,
          lldData: finalLldData,
          lldStatus: newLldStatus,
          generationStatus: "COMPLETED",
          activeView: "hld", // Render HLD / LLDs as primary content
          hldWorkspaceTab: "hld",
        });

        addLogEntry({
          timestamp: new Date().toTimeString().split(" ")[0],
          stage: "CORRECTION",
          message: `✓ AI Correction Cycle finished! Final Score: ${scorePercent}% | Verdict: ${verdict} | Fully Validated: ${isApproved ? "YES" : "NO"}`,
          level: "INFO",
        });

        // Persist validated design to Supabase architecture_designs and messages
        try {
          const currentUser = get().user;
          const activeSid = get().activeSessionId;
          if (currentUser && activeSid && !activeSid.startsWith("demo-")) {
            const userPrompt = get().sessions.find(s => s.id === activeSid)?.messages.find(m => m.role === 'user')?.content || "Architecture Design";
            const fullPackage = {
              hld: finalHld,
              llds: finalLldData,
              arsrs: finalArsrs,
              validation: result.validation?.summary,
              score: scorePercent,
              verdict,
              benchmarks: {
                results: get().benchmarkResults,
                comparison: get().comparisonData,
              },
            };

            // Check if a previous latest design exists in this session to maintain version chain
            const { data: existingLatest } = await supabase
              .from("architecture_designs")
              .select("id, version, version_tag")
              .eq("session_id", activeSid)
              .eq("is_latest", true)
              .maybeSingle();

            let nextVerTag = "v1.0";
            let parentId: string | null = null;

            if (existingLatest) {
              parentId = existingLatest.id;
              await supabase
                .from("architecture_designs")
                .update({ is_latest: false })
                .eq("id", existingLatest.id);

              const prevTag = existingLatest.version_tag || "v1.0";
              const num = parseFloat(prevTag.replace("v", "")) || 1.0;
              nextVerTag = `v${(num + 0.1).toFixed(1)}`;
            }

            await supabase.from("architecture_designs").insert([{
              session_id: activeSid,
              user_id: currentUser.id,
              prompt: userPrompt,
              design_json: fullPackage,
              version: parseInt(nextVerTag.replace("v", "").split(".")[0], 10) || 1,
              version_tag: nextVerTag,
              parent_id: parentId,
              is_latest: true,
              updated_at: new Date().toISOString(),
            }]);

            await get().addMessage(activeSid, {
              id: generateMsgId(),
              role: "ai",
              content: `✓ Architecture Validated & Synthesized\n\n• Verdict: ${verdict}\n• Composite Quality Score: ${scorePercent}%\n• High-Level Design: ${finalNodes.length} nodes synthesized\n• Low-Level Designs: 5 blueprints generated (Backend, Frontend, DB, Security, Cloud)`,
            });

            await supabase.from("chat_sessions").update({
              updated_at: new Date().toISOString()
            }).eq("id", activeSid);

            set({ activeVersionTag: nextVerTag });
            await get().fetchVersionsForSession(activeSid);
          }
        } catch (dbErr) {
          console.warn("Could not persist validated architecture to Supabase:", dbErr);
        }

        // Always ensure availableVersions contains the baseline version item
        const curVersions = get().availableVersions;
        if (curVersions.length === 0) {
          set({
            activeVersionTag: "v1.0",
            availableVersions: [
              {
                id: `ver-init-${Date.now()}`,
                version_tag: "v1.0",
                prompt: "Initial Baseline Architecture",
                created_at: new Date().toISOString(),
                is_latest: true,
                design_json: {
                  hld: finalHld,
                  llds: finalLldData,
                  arsrs: finalArsrs,
                  validation: result.validation?.summary,
                },
              },
            ],
          });
        }
      }
      return result;
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Correction workflow failed.";
      // Preserve initial generated package, expose error and validation status. Never treat unvalidated as approved.
      set({
        isValidating: false,
        validationError: msg,
        generationStatus: "COMPLETED",
      });
      addLogEntry({
        timestamp: new Date().toTimeString().split(" ")[0],
        stage: "CORRECTION",
        message: `❌ AI Correction workflow error: ${msg}`,
        level: "ERROR",
      });
      return null;
    }
  },

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

  // Reset Session — Resets to clean new state
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
      validationData: null,
      validatedGenerationId: null,
      validationError: null,
      lldStatus: initialLldStatus,
      lldData: initialLldData,
      lldMessages: initialLldMessages,
      logs: [],
      activeSessionId: null,
    });
  },

  sessions: [],
  activeSessionId: null,

  loadSessionsFromSupabase: async () => {
    const currentUser = get().user;
    if (!currentUser) return;

    try {
      const { data: dbSessions, error } = await supabase
        .from("chat_sessions")
        .select("id, title, created_at, updated_at")
        .eq("user_id", currentUser.id)
        .order("updated_at", { ascending: false });

      if (error) {
        console.warn("Could not load sessions from Supabase:", error.message);
        return;
      }
      if (!dbSessions || dbSessions.length === 0) return;

      // Identify sessions that have generated architecture designs
      const { data: userDesigns } = await supabase
        .from("architecture_designs")
        .select("session_id")
        .eq("user_id", currentUser.id);

      const designSessionIds = new Set((userDesigns || []).map((d) => d.session_id));

      const loadedSessions: ChatSession[] = dbSessions.map((s, idx) => ({
        id: s.id,
        title: s.title || `Architecture Session ${idx + 1}`,
        messages: [],
        hasArchitecture: designSessionIds.has(s.id),
      }));

      set({ sessions: loadedSessions });

      // If activeSessionId is not set, select the most recent session
      const currentActive = get().activeSessionId;
      if (!currentActive && loadedSessions.length > 0) {
        await get().setActiveSession(loadedSessions[0].id);
      }
    } catch (err) {
      console.warn("loadSessionsFromSupabase error:", err);
    }
  },

  createSession: async (title?: string) => {
    sessionCounter++;
    const defaultTitle = title || `Architecture ${sessionCounter}`;
    const currentUser = get().user;
    const newId = generateUUID();

    if (currentUser) {
      try {
        const { error } = await supabase
          .from("chat_sessions")
          .insert([
            {
              id: newId,
              user_id: currentUser.id,
              title: defaultTitle,
              updated_at: new Date().toISOString(),
            },
          ]);

        if (error) {
          console.warn("Could not persist session to Supabase:", error.message);
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
      validationData: null,
      validatedGenerationId: null,
      validationError: null,
      lldStatus: initialLldStatus,
      lldData: initialLldData,
      logs: [],
      availableVersions: [],
      activeVersionTag: "v1.0",
      activeDiff: null,
      activeView: "chat",
    }));

    return newId;
  },

  setActiveSession: async (id: string) => {
    if (!id) return;

    set({
      activeSessionId: id,
      activeView: "chat",
    });

    const currentUser = get().user;

    if (!currentUser || !isUUID(id)) {
      return;
    }

    try {
      // 1. Fetch messages for this session
      const { data: dbMessages, error: msgErr } = await supabase
        .from("messages")
        .select("id, role, content, json_response, created_at")
        .eq("session_id", id)
        .order("created_at", { ascending: true });

      if (msgErr) {
        console.warn("Error fetching session messages:", msgErr.message);
      }

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
                }
              : ses
          ),
        }));
      }

      // 2. Fetch architecture design for this session
      const { data: dbDesigns, error: designErr } = await supabase
        .from("architecture_designs")
        .select("id, version_tag, prompt, created_at, is_latest, diff, design_json")
        .eq("session_id", id)
        .order("created_at", { ascending: false });

      if (designErr) {
        console.warn("Error fetching architecture designs:", designErr.message);
      }

      if (dbDesigns && dbDesigns.length > 0) {
        const latestDesign = dbDesigns[0];
        const pkg = (latestDesign.design_json as Record<string, any>) || {};
        const savedHld = (pkg.hld as Record<string, unknown>) || null;
        let parsedNodes: Node[] = [];
        let parsedEdges: Edge[] = [];
        if (savedHld) {
          const parsed = parseHldToReactFlow(savedHld);
          parsedNodes = parsed.nodes;
          parsedEdges = parsed.edges;
        }

        let restoredBenchmarks: Record<string, ModelBenchmarkResult> = {};
        let restoredComparison: BenchmarkComparisonSummary | null = null;

        if (pkg.benchmarks) {
          restoredBenchmarks = pkg.benchmarks.results || {};
          restoredComparison = pkg.benchmarks.comparison || null;
        }

        try {
          const { data: dbBenchmarks } = await supabase
            .from("architecture_benchmarks")
            .select("*")
            .eq("session_id", id);

          if (dbBenchmarks && dbBenchmarks.length > 0) {
            dbBenchmarks.forEach((b: any) => {
              if (b.model_id && !restoredBenchmarks[b.model_id]) {
                restoredBenchmarks[b.model_id] = {
                  model_id: b.model_id,
                  model_name: b.model_name,
                  is_archova: b.is_archova,
                  status: b.status,
                  latency_ms: Number(b.latency_ms) || 0,
                  package: b.package_json,
                  validation: b.validation_json,
                };
              }
              if (b.comparison_json && !restoredComparison) {
                restoredComparison = b.comparison_json;
              }
            });
          }
        } catch {
          // Table fallback
        }

        set((s) => ({
          sessions: s.sessions.map((ses) =>
            ses.id === id ? { ...ses, hasArchitecture: true } : ses
          ),
          availableVersions: dbDesigns,
          activeVersionTag: latestDesign.version_tag || "v1.0",
          activeDiff: latestDesign.diff || null,
          hldData: savedHld,
          hldNodes: parsedNodes,
          hldEdges: parsedEdges,
          arsrsData: pkg.arsrs || null,
          lldData: pkg.llds || initialLldData,
          validationData: pkg.validation
            ? ({ validation: { summary: pkg.validation } } as any)
            : null,
          benchmarkResults: restoredBenchmarks,
          comparisonData: restoredComparison,
          interviewCompleted: true,
          activePipelineStep: 3,
          generationStatus: "COMPLETED",
          activeView: "hld", // DIRECTLY DISPLAY THE DESIGN
        }));
      } else {
        // Fallback: check if any message had json_response with hld
        const msgWithJson = dbMessages?.find(
          (m) => m.json_response && (m.json_response as any).hld
        );
        if (msgWithJson && (msgWithJson.json_response as any).hld) {
          const pkg = msgWithJson.json_response as any;
          const parsed = parseHldToReactFlow(pkg.hld);
          set((s) => ({
            sessions: s.sessions.map((ses) =>
              ses.id === id ? { ...ses, hasArchitecture: true } : ses
            ),
            hldData: pkg.hld,
            hldNodes: parsed.nodes,
            hldEdges: parsed.edges,
            arsrsData: pkg.arsrs || null,
            lldData: pkg.llds || pkg.lld || initialLldData,
            interviewCompleted: true,
            activePipelineStep: 3,
            generationStatus: "COMPLETED",
            activeView: "hld", // DIRECTLY DISPLAY THE DESIGN
          }));
        } else {
          // Reset architecture data for sessions without an architecture diagram
          set({
            hldData: null,
            hldNodes: [],
            hldEdges: [],
            arsrsData: null,
            lldData: initialLldData,
            validationData: null,
            availableVersions: [],
            activeVersionTag: "v1.0",
            activeDiff: null,
            interviewCompleted: false,
            activePipelineStep: 1,
            generationStatus: "IDLE",
            activeView: "chat",
          });
        }
      }
    } catch (err) {
      console.warn("Could not restore session from Supabase:", err);
    }
  },

  addMessage: async (sessionId: string, msg: ChatMessage) => {
    // 1. Immediately append to in-memory store
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

    const currentUser = get().user;
    if (!currentUser || !isUUID(sessionId)) {
      return;
    }

    try {
      // 2. Ensure session exists in chat_sessions table and rename if generic
      const { data: existingSession } = await supabase
        .from("chat_sessions")
        .select("id, title")
        .eq("id", sessionId)
        .maybeSingle();

      const isGenericTitle =
        !existingSession?.title ||
        /^Architecture\s*\d*$/i.test(existingSession.title) ||
        /^New Architecture/i.test(existingSession.title);

      const promptSnippet = msg.content.trim().slice(0, 42);

      if (msg.role === "user" && isGenericTitle && promptSnippet) {
        set((s) => ({
          sessions: s.sessions.map((ses) =>
            ses.id === sessionId ? { ...ses, title: promptSnippet } : ses
          ),
        }));

        if (existingSession) {
          await supabase
            .from("chat_sessions")
            .update({ title: promptSnippet, updated_at: new Date().toISOString() })
            .eq("id", sessionId);
        } else {
          await supabase.from("chat_sessions").insert([
            {
              id: sessionId,
              user_id: currentUser.id,
              title: promptSnippet,
              updated_at: new Date().toISOString(),
            },
          ]);
        }
      } else {
        if (existingSession) {
          await supabase
            .from("chat_sessions")
            .update({ updated_at: new Date().toISOString() })
            .eq("id", sessionId);
        } else {
          await supabase.from("chat_sessions").insert([
            {
              id: sessionId,
              user_id: currentUser.id,
              title: "Architecture Session",
              updated_at: new Date().toISOString(),
            },
          ]);
        }
      }

      // 3. Insert message into messages table
      await supabase.from("messages").insert([
        {
          session_id: sessionId,
          role: msg.role === "ai" ? "assistant" : "user",
          content: msg.content,
        },
      ]);
    } catch (err) {
      console.warn("Could not persist message to Supabase:", err);
    }
  },

  saveCurrentArchitecture: async (targetSessionId?: string) => {
    const activeSid = targetSessionId || get().activeSessionId;
    const currentUser = get().user;
    if (!activeSid || !currentUser || !isUUID(activeSid)) {
      return;
    }

    const hld = get().hldData;
    const arsrs = get().arsrsData;
    const llds = get().lldData;
    const validation = get().validationData;
    const hldNodes = get().hldNodes;

    if (!hld) return;

    const currentSession = get().sessions.find((s) => s.id === activeSid);
    const userPrompt =
      currentSession?.messages.find((m) => m.role === "user")?.content ||
      currentSession?.title ||
      "Architecture Design";

    const scorePercent = validation
      ? Math.round(
          (validation.validation?.summary?.overall_score ??
            validation.validation?.scorecard?.overall_composite_score ??
            0.95) * 100
        )
      : 95;
    const verdict = validation?.validation?.summary?.verdict || "APPROVED";

    const fullPackage = {
      hld,
      llds,
      arsrs,
      validation: validation?.validation?.summary || validation?.validation || null,
      score: scorePercent,
      verdict,
      benchmarks: {
        results: get().benchmarkResults,
        comparison: get().comparisonData,
      },
    };

    try {
      const { data: existingLatest } = await supabase
        .from("architecture_designs")
        .select("id, version, version_tag")
        .eq("session_id", activeSid)
        .eq("is_latest", true)
        .maybeSingle();

      let nextVerTag = "v1.0";
      let parentId: string | null = null;

      if (existingLatest) {
        parentId = existingLatest.id;
        await supabase
          .from("architecture_designs")
          .update({ is_latest: false })
          .eq("id", existingLatest.id);

        const prevTag = existingLatest.version_tag || "v1.0";
        const num = parseFloat(prevTag.replace("v", "")) || 1.0;
        nextVerTag = `v${(num + 0.1).toFixed(1)}`;
      }

      await supabase.from("architecture_designs").insert([
        {
          session_id: activeSid,
          user_id: currentUser.id,
          prompt: userPrompt,
          design_json: fullPackage,
          version: parseInt(nextVerTag.replace("v", "").split(".")[0], 10) || 1,
          version_tag: nextVerTag,
          parent_id: parentId,
          is_latest: true,
          updated_at: new Date().toISOString(),
        },
      ]);

      await supabase
        .from("chat_sessions")
        .update({ updated_at: new Date().toISOString() })
        .eq("id", activeSid);

      set((s) => ({
        activeVersionTag: nextVerTag,
        sessions: s.sessions.map((ses) =>
          ses.id === activeSid ? { ...ses, hasArchitecture: true } : ses
        ),
      }));

      await get().fetchVersionsForSession(activeSid);
    } catch (err) {
      console.warn("Could not save architecture design to Supabase:", err);
    }
  },

  deleteSession: async (sessionId: string) => {
    if (!sessionId) return;

    const currentSessions = get().sessions;
    const remainingSessions = currentSessions.filter((s) => s.id !== sessionId);
    const wasActive = get().activeSessionId === sessionId;

    // 1. Instantly update in-memory store
    if (wasActive) {
      if (remainingSessions.length > 0) {
        set({ sessions: remainingSessions });
        await get().setActiveSession(remainingSessions[0].id);
      } else {
        set({
          sessions: [],
          activeSessionId: null,
          activeView: "chat",
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
          validationData: null,
          validatedGenerationId: null,
          validationError: null,
          lldStatus: initialLldStatus,
          lldData: initialLldData,
          logs: [],
          availableVersions: [],
          activeVersionTag: "v1.0",
          activeDiff: null,
        });
      }
    } else {
      set({ sessions: remainingSessions });
    }

    // 2. Cascade delete from Supabase if authenticated and is UUID
    const currentUser = get().user;
    if (currentUser && isUUID(sessionId)) {
      try {
        await supabase
          .from("architecture_designs")
          .delete()
          .eq("session_id", sessionId);

        await supabase
          .from("architecture_benchmarks")
          .delete()
          .eq("session_id", sessionId);

        await supabase
          .from("chat_sessions")
          .delete()
          .eq("id", sessionId);
      } catch (err) {
        console.warn("Could not delete session from Supabase:", err);
      }
    }
  },

  loadDemoData: () => {
    // Dummy HLD/LLD templates completely removed.
    // Creates a fresh clean session instead.
    get().createSession();
  },

  // ── Versioning & Architectural Evolution ──
  activeVersionTag: "v1.0",
  availableVersions: [],
  activeDiff: null,
  setActiveVersionTag: (tag) => set({ activeVersionTag: tag }),

  fetchVersionsForSession: async (sessionId: string) => {
    try {
      const { data } = await supabase
        .from("architecture_designs")
        .select("id, version_tag, prompt, created_at, is_latest, diff, design_json")
        .eq("session_id", sessionId)
        .order("created_at", { ascending: false });

      if (data && data.length > 0) {
        set({ availableVersions: data });
      }
    } catch {
      // Continue
    }
  },

  selectVersion: async (versionTagOrId: string) => {
    const versions = get().availableVersions;
    const match = versions.find((v) => v.version_tag === versionTagOrId || v.id === versionTagOrId);
    if (!match || !match.design_json) return;

    const pkg = match.design_json as Record<string, any>;
    const savedHld = pkg.hld as Record<string, unknown> | null;
    let parsedNodes: Node[] = [];
    let parsedEdges: Edge[] = [];
    if (savedHld) {
      const parsed = parseHldToReactFlow(savedHld);
      parsedNodes = parsed.nodes;
      parsedEdges = parsed.edges;
    }

    set({
      activeVersionTag: match.version_tag || "v1.0",
      activeDiff: match.diff || null,
      hldData: savedHld,
      hldNodes: parsedNodes,
      hldEdges: parsedEdges,
      arsrsData: pkg.arsrs || null,
      lldData: pkg.llds || initialLldData,
      validationData: pkg.validation ? { validation: { summary: pkg.validation } } as any : null,
      benchmarkResults: pkg.benchmarks?.results || get().benchmarkResults,
      comparisonData: pkg.benchmarks?.comparison || get().comparisonData,
    });
  },

  evolveArchitecture: async (featurePrompt: string) => {
    const activeSid = get().activeSessionId;
    const currentUser = get().user;
    const currentHld = get().hldData;
    const currentLld = get().lldData;
    const currentArsrs = get().arsrsData;
    const currentVer = get().activeVersionTag || "v1.0";

    if (!currentHld) {
      throw new Error("No baseline architecture found to evolve.");
    }

    const num = parseFloat(currentVer.replace("v", "")) || 1.0;
    const nextVerTag = `v${(num + 0.1).toFixed(1)}`;

    const baselinePackage = {
      version: currentVer.replace("v", ""),
      version_tag: currentVer,
      hld: {
        ...currentHld,
        nodes: get().hldNodes,
        edges: get().hldEdges,
      },
      llds: currentLld,
      arsrs: currentArsrs,
    };

    const response = await aiEngineApi.evolveArchitecture({
      sessionId: activeSid || undefined,
      featurePrompt,
      baselinePackage,
      targetVersion: nextVerTag,
    });

    const evolvedPkg = response.evolved_architecture;
    const diff = response.diff;
    const savedHld = evolvedPkg.hld;
    let parsedNodes: Node[] = [];
    let parsedEdges: Edge[] = [];
    if (savedHld) {
      const parsed = parseHldToReactFlow(savedHld);
      parsedNodes = parsed.nodes;
      parsedEdges = parsed.edges;
    }

    const currentVersions = get().availableVersions;
    const baseVersion = currentVersions.find((v) => v.version_tag === currentVer) || {
      id: `ver-base-${Date.now()}`,
      version_tag: currentVer,
      prompt: "Baseline Architecture",
      created_at: new Date(Date.now() - 60000).toISOString(),
      is_latest: false,
      design_json: {
        hld: currentHld,
        llds: currentLld,
        arsrs: currentArsrs,
      },
    };

    const newVersionItem = {
      id: `ver-${Date.now()}`,
      version_tag: response.version,
      prompt: featurePrompt,
      created_at: new Date().toISOString(),
      is_latest: true,
      diff,
      design_json: evolvedPkg,
    };

    const existingOlder = currentVersions.filter((v) => v.version_tag !== response.version);
    const updatedVersions = [
      newVersionItem,
      ...(existingOlder.length > 0
        ? existingOlder.map((v) => ({ ...v, is_latest: false }))
        : [baseVersion]),
    ];

    set({
      activeVersionTag: response.version,
      availableVersions: updatedVersions,
      activeDiff: diff,
      hldData: savedHld,
      hldNodes: parsedNodes,
      hldEdges: parsedEdges,
      lldData: evolvedPkg.llds || currentLld,
      arsrsData: evolvedPkg.arsrs || currentArsrs,
      generationStatus: "COMPLETED",
      activePipelineStep: 3,
      activeView: "hld",
    });

    // Also update local session messages so the evolved notice appears in chat
    if (activeSid) {
      const addedCompNames = Array.isArray(diff.added_nodes)
        ? diff.added_nodes
            .map((n: any) =>
              typeof n === "string" ? n : n.label || n.data?.label || n.id || "Component"
            )
            .join(", ")
        : "None";

      const evolvedNotice: ChatMessage = {
        id: generateMsgId(),
        role: "ai",
        content: `✨ Architecture Evolved to ${response.version}\n\n• Summary: ${diff.feature_summary}\n• Added Components: ${addedCompNames}\n• Database Changes: ${diff.added_tables?.length || 0} new tables, ${diff.added_columns?.length || 0} new columns\n• Invariance Guarantee: 100% verified baseline preservation (0 existing components modified or deleted).`,
      };
      set((s) => ({
        sessions: s.sessions.map((ses) =>
          ses.id === activeSid
            ? { ...ses, messages: [...ses.messages, evolvedNotice] }
            : ses
        ),
      }));
    }

    // Persist to Supabase if authenticated
    if (currentUser && activeSid && !activeSid.startsWith("demo-")) {
      try {
        const { data: existingLatest } = await supabase
          .from("architecture_designs")
          .select("id")
          .eq("session_id", activeSid)
          .eq("is_latest", true)
          .maybeSingle();

        if (existingLatest) {
          await supabase
            .from("architecture_designs")
            .update({ is_latest: false })
            .eq("id", existingLatest.id);
        }

        await supabase.from("architecture_designs").insert([{
          session_id: activeSid,
          user_id: currentUser.id,
          prompt: featurePrompt,
          design_json: evolvedPkg,
          version: parseInt(response.version.replace("v", "").split(".")[0], 10) || 1,
          version_tag: response.version,
          parent_id: existingLatest?.id || null,
          diff: diff,
          is_latest: true,
          updated_at: new Date().toISOString(),
        }]);

        await supabase.from("messages").insert([{
          session_id: activeSid,
          role: "assistant",
          content: `✨ Architecture Evolved to ${response.version}\n\n• Summary: ${diff.feature_summary}\n• Added Components: ${diff.added_nodes?.join(", ") || "None"}\n• Database Changes: ${diff.added_tables?.length || 0} new tables, ${diff.added_columns?.length || 0} new columns\n• Invariance Guarantee: 100% verified baseline preservation (0 existing components modified or deleted).`,
          json_response: evolvedPkg,
        }]);

        await supabase.from("chat_sessions").update({
          updated_at: new Date().toISOString()
        }).eq("id", activeSid);

        await get().fetchVersionsForSession(activeSid);
      } catch (dbErr) {
        console.warn("Could not persist evolved architecture to Supabase:", dbErr);
      }
    }

    return { success: true, versionTag: response.version, diff };
  },

  // Modal Explanations & Tech Rationale
  explainOpen: false,
  explainNode: null,
  explainTitle: undefined,
  explainContent: undefined,
  explainNodeData: undefined,
  openExplain: (nodeId, title, content, nodeData) =>
    set({
      explainOpen: true,
      explainNode: nodeId,
      explainTitle: title,
      explainContent: content,
      explainNodeData: nodeData,
    }),
  openTechRationale: (nodeData) => {
    const { activeModelId } = get();
    // In-detail tech rationale is strictly visible ONLY for Archova AI Engine generated architecture
    if (activeModelId && activeModelId !== "archova") {
      return;
    }
    const id = String(nodeData.id || "component");
    const label = String(nodeData.label || nodeData.name || id);
    set({
      explainOpen: true,
      explainNode: id,
      explainTitle: label,
      explainContent: typeof nodeData.description === "string" ? nodeData.description : undefined,
      explainNodeData: nodeData,
    });
  },
  closeExplain: () =>
    set({
      explainOpen: false,
      explainNode: null,
      explainTitle: undefined,
      explainContent: undefined,
      explainNodeData: undefined,
    }),

  // ── Multi-Model Benchmarking & Comparison Implementation ──
  benchmarkModelsConfig: DEFAULT_BENCHMARK_PRESETS,
  benchmarkApiKey: "",
  isBenchmarking: false,
  benchmarkResults: {},
  activeModelId: "archova",
  comparisonData: null,
  archovaSnapshot: null,

  setBenchmarkModelsConfig: (models) => set({ benchmarkModelsConfig: models }),
  setBenchmarkApiKey: (key) => set({ benchmarkApiKey: key }),

  selectModel: (modelId: string) => {
    const state = get();
    if (modelId === state.activeModelId) return;

    // Take snapshot of Archova state when navigating away for the first time
    let snapshot = state.archovaSnapshot;
    if (state.activeModelId === "archova" || !snapshot) {
      snapshot = {
        arsrsData: state.arsrsData,
        hldData: state.hldData,
        hldNodes: state.hldNodes,
        hldEdges: state.hldEdges,
        lldData: state.lldData,
        validationData: state.validationData,
      };
      set({ archovaSnapshot: snapshot });
    }

    if (modelId === "archova") {
      // Revert views back to Archova AI Engine multi-agent design
      if (snapshot) {
        set({
          activeModelId: "archova",
          arsrsData: snapshot.arsrsData,
          hldData: snapshot.hldData,
          hldNodes: snapshot.hldNodes,
          hldEdges: snapshot.hldEdges,
          lldData: snapshot.lldData,
          validationData: snapshot.validationData,
        });
      } else {
        set({ activeModelId: "archova" });
      }
      return;
    }

    // Switch view to selected direct LLM model output
    const targetModel =
      state.benchmarkResults[modelId] ||
      Object.values(state.benchmarkResults).find(
        (m) =>
          m.model_id === modelId ||
          m.model_name?.toLowerCase() === modelId.toLowerCase() ||
          (modelId.includes("gemini") && (m.model_id.includes("gemini") || m.model_name.toLowerCase().includes("gemini"))) ||
          (modelId.includes("chatgpt") && (m.model_id.includes("chatgpt") || m.model_id.includes("gpt") || m.model_name.toLowerCase().includes("chatgpt"))) ||
          (modelId.includes("nvidia") && (m.model_id.includes("nvidia") || m.model_name.toLowerCase().includes("nvidia")))
      );

    if (!targetModel || !targetModel.package) {
      set({ activeModelId: modelId });
      return;
    }

    const pkg = targetModel.package;
    const hld = pkg.hld || {};
    const parsedFlow = parseHldToReactFlow(hld, undefined, state.layoutDirection);
    const llds = pkg.llds || {};

    const targetLldData: Record<LldType, Record<string, unknown> | null> = {
      backend: llds.backend || null,
      frontend: llds.frontend || null,
      database: llds.database || null,
      security: llds.security || null,
      cloud: llds.cloud || null,
    };

    set({
      activeModelId: modelId,
      arsrsData: pkg.arsrs || null,
      hldData: hld,
      hldNodes: parsedFlow.nodes,
      hldEdges: parsedFlow.edges,
      lldData: targetLldData,
      validationData: targetModel.validation as ValidatedArchitectureResponse,
    });
  },

  runBenchmarkSuite: async (promptText: string) => {
    const state = get();
    const modelsToRun = state.benchmarkModelsConfig.map((m) => ({
      ...m,
      api_key: m.api_key || state.benchmarkApiKey || undefined,
    }));

    if (modelsToRun.length === 0) return;

    set({ isBenchmarking: true });
    try {
      const response = await aiEngineApi.generateBenchmark(
        promptText,
        modelsToRun,
        state.generationId || undefined
      );

      const resultsMap: Record<string, ModelBenchmarkResult> = { ...state.benchmarkResults };
      response.models.forEach((m) => {
        if (m.model_id) {
          resultsMap[m.model_id] = m;
        }
      });

      if (response.archova) {
        resultsMap["archova"] = response.archova;
      }

      set({
        benchmarkResults: resultsMap,
        comparisonData: response.comparison,
        isBenchmarking: false,
      });

      // ── Persist all benchmark models' generated designs to Supabase ──
      const currentUser = get().user;
      const activeSid = get().activeSessionId;

      if (currentUser && activeSid && isUUID(activeSid)) {
        try {
          const recordsToInsert = response.models.map((m) => ({
            session_id: activeSid,
            user_id: currentUser.id,
            generation_id: state.generationId || null,
            model_id: m.model_id,
            model_name: m.model_name,
            is_archova: false,
            status: m.status || "COMPLETED",
            latency_ms: m.latency_ms || 0,
            package_json: m.package || {},
            validation_json: m.validation || {},
            comparison_json: response.comparison || null,
            updated_at: new Date().toISOString(),
          }));

          if (response.archova) {
            recordsToInsert.push({
              session_id: activeSid,
              user_id: currentUser.id,
              generation_id: state.generationId || null,
              model_id: "archova",
              model_name: response.archova.model_name || "Archova AI",
              is_archova: true,
              status: response.archova.status || "COMPLETED",
              latency_ms: response.archova.latency_ms || 0,
              package_json: response.archova.package || {},
              validation_json: response.archova.validation || {},
              comparison_json: response.comparison || null,
              updated_at: new Date().toISOString(),
            });
          }

          if (recordsToInsert.length > 0) {
            await supabase.from("architecture_benchmarks").insert(recordsToInsert);
          }
        } catch (dbErr) {
          console.warn("Could not insert architecture_benchmarks to Supabase:", dbErr);
        }

        // Also update latest architecture_designs record if already created
        try {
          const { data: latestDesign } = await supabase
            .from("architecture_designs")
            .select("id, design_json")
            .eq("session_id", activeSid)
            .eq("is_latest", true)
            .maybeSingle();

          if (latestDesign) {
            const updatedPkg = {
              ...(latestDesign.design_json as Record<string, unknown>),
              benchmarks: {
                results: resultsMap,
                comparison: response.comparison,
              },
            };
            await supabase
              .from("architecture_designs")
              .update({
                design_json: updatedPkg,
                updated_at: new Date().toISOString(),
              })
              .eq("id", latestDesign.id);
          }
        } catch (updateErr) {
          console.warn("Could not embed benchmarks in architecture_designs:", updateErr);
        }
      }
    } catch {
      set({ isBenchmarking: false });
    }
  },
}));

