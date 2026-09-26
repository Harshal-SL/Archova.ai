"use client";

import React, { useEffect, useRef, useCallback, useState, useTransition } from "react";
import { cn } from "@/lib/utils";
import {
  ImageIcon,
  FileUp,
  Figma,
  MonitorIcon,
  CircleUserRound,
  ArrowUpIcon,
  Paperclip,
  PlusIcon,
  SendIcon,
  XIcon,
  LoaderIcon,
  Sparkles,
  Command,
  Workflow,
  Database,
  Cpu,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface UseAutoResizeTextareaProps {
  minHeight: number;
  maxHeight?: number;
}

function useAutoResizeTextarea({ minHeight, maxHeight }: UseAutoResizeTextareaProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustHeight = useCallback(
    (reset?: boolean) => {
      const textarea = textareaRef.current;
      if (!textarea) return;

      if (reset) {
        textarea.style.height = `${minHeight}px`;
        return;
      }

      textarea.style.height = `${minHeight}px`;
      const newHeight = Math.max(
        minHeight,
        Math.min(textarea.scrollHeight, maxHeight ?? Number.POSITIVE_INFINITY)
      );

      textarea.style.height = `${newHeight}px`;
    },
    [minHeight, maxHeight]
  );

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = `${minHeight}px`;
    }
  }, [minHeight]);

  useEffect(() => {
    const handleResize = () => adjustHeight();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [adjustHeight]);

  return { textareaRef, adjustHeight };
}

interface CommandSuggestion {
  icon: React.ReactNode;
  label: string;
  description: string;
  prefix: string;
}

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  containerClassName?: string;
  showRing?: boolean;
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, containerClassName, showRing = true, ...props }, ref) => {
    const [isFocused, setIsFocused] = React.useState(false);

    return (
      <div className={cn("relative", containerClassName)}>
        <textarea
          className={cn(
            "flex min-h-[60px] w-full rounded-md border-0 bg-transparent px-3 py-2 text-sm",
            "transition-all duration-200 ease-in-out",
            "placeholder:text-neutral-500 text-white",
            "disabled:cursor-not-allowed disabled:opacity-50",
            showRing ? "focus-visible:outline-none focus-visible:ring-0 focus-visible:ring-offset-0" : "",
            className
          )}
          ref={ref}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          {...props}
        />

        {showRing && isFocused && (
          <motion.span
            className="absolute inset-0 rounded-xl pointer-events-none ring-2 ring-offset-0 ring-white/10"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          />
        )}
      </div>
    );
  }
);
Textarea.displayName = "Textarea";

export interface AnimatedAIChatProps {
  onSend?: (text: string) => void;
  disabled?: boolean;
  userName?: string;
  className?: string;
}

