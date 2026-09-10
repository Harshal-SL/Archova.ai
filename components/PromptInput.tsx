"use client";

import { useState } from "react";
import { Send } from "lucide-react";

interface Props {
  onSend: (text: string) => void;
}

export default function PromptInput({ onSend }: Props) {
  const [value, setValue] = useState("");

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setValue("");
  };

  return (
    <div className="shrink-0 border-t border-neutral-200 bg-white px-4 pt-3 pb-3.5 dark:border-neutral-800 dark:bg-black">
      <div className="mx-auto flex max-w-3xl items-end gap-2.5 rounded-2xl border border-neutral-300 bg-white px-4 py-2.5 shadow-sm transition-all duration-200 focus-within:border-black focus-within:ring-2 focus-within:ring-black/10 dark:border-neutral-800 dark:bg-[#0a0a0a] dark:focus-within:border-white dark:focus-within:ring-white/10">
        <textarea
          rows={1}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="Describe your system architecture requirements in natural language..."
          className="max-h-32 flex-1 resize-none bg-transparent py-1 text-xs sm:text-sm text-black placeholder:text-neutral-400 outline-none dark:text-white dark:placeholder:text-neutral-500"
        />
        <button
          onClick={handleSend}
          disabled={!value.trim()}
          title="Send prompt (Enter)"
          aria-label="Send prompt"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-black text-white dark:bg-white dark:text-black shadow-sm transition-all duration-200 hover:bg-neutral-800 dark:hover:bg-neutral-200 hover:scale-105 active:scale-95 disabled:opacity-30 disabled:hover:scale-100 disabled:cursor-not-allowed"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
      <p className="mt-2 text-center text-[11px] text-neutral-500 dark:text-neutral-400">
        ArchAI multi-agent engine • Press <span className="font-mono font-semibold text-black dark:text-white">Enter ↵</span> to synthesize architecture
      </p>
    </div>
  );
}
