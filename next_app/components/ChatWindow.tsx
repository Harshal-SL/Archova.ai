"use client";

import { useRef, useEffect, useState } from "react";
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
  const typingTimeoutRef = useRef<number | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [streamingState, setStreamingState] = useState<{
    id: string;
    sessionId: string;
    content: string;
    isThinking: boolean;
  } | null>(null);

  const session = sessions.find((s) => s.id === activeSessionId);
  const messages = session?.messages ?? [];
  const activeStreamContent =
    streamingState && session && streamingState.sessionId === session.id
      ? streamingState.content
      : "";

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, activeStreamContent]);

  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current !== null) {
        window.clearTimeout(typingTimeoutRef.current);
      }
    };
  }, []);

  const clearTypingTimer = () => {
    if (typingTimeoutRef.current !== null) {
      window.clearTimeout(typingTimeoutRef.current);
      typingTimeoutRef.current = null;
    }
  };

  const handleSend = async (text: string) => {
    if (isGenerating) return;

    let sid = activeSessionId;
    if (!sid) {
      sid = createSession();
    }

    addMessage(sid, { id: generateMsgId(), role: "user", content: text });

    setIsGenerating(true);
    clearTypingTimer();

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
        setIsGenerating(false);
        return;
      }

      const fullResponse = data.response;
      const streamId = generateMsgId();
      setStreamingState({ id: streamId, sessionId: sid, content: "", isThinking: true });

      let cursor = 0;
      const tokens = fullResponse.match(/\S+\s*/g) ?? [fullResponse];
      let tokenIndex = 0;

      const startStreaming = () => {
        setStreamingState((prev) => {
          if (!prev) return prev;
          return { ...prev, isThinking: false };
        });

        const tick = () => {
          const nextChunk = tokens[tokenIndex] ?? "";
          tokenIndex += 1;
          cursor = Math.min(fullResponse.length, cursor + nextChunk.length);

          setStreamingState((prev) => {
            if (!prev) return prev;
            return { ...prev, content: fullResponse.slice(0, cursor) };
          });

          if (cursor >= fullResponse.length || tokenIndex >= tokens.length) {
            addMessage(sid, {
              id: streamId,
              role: "ai",
              content: fullResponse,
            });
            setStreamingState(null);
            setIsGenerating(false);

            const latestSession = useAppStore.getState().sessions.find((s) => s.id === sid);
            if (!latestSession?.hasArchitecture) {
              setArchitectureReady(sid);
            }
            return;
          }

          const chunk = nextChunk.trim();
          const delay = /[,.!?]$/.test(chunk)
            ? 130 + Math.floor(Math.random() * 120)
            : 28 + Math.floor(Math.random() * 58);

          typingTimeoutRef.current = window.setTimeout(tick, delay);
        };

        typingTimeoutRef.current = window.setTimeout(tick, 20);
      };

      typingTimeoutRef.current = window.setTimeout(
        startStreaming,
        420 + Math.floor(Math.random() * 380)
      );
    } catch {
      setStreamingState(null);
      setIsGenerating(false);
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
        <div className="flex flex-1 items-center justify-center px-4 pb-8">
          <div className="w-full max-w-3xl">
            <div className="mb-4 text-center text-sm text-slate-500 dark:text-gray-400">
              Try one of these prompts to start
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {[
                "Design an e-commerce platform",
                "Build a real-time chat system",
                "Create a streaming platform",
                "Design a social media app",
              ].map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => handleSend(prompt)}
                  disabled={isGenerating}
                  className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-left text-sm text-slate-900 transition-all duration-200 hover:-translate-y-0.5 hover:bg-slate-50 hover:shadow-lg hover:shadow-black/10 disabled:cursor-not-allowed disabled:opacity-50 dark:border-white/10 dark:bg-white/5 dark:text-gray-200 dark:hover:bg-white/10 dark:hover:shadow-black/20"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        </div>
        <PromptInput onSend={handleSend} disabled={isGenerating} />
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
          {streamingState && session && streamingState.sessionId === session.id && (
            <ChatMessage
              msg={{ id: streamingState.id, role: "ai", content: "" }}
              isStreaming
              streamedContent={streamingState.content}
              isThinking={streamingState.isThinking}
            />
          )}
          <div ref={bottomRef} />
        </div>
      </div>
      <PromptInput onSend={handleSend} disabled={isGenerating} />
    </div>
  );
}
