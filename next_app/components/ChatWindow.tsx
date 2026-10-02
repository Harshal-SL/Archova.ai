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
    title: "Campus Library System",
    category: "ACID Transactions",
    text: "Build a College Library Management System with catalog search, inventory circulation, and automated overdue calculation.",
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
  } = useAppStore();

  const [starting, setStarting] = useState(false);
  const [showTemplatesModal, setShowTemplatesModal] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const session = sessions.find((s) => s.id === activeSessionId);
  const messages = session?.messages ?? [];

  // User display name from account or fallback to "Harshal" as in user's reference image
  const fullName =
    user?.user_metadata?.name ||
    user?.user_metadata?.full_name ||
    user?.email?.split("@")[0] ||
    "Harshal";

  const firstName = fullName.split(" ")[0] || "Harshal";

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, starting, currentQuestion, interviewCompleted]);

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

    // Set active agent to Requirements Engineering (REE)
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
      const response = await aiEngineApi.startGeneration(promptText);

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
            {/* Quick Load Basic HLD & LLD Template Button */}
            <div className="mt-3 flex items-center justify-center">
              <button
                type="button"
                onClick={() => loadDemoData()}
                className="group flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-4 py-2 text-xs font-semibold text-blue-600 hover:bg-blue-500/20 dark:border-blue-400/30 dark:bg-blue-950/40 dark:text-blue-300 dark:hover:bg-blue-900/50 transition-all cursor-pointer shadow-xs"
              >
                <Layers className="h-3.5 w-3.5 text-blue-500 transition-transform group-hover:scale-110" />
                <span>Or load the basic HLD & LLD architecture template</span>
                <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
              </button>
            </div>
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
                        : "max-w-[85%] border border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-900/90 text-neutral-900 dark:text-neutral-100 rounded-bl-sm"
                    )}
                  >
                    {m.content}
                  </div>

                  {isUser && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-neutral-300 bg-neutral-100 text-black dark:border-neutral-700 dark:bg-neutral-900 dark:text-white shadow-xs mt-0.5">
                      <UserIcon className="h-4 w-4" />
                    </div>
                  )}
                </div>
              );
            })}

            {/* Working Agent AI Loader */}
            {starting && activeAgent && (
              <AiLoader
                fullscreen={false}
                size={140}
                text="Analyzing"
                agentName={activeAgent.name}
                agentRole={activeAgent.role}
                stage={activeAgent.stage}
                task={activeAgent.task}
                thought={activeAgent.thought}
                progressPercent={activeAgent.progressPercent}
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
          <div className="relative w-full max-w-xl rounded-3xl border border-neutral-300 bg-white p-6 shadow-2xl dark:border-neutral-800 dark:bg-neutral-900 text-neutral-900 dark:text-white">
            <button
              type="button"
              onClick={() => setShowTemplatesModal(false)}
              className="absolute right-4 top-4 p-1.5 text-neutral-400 hover:text-black dark:hover:text-white transition-colors"
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
                  className="group flex flex-col p-3 rounded-2xl border border-neutral-200 bg-neutral-50 hover:border-blue-500 hover:bg-blue-50/20 dark:border-neutral-800 dark:bg-black/50 dark:hover:border-blue-500/50 cursor-pointer transition-all"
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
