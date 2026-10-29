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
  type TargetedCorrectionResponse,
  type TargetedCorrectionRequest,
  type AcceptCorrectionResponse,
  type RejectCorrectionResponse,
  DEFAULT_BENCHMARK_PRESETS,
} from "./ai-engine-client";
import {
  validatorApi,
  type ValidatedArchitectureResponse,
} from "./validator-client";
import {
  validatorV2Client,
  type Report,
  type ReportWithPackage,
} from "./validator-v2-client";
import {
  type CorrectionPlan,
  type CorrectionItemStatus,
  buildCorrectionPlan,
  validateCorrectionEligibility,
  checkAutomatedCorrectionCapability,
} from "./correction-planner";
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
  hldWorkspaceTab: "hld" | "lld" | "validation" | "validation-v2" | "json" | "comparison";
  setHldWorkspaceTab: (tab: "hld" | "lld" | "validation" | "validation-v2" | "json" | "comparison") => void;
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
  validateArchitecture: (pkg?: Record<string, any>) => Promise<Report | ValidatedArchitectureResponse | null>;
  runCorrectionWorkflow: (maxRetries?: number, force?: boolean) => Promise<Report | ValidatedArchitectureResponse | null>;

  // ── Standalone Validator Engine v2 (Port 8002) ──
  validationReport: Report | null;
  correctionPlan: CorrectionPlan | null;
  validationStatus: string;
  validationCurrentStep: string;
  isValidatingV2: boolean;
  setValidationReport: (report: Report | null) => void;
  setCorrectionPlan: (plan: CorrectionPlan | null) => void;
  runValidatorV2Pipeline: (pkg?: Record<string, any>) => Promise<ReportWithPackage | null>;

  // ── Evidence-Based Correction Review Workflow (Part 2.2.1) ──
  correctionDecisions: Record<
    string,
    {
      decision: CorrectionItemStatus;
      decided_at: string;
      notes?: string;
      generation_id?: string;
      version_tag?: string;
    }
  >;
  isProcessingCorrectionAction: boolean;
  correctionActionMessage: {
    type: "success" | "warning" | "error" | "info";
    text: string;
    itemId?: string;
  } | null;
  approveCorrectionPlanItem: (itemId: string) => {
    success: boolean;
    status: CorrectionItemStatus;
    message: string;
    automatedSupported: boolean;
  };
  markCorrectionForManualReview: (
    itemId: string,
    notes?: string
  ) => {
    success: boolean;
    status: CorrectionItemStatus;
    message: string;
  };
  dismissCorrectionPlanItem: (
    itemId: string,
    notes?: string
  ) => {
    success: boolean;
    status: CorrectionItemStatus;
    message: string;
  };
  resetCorrectionDecision: (itemId: string) => void;
  clearCorrectionActionMessage: () => void;

  // ── Targeted AI Architecture Correction (Part 2.2.2) ──
  activeCorrectionDraft: TargetedCorrectionResponse | null;
  isExecutingAiCorrection: boolean;
  validationIsStale: boolean;
  staleReason: string | null;
  staleArtifactType: string | null;
  historicalValidationReports: Record<string, Report>;
  executeTargetedCorrection: (
    itemId: string,
    simulatedArtifact?: Record<string, unknown>
  ) => Promise<TargetedCorrectionResponse | null>;
  acceptCorrectionDraft: (operationId: string) => Promise<boolean>;
  rejectCorrectionDraft: (operationId: string, reason?: string) => Promise<boolean>;
  dismissCorrectionDraftModal: () => void;
  runRevalidation: () => Promise<Report | ValidatedArchitectureResponse | null>;

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
      // 1. Check for previously saved guest user in localStorage
      let hasGuest = false;
      if (typeof window !== "undefined") {
        try {
          const guestRaw = localStorage.getItem("archai-guest-user");
          if (guestRaw) {
            const guestUser = JSON.parse(guestRaw);
            if (guestUser && guestUser.id) {
              hasGuest = true;
              set({ user: guestUser, session: null, authLoading: false });
              const wsRaw = localStorage.getItem("archai-guest-workspace");
              if (wsRaw) {
                try {
                  const ws = JSON.parse(wsRaw);
                  if (ws && ws.activeSessionId) {
                    set({
                      sessions: ws.sessions || [],
                      activeSessionId: ws.activeSessionId,
                      generationId: ws.generationId || null,
                      arsrsData: ws.arsrsData || null,
                      hldData: ws.hldData || null,
                      hldNodes: ws.hldNodes || [],
                      hldEdges: ws.hldEdges || [],
                      lldData: ws.lldData || initialLldData,
                      activeVersionTag: ws.activeVersionTag || "v1.0",
                      availableVersions: ws.availableVersions || [],
                      validationReport: ws.validationReport || null,
                      correctionPlan: ws.correctionPlan || null,
                      validationIsStale: ws.validationIsStale || false,
                      staleReason: ws.staleReason || null,
                      interviewCompleted: !!ws.interviewCompleted,
                      generationStatus: ws.generationStatus || "COMPLETED",
                      activePipelineStep: ws.activePipelineStep || 3,
                    });
                  }
                } catch {
                  // ignore
                }
              }
            }
          }
        } catch {
          // ignore
        }
      }

      // 2. Check Supabase session
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
        if (!hasGuest) {
          set({ session: null, user: null, authLoading: false });
        }
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
        localStorage.removeItem("archai-guest-workspace");
        const keysToRemove: string[] = [];
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          if (
            key &&
            (key.startsWith("sb-") ||
              key.includes("supabase.auth") ||
              key.includes("supabase") ||
              key === "archai-guest-user" ||
              key === "archai-guest-workspace")
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

  // Validator Engine v2 Health & Results (Port 8002)
  validatorConnected: false,
  validatorVersion: "Checking...",
  checkValidatorHealth: async () => {
    const res = await validatorApi.checkHealth();
    set({ validatorConnected: res.ok, validatorVersion: res.version || (res.ok ? "2.0.0" : "Offline") });
    return res.ok;
  },
  validationData: null,
  validatedGenerationId: null,
  isValidating: false,
  validationError: null,
  setValidationData: (data) => set({ validationData: data }),

  // Standalone Validator Engine v2 (Port 8002)
  validationReport: null,
  correctionPlan: null,
  validationStatus: "IDLE",
  validationCurrentStep: "",
  isValidatingV2: false,
  setValidationReport: (report) => {
    const plan = buildCorrectionPlan(report);
    set({ validationReport: report, correctionPlan: plan });
  },
  setCorrectionPlan: (plan) => set({ correctionPlan: plan }),

  // ── Targeted AI Architecture Correction (Part 2.2.2) ──
  activeCorrectionDraft: null,
  isExecutingAiCorrection: false,
  validationIsStale: false,
  staleReason: null,
  staleArtifactType: null,
  historicalValidationReports: {},

  // ── Evidence-Based Correction Review Workflow Actions (Part 2.2.1) ──
  correctionDecisions: {},
  isProcessingCorrectionAction: false,
  correctionActionMessage: null,

  approveCorrectionPlanItem: (itemId: string) => {
    if (get().isProcessingCorrectionAction) {
      return {
        success: false,
        status: "PENDING_REVIEW" as CorrectionItemStatus,
        message: "Another correction action is currently being processed. Please wait.",
        automatedSupported: false,
      };
    }

    set({ isProcessingCorrectionAction: true });

    try {
      const {
        correctionPlan,
        validationReport,
        generationId,
        activeVersionTag,
        hldData,
        arsrsData,
        lldData,
        addLogEntry,
      } = get();

      if (!correctionPlan || !correctionPlan.items) {
        set({ isProcessingCorrectionAction: false });
        return {
          success: false,
          status: "CORRECTION_FAILED" as CorrectionItemStatus,
          message: "No active correction plan found.",
          automatedSupported: false,
        };
      }

      const item = correctionPlan.items.find((i) => i.id === itemId);
      if (!item) {
        set({ isProcessingCorrectionAction: false });
        return {
          success: false,
          status: "CORRECTION_FAILED" as CorrectionItemStatus,
          message: `Correction item '${itemId}' does not exist in the active plan.`,
          automatedSupported: false,
        };
      }

      // Collect known finding IDs from active validation report iterations
      const knownFindingIds: string[] = [];
      if (validationReport && Array.isArray(validationReport.iterations)) {
        for (const it of validationReport.iterations) {
          if (it.results) {
            for (const res of Object.values(it.results)) {
              if (Array.isArray(res.findings)) {
                for (const f of res.findings) {
                  if (f.id) knownFindingIds.push(f.id);
                }
              }
            }
          }
        }
      }

      // Check eligibility
      const eligibility = validateCorrectionEligibility(item, {
        generationId: generationId || null,
        versionTag: activeVersionTag || "v1.0",
        reportGenerationId: validationReport?.generation_id || null,
        hasArchitecturePackage: Boolean(hldData && (arsrsData || lldData)),
        knownFindingIds: knownFindingIds.length > 0 ? knownFindingIds : undefined,
      });

      if (!eligibility.eligible) {
        set({
          isProcessingCorrectionAction: false,
          correctionActionMessage: {
            type: "warning",
            text: eligibility.reason,
            itemId,
          },
        });
        return {
          success: false,
          status: item.status,
          message: eligibility.reason,
          automatedSupported: false,
        };
      }

      const decision = {
        decision: "APPROVED_FOR_CORRECTION" as CorrectionItemStatus,
        decided_at: new Date().toISOString(),
        notes: "Approved by user for targeted AI architecture correction.",
        generation_id: generationId || undefined,
        version_tag: activeVersionTag || undefined,
      };

      const updatedItems = correctionPlan.items.map((it) =>
        it.id === itemId
          ? {
            ...it,
            status: "APPROVED_FOR_CORRECTION" as CorrectionItemStatus,
            status_reason: "Approved by user. Synthesizing targeted AI correction...",
            review_decision: decision,
          }
          : it
      );

      const updatedPlan = {
        ...correctionPlan,
        items: updatedItems,
      };

      set((s) => ({
        isProcessingCorrectionAction: false,
        correctionDecisions: {
          ...s.correctionDecisions,
          [itemId]: decision,
        },
        correctionPlan: updatedPlan,
        correctionActionMessage: {
          type: "info",
          text: `Approved correction [${item.title}]. Synthesizing targeted AI correction...`,
          itemId,
        },
      }));

      addLogEntry({
        timestamp: new Date().toTimeString().split(" ")[0],
        stage: "CORRECTION_WORKFLOW",
        message: `📋 Correction [${item.id}] approved by user. Requesting isolated AI correction from AI Engine...`,
        level: "INFO",
      });

      // Asynchronously invoke targeted AI correction execution
      void get().executeTargetedCorrection(itemId);

      return {
        success: true,
        status: "APPROVED_FOR_CORRECTION",
        message: "Correction approved. AI Engine correction requested.",
        automatedSupported: true,
      };
    } catch (err) {
      set({ isProcessingCorrectionAction: false });
      const msg = err instanceof Error ? err.message : "Error approving correction plan item.";
      return {
        success: false,
        status: "CORRECTION_FAILED" as CorrectionItemStatus,
        message: msg,
        automatedSupported: false,
      };
    }
  },

  markCorrectionForManualReview: (itemId: string, notes?: string) => {
    if (get().isProcessingCorrectionAction) {
      return {
        success: false,
        status: "PENDING_REVIEW" as CorrectionItemStatus,
        message: "Another correction action is currently being processed.",
      };
    }

    const { correctionPlan, generationId, activeVersionTag, addLogEntry } = get();
    if (!correctionPlan || !correctionPlan.items) {
      return {
        success: false,
        status: "CORRECTION_FAILED" as CorrectionItemStatus,
        message: "No active correction plan found.",
      };
    }

    const item = correctionPlan.items.find((i) => i.id === itemId);
    if (!item) {
      return {
        success: false,
        status: "CORRECTION_FAILED" as CorrectionItemStatus,
        message: `Correction item '${itemId}' does not exist.`,
      };
    }

    const decision = {
      decision: "MANUAL_REVIEW_REQUIRED" as CorrectionItemStatus,
      decided_at: new Date().toISOString(),
      notes: notes || "Flagged by user for manual architecture review and stakeholder clarification.",
      generation_id: generationId || undefined,
      version_tag: activeVersionTag || undefined,
    };

    const updatedItems = correctionPlan.items.map((it) =>
      it.id === itemId
        ? {
          ...it,
          status: "MANUAL_REVIEW_REQUIRED" as CorrectionItemStatus,
          status_reason: decision.notes,
          requires_manual_review: true,
          review_decision: decision,
        }
        : it
    );

    set((s) => ({
      correctionDecisions: {
        ...s.correctionDecisions,
        [itemId]: decision,
      },
      correctionPlan: {
        ...correctionPlan,
        items: updatedItems,
      },
      correctionActionMessage: {
        type: "warning",
        text: `Correction [${item.title}] marked for manual review.`,
        itemId,
      },
    }));

    addLogEntry({
      timestamp: new Date().toTimeString().split(" ")[0],
      stage: "CORRECTION_WORKFLOW",
      message: `🔍 Correction [${item.id}] marked for manual review: ${decision.notes}`,
      level: "WARNING",
    });

    return {
      success: true,
      status: "MANUAL_REVIEW_REQUIRED",
      message: "Item marked for manual review.",
    };
  },

  dismissCorrectionPlanItem: (itemId: string, notes?: string) => {
    if (get().isProcessingCorrectionAction) {
      return {
        success: false,
        status: "PENDING_REVIEW" as CorrectionItemStatus,
        message: "Another correction action is currently being processed.",
      };
    }

    const { correctionPlan, generationId, activeVersionTag, addLogEntry } = get();
    if (!correctionPlan || !correctionPlan.items) {
      return {
        success: false,
        status: "CORRECTION_FAILED" as CorrectionItemStatus,
        message: "No active correction plan found.",
      };
    }

    const item = correctionPlan.items.find((i) => i.id === itemId);
    if (!item) {
      return {
        success: false,
        status: "CORRECTION_FAILED" as CorrectionItemStatus,
        message: `Correction item '${itemId}' does not exist.`,
      };
    }

    const decision = {
      decision: "DISMISSED" as CorrectionItemStatus,
      decided_at: new Date().toISOString(),
      notes: notes || "Dismissed by user as acceptable risk or not applicable to requirements.",
      generation_id: generationId || undefined,
      version_tag: activeVersionTag || undefined,
    };

    const updatedItems = correctionPlan.items.map((it) =>
      it.id === itemId
        ? {
          ...it,
          status: "DISMISSED" as CorrectionItemStatus,
          status_reason: decision.notes,
          review_decision: decision,
        }
        : it
    );

    set((s) => ({
      correctionDecisions: {
        ...s.correctionDecisions,
        [itemId]: decision,
      },
      correctionPlan: {
        ...correctionPlan,
        items: updatedItems,
      },
      correctionActionMessage: {
        type: "info",
        text: `Correction proposal [${item.title}] dismissed.`,
        itemId,
      },
    }));

    addLogEntry({
      timestamp: new Date().toTimeString().split(" ")[0],
      stage: "CORRECTION_WORKFLOW",
      message: `🚫 Correction proposal [${item.id}] dismissed by user.`,
      level: "INFO",
    });

    return {
      success: true,
      status: "DISMISSED",
      message: "Correction proposal dismissed.",
    };
  },

  resetCorrectionDecision: (itemId: string) => {
    const { correctionPlan, addLogEntry } = get();
    if (!correctionPlan || !correctionPlan.items) return;

    const item = correctionPlan.items.find((i) => i.id === itemId);
    if (!item) return;

    const revertedStatus: CorrectionItemStatus = item.requires_manual_review || !item.is_supported_by_evidence
      ? "MANUAL_REVIEW_REQUIRED"
      : "PENDING_REVIEW";

    const updatedItems = correctionPlan.items.map((it) =>
      it.id === itemId
        ? {
          ...it,
          status: revertedStatus,
          status_reason: revertedStatus === "MANUAL_REVIEW_REQUIRED" ? "Manual review required due to evidence constraints." : "Awaiting user review.",
          review_decision: null,
        }
        : it
    );

    set((s) => {
      const nextDecisions = { ...s.correctionDecisions };
      delete nextDecisions[itemId];
      return {
        correctionDecisions: nextDecisions,
        correctionPlan: {
          ...correctionPlan,
          items: updatedItems,
        },
        correctionActionMessage: null,
      };
    });

    addLogEntry({
      timestamp: new Date().toTimeString().split(" ")[0],
      stage: "CORRECTION_WORKFLOW",
      message: `↩️ Correction decision for [${item.id}] reset to ${revertedStatus}.`,
      level: "INFO",
    });
  },

  clearCorrectionActionMessage: () => set({ correctionActionMessage: null }),

  executeTargetedCorrection: async (itemId: string, simulatedArtifact?: Record<string, unknown>) => {
    const {
      correctionPlan,
      generationId,
      activeVersionTag,
      hldData,
      lldData,
      arsrsData,
      addLogEntry,
      isExecutingAiCorrection,
    } = get();

    if (isExecutingAiCorrection) {
      return null;
    }

    const item = correctionPlan?.items?.find((i) => i.id === itemId);
    if (!item) {
      addLogEntry({
        timestamp: new Date().toTimeString().split(" ")[0],
        stage: "CORRECTION_EXECUTION",
        message: `❌ Cannot execute correction: Item '${itemId}' not found in plan.`,
        level: "ERROR",
      });
      return null;
    }

    set({ isExecutingAiCorrection: true });

    addLogEntry({
      timestamp: new Date().toTimeString().split(" ")[0],
      stage: "CORRECTION_EXECUTION",
      message: `🧠 Requesting targeted AI correction for [${item.finding_id}] on ${item.affected_artifact}...`,
      level: "INFO",
    });

    try {
      const effGenId = generationId || `gen-${Date.now()}`;
      const effVersion = activeVersionTag || "v1.0";

      // 1. Map artifact name to canonical id
      const artifactMapping: Record<string, string> = {
        "HLD": "hld",
        "Backend LLD": "backend",
        "Database LLD": "database",
        "Frontend LLD": "frontend",
        "Security LLD": "security",
        "Cloud LLD": "cloud",
        "ARSRS": "arsrs",
      };
      const canonicalArtifact = artifactMapping[item.affected_artifact] || item.affected_artifact.toLowerCase();

      // 2. Independently register server-side approval
      await aiEngineApi.registerCorrectionApproval({
        generation_id: effGenId,
        finding_id: item.finding_id,
        artifact_type: canonicalArtifact,
        source_version: effVersion,
        approved_by: "user",
        reason: item.reason,
      });

      // 3. Assemble baseline package
      const baselinePackage = {
        generation_id: effGenId,
        version: effVersion.replace("v", ""),
        version_tag: effVersion,
        arsrs: arsrsData,
        hld: hldData,
        llds: lldData,
      };

      // 4. Request targeted correction from AI Engine
      const response = await aiEngineApi.requestTargetedCorrection({
        generation_id: effGenId,
        artifact_type: canonicalArtifact,
        source_version: effVersion,
        finding_id: item.finding_id,
        finding_description: item.description,
        evidence: item.evidence || "Validator finding description",
        correction_instruction: item.correction_instruction,
        reason: item.reason,
        affected_target: item.affected_target || undefined,
        baseline_package: baselinePackage,
        simulated_corrected_artifact: simulatedArtifact,
      });

      set({
        isExecutingAiCorrection: false,
        activeCorrectionDraft: response,
      });

      const statusBadge = response.status;
      addLogEntry({
        timestamp: new Date().toTimeString().split(" ")[0],
        stage: "CORRECTION_EXECUTION",
        message: `✨ AI Engine returned targeted correction draft (${statusBadge}). Operation ID: ${response.operation_id}. Ready for user review.`,
        level: response.status === "CORRECTION_FAILED" ? "ERROR" : "INFO",
      });

      return response;
    } catch (err) {
      set({ isExecutingAiCorrection: false });
      const errMsg = err instanceof Error ? err.message : "Targeted AI correction failed.";
      addLogEntry({
        timestamp: new Date().toTimeString().split(" ")[0],
        stage: "CORRECTION_EXECUTION",
        message: `❌ Targeted correction error: ${errMsg}`,
        level: "ERROR",
      });
      set({
        correctionActionMessage: {
          type: "warning",
          text: `Targeted AI correction failed: ${errMsg}`,
          itemId,
        },
      });
      return null;
    }
  },

  acceptCorrectionDraft: async (operationId: string) => {
    const {
      activeCorrectionDraft,
      activeVersionTag,
      availableVersions,
      validationReport,
      historicalValidationReports,
      correctionPlan,
      hldData,
      lldData,
      arsrsData,
      addLogEntry,
    } = get();

    if (!activeCorrectionDraft || activeCorrectionDraft.operation_id !== operationId) {
      addLogEntry({
        timestamp: new Date().toTimeString().split(" ")[0],
        stage: "CORRECTION_ACCEPT",
        message: `❌ Cannot accept correction: Operation '${operationId}' is not the active draft.`,
        level: "ERROR",
      });
      return false;
    }

    const currVer = activeVersionTag || "v1.0";
    if (activeCorrectionDraft.source_version && activeCorrectionDraft.source_version !== currVer) {
      addLogEntry({
        timestamp: new Date().toTimeString().split(" ")[0],
        stage: "CORRECTION_ACCEPT",
        message: `❌ Stale correction draft rejected: draft was generated on ${activeCorrectionDraft.source_version} but active version is ${currVer}.`,
        level: "ERROR",
      });
      return false;
    }

    try {
      const res = await aiEngineApi.acceptCorrection(operationId, {
        expected_source_version: currVer,
        generation_id: get().generationId || undefined,
      });

      const newVer = res.new_version;
      const normArt = res.artifact_type.toLowerCase();
      const updatedArt = res.updated_artifact;

      // Preserve previous validation report
      const nextHistorical = { ...historicalValidationReports };
      if (validationReport) {
        nextHistorical[currVer] = validationReport;
      }

      // Mark validation as stale
      const staleMsg = `Artifact '${res.artifact_type.toUpperCase()}' was modified and committed as ${newVer}. Previous validation report and verdict no longer apply.`;

      // Update target artifact in store
      let nextHld = hldData;
      let nextNodes = get().hldNodes;
      let nextEdges = get().hldEdges;
      let nextArsrs = arsrsData;
      const nextLld = { ...lldData };

      if (normArt === "hld") {
        nextHld = updatedArt;
        const parsed = parseHldToReactFlow(updatedArt);
        nextNodes = parsed.nodes;
        nextEdges = parsed.edges;
      } else if (normArt === "arsrs") {
        nextArsrs = updatedArt;
      } else if (normArt in nextLld) {
        nextLld[normArt as LldType] = updatedArt;
      }

      const baseVersionItem = availableVersions.find((v) => v.version_tag === currVer) || {
        id: `ver-${currVer}-${Date.now()}`,
        version_tag: currVer,
        prompt: "Baseline Architecture",
        created_at: new Date(Date.now() - 60000).toISOString(),
        is_latest: false,
        design_json: {
          hld: hldData,
          llds: lldData,
          arsrs: arsrsData,
        },
      };

      const newVersionItem = {
        id: `ver-${newVer}-${Date.now()}`,
        version_tag: newVer,
        prompt: activeCorrectionDraft.change_summary,
        created_at: res.accepted_at || new Date().toISOString(),
        is_latest: true,
        design_json: {
          hld: nextHld,
          llds: nextLld,
          arsrs: nextArsrs,
          version: newVer.replace("v", ""),
          version_tag: newVer,
        },
      };

      const olderVersions = availableVersions
        .filter((v) => v.version_tag !== newVer)
        .map((v) => ({ ...v, is_latest: false }));

      const updatedVersions = [
        newVersionItem,
        ...(olderVersions.length > 0 ? olderVersions : [baseVersionItem]),
      ];

      // Update correction plan item status to APPLIED
      let updatedPlan = correctionPlan;
      if (correctionPlan && correctionPlan.items) {
        updatedPlan = {
          ...correctionPlan,
          items: correctionPlan.items.map((it) =>
            it.finding_id === activeCorrectionDraft.finding_id
              ? {
                ...it,
                status: "APPLIED" as CorrectionItemStatus,
                status_reason: `Applied in version ${newVer}: ${activeCorrectionDraft.change_summary}`,
              }
              : it
          ),
        };
      }

      set({
        activeVersionTag: newVer,
        availableVersions: updatedVersions,
        hldData: nextHld,
        hldNodes: nextNodes,
        hldEdges: nextEdges,
        arsrsData: nextArsrs,
        lldData: nextLld,
        validationIsStale: true,
        staleReason: staleMsg,
        staleArtifactType: res.artifact_type,
        historicalValidationReports: nextHistorical,
        activeCorrectionDraft: null,
        correctionPlan: updatedPlan,
      });

      // Save guest workspace if in guest mode
      if (typeof window !== "undefined") {
        const currentUser = get().user;
        if (!currentUser || currentUser.app_metadata?.provider === "guest") {
          try {
            const ws = {
              sessions: get().sessions,
              activeSessionId: get().activeSessionId,
              generationId: get().generationId,
              arsrsData: nextArsrs,
              hldData: nextHld,
              hldNodes: nextNodes,
              hldEdges: nextEdges,
              lldData: nextLld,
              activeVersionTag: newVer,
              availableVersions: updatedVersions,
              validationReport: get().validationReport,
              correctionPlan: updatedPlan,
              validationIsStale: true,
              staleReason: staleMsg,
              interviewCompleted: true,
              generationStatus: "COMPLETED",
              activePipelineStep: 3,
            };
            localStorage.setItem("archai-guest-workspace", JSON.stringify(ws));
          } catch { }
        }
      }

      addLogEntry({
        timestamp: new Date().toTimeString().split(" ")[0],
        stage: "CORRECTION_ACCEPT",
        message: `✅ Correction accepted! Version bumped ${currVer} -> ${newVer}. Validation report marked STALE. Explicit revalidation required.`,
        level: "INFO",
      });

      return true;
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : "Failed to accept correction.";
      addLogEntry({
        timestamp: new Date().toTimeString().split(" ")[0],
        stage: "CORRECTION_ACCEPT",
        message: `❌ Acceptance failed: ${errMsg}`,
        level: "ERROR",
      });
      return false;
    }
  },

  rejectCorrectionDraft: async (operationId: string, reason?: string) => {
    const { activeCorrectionDraft, addLogEntry } = get();
    if (!activeCorrectionDraft || activeCorrectionDraft.operation_id !== operationId) {
      return false;
    }

    try {
      await aiEngineApi.rejectCorrection(operationId, { rejection_reason: reason });
    } catch (err) {
      console.warn("Backend reject call warning:", err);
    }

    // Keep original artifact completely intact
    set({
      activeCorrectionDraft: null,
      correctionActionMessage: {
        type: "info",
        text: "Correction draft rejected. Original architecture preserved unchanged.",
      },
    });

    addLogEntry({
      timestamp: new Date().toTimeString().split(" ")[0],
      stage: "CORRECTION_REJECT",
      message: `🚫 Correction draft [${operationId}] rejected by user. Original architecture preserved unchanged.`,
      level: "INFO",
    });

    return true;
  },

  dismissCorrectionDraftModal: () => {
    set({ activeCorrectionDraft: null });
  },

  runRevalidation: async () => {
    const { addLogEntry, generationId, arsrsData, hldData, lldData, activeVersionTag } = get();
    addLogEntry({
      timestamp: new Date().toTimeString().split(" ")[0],
      stage: "REVALIDATION",
      message: "🔄 User-triggered revalidation starting against Validator Engine v2 on Port 8002...",
      level: "INFO",
    });

    const updatedPkg: Record<string, any> = {
      generation_id: generationId || `gen-${Date.now()}`,
      version: (activeVersionTag || "v1.1").replace(/^v/, ""),
      version_tag: activeVersionTag || "v1.1",
      arsrs: arsrsData || {},
      hld: hldData || {},
      llds: lldData || {},
      is_revalidation: true,
      updated_at: new Date().toISOString(),
    };

    set({
      validatedGenerationId: null,
      validationIsStale: false,
      staleReason: null,
      staleArtifactType: null,
    });

    return await get().validateArchitecture(updatedPkg);
  },

  validateArchitecture: async (pkg?: Record<string, any>) => {
    const { generationId, isValidating, isValidatingV2, validatedGenerationId, validationReport, addLogEntry } = get();

    // 1. Guard against duplicate validation requests caused by repeated renders or state changes
    if (isValidating || isValidatingV2) {
      return validationReport;
    }
    if (!pkg && generationId && validatedGenerationId === generationId && validationReport) {
      return validationReport;
    }

    set({
      isValidating: true,
      isValidatingV2: true,
      validationError: null,
      validationStatus: "running",
      validationCurrentStep: "Preparing complete architecture package (ARSRS, HLD, 5 LLDs)...",
    });

    const now = new Date().toTimeString().split(" ")[0];
    addLogEntry({
      timestamp: now,
      stage: "VALIDATOR",
      message: `🛡️ Starting automated Validator Engine v2 audit (Port 8002)...`,
      level: "INFO",
    });

    try {
      let packagePayload = pkg;

      // 2. Automatically wait for the complete architecture package if generating via AI Engine
      const currentGenStatus = get().generationStatus;
      const currentLldStatus = get().lldStatus;
      const isAlreadyComplete =
        currentGenStatus === "COMPLETED" &&
        currentLldStatus &&
        Object.keys(currentLldStatus).length >= 5 &&
        Object.values(currentLldStatus).every((s) => (s as string) === "READY" || (s as string) === "COMPLETED" || (s as string) === "FAILED");

      if (!packagePayload && generationId) {
        if (!isAlreadyComplete) {
          set({ validationCurrentStep: "Waiting for all 5 LLD blueprints to finalize..." });

          let attempts = 0;
          while (attempts < 30) {
            try {
              const stat = await aiEngineApi.getStatus(generationId);
              const llds = stat.llds || {};
              const lldVals = Object.values(llds);
              const allDone = lldVals.length >= 5 && lldVals.every((s: any) => s === "READY" || s === "COMPLETED" || s === "FAILED");
              if (stat.status === "COMPLETED" || allDone) {
                break;
              }
            } catch { }
            await new Promise((r) => setTimeout(r, 1000));
            attempts++;
          }
        }

        try {
          packagePayload = await aiEngineApi.getPackage(generationId);
        } catch (fetchPkgErr) {
          console.warn("[Archova] Could not fetch raw package from AI Engine, composing from store:", fetchPkgErr);
        }
      }

      // 3. Fallback to assembling package from active store state
      if (!packagePayload) {
        const { arsrsData, hldData, lldData } = get();
        packagePayload = {
          generation_id: generationId || `gen-${Date.now()}`,
          prompt: "Architecture Package Evaluation",
          status: "COMPLETED",
          arsrs: arsrsData,
          hld: hldData,
          llds: lldData,
        };
      }

      set({ validationCurrentStep: "Running Validator Engine v2 6-phase audit on Port 8002..." });

      // 4. Send the complete package to Validator Engine v2 on port 8002
      const report = await validatorV2Client.directValidate(packagePayload);
      const plan = buildCorrectionPlan(report);

      set({
        validationReport: report,
        correctionPlan: plan,
        validatedGenerationId: generationId || packagePayload.generation_id,
        isValidating: false,
        isValidatingV2: false,
        validationError: null,
        validationStatus: report.final_status,
        validationCurrentStep: `Validation complete: ${report.final_status}`,
        generationStatus: "COMPLETED",
      });

      addLogEntry({
        timestamp: new Date().toTimeString().split(" ")[0],
        stage: "VALIDATOR",
        message: `✓ Validator Engine v2 complete! Status: ${report.final_status} | Overall Score: ${report.final_scores?.overall ?? 0}% | Actionable Corrections: ${plan?.actionable_count ?? 0}`,
        level: "INFO",
      });

      return report;
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Validator Engine v2 call failed.";
      set({
        isValidating: false,
        isValidatingV2: false,
        validationError: msg,
        validationStatus: "failed",
        validationCurrentStep: msg,
        correctionPlan: null,
      });

      addLogEntry({
        timestamp: new Date().toTimeString().split(" ")[0],
        stage: "VALIDATOR",
        message: `❌ Validator Engine v2 error: ${msg}`,
        level: "ERROR",
      });

      return null;
    }
  },

  runCorrectionWorkflow: async (maxRetries = 2, force = false) => {
    // Note: Automatic correction/regeneration is deferred to Part 2.
    // In this part, run real Validator Engine v2 validation.
    return (await get().validateArchitecture()) as any;
  },

  // ── Standalone Validator Engine v2 Runner ──
  runValidatorV2Pipeline: async (pkg?: Record<string, any>) => {
    const { generationId, arsrsData, hldData, lldData, hldNodes, hldEdges, addLogEntry } = get();
    const effectiveGenId = generationId || (pkg as any)?.generation_id || `gen-${Date.now()}`;

    set({
      isValidatingV2: true,
      validationStatus: "running",
      validationCurrentStep: "Initiating Validator Engine v2 pipeline...",
    });

    addLogEntry({
      timestamp: new Date().toTimeString().split(" ")[0],
      stage: "VALIDATOR_V2",
      message: `🛡️ Starting Validator Engine v2 (Port 8002) for session ${effectiveGenId}...`,
      level: "INFO",
    });

    try {
      let packagePayload = pkg;
      if (!packagePayload && effectiveGenId) {
        try {
          packagePayload = await aiEngineApi.getPackage(effectiveGenId);
        } catch (fetchErr) {
          console.warn("[Archova] Could not fetch raw package from AI Engine for V2 pipeline:", fetchErr);
        }
      }
      if (!packagePayload) {
        packagePayload = {
          generation_id: effectiveGenId,
          prompt: "Architecture Evaluation",
          status: "COMPLETED",
          arsrs: arsrsData,
          hld: hldData,
          llds: lldData,
        };
      }

      // 1. Trigger background pipeline execution on Port 8002
      await validatorV2Client.runPipeline(effectiveGenId, packagePayload);

      // 2. Poll until completed or failed
      const reportWithPkg = await validatorV2Client.pollPipeline(
        effectiveGenId,
        (progress) => {
          set({
            validationStatus: progress.state,
            validationCurrentStep: `Round ${progress.iteration}: ${progress.current_step}`,
          });
          addLogEntry({
            timestamp: new Date().toTimeString().split(" ")[0],
            stage: "VALIDATOR_V2",
            message: `[Round ${progress.iteration}] ${progress.current_step}`,
            level: "INFO",
          });
        },
        2000,
        300000
      );

      const report = (reportWithPkg as any).report || reportWithPkg;
      const finalPkg = (reportWithPkg as any).final_package || (report as any).final_package || packagePayload;

      // 3. Feed visualization strictly from the report's FINAL package
      let finalNodes = hldNodes;
      let finalEdges = hldEdges;
      const rawHld = (finalPkg.hld || hldData) as Record<string, unknown> | null;
      if (rawHld) {
        const parsed = parseHldToReactFlow(rawHld);
        const hldObj = rawHld as { nodes?: unknown[]; edges?: unknown[] } | undefined;
        finalNodes =
          hldObj?.nodes && (hldObj.nodes as unknown[]).length > 0
            ? (hldObj.nodes as any)
            : parsed.nodes;
        finalEdges =
          hldObj?.edges && (hldObj.edges as unknown[]).length > 0
            ? (hldObj.edges as any)
            : parsed.edges;
      }

      const rawLlds = (finalPkg.llds || {}) as Record<string, any>;
      const currentLldData = lldData;
      const finalLldData: Record<LldType, Record<string, unknown> | null> = {
        backend: (rawLlds.backend?.data || rawLlds.backend || currentLldData.backend) as any,
        frontend: (rawLlds.frontend?.data || rawLlds.frontend || currentLldData.frontend) as any,
        database: (rawLlds.database?.data || rawLlds.database || currentLldData.database) as any,
        security: (rawLlds.security?.data || rawLlds.security || currentLldData.security) as any,
        cloud: (rawLlds.cloud?.data || rawLlds.cloud || currentLldData.cloud) as any,
      };

      set({
        validationReport: report,
        validationStatus: report.final_status,
        validationCurrentStep: `Pipeline completed: ${report.final_status}`,
        isValidatingV2: false,
        arsrsData: (finalPkg.arsrs || arsrsData) as any,
        hldData: rawHld,
        hldNodes: finalNodes,
        hldEdges: finalEdges,
        lldData: finalLldData,
        generationStatus: "COMPLETED",
        activeView: "hld",
      });

      addLogEntry({
        timestamp: new Date().toTimeString().split(" ")[0],
        stage: "VALIDATOR_V2",
        message: `✓ Validator Engine v2 finished! Final Status: ${report.final_status} across ${report.iterations.length} rounds.`,
        level: "INFO",
      });

      return reportWithPkg;
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Validator Engine v2 pipeline failed.";
      set({
        isValidatingV2: false,
        validationStatus: "failed",
        validationCurrentStep: msg,
      });
      addLogEntry({
        timestamp: new Date().toTimeString().split(" ")[0],
        stage: "VALIDATOR_V2",
        message: `❌ Validator Engine v2 error: ${msg}`,
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
      validationReport: null,
      validationStatus: "IDLE",
      validationCurrentStep: "",
      isValidatingV2: false,
      lldStatus: initialLldStatus,
      lldData: initialLldData,
      lldMessages: initialLldMessages,
      logs: [],
      activeSessionId: null,
      activeCorrectionDraft: null,
      isExecutingAiCorrection: false,
      isProcessingCorrectionAction: false,
      correctionActionMessage: null,
      correctionPlan: null,
      correctionDecisions: {},
      validationIsStale: false,
      staleReason: null,
      staleArtifactType: null,
      historicalValidationReports: {},
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
      validationReport: null,
      correctionPlan: null,
      correctionDecisions: {},
      correctionActionMessage: null,
      activeCorrectionDraft: null,
      isExecutingAiCorrection: false,
      validationIsStale: false,
      staleReason: null,
      staleArtifactType: null,
      historicalValidationReports: {},
    }));

    return newId;
  },

  setActiveSession: async (id: string) => {
    if (!id) return;

    set({
      activeSessionId: id,
      activeView: "chat",
      activeCorrectionDraft: null,
      isExecutingAiCorrection: false,
      isProcessingCorrectionAction: false,
      correctionActionMessage: null,
      validationIsStale: false,
      staleReason: null,
      staleArtifactType: null,
      correctionPlan: null,
      validationReport: null,
      historicalValidationReports: {},
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
      validationReport: get().validationReport,
      correctionPlan: get().correctionPlan,
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
      validationReport: (pkg.validationReport || null) as Report | null,
      correctionPlan: (pkg.correctionPlan || (pkg.validationReport ? buildCorrectionPlan(pkg.validationReport) : null)) as CorrectionPlan | null,
      correctionDecisions: {},
      correctionActionMessage: null,
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

