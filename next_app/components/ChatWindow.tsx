"use client";

import { useRef, useEffect } from "react";
import { Cpu } from "lucide-react";
import { useAppStore, generateMsgId } from "@/lib/store";
import ChatMessage from "./ChatMessage";
import PromptInput from "./PromptInput";

export default function ChatWindow() {
  const {
    sessions,
    activeSessionId,
    addMessage,
    setArchitectureReady,
    createSession,
  } = useAppStore();

  const bottomRef = useRef<HTMLDivElement>(null);

  const session = sessions.find((s) => s.id === activeSessionId);
  const messages = session?.messages ?? [];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  const handleSend = async (text: string) => {
    let sid = activeSessionId;
    if (!sid) {
      sid = createSession();
    }

    // Add user message
    addMessage(sid, { id: generateMsgId(), role: "user", content: text });

    try {
      const response = await fetch("/api/ai/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sid,
          message: text,
        }),
      });

      const data = (await response.json()) as { response?: string; error?: string };

      if (!response.ok || !data.response) {
        const errorMessage =
          data.error ?? "Something went wrong while generating the AI response.";
        addMessage(sid, {
          id: generateMsgId(),
          role: "ai",
          content: `Error: ${errorMessage}`,
        });
        return;
      }

      addMessage(sid, {
        id: generateMsgId(),
        role: "ai",
        content: data.response,
      });

      // Show architecture after first AI response
      const currentSession = useAppStore.getState().sessions.find((s) => s.id === sid);
      if (!currentSession?.hasArchitecture) {
        setArchitectureReady(sid);
      }
    } catch {
      addMessage(sid, {
        id: generateMsgId(),
        role: "ai",
        content: "Error: Unable to reach the AI service. Please try again.",
      });
    }
  };

  // Empty state
  if (!session || messages.length === 0) {
    return (
      <div className="flex flex-1 flex-col">
        <div className="flex flex-1 flex-col items-center justify-center gap-4 px-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600">
            <Cpu className="h-8 w-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold">ArchAI</h2>
          <p className="max-w-md text-center text-sm text-gray-500">
            Describe your system and I&apos;ll generate a complete architecture
            with HLD and LLD visualizations.
          </p>
          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
            {[
              "Design an e-commerce platform",
              "Build a real-time chat system",
              "Create a streaming platform",
              "Design a social media app",
            ].map((prompt) => (
              <button
                key={prompt}
                onClick={() => handleSend(prompt)}
                className="rounded-xl border border-gray-200 px-4 py-3 text-left text-sm transition-colors hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
        <PromptInput onSend={handleSend} />
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col">
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl py-4">
          {messages.map((m) => (
            <ChatMessage key={m.id} msg={m} />
          ))}
          <div ref={bottomRef} />
        </div>
      </div>
      <PromptInput onSend={handleSend} />
    </div>
  );
}
