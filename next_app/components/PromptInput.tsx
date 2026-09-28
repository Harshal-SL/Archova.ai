"use client";

import React, { useState, useRef, useEffect } from "react";
import { Plus, Brain, Mic, ArrowUp } from "lucide-react";
import { cn } from "@/lib/utils";

interface PromptInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
  variant?: "center" | "bottom";
  onOpenTemplates?: () => void;
}

export default function PromptInput({
  onSend,
  disabled = false,
  placeholder = "Ask anything",
  variant = "bottom",
  onOpenTemplates,
}: PromptInputProps) {
  const [value, setValue] = useState("");
  const [thinkActive, setThinkActive] = useState(true);
  const [isListening, setIsListening] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = `${Math.min(scrollHeight, 140)}px`;
    }
  }, [value]);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Voice input toggle
  const handleToggleVoice = () => {
    if (typeof window === "undefined") return;
    const SpeechRecognition =
      (window as unknown as { SpeechRecognition?: any }).SpeechRecognition ||
      (window as unknown as { webkitSpeechRecognition?: any }).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser. Please type your requirements.");
      return;
    }

    if (isListening) {
      setIsListening(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = "en-US";

      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => setIsListening(false);
      recognition.onerror = () => setIsListening(false);
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          setValue((prev) => (prev ? `${prev} ${transcript}` : transcript));
        }
      };

      recognition.start();
    } catch {
      setIsListening(false);
    }
  };

  const hasValue = value.trim().length > 0;

  return (
    <div
      className={cn(
        "w-full transition-all duration-200",
        variant === "center" ? "max-w-[700px] px-4" : "max-w-3xl mx-auto px-4 pb-4 pt-2"
      )}
    >
      {/* Pill-shaped ChatGPT input container */}
      <div
        className={cn(
          "relative flex items-center gap-2 rounded-full border transition-all duration-200",
          "border-neutral-200 bg-white/95 text-neutral-900 focus-within:border-neutral-400 focus-within:shadow-xl",
          "dark:border-white/[0.08] dark:bg-[#212121] dark:text-white dark:focus-within:border-neutral-600 shadow-2xl",
          variant === "center" ? "p-2 pl-3.5 sm:pl-4 min-h-[52px]" : "p-1.5 pl-3 min-h-[48px]"
        )}
      >
        {/* Left: '+' Action Button */}
        <button
          type="button"
          onClick={onOpenTemplates}
          title="Add files or select architectural templates"
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-neutral-400 hover:bg-neutral-100 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-white/10 dark:hover:text-white transition-colors cursor-pointer"
        >
          <Plus className="h-5 w-5 stroke-[1.9]" />
        </button>

        {/* Center: Clean Textarea / Input */}
        <textarea
          ref={textareaRef}
          rows={1}
          value={value}
          disabled={disabled}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isListening ? "Listening... Speak your requirements" : placeholder}
          className="w-full resize-none bg-transparent py-1.5 text-sm sm:text-base text-neutral-900 placeholder:text-neutral-400 outline-none dark:text-white dark:placeholder:text-[#8E8E8E] leading-relaxed max-h-36 overflow-y-auto"
        />

        {/* Right side controls (exact ChatGPT order: Think, Mic, Audio/Send) */}
        <div className="flex shrink-0 items-center gap-1 sm:gap-1.5 pr-0.5">
          {/* Think pill button */}
          <button
            type="button"
            onClick={() => setThinkActive(!thinkActive)}
            title="Multi-Agent Architectural Reasoning"
            className={cn(
              "flex items-center gap-1.5 rounded-full px-2.5 py-1 text-sm font-medium transition-colors cursor-pointer",
              thinkActive
                ? "text-neutral-800 dark:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-white/10"
                : "text-neutral-400 hover:text-neutral-600 dark:text-neutral-500 dark:hover:text-neutral-300"
            )}
          >
            <Brain className="h-4 w-4" />
            <span className="text-sm">Think</span>
          </button>

          {/* Microphone button */}
          <button
            type="button"
            onClick={handleToggleVoice}
            title={isListening ? "Stop listening" : "Dictate requirements"}
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-full text-neutral-400 hover:bg-neutral-100 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-white/10 dark:hover:text-white transition-colors cursor-pointer",
              isListening && "text-red-500 dark:text-red-400 animate-pulse bg-red-500/10"
            )}
          >
            <Mic className="h-4 w-4" />
          </button>

          {/* Circular Blue Action Button (Waveform when empty, ArrowUp when text typed) */}
          <button
            type="button"
            onClick={hasValue ? handleSend : handleToggleVoice}
            disabled={disabled}
            title={hasValue ? "Send (Enter ↵)" : "Start Voice dictation"}
            className={cn(
              "flex h-9 w-9 shrink-0 items-center justify-center rounded-full transition-all duration-200 shadow-sm cursor-pointer active:scale-95",
              hasValue && !disabled
                ? "bg-blue-600 text-white hover:bg-blue-500 shadow-blue-500/30"
                : "bg-[#1068eb] hover:bg-[#0d60d8] text-white"
            )}
          >
            {hasValue ? (
              <ArrowUp className="h-4 w-4 stroke-[2.5]" />
            ) : (
              /* Waveform Icon matching Image 2 */
              <svg
                className="h-4 w-4 text-white"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="6" y1="9" x2="6" y2="15" />
                <line x1="10" y1="5" x2="10" y2="19" />
                <line x1="14" y1="7" x2="14" y2="17" />
                <line x1="18" y1="10" x2="18" y2="14" />
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
