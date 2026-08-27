"use client";

import clsx from "clsx";
import type { ChatMessage as ChatMsg } from "@/lib/store";
import { Cpu } from "lucide-react";

export default function ChatMessage({ msg }: { msg: ChatMsg }) {
  const isUser = msg.role === "user";

  return (
    <div
      className={clsx(
        "flex w-full gap-4 px-4 py-6",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-[#333333] bg-black">
          <Cpu className="h-4 w-4 text-white" />
        </div>
      )}

      <div
        className={clsx(
          "max-w-[80%] rounded-2xl px-5 py-4 text-[15px] leading-relaxed whitespace-pre-wrap font-sans",
          isUser
            ? "bg-white text-black"
            : "bg-[#1A1A1A] text-white border border-[#333333]"
        )}
      >
        {msg.content}
      </div>
    </div>
  );
}
