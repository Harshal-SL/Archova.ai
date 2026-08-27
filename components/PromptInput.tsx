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
    <div className="shrink-0 border-t border-gray-200 bg-white px-4 pt-3 pb-3.5 dark:border-gray-800 dark:bg-black">
      <div className="mx-auto flex max-w-3xl items-end gap-2.5 rounded-2xl border border-gray-300/80 bg-gray-50/80 px-4 py-2.5 shadow-sm transition-all focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/20 dark:border-gray-700/80 dark:bg-gray-900/80">
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
          placeholder="Describe your system architecture requirements..."
          className="max-h-32 flex-1 resize-none bg-transparent py-1 text-sm outline-none placeholder:text-gray-400 dark:text-white"
        />
        <button
          onClick={handleSend}
          disabled={!value.trim()}
          title="Send prompt"
          aria-label="Send prompt"
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-sm transition-all hover:opacity-95 hover:shadow-md disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
      <p className="mt-2 text-center text-[11px] text-gray-400">
        ArchAI can make mistakes. Verify important architecture decisions.
      </p>
    </div>
  );
}
