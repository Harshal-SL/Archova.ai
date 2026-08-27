"use client";

import { useRef, useEffect, useState } from "react";
import { Cpu, Loader2 } from "lucide-react";
import { useAppStore, generateMsgId } from "@/lib/store";
import { apiGenerate, apiCreateSession, apiUpdateSessionTitle } from "@/lib/api";
import ChatMessage from "./ChatMessage";
import PromptInput from "./PromptInput";

// Typing indicator – three blinking dots
function TypingIndicator() {
  return (
    <div className="flex w-full gap-4 px-4 py-6 justify-start">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-[#333333] bg-black">
        <Cpu className="h-4 w-4 text-white" />
      </div>
      <div className="max-w-[80%] rounded-2xl px-5 py-4 border border-[#333333] bg-[#1A1A1A] flex items-center gap-1.5">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-2 w-2 rounded-full bg-white animate-bounce"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  );
}

const STARTER_PROMPTS = [
  "Design a URL shortener like Bitly",
  "Build a real-time chat system",
  "Create a scalable e-commerce platform",
  "Design a video streaming service",
];

export default function ChatWindow() {
  const {
    sessions,
    activeSessionId,
    addMessage,
    setArchitectureReady,
    createSession,
    updateSessionTitle,
    isGenerating,
    setIsGenerating,
    user,
  } = useAppStore();

  const bottomRef = useRef<HTMLDivElement>(null);
  const session = sessions.find((s) => s.id === activeSessionId);
  const messages = session?.messages ?? [];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, isGenerating]);

  const handleSend = async (text: string) => {
    // Create session if none active
    let sid = activeSessionId;
    if (!sid) {
      // Try to create in Supabase if logged in
      if (user) {
        const dbSess = await apiCreateSession(user.id, text.slice(0, 60));
        if (dbSess) {
          createSession(dbSess.id, dbSess.title);
          sid = dbSess.id;
        } else {
          sid = createSession();
        }
      } else {
        sid = createSession();
      }
    }

    // Add user message optimistically
    addMessage(sid, { id: generateMsgId(), role: "user", content: text });

    // Update session title from first message
    if (!session || session.messages.length === 0) {
      const title = text.length > 50 ? text.slice(0, 50) + "…" : text;
      updateSessionTitle(sid, title);
      if (user) apiUpdateSessionTitle(sid, title).catch(() => {});
    }

    setIsGenerating(true);

    try {
      const data = await apiGenerate(sid, text, user?.id);

      if (data.error) {
        addMessage(sid, {
          id: generateMsgId(),
          role: "ai",
          content: `⚠️ ${data.error}`,
        });
        return;
      }

      const responseText = data.response ?? "Here is your system design.";
      addMessage(sid, {
        id: generateMsgId(),
        role: "ai",
        content: responseText,
      });

      // Attach architecture data to session
      if (data.architectureData) {
        setArchitectureReady(sid, data.architectureData);
      } else {
        setArchitectureReady(sid);
      }
    } catch {
      addMessage(sid, {
        id: generateMsgId(),
        role: "ai",
        content: "⚠️ Unable to reach the AI service. Make sure Ollama is running on localhost:11434 (`ollama serve`).",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  // Empty state
  if (!session || messages.length === 0) {
    return (
      <div className="flex flex-1 flex-col bg-[#0A0A0A]">
        <div className="flex flex-1 flex-col items-center justify-center gap-6 px-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-[#333333] bg-black">
            <Cpu className="h-8 w-8 text-white" />
          </div>
          <div className="text-center">
            <h2 className="text-2xl font-bold text-white mb-2">What are we designing today?</h2>
            <p className="text-sm text-[#555555] font-mono">Powered by Ollama · Saved to Supabase</p>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 max-w-2xl w-full mt-2">
            {STARTER_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                onClick={() => handleSend(prompt)}
                disabled={isGenerating}
                className="rounded-xl border border-[#2A2A2A] bg-[#111111] px-4 py-3 text-left text-sm text-[#AAAAAA] transition-colors hover:bg-[#1A1A1A] hover:border-[#555] hover:text-white disabled:opacity-50"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
        <PromptInput onSend={handleSend} disabled={isGenerating} />
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col bg-[#0A0A0A] min-w-0">
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-4xl py-6">
          {messages.map((m) => (
            <ChatMessage key={m.id} msg={m} />
          ))}
          {isGenerating && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>
      </div>
      <PromptInput onSend={handleSend} disabled={isGenerating} />
    </div>
  );
}
