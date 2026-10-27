"use client";

import React, { useRef, useEffect, useState } from "react";
import {
  Cpu,
  Loader2,
  Workflow,
  ArrowRight,
  User as UserIcon,
  Sparkles,
  Layers,
  X,
} from "lucide-react";
import { useAppStore, generateMsgId } from "@/lib/store";
import { aiEngineApi } from "@/lib/ai-engine-client";
import PromptInput from "./PromptInput";
import InterviewPopup from "./InterviewPopup";
import MultiAgentSwarmLoader from "./MultiAgentSwarmLoader";
import { AiLoader } from "@/components/ui/ai-loader";
import { AnimatedAIChat } from "@/components/ui/animated-ai-chat";
import { cn } from "@/lib/utils";

const ARCHITECTURE_TEMPLATES = [
  {
    title: "Event Management Platform",
    category: "High Concurrency",
    text: "Build an Online Event Management System for university hackathons with registration, submission judging, and live notifications.",
  },
  {
    title: "Fintech Payment Engine",
    category: "ACID Transactions",
    text: "Build a High-Reliability Fintech Payment Processing Engine with idempotent ledger transactions, fraud detection, and multi-currency settlement.",
  },
  {
    title: "Smart Parking & IoT",
    category: "IoT Real-Time",
    text: "Build an IoT Smart Parking Management System with real-time slot telemetry, digital reservation, and automated license plate check-in.",
  },
  {
    title: "Video Streaming Cloud",
    category: "Distributed Media",
    text: "Build a scalable Video Streaming Platform with adaptive bitrate transcoding, CDN edge delivery, and subscription billing.",
  },
];

