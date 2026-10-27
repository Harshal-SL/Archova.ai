import React, { useState, useRef, useEffect } from "react";
import { Plus, Brain, Mic, ArrowUp, Scale } from "lucide-react";
import { cn } from "@/lib/utils";
import { ShimmerButton } from "@/components/ui/shimmer-button";
import { useAppStore } from "@/lib/store";
import BenchmarkConfigModal from "./BenchmarkConfigModal";

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
  const { benchmarkModelsConfig } = useAppStore();
  const [value, setValue] = useState("");
  const [thinkActive, setThinkActive] = useState(true);
  const [isListening, setIsListening] = useState(false);
  const [showBenchmarkModal, setShowBenchmarkModal] = useState(false);
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
        variant === "center" ? "max-w-[700px] px-2 sm:px-4" : "max-w-3xl mx-auto px-2 sm:px-4 pb-3 sm:pb-4 pt-1 sm:pt-2"
      )}
    >
      {/* Pill-shaped ChatGPT input container */}
      <div
        className={cn(
          "relative flex items-center gap-1.5 sm:gap-2 rounded-full border transition-all duration-200",
          "border-neutral-200/80 bg-white/95 text-neutral-900 focus-within:border-black focus-within:shadow-xl",
          "dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-white dark:focus-within:border-white/20 shadow-2xl backdrop-blur-md",
          variant === "center" ? "p-1.5 sm:p-2 pl-2.5 sm:pl-4 min-h-[48px] sm:min-h-[52px]" : "p-1 sm:p-1.5 pl-2 sm:pl-3 min-h-[44px] sm:min-h-[48px]"
        )}
      >
        {/* Left: '+' Action Button */}
        <button
          type="button"
          onClick={onOpenTemplates}
          title="Add files or select architectural templates"
          className="flex h-7 w-7 sm:h-8 sm:w-8 shrink-0 items-center justify-center rounded-full text-neutral-400 hover:bg-neutral-100 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-[#161619] dark:hover:text-white transition-colors cursor-pointer"
        >
          <Plus className="h-4 w-4 sm:h-5 sm:w-5 stroke-[1.9]" />
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
          className="w-full resize-none bg-transparent py-1 text-xs sm:text-base text-neutral-900 placeholder:text-neutral-400 outline-none dark:text-white dark:placeholder:text-[#8E8E8E] leading-relaxed max-h-36 overflow-y-auto"
        />

        {/* Right side controls (exact ChatGPT order: Think, Mic, Audio/Send) */}
        <div className="flex shrink-0 items-center gap-1 sm:gap-1.5 pr-0.5">
          {/* Think pill button */}
          <button
            type="button"
            onClick={() => setThinkActive(!thinkActive)}
            title="Multi-Agent Architectural Reasoning"
            className={cn(
              "flex items-center gap-1 sm:gap-1.5 rounded-full px-2 sm:px-2.5 py-1 text-xs sm:text-sm font-medium transition-colors cursor-pointer",
              thinkActive
                ? "text-neutral-800 dark:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-[#161619]"
                : "text-neutral-400 hover:text-neutral-600 dark:text-neutral-500 dark:hover:text-neutral-300"
            )}
          >
            <Brain className="h-4 w-4" />
            <span className="text-xs sm:text-sm hidden sm:inline">Think</span>
          </button>

          {/* Microphone button */}
          <button
            type="button"
            onClick={handleToggleVoice}
            title={isListening ? "Stop listening" : "Dictate requirements"}
            className={cn(
              "flex h-7 w-7 sm:h-8 sm:w-8 items-center justify-center rounded-full text-neutral-400 hover:bg-neutral-100 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-[#161619] dark:hover:text-white transition-colors cursor-pointer",
              isListening && "text-red-500 dark:text-red-400 animate-pulse bg-red-500/10"
            )}
          >
            <Mic className="h-4 w-4" />
          </button>

          {/* Circular Blue Action Button with Shimmer Animation */}
          <ShimmerButton
            type="button"
            onClick={hasValue ? handleSend : handleToggleVoice}
            disabled={disabled}
            borderRadius="9999px"
            shimmerColor="rgba(255, 255, 255, 0.85)"
            shimmerDuration="2.5s"
            background={hasValue && !disabled ? "rgba(37, 99, 235, 1)" : "rgba(16, 104, 235, 1)"}
            className={cn(
              "flex h-8 w-8 sm:h-9 sm:w-9 p-0 shrink-0 items-center justify-center rounded-full transition-all duration-200 shadow-md cursor-pointer active:scale-95 border border-white/20",
              hasValue && !disabled && "shadow-blue-500/30"
            )}
            title={hasValue ? "Send (Enter ↵)" : "Start Voice dictation"}
          >
            {hasValue ? (
              <ArrowUp className="h-4 w-4 stroke-[2.5] text-white" />
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
          </ShimmerButton>
        </div>
      </div>

      {/* Benchmark Models & API Keys Modal */}
      <BenchmarkConfigModal
        isOpen={showBenchmarkModal}
        onClose={() => setShowBenchmarkModal(false)}
      />
    </div>
  );
}

