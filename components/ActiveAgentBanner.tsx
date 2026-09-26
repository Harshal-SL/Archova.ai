"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain,
  Mic,
  Cpu,
  Network,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Activity,
  CheckCircle2,
  Terminal,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import { AiLoader } from "@/components/ui/ai-loader";
import { cn } from "@/lib/utils";

export default function ActiveAgentBanner() {
  const { activeAgent, logs } = useAppStore();
  const [expanded, setExpanded] = useState(false);
  const [showLoaderModal, setShowLoaderModal] = useState(false);

  if (!activeAgent) return null;

  const isWorking = activeAgent.status === "working" || activeAgent.status === "thinking";
  const isCompleted = activeAgent.status === "completed";

  const getAgentIcon = (iconName: string) => {
    switch (iconName) {
      case "brain":
        return <Brain className="h-4 w-4" />;
      case "mic":
        return <Mic className="h-4 w-4" />;
      case "cpu":
        return <Cpu className="h-4 w-4" />;
      case "network":
        return <Network className="h-4 w-4" />;
      default:
        return <Sparkles className="h-4 w-4" />;
    }
  };

  const recentLog = logs[logs.length - 1];

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="w-full shrink-0 border-b border-neutral-200 bg-neutral-50/95 px-4 py-2.5 backdrop-blur-md dark:border-neutral-800/80 dark:bg-neutral-950/90 transition-colors"
    >
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-3">
        {/* Left: Agent Identity & Status */}
        <div className="flex min-w-0 items-center gap-3">
          {/* Agent Avatar Badge with pulsing radar ring */}
          <div className="relative flex shrink-0 items-center justify-center">
            <div
              className={cn(
                "flex h-8 w-8 items-center justify-center rounded-xl border text-white shadow-xs transition-colors",
                isWorking
                  ? "border-blue-500/50 bg-blue-600/90 text-white shadow-[0_0_15px_rgba(59,130,246,0.35)]"
                  : isCompleted
                  ? "border-emerald-500/50 bg-emerald-600/90 text-white shadow-[0_0_15px_rgba(16,185,129,0.35)]"
                  : "border-neutral-300 bg-neutral-800 text-neutral-200 dark:border-neutral-700"
              )}
            >
              {getAgentIcon(activeAgent.icon)}
            </div>

            {/* Live activity pulse ring */}
            {isWorking && (
              <span className="absolute -top-0.5 -right-0.5 flex h-2.5 w-2.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75" />
                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-blue-500" />
              </span>
            )}
          </div>

          {/* Name & Task */}
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="truncate text-xs font-bold tracking-tight text-neutral-900 dark:text-white">
                {activeAgent.name}
              </span>
              <span className="hidden sm:inline-flex items-center rounded-md border border-neutral-200 bg-white px-1.5 py-0.5 text-[10px] font-semibold text-neutral-600 dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-400">
                {activeAgent.stage}
              </span>
              {isWorking && (
                <span className="flex items-center gap-1 text-[11px] font-semibold text-blue-500 dark:text-blue-400">
                  <Activity className="h-3 w-3 animate-pulse" />
                  <span className="hidden md:inline">Processing</span>
                </span>
              )}
              {isCompleted && (
                <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-500 dark:text-emerald-400">
                  <CheckCircle2 className="h-3 w-3" />
                  <span className="hidden md:inline">Ready</span>
                </span>
              )}
            </div>

            <p className="truncate text-[11px] text-neutral-600 dark:text-neutral-400">
              {activeAgent.task}
            </p>
          </div>
        </div>

        {/* Right: Thought Stream / Telemetry Details */}
        <div className="flex items-center gap-2">
          {activeAgent.thought && (
            <div className="hidden lg:flex items-center gap-1.5 rounded-lg border border-neutral-200 bg-white/70 px-3 py-1 text-[11px] text-neutral-600 dark:border-neutral-800 dark:bg-neutral-900/70 dark:text-neutral-300 max-w-sm truncate">
              <span className="text-blue-500 font-bold">Thought:</span>
              <span className="truncate">{activeAgent.thought}</span>
            </div>
          )}

          <button
            type="button"
            onClick={() => setShowLoaderModal(true)}
            className="flex items-center gap-1.5 rounded-lg border border-sky-500/30 bg-sky-500/10 px-2.5 py-1 text-xs font-semibold text-sky-400 hover:bg-sky-500/20 transition-colors cursor-pointer"
            title="Open AI Agent Loader Monitor"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Monitor</span>
          </button>

          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 rounded-lg border border-neutral-200 bg-white px-2.5 py-1 text-xs font-medium text-neutral-700 transition-colors hover:bg-neutral-100 hover:text-black dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-300 dark:hover:bg-neutral-800 dark:hover:text-white"
            title="Toggle Agent Trace"
          >
            <Terminal className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Trace</span>
            {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>

      {/* Expandable Reasoning Trace */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="mx-auto mt-2.5 max-w-5xl rounded-xl border border-neutral-200 bg-white p-3 text-xs font-mono dark:border-neutral-800 dark:bg-black/90">
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-neutral-200 dark:border-neutral-800 text-[11px] text-neutral-500">
                <span className="flex items-center gap-1.5">
                  <Activity className="h-3.5 w-3.5 text-blue-400" />
                  <span>Agent Execution Trace • {activeAgent.role}</span>
                </span>
                <span>Stage: {activeAgent.stage}</span>
              </div>
              <p className="text-neutral-700 dark:text-neutral-300 mb-1.5">
                <strong className="text-blue-500 dark:text-blue-400">Current Objective:</strong> {activeAgent.task}
              </p>
              {activeAgent.thought && (
                <p className="text-neutral-600 dark:text-neutral-400 mb-1.5">
                  <strong className="text-purple-500 dark:text-purple-400">Reasoning:</strong> {activeAgent.thought}
                </p>
              )}
              {recentLog && (
                <p className="text-[11px] text-neutral-500 truncate">
                  Latest telemetry: [{recentLog.stage}] {recentLog.message}
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Fullscreen AI Loader Agent Monitor Modal */}
      {showLoaderModal && (
        <AiLoader
          fullscreen={true}
          size={180}
          text={
            activeAgent.status === "working"
              ? activeAgent.stage === "REE"
                ? "Analyzing"
                : activeAgent.stage === "INTERVIEW"
                ? "Interviewing"
                : "Synthesizing"
              : "Active"
          }
          agentName={activeAgent.name}
          agentRole={activeAgent.role}
          stage={activeAgent.stage}
          task={activeAgent.task}
          thought={activeAgent.thought}
          progressPercent={activeAgent.progressPercent}
          onDismiss={() => setShowLoaderModal(false)}
        />
      )}
    </motion.div>
  );
}
