"use client";

import * as React from "react";
import { Brain, Mic, Cpu, Network, Sparkles, Activity, X } from "lucide-react";
import { cn } from "@/lib/utils";

export interface LoaderProps {
  size?: number;
  text?: string;
  agentName?: string;
  agentRole?: string;
  task?: string;
  thought?: string;
  stage?: string;
  progressPercent?: number;
  fullscreen?: boolean;
  className?: string;
  onDismiss?: () => void;
}

export const Component: React.FC<LoaderProps> = ({
  size = 180,
  text = "Generating",
  agentName,
  agentRole,
  task,
  thought,
  stage,
  progressPercent,
  fullscreen = true,
  className,
  onDismiss,
}) => {
  const letters = text.split("");

  const getAgentIcon = (stageName?: string) => {
    switch (stageName?.toUpperCase()) {
      case "REE":
        return <Brain className="h-4 w-4 text-sky-400" />;
      case "INTERVIEW":
        return <Mic className="h-4 w-4 text-blue-400" />;
      case "SAE":
        return <Cpu className="h-4 w-4 text-indigo-400" />;
      case "HLD":
        return <Network className="h-4 w-4 text-emerald-400" />;
      default:
        return <Sparkles className="h-4 w-4 text-blue-400" />;
    }
  };

  const content = (
    <div className="flex flex-col items-center justify-center gap-6 text-center select-none px-4">
      {/* ── Rotating Glowing Neon Orb with Animated Letters ── */}
      <div
        className="relative flex items-center justify-center font-mono select-none"
        style={{ width: size, height: size }}
      >
        <div className="flex items-center justify-center z-10 px-3">
          {letters.map((letter, index) => (
            <span
              key={index}
              className="inline-block text-white font-bold tracking-widest text-sm sm:text-base opacity-40 animate-loaderLetter drop-shadow-[0_0_8px_rgba(56,189,248,0.5)]"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              {letter === " " ? "\u00A0" : letter}
            </span>
          ))}
        </div>

        {/* The rotating gradient neon ring */}
        <div className="absolute inset-0 rounded-full animate-loaderCircle pointer-events-none" />
      </div>

      {/* ── Working Agent Telemetry Details ── */}
      {(agentName || task || stage) && (
        <div className="flex flex-col items-center max-w-lg space-y-2.5 z-10 animate-fadeIn">
          {/* Agent Stage & Name Badge */}
          <div className="inline-flex items-center gap-2 rounded-full border border-sky-500/30 bg-sky-500/10 px-3.5 py-1 text-xs font-semibold text-sky-300 backdrop-blur-md shadow-[0_0_15px_rgba(56,189,248,0.2)]">
            {getAgentIcon(stage)}
            <span>{agentName || "Autonomous Architecture Agent"}</span>
            {stage && (
              <span className="rounded bg-sky-400/20 px-1.5 py-0.2 text-[10px] font-mono text-sky-200">
                {stage}
              </span>
            )}
            <Activity className="h-3 w-3 animate-pulse text-sky-400" />
          </div>

          {/* Role */}
          {agentRole && (
            <p className="text-[11px] font-medium uppercase tracking-wider text-neutral-400">
              {agentRole}
            </p>
          )}

          {/* Current Micro-Task */}
          {task && (
            <p className="text-xs sm:text-sm font-medium text-neutral-200 leading-relaxed max-w-md">
              {task}
            </p>
          )}

          {/* Reasoning / Thought Stream */}
          {thought && (
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-3 text-xs text-neutral-300 max-w-md backdrop-blur-md">
              <span className="text-sky-400 font-bold mr-1.5 font-mono">Agent Reasoning:</span>
              <span className="italic leading-relaxed">{thought}</span>
            </div>
          )}

          {/* Progress Percent Bar */}
          {typeof progressPercent === "number" && (
            <div className="w-56 mt-2">
              <div className="flex items-center justify-between text-[10px] text-neutral-400 font-mono mb-1">
                <span>STAGE PIPELINE</span>
                <span>{progressPercent}%</span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-white/10 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-sky-400 via-blue-500 to-indigo-500 transition-all duration-500 shadow-[0_0_10px_rgba(56,189,248,0.5)]"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Dismiss / Minimize button in fullscreen mode */}
      {fullscreen && onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="mt-2 text-xs text-neutral-400 hover:text-white transition-colors underline underline-offset-4 cursor-pointer"
        >
          Run in background & keep viewing workspace
        </button>
      )}
    </div>
  );

  if (!fullscreen) {
    return (
      <div
        className={cn(
          "relative flex items-center justify-center p-6 rounded-3xl border border-sky-500/20 bg-neutral-900/80 backdrop-blur-xl shadow-2xl overflow-hidden",
          className
        )}
      >
        {/* Subtle radial backdrop glow */}
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-[#1a3379]/30 via-[#0f172a]/20 to-black/60 blur-xl" />
        {content}
      </div>
    );
  }

  return (
    <div
      className={cn(
        "fixed inset-0 z-50 flex items-center justify-center bg-gradient-to-b from-[#1a3379]/85 via-[#0f172a]/95 to-black/98 backdrop-blur-2xl transition-all",
        className
      )}
    >
      {/* Background ambient lighting */}
      <div className="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-gradient-to-b from-sky-500/20 via-blue-600/10 to-transparent blur-3xl rounded-full" />

      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          title="Minimize overlay"
          className="absolute top-6 right-6 p-2 rounded-full border border-white/10 bg-white/5 text-neutral-400 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
        >
          <X className="h-5 w-5" />
        </button>
      )}

      {content}
    </div>
  );
};

export const AiLoader = Component;
export default Component;
