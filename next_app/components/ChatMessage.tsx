"use client";

import clsx from "clsx";
import { Bot, User } from "lucide-react";
import type { ChatMessage as ChatMsg } from "@/lib/store";

interface ChatMessageProps {
  msg: ChatMsg;
  isStreaming?: boolean;
  streamedContent?: string;
  isThinking?: boolean;
}

export default function ChatMessage({
  msg,
  isStreaming = false,
  streamedContent = "",
  isThinking = false,
}: ChatMessageProps) {
  const isUser = msg.role === "user";
  const content = isStreaming ? streamedContent : msg.content;

  return (
    <div
      className={clsx(
        "chat-message-enter flex w-full gap-3 px-4 py-3",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {!isUser && (
        <div
          className={clsx(
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#10B981] shadow-md shadow-emerald-500/30",
            isStreaming && "animate-pulse"
          )}
        >
          <Bot className="h-4 w-4 text-white" />
        </div>
      )}

      <div
        className={clsx(
          "max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-7 whitespace-pre-wrap transition-all duration-300 sm:max-w-[78%]",
          isUser
            ? "bg-gradient-to-br from-[#2563EB] to-[#1E40AF] text-white shadow-lg shadow-blue-600/25"
            : "border border-slate-200 bg-white text-slate-900 shadow-lg shadow-black/10 backdrop-blur-sm dark:border-white/10 dark:bg-white/[0.045] dark:text-gray-100 dark:shadow-black/15"
        )}
      >
        {isStreaming && isThinking ? (
          <span className="typing-dots" aria-label="Assistant is typing">
            <span className="typing-dot" />
            <span className="typing-dot" />
            <span className="typing-dot" />
          </span>
        ) : (
          content
        )}
        {isStreaming && !isThinking && (
          <span className="typing-cursor ml-0.5 inline-block h-5 w-[2px] translate-y-1 rounded-full bg-current align-middle" />
        )}
      </div>

      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#E2E8F0] shadow-sm dark:bg-gray-700">
          <User className="h-4 w-4 text-[#64748B] dark:text-gray-300" />
        </div>
      )}
    </div>
  );
}
