"use client";

import clsx from "clsx";
import { Bot, User } from "lucide-react";
import type { ChatMessage as ChatMsg } from "@/lib/store";

export default function ChatMessage({ msg }: { msg: ChatMsg }) {
  const isUser = msg.role === "user";

  return (
    <div
      className={clsx(
        "flex w-full gap-3 px-2 py-2",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-black text-white dark:bg-white dark:text-black shadow-sm">
          <Bot className="h-4 w-4" />
        </div>
      )}

      <div
        className={clsx(
          "max-w-[78%] rounded-2xl px-4 py-3 text-xs sm:text-sm leading-relaxed whitespace-pre-wrap shadow-xs transition-all",
          isUser
            ? "bg-black text-white dark:bg-white dark:text-black shadow-sm font-medium"
            : "border-l-4 border-l-black dark:border-l-white border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-[#0a0a0a] text-black dark:text-white shadow-sm"
        )}
      >
        {msg.content}
      </div>

      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-neutral-300 bg-neutral-100 text-black dark:border-neutral-700 dark:bg-neutral-900 dark:text-white shadow-2xs">
          <User className="h-4 w-4" />
        </div>
      )}
    </div>
  );
}
