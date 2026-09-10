"use client";

import { useRef, useEffect, useState } from "react";
import {
  Cpu,
  Loader2,
  Sparkles,
} from "lucide-react";
import { useAppStore, generateMsgId } from "@/lib/store";
import { aiEngineApi } from "@/lib/ai-engine-client";
import ChatMessage from "./ChatMessage";
import PromptInput from "./PromptInput";
import InterviewCard from "./InterviewCard";

const SAMPLE_PROMPTS = [
  {
    label: "Event Management",
    text: "Build a modern Online Event Management System for university hackathons. Users can browse events, register, submit artifacts, and receive live notifications. Organizers manage schedules, judge scoring, and track real-time attendance.",
  },
  {
    label: "College Library",
    text: "Build a modern College Library Management System. Students authenticate securely, search the catalog, and borrow or reserve books. Librarians manage inventory, circulation, overdue fines, and administrative reports.",
  },
  {
    label: "Smart Parking",
    text: "Build an IoT-Enabled Smart Parking Management System. Drivers view real-time parking slot availability, reserve slots, and pay digital fees. Attendants verify vehicle check-in with automated license plate recognition.",
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
    checkApiHealth,
    addLogEntry,
  } = useAppStore();

  const [starting, setStarting] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const session = sessions.find((s) => s.id === activeSessionId);
  const messages = session?.messages ?? [];

  // Standalone frontend mode active

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, starting, currentQuestion, interviewCompleted]);

  const handleStartGeneration = async (promptText: string) => {
    let sid = activeSessionId;
    if (!sid) {
      sid = await createSession(promptText.slice(0, 30));
    }

    // 1. Add user prompt to chat
    await addMessage(sid, {
      id: generateMsgId(),
      role: "user",
      content: promptText,
    });

    setStarting(true);
    const now = new Date().toTimeString().split(" ")[0];

    addLogEntry({
      timestamp: now,
      stage: "CLIENT",
      message: "🚀 Sending problem statement to AI Architecture Engine...",
      level: "INFO",
    });

    try {
      // 2. Call POST /api/v1/generations
      const response = await aiEngineApi.startGeneration(promptText);

      useAppStore.setState({
        generationId: response.generation_id,
        generationStatus: response.status || "INTERVIEW_IN_PROGRESS",
        currentQuestion: response.current_question || null,
        interviewCompleted: response.status === "INTERVIEW_COMPLETED",
      });

      addLogEntry({
        timestamp: new Date().toTimeString().split(" ")[0],
        stage: "REE",
        message: `Generation session started: ${response.generation_id}`,
        level: "INFO",
      });

      // 3. Add assistant acknowledgment
      await addMessage(sid, {
        id: generateMsgId(),
        role: "ai",
        content: `I've received your requirements and initialized the **REE Input Understanding** multi-agent pipeline.\n\nPlease answer the clarifying interview questions below to complete the architecture specification.`,
      });
    } catch (err) {
      const msg =
        err instanceof Error
          ? err.message
          : "Failed to process requirements in Architecture Engine.";

      addLogEntry({
        timestamp: new Date().toTimeString().split(" ")[0],
        stage: "CLIENT",
        message: `❌ Error: ${msg}`,
        level: "ERROR",
      });

      await addMessage(sid, {
        id: generateMsgId(),
        role: "ai",
        content: `⚠️ **Error initializing Architecture Engine**\n\n${msg}`,
      });
    } finally {
      setStarting(false);
    }
  };

  return (
    <div className="flex h-full w-full flex-col justify-between overflow-hidden bg-white text-black dark:bg-black dark:text-white min-h-0 transition-colors">
      {/* Messages / Main Workflow Scroll Area */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 min-h-0">
        {/* Welcome / Starter state */}
        {messages.length === 0 && !generationId && (
          <div className="mx-auto max-w-2xl py-12 flex flex-col items-center text-center">
            <div className="relative mb-2">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-black text-white dark:bg-white dark:text-black shadow-lg">
                <Cpu className="h-8 w-8" />
              </div>
            </div>

            <h2 className="font-heading mt-4 text-3xl font-extrabold tracking-tight">
              Arch<span className="text-neutral-500">AI</span> Studio
            </h2>
            <p className="mt-2 text-xs sm:text-sm text-neutral-600 dark:text-neutral-400 max-w-md leading-relaxed">
              Describe your software system to synthesize formal ARSRS specs,
              interactive High-Level Architecture, and 5 parallel Low-Level Designs.
            </p>

            {/* Quick Samples Bar with monochrome accents */}
            <div className="mt-8 flex flex-col items-center gap-3">
              <span className="text-xs font-bold uppercase tracking-wider text-neutral-500">
                Quick Sample Architectures:
              </span>
              <div className="flex flex-wrap justify-center gap-2">
                {SAMPLE_PROMPTS.map((sample, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleStartGeneration(sample.text)}
                    className="group flex items-center gap-2 rounded-full border border-neutral-300 bg-white px-4 py-2 text-xs font-semibold text-neutral-800 shadow-xs transition-all duration-200 hover:border-black hover:text-black dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-200 dark:hover:border-white dark:hover:text-white hover:-translate-y-0.5"
                  >
                    <Sparkles className="h-3 w-3 text-black dark:text-white transition-transform duration-200 group-hover:scale-125" />
                    <span>{sample.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Chat Messages */}
        <div className="mx-auto max-w-3xl space-y-3.5">
          {messages.map((m) => (
            <ChatMessage key={m.id} msg={m} />
          ))}

          {/* Loading prompt analyzer indicator */}
          {starting && (
            <div className="flex items-center gap-3 rounded-2xl border border-neutral-300 bg-neutral-100 p-4 text-xs font-semibold text-black shadow-sm dark:border-neutral-700 dark:bg-neutral-900 dark:text-white">
              <Loader2 className="h-5 w-5 animate-spin text-black dark:text-white shrink-0" />
              <span>Analyzing problem statement with REE Multi-Agent pipeline...</span>
            </div>
          )}

          {/* Interactive Interview Step */}
          {generationId && (
            <div className="pt-2">
              <InterviewCard />
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Fixed/Pinned Prompt Input at Bottom */}
      <PromptInput onSend={handleStartGeneration} />
    </div>
  );
}