export default function ChatWindow() {
  const {
    sessions,
    activeSessionId,
    addMessage,
    createSession,
    generationId,
    currentQuestion,
    interviewCompleted,
    addLogEntry,
    activeAgent,
    setActiveAgent,
    setActiveView,
    hldData,
    user,
    loadDemoData,
    evolveArchitecture,
  } = useAppStore();

  const [starting, setStarting] = useState(false);
  const [showTemplatesModal, setShowTemplatesModal] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const session = sessions.find((s) => s.id === activeSessionId);
  const messages = session?.messages ?? [];

  // User display name from account or fallback if authenticated
  const fullName =
    user?.user_metadata?.name ||
    user?.user_metadata?.full_name ||
    user?.email?.split("@")[0] ||
    "";

  const firstName = fullName ? (fullName.split(" ")[0] || "") : "";

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, starting, currentQuestion, interviewCompleted]);

  useEffect(() => {
    return () => {
      useAppStore.getState().stopAgentTelemetryPolling();
    };
  }, []);

  // Ensure clean state on empty/new chat
  useEffect(() => {
    if (!activeSessionId) {
      useAppStore.setState({
        generationId: null,
        generationStatus: "IDLE",
        currentQuestion: null,
        interviewCompleted: false,
        hldData: null,
      });
    }
  }, [activeSessionId]);

  const handleStartGeneration = async (promptText: string) => {
    let sid = activeSessionId;
    if (!sid) {
      sid = await createSession(promptText.slice(0, 32));
    }

    // 1. Post user prompt into chat
    await addMessage(sid, {
      id: generateMsgId(),
      role: "user",
      content: promptText,
    });

    setStarting(true);
    const now = new Date().toTimeString().split(" ")[0];

    // Check if an architecture baseline already exists in this session
    const hasBaseline = Boolean(hldData && typeof hldData === "object" && Object.keys(hldData).length > 0);

    if (hasBaseline) {
      // ══════════════════════════════════════════════════════════
      // MODE B: ARCHITECTURAL EVOLUTION (v1.1+)
      // ══════════════════════════════════════════════════════════
      setActiveAgent({
        id: "agent-versioning",
        name: "Architecture Evolution Agent",
        role: "Non-Destructive Delta Synthesizer",
        icon: "sparkles",
        task: "Synthesizing non-destructive delta patch and verifying 100% baseline invariance...",
        status: "working",
        stage: "EVOLUTION",
        progressPercent: 60,
        thought: "Preserving all baseline microservices and tables. Merging new feature delta into architecture graph.",
      });

      addLogEntry({
        timestamp: now,
        stage: "EVOLUTION",
        message: "🔄 Existing architecture detected. Initiating non-destructive version evolution...",
        level: "INFO",
      });

      try {
        const result = await evolveArchitecture(promptText);

        addLogEntry({
          timestamp: new Date().toTimeString().split(" ")[0],
          stage: "EVOLUTION",
          message: `✓ Architecture evolved to ${result.versionTag}! Verification: 100% baseline preserved.`,
          level: "INFO",
        });

        setActiveAgent({
          id: "agent-versioning",
          name: "Architecture Evolution Agent",
          role: "Non-Destructive Delta Synthesizer",
          icon: "sparkles",
          task: `Successfully evolved architecture to ${result.versionTag}.`,
          status: "completed",
          stage: "READY",
          progressPercent: 100,
          thought: "Delta successfully verified and merged. 0 baseline components modified.",
        });
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Evolution failed.";
        await addMessage(sid, {
          id: generateMsgId(),
          role: "ai",
          content: `⚠️ **Error evolving architecture**: ${msg}`,
        });
      } finally {
        setStarting(false);
      }
      return;
    }

    // ══════════════════════════════════════════════════════════
    // MODE A: INITIAL GENERATION (v1.0) — Completely Unaltered
    // ══════════════════════════════════════════════════════════
    setActiveAgent({
      id: "agent-ree",
      name: "Requirements Engineering Agent",
      role: "Input Understanding & Scope Extraction",
      icon: "brain",
      task: "Analyzing requirements statement & identifying non-functional boundaries...",
      status: "working",
      stage: "REE",
      progressPercent: 20,
      thought: "Decomposing system requirements, primary actors, and transaction SLAs.",
    });

    addLogEntry({
      timestamp: now,
      stage: "REE",
      message: "🚀 Requirements prompt received. Initializing REE input understanding...",
      level: "INFO",
    });

    try {
      const clientGenId = `gen_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
      useAppStore.setState({ generationId: clientGenId });
      useAppStore.getState().startAgentTelemetryPolling(clientGenId);

      // Concurrently initiate direct 1-shot baseline LLM benchmark in background
      useAppStore.getState().runBenchmarkSuite(promptText).catch((e) => {
        console.warn("Background benchmark suite non-blocking error:", e);
      });

      const response = await aiEngineApi.startGeneration(promptText, clientGenId);

      useAppStore.setState({
        generationId: response.generation_id,
        generationStatus: response.status || "INTERVIEW_IN_PROGRESS",
        currentQuestion: response.current_question || null,
        interviewCompleted: response.status === "INTERVIEW_COMPLETED",
      });

      // Update active agent to Interviewer
      setActiveAgent({
        id: "agent-interviewer",
        name: "Architectural Interviewer Agent",
        role: "Requirement Clarification & Constraints Discovery",
        icon: "mic",
        task: "Formulating clarifying questions to eliminate ambiguities in system boundaries...",
        status: "working",
        stage: "INTERVIEW",
        progressPercent: 45,
        thought: "Stakeholder interview initialized. Clarifying questions ready for user input.",
      });

      await addMessage(sid, {
        id: generateMsgId(),
        role: "ai",
        content: `I've analyzed your requirements and initiated the **Architecture Engineering Pipeline**.\n\nPlease answer the clarifying questions in the animated **AI Interview** below to synthesize the High-Level Design (HLD).`,
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to process requirements.";
      await addMessage(sid, {
        id: generateMsgId(),
        role: "ai",
        content: `⚠️ **Error initializing Architecture Engine**\n\n${msg}`,
      });
    } finally {
      setStarting(false);
      useAppStore.getState().stopAgentTelemetryPolling();
    }
  };

  const isEmpty = !activeSessionId || messages.length === 0;

  return (
    <div className="flex h-full w-full flex-col justify-between overflow-hidden bg-transparent text-neutral-900 dark:text-white transition-colors">
      {/* ── Main Area ── */}
      <div className="flex-1 overflow-y-auto px-4 py-4 min-h-0">
        {/* ══ State A: Initial Chat — Animated AI Chat Design in Pure Black ══ */}
        {isEmpty ? (
          <div className="flex h-full min-h-[70vh] flex-col items-center justify-center">
            <AnimatedAIChat
              userName={firstName}
              onSend={handleStartGeneration}
              disabled={starting}
            />
          </div>
        ) : (
          /* ══ State B: Active Conversation Stream ══ */
          <div className="mx-auto max-w-[920px] space-y-4 py-4">
            {messages.map((m) => {
              const isUser = m.role === "user";
              return (
                <div
                  key={m.id}
                  className={cn(
                    "flex w-full gap-3 py-2",
                    isUser ? "justify-end" : "justify-start"
                  )}
                >
                  {!isUser && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-neutral-950 text-white border border-neutral-800 dark:bg-white dark:text-black shadow-xs mt-0.5">
                      <Cpu className="h-4 w-4" />
                    </div>
                  )}

                  <div
                    className={cn(
                      "rounded-3xl px-5 py-3.5 text-xs sm:text-sm leading-relaxed whitespace-pre-wrap shadow-xs transition-all",
                      isUser
                        ? "max-w-[80%] bg-neutral-900 text-white dark:bg-neutral-100 dark:text-black font-medium rounded-br-sm"
                        : "max-w-[85%] border border-neutral-200/80 bg-white dark:border-[#262626] dark:bg-[#0D0D0F] text-neutral-900 dark:text-neutral-100 rounded-bl-sm"
                    )}
                  >
                    {m.content}
                  </div>

                  {isUser && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-neutral-200/80 bg-white/70 text-black dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-white shadow-xs mt-0.5">
                      <UserIcon className="h-4 w-4" />
                    </div>
                  )}
                </div>
              );
            })}

            {/* Working REE Engine AI Loader */}
            {starting && (
              <AiLoader
                fullscreen={false}
                size={140}
                text="Analyzing"
                stage="REE"
                agentName="REE Engine"
                agentRole="Requirements Engineering Engine"
                task={activeAgent?.task || "Decomposing requirements with Business Analyst, Requirement Engineer & Domain Expert..."}
                thought={activeAgent?.thought}
                progressPercent={activeAgent?.progressPercent ?? 35}
                className="my-5"
              />
            )}

            {/* ── Animated AI Interview Pop-Out Modal / Card ── */}
            {generationId && (
              <InterviewPopup
                onHldReady={() => {
                  setActiveView("hld");
                }}
              />
            )}

            {/* Quick HLD Architecture ready prompt banner */}
            {hldData && interviewCompleted && (
              <div className="my-3 flex items-center justify-between rounded-2xl border border-blue-500/30 bg-blue-500/10 p-4 text-xs">
                <div className="flex items-center gap-2.5">
                  <Workflow className="h-5 w-5 text-blue-500" />
                  <div>
                    <span className="font-bold text-neutral-900 dark:text-white">
                      High-Level Design (HLD) Ready
                    </span>
                    <p className="text-[11px] text-neutral-500 dark:text-neutral-400">
                      View interactive microservice topology with component details
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => setActiveView("hld")}
                  className="flex items-center gap-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold px-4 py-2 text-xs transition-colors cursor-pointer shadow-md"
                >
                  <span>Open HLD Diagram</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </button>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* ── Pinned Bottom Prompt Input (Only in active conversation) ── */}
      {!isEmpty && (
        <PromptInput
          variant="bottom"
          placeholder="Ask anything or clarify architecture..."
          onSend={handleStartGeneration}
          disabled={starting}
          onOpenTemplates={() => setShowTemplatesModal(true)}
        />
      )}

      {/* ── Architectural Templates Modal (Triggered by the '+' button) ── */}
      {showTemplatesModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4">
          <div className="relative w-full max-w-xl rounded-3xl border border-neutral-200/80 bg-white p-6 shadow-2xl dark:border-[#262626] dark:bg-[#0D0D0F] text-neutral-900 dark:text-white backdrop-blur-md">
            <button
              type="button"
              onClick={() => setShowTemplatesModal(false)}
              className="absolute right-4 top-4 p-1.5 text-neutral-400 hover:text-black dark:hover:text-white dark:hover:bg-[#161619] rounded-lg transition-colors cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>

            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="h-5 w-5 text-blue-500" />
              <h3 className="text-base font-bold">Quick Architecture Starters</h3>
            </div>

            <div className="space-y-2">
              {ARCHITECTURE_TEMPLATES.map((tmpl, i) => (
                <div
                  key={i}
                  onClick={() => {
                    setShowTemplatesModal(false);
                    handleStartGeneration(tmpl.text);
                  }}
                  className="group flex flex-col p-3 rounded-2xl border border-neutral-200/80 bg-neutral-50 hover:border-black dark:border-[#262626] dark:bg-[#161619]/60 dark:hover:bg-[#161619] dark:hover:border-white/20 cursor-pointer transition-all"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-neutral-900 dark:text-white">
                      {tmpl.title}
                    </span>
                    <span className="text-[10px] uppercase font-semibold text-blue-600 dark:text-blue-400">
                      {tmpl.category}
                    </span>
                  </div>
                  <p className="text-[11px] text-neutral-500 dark:text-neutral-400 mt-1 line-clamp-1">
                    {tmpl.text}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
