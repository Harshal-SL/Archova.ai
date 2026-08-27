"use client";

import { useState } from "react";
import { ArrowUp } from "lucide-react";

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export default function PromptInput({ onSend, disabled = false }: Props) {
  const [value, setValue] = useState("");

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  return (
    <div className="border-t border-[#2A2A2A] bg-[#0A0A0A] px-4 py-4 shrink-0">
      <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-[#333333] bg-[#111111] px-4 py-3 transition-colors focus-within:border-white focus-within:ring-1 focus-within:ring-white">
        <textarea
          id="prompt-input"
          rows={1}
          value={value}
          disabled={disabled}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder={disabled ? "Generating your design…" : "Describe a system to design…"}
          className="max-h-40 flex-1 resize-none bg-transparent py-1 text-[15px] font-sans outline-none text-white placeholder:text-[#555555] disabled:opacity-50"
        />
        <button
          id="send-btn"
          onClick={handleSend}
          disabled={!value.trim() || disabled}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white text-black transition-transform hover:scale-105 active:scale-95 disabled:opacity-30 disabled:hover:scale-100"
        >
          <ArrowUp className="h-5 w-5" strokeWidth={3} />
        </button>
      </div>
    </div>
  );
}
