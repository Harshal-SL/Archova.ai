"use client";

import clsx from "clsx";
import { Bot, User } from "lucide-react";
import type { ChatMessage as ChatMsg } from "@/lib/store";

export default function ChatMessage({ msg }: { msg: ChatMsg }) {
  const isUser = msg.role === "user";

  return (
    <div
      className={clsx(
        "flex w-full gap-3 px-4 py-4",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-600">
          <Bot className="h-4 w-4 text-white" />
        </div>
      )}

      <div
        className={clsx(
          "max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap",
          isUser
            ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white"
            : "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200"
        )}
      >
        {msg.content}
      </div>

      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-300 dark:bg-gray-700">
          <User className="h-4 w-4 text-gray-600 dark:text-gray-300" />
        </div>
      )}
    </div>
  );
}
