"use client";

import { useEffect, useRef, useState } from "react";
import { Send } from "lucide-react";

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export default function PromptInput({ onSend, disabled = false }: Props) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 140)}px`;
  }, [value]);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  return (
    <div className="border-t border-slate-200 bg-white/90 px-3 py-3 backdrop-blur-xl dark:border-white/10 dark:bg-[#040815]/82 sm:px-4">
      <div className="mx-auto flex w-full max-w-3xl items-end gap-2 rounded-3xl border border-slate-200 bg-white px-4 py-2 shadow-[0_12px_32px_rgba(0,0,0,0.12)] transition-all duration-300 focus-within:border-blue-400/70 focus-within:bg-white dark:border-white/12 dark:bg-white/[0.04] dark:shadow-[0_12px_32px_rgba(0,0,0,0.42)] dark:focus-within:bg-white/[0.06]">
        <textarea
          ref={textareaRef}
          rows={1}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={disabled}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder={disabled ? "Assistant is generating..." : "Message ArchAI..."}
          className="max-h-[140px] min-h-6 flex-1 resize-none overflow-y-auto bg-transparent py-1 text-[15px] leading-6 text-slate-900 outline-none placeholder:text-slate-400 disabled:cursor-not-allowed disabled:opacity-70 dark:text-gray-100 dark:placeholder:text-gray-500"
        />
        <button
          onClick={handleSend}
          disabled={!value.trim() || disabled}
          aria-label="Send message"
          title="Send"
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-[#2563EB] to-[#1E40AF] text-white shadow-md shadow-blue-500/30 transition-all duration-200 hover:-translate-y-0.5 hover:scale-[1.02] hover:shadow-xl hover:shadow-blue-500/35 disabled:translate-y-0 disabled:scale-100 disabled:opacity-45"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
      <p className="mt-1 text-center text-xs text-slate-500 dark:text-gray-500">
        ArchAI can make mistakes. Verify important architecture decisions.
      </p>
    </div>
  );
}
