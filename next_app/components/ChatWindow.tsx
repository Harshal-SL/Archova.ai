"use client";

import { useRef, useEffect, useState } from "react";
import {
  Cpu,
  Loader2,
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

  useEffect(() => {
    checkApiHealth();
  }, [checkApiHealth]);

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
    <div className="flex h-full w-full flex-col justify-between overflow-hidden bg-white dark:bg-black min-h-0">
      {/* Messages / Main Workflow Scroll Area */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 min-h-0">
        {/* Welcome / Compact starter state matching reference screenshot */}
        {messages.length === 0 && !generationId && (
          <div className="mx-auto max-w-2xl py-12 flex flex-col items-center text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/25">
              <Cpu className="h-7 w-7 text-white" />
            </div>
            <h2 className="mt-3 text-2xl font-bold text-gray-900 dark:text-white">
              ArchAI
            </h2>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 max-w-md">
              Describe your system to generate an end-to-end architecture with ARSRS,
              High-Level Design, and 5 Low-Level Designs.
            </p>

            {/* Compact Quick Samples Bar (Identical to reference screenshot) */}
            <div className="mt-6 flex items-center justify-center gap-2 flex-wrap text-xs">
              <span className="text-gray-500 dark:text-gray-400">Quick Samples:</span>
              {SAMPLE_PROMPTS.map((sample, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleStartGeneration(sample.text)}
                  className="rounded-full border border-gray-200 bg-gray-100/90 px-3.5 py-1 text-xs font-medium text-gray-700 transition-all hover:border-indigo-400 hover:bg-indigo-50/60 dark:border-gray-800 dark:bg-gray-800/80 dark:text-gray-300 dark:hover:border-indigo-600 dark:hover:bg-indigo-950/40"
                >
                  {sample.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Chat Messages */}
        <div className="mx-auto max-w-3xl space-y-3">
          {messages.map((m) => (
            <ChatMessage key={m.id} msg={m} />
          ))}

          {/* Loading prompt analyzer indicator */}
          {starting && (
            <div className="flex items-center gap-2.5 rounded-2xl bg-indigo-50/80 p-3.5 text-xs text-indigo-900 dark:bg-indigo-950/30 dark:text-indigo-200">
              <Loader2 className="h-4 w-4 animate-spin text-indigo-500" />
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