export function AnimatedAIChat({
  onSend,
  disabled = false,
  userName = "Harshal",
  className,
}: AnimatedAIChatProps) {
  const [value, setValue] = useState("");
  const [attachments, setAttachments] = useState<string[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [, startTransition] = useTransition();
  const [activeSuggestion, setActiveSuggestion] = useState<number>(-1);
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [recentCommand, setRecentCommand] = useState<string | null>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const { textareaRef, adjustHeight } = useAutoResizeTextarea({
    minHeight: 60,
    maxHeight: 180,
  });
  const [inputFocused, setInputFocused] = useState(false);
  const commandPaletteRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const commandSuggestions: CommandSuggestion[] = [
    {
      icon: <Workflow className="w-4 h-4 text-sky-400" />,
      label: "Event Management Platform",
      description: "High concurrency hackathon submission & judging system",
      prefix: "Build an Online Event Management System for university hackathons with registration, submission judging, and live notifications.",
    },
    {
      icon: <Database className="w-4 h-4 text-purple-400" />,
      label: "Campus Library System",
      description: "ACID transactions, circulation tracking & automated overdue fines",
      prefix: "Build a College Library Management System with catalog search, inventory circulation, and automated overdue calculation.",
    },
    {
      icon: <MonitorIcon className="w-4 h-4 text-emerald-400" />,
      label: "Smart Parking & IoT",
      description: "Real-time sensor telemetry & automated license plate check-in",
      prefix: "Build an IoT Smart Parking Management System with real-time slot telemetry, digital reservation, and automated license plate check-in.",
    },
    {
      icon: <Cpu className="w-4 h-4 text-blue-400" />,
      label: "Video Streaming Cloud",
      description: "Distributed media transcoding, CDN edge delivery & subscription",
      prefix: "Build a scalable Video Streaming Platform with adaptive bitrate transcoding, CDN edge delivery, and subscription billing.",
    },
  ];

  useEffect(() => {
    if (value.startsWith("/") && !value.includes(" ")) {
      setShowCommandPalette(true);

      const matchingSuggestionIndex = commandSuggestions.findIndex((cmd) =>
        cmd.label.toLowerCase().includes(value.slice(1).toLowerCase())
      );

      if (matchingSuggestionIndex >= 0) {
        setActiveSuggestion(matchingSuggestionIndex);
      } else {
        setActiveSuggestion(-1);
      }
    } else {
      setShowCommandPalette(false);
    }
  }, [value]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
    };
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      const commandButton = document.querySelector("[data-command-button]");

      if (
        commandPaletteRef.current &&
        !commandPaletteRef.current.contains(target) &&
        !commandButton?.contains(target)
      ) {
        setShowCommandPalette(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (showCommandPalette) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setActiveSuggestion((prev) =>
          prev < commandSuggestions.length - 1 ? prev + 1 : 0
        );
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setActiveSuggestion((prev) =>
          prev > 0 ? prev - 1 : commandSuggestions.length - 1
        );
      } else if (e.key === "Tab" || e.key === "Enter") {
        e.preventDefault();
        if (activeSuggestion >= 0) {
          const selectedCommand = commandSuggestions[activeSuggestion];
          setValue(selectedCommand.prefix);
          setShowCommandPalette(false);
          setRecentCommand(selectedCommand.label);
          setTimeout(() => setRecentCommand(null), 3500);
        }
      } else if (e.key === "Escape") {
        e.preventDefault();
        setShowCommandPalette(false);
      }
    } else if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim()) {
        handleSendMessage();
      }
    }
  };

  const handleSendMessage = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;

    if (onSend) {
      onSend(trimmed);
      setValue("");
      adjustHeight(true);
    } else {
      startTransition(() => {
        setIsTyping(true);
        setTimeout(() => {
          setIsTyping(false);
          setValue("");
          adjustHeight(true);
        }, 2500);
      });
    }
  };

  const handleAttachFile = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const names = Array.from(files).map((f) => f.name);
    setAttachments((prev) => [...prev, ...names]);
  };

  const removeAttachment = (index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
  };

  const selectCommandSuggestion = (index: number) => {
    const selectedCommand = commandSuggestions[index];
    setValue(selectedCommand.prefix);
    setShowCommandPalette(false);
    setRecentCommand(selectedCommand.label);
    setTimeout(() => setRecentCommand(null), 2000);
  };

  return (
    <div
      className={cn(
        "flex flex-col w-full items-center justify-center bg-black text-white p-4 sm:p-6 relative select-none",
        className
      )}
    >
      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        multiple
        className="hidden"
      />

      {/* Ambient background subtle lighting on deep black */}
      <div className="absolute inset-0 w-full h-full pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/[0.04] rounded-full filter blur-[128px] animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-indigo-500/[0.04] rounded-full filter blur-[128px] animate-pulse delay-700" />
      </div>

      <div className="w-full max-w-2xl mx-auto relative z-10">
        <motion.div
          className="relative z-10 space-y-7"
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        >
          {/* Centered Heading */}
          <div className="text-center space-y-2">
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15, duration: 0.4 }}
              className="inline-block"
            >
              <h1 className="text-2xl sm:text-3xl font-medium tracking-tight text-white pb-1">
                How can I help, {userName}?
              </h1>
              <motion.div
                className="h-px bg-gradient-to-r from-transparent via-white/20 to-transparent mx-auto"
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: "100%", opacity: 1 }}
                transition={{ delay: 0.35, duration: 0.6 }}
              />
            </motion.div>
            <motion.p
              className="text-xs sm:text-sm text-neutral-400"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.25 }}
            >
              Describe your software requirements or select a system starter
            </motion.p>
          </div>

          {/* Main Black Glass Container */}
          <motion.div
            className="relative backdrop-blur-2xl bg-[#0f0f11]/90 rounded-2xl border border-white/[0.08] shadow-[0_20px_50px_rgba(0,0,0,0.8)] transition-all"
            initial={{ scale: 0.98 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.1 }}
          >
            {/* Command Palette Dropdown */}
            <AnimatePresence>
              {showCommandPalette && (
                <motion.div
                  ref={commandPaletteRef}
                  className="absolute left-3 right-3 bottom-full mb-2 backdrop-blur-2xl bg-black/95 rounded-xl z-50 shadow-2xl border border-white/10 overflow-hidden"
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 5 }}
                  transition={{ duration: 0.15 }}
                >
                  <div className="py-1 bg-black/95">
                    <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-neutral-500 border-b border-white/5">
                      Architecture Presets
                    </div>
                    {commandSuggestions.map((suggestion, index) => (
                      <motion.div
                        key={suggestion.label}
                        className={cn(
                          "flex items-center gap-2.5 px-3 py-2 text-xs transition-colors cursor-pointer",
                          activeSuggestion === index
                            ? "bg-white/10 text-white"
                            : "text-neutral-300 hover:bg-white/5"
                        )}
                        onClick={() => selectCommandSuggestion(index)}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: index * 0.02 }}
                      >
                        <div className="w-5 h-5 flex items-center justify-center shrink-0">
                          {suggestion.icon}
                        </div>
                        <div className="font-semibold">{suggestion.label}</div>
                        <div className="text-neutral-500 text-[11px] ml-auto truncate max-w-[220px]">
                          {suggestion.description}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Textarea */}
            <div className="p-3 sm:p-4">
              <Textarea
                ref={textareaRef}
                value={value}
                onChange={(e) => {
                  setValue(e.target.value);
                  adjustHeight();
                }}
                onKeyDown={handleKeyDown}
                onFocus={() => {
                  setInputFocused(true);
                }}
                onBlur={() => {
                  setInputFocused(false);
                }}
                placeholder="Describe your system architecture requirements or type / for templates..."
                containerClassName="w-full"
                className={cn(
                  "w-full px-3 py-2",
                  "resize-none",
                  "bg-transparent",
                  "border-none",
                  "text-white text-sm sm:text-base leading-relaxed",
                  "focus:outline-none",
                  "placeholder:text-neutral-500",
                  "min-h-[60px]"
                )}
                style={{
                  overflow: "hidden",
                }}
                showRing={false}
              />
            </div>

            {/* Attachments List */}
            <AnimatePresence>
              {attachments.length > 0 && (
                <motion.div
                  className="px-4 pb-3 flex gap-2 flex-wrap"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  {attachments.map((file, index) => (
                    <motion.div
                      key={index}
                      className="flex items-center gap-2 text-xs bg-white/[0.05] py-1.5 px-3 rounded-lg text-neutral-300 border border-white/5"
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                    >
                      <span>{file}</span>
                      <button
                        type="button"
                        onClick={() => removeAttachment(index)}
                        className="text-neutral-500 hover:text-white transition-colors cursor-pointer"
                      >
                        <XIcon className="w-3 h-3" />
                      </button>
                    </motion.div>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Bottom Actions Bar */}
            <div className="p-3 sm:p-4 border-t border-white/[0.06] flex items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                {/* Paperclip / Attach File */}
                <motion.button
                  type="button"
                  onClick={handleAttachFile}
                  whileTap={{ scale: 0.94 }}
                  title="Attach requirements spec or architecture doc"
                  className="p-2 text-neutral-400 hover:text-white rounded-lg transition-colors relative group cursor-pointer"
                >
                  <Paperclip className="w-4 h-4" />
                  <motion.span
                    className="absolute inset-0 bg-white/[0.06] rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                    layoutId="button-highlight"
                  />
                </motion.button>

                {/* Command Suggestions Toggle */}
                <motion.button
                  type="button"
                  data-command-button
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowCommandPalette((prev) => !prev);
                  }}
                  whileTap={{ scale: 0.94 }}
                  title="Architecture Presets (/)"
                  className={cn(
                    "p-2 text-neutral-400 hover:text-white rounded-lg transition-colors relative group cursor-pointer",
                    showCommandPalette && "bg-white/10 text-white"
                  )}
                >
                  <Command className="w-4 h-4" />
                  <motion.span
                    className="absolute inset-0 bg-white/[0.06] rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                    layoutId="button-highlight"
                  />
                </motion.button>
              </div>

              {/* Send Button */}
              <motion.button
                type="button"
                onClick={handleSendMessage}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                disabled={disabled || isTyping || !value.trim()}
                className={cn(
                  "px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer",
                  "flex items-center gap-2",
                  value.trim() && !disabled
                    ? "bg-white text-black hover:bg-neutral-200 shadow-md shadow-white/10"
                    : "bg-white/[0.06] text-neutral-500 cursor-not-allowed"
                )}
              >
                {isTyping ? (
                  <LoaderIcon className="w-4 h-4 animate-spin text-black" />
                ) : (
                  <SendIcon className="w-3.5 h-3.5" />
                )}
                <span>Synthesize</span>
              </motion.button>
            </div>
          </motion.div>

          {/* Suggestion Chips Below */}
          <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
            {commandSuggestions.map((suggestion, index) => (
              <motion.button
                key={suggestion.label}
                onClick={() => selectCommandSuggestion(index)}
                className="flex items-center gap-2 px-3.5 py-2 bg-neutral-900/90 hover:bg-neutral-800/90 border border-white/[0.06] hover:border-white/20 rounded-xl text-xs sm:text-sm text-neutral-300 hover:text-white transition-all relative group cursor-pointer shadow-xs"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.08 }}
              >
                {suggestion.icon}
                <span>{suggestion.label}</span>
              </motion.button>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Floating Thinking indicator */}
      <AnimatePresence>
        {isTyping && (
          <motion.div
            className="fixed bottom-8 mx-auto transform backdrop-blur-2xl bg-black/90 rounded-full px-4 py-2 shadow-2xl border border-white/10 z-50"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
          >
            <div className="flex items-center gap-3">
              <div className="w-7 h-7 rounded-full bg-white/10 flex items-center justify-center text-center">
                <span className="text-[11px] font-bold text-white">AI</span>
              </div>
              <div className="flex items-center gap-2 text-xs font-semibold text-neutral-200">
                <span>Analyzing requirements</span>
                <TypingDots />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Mouse Follower Glow */}
      {inputFocused && (
        <motion.div
          className="fixed w-[40rem] h-[40rem] rounded-full pointer-events-none z-0 opacity-[0.03] bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 blur-[96px]"
          animate={{
            x: mousePosition.x - 320,
            y: mousePosition.y - 320,
          }}
          transition={{
            type: "spring",
            damping: 30,
            stiffness: 140,
            mass: 0.5,
          }}
        />
      )}
    </div>
  );
}

function TypingDots() {
  return (
    <div className="flex items-center ml-1">
      {[1, 2, 3].map((dot) => (
        <motion.div
          key={dot}
          className="w-1.5 h-1.5 bg-white rounded-full mx-0.5"
          initial={{ opacity: 0.3 }}
          animate={{
            opacity: [0.3, 0.9, 0.3],
            scale: [0.85, 1.1, 0.85],
          }}
          transition={{
            duration: 1.2,
            repeat: Infinity,
            delay: dot * 0.15,
            ease: "easeInOut",
          }}
          style={{
            boxShadow: "0 0 4px rgba(255, 255, 255, 0.4)",
          }}
        />
      ))}
    </div>
  );
}

export default AnimatedAIChat;
