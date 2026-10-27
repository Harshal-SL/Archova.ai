"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain,
  Briefcase,
  Code2,
  ShieldAlert,
  CheckCircle2,
  Sparkles,
  Layers,
  Network,
  Server,
  Layout,
  Database,
  Lock,
  Cloud,
  FileCheck,
  Activity,
  Terminal,
  Cpu,
  ChevronDown,
  ChevronUp,
  Radio,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import type { AgentTelemetry } from "@/lib/ai-engine-client";
import { cn } from "@/lib/utils";

interface MultiAgentSwarmLoaderProps {
  className?: string;
  stageTitle?: string;
  isGenerating?: boolean;
  fullscreen?: boolean;
}

export default function MultiAgentSwarmLoader({
  className,
  stageTitle = "Multi-Agent Intelligence Swarm",
  isGenerating = true,
  fullscreen = false,
}: MultiAgentSwarmLoaderProps) {
  const { agentSwarm, activeAgentsList } = useAppStore();
  const [collapsed, setCollapsed] = useState(false);

  // Group and sort agents
  const allAgents: AgentTelemetry[] = Object.values(agentSwarm);

  // Fallback defaults if backend is just spinning up
  const displayAgents: AgentTelemetry[] =
    allAgents.length > 0
      ? allAgents
      : [
          {
            agent_id: "business_analyst",
            name: "Business Analyst Agent",
            role: "Business Goals, User Journeys & KPIs",
            icon: "briefcase",
            stage: "REE",
            status: "running",
            current_task: "Synthesizing business goals and primary actor personas...",
            thought: "Extracting measurable business outcomes and stakeholder constraints from prompt.",
            progress_percent: 65,
          },
          {
            agent_id: "requirement_engineer",
            name: "Requirement Engineer Agent",
            role: "Technical Scope & Functional Invariants",
            icon: "code",
            stage: "REE",
            status: "running",
            current_task: "Decomposing functional boundaries and core operations...",
            thought: "Formulating strict API invariants and entity state machines.",
            progress_percent: 55,
          },
          {
            agent_id: "domain_expert",
            name: "Domain Expert Agent",
            role: "Industry Standards & Regulatory Compliance",
            icon: "shield",
            stage: "REE",
            status: "running",
            current_task: "Checking architectural best practices and compliance patterns...",
            thought: "Evaluating SLA feasibility, latency budgets, and failover requirements.",
            progress_percent: 45,
          },
        ];

  const runningAgents = displayAgents.filter((a) => a.status === "running");
  const completedAgents = displayAgents.filter((a) => a.status === "completed");
  const waitingAgents = displayAgents.filter((a) => a.status === "waiting");

  const getAgentIcon = (iconName: string) => {
    switch (iconName.toLowerCase()) {
      case "briefcase":
        return <Briefcase className="h-4 w-4" />;
      case "code":
      case "code2":
        return <Code2 className="h-4 w-4" />;
      case "shield":
      case "shieldalert":
        return <ShieldAlert className="h-4 w-4" />;
      case "brain":
        return <Brain className="h-4 w-4" />;
      case "file-check":
        return <FileCheck className="h-4 w-4" />;
      case "layers":
        return <Layers className="h-4 w-4" />;
      case "network":
        return <Network className="h-4 w-4" />;
      case "server":
        return <Server className="h-4 w-4" />;
      case "layout":
        return <Layout className="h-4 w-4" />;
      case "database":
        return <Database className="h-4 w-4" />;
      case "lock":
        return <Lock className="h-4 w-4" />;
      case "cloud":
        return <Cloud className="h-4 w-4" />;
      case "cpu":
        return <Cpu className="h-4 w-4" />;
      default:
        return <Sparkles className="h-4 w-4" />;
    }
  };

  const cardContent = (
    <div
      className={cn(
        "relative w-full rounded-2xl border border-blue-500/30 bg-neutral-950/90 text-white shadow-2xl backdrop-blur-xl overflow-hidden transition-all duration-300",
        className
      )}
    >
      {/* Dynamic ambient background glow */}
      <div className="pointer-events-none absolute -top-16 -left-16 h-48 w-48 rounded-full bg-blue-600/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-16 -right-16 h-48 w-48 rounded-full bg-purple-600/20 blur-3xl" />

      {/* ── Top Swarm Header ── */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 px-5 py-3.5 bg-white/[0.03]">
        <div className="flex items-center gap-3">
          <div className="relative flex h-8 w-8 items-center justify-center rounded-xl bg-blue-600/30 text-blue-400 border border-blue-500/40 shadow-inner">
            <Radio className="h-4 w-4 animate-pulse text-blue-400" />
            <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-blue-500" />
            </span>
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold tracking-wide uppercase text-white/90">
                {stageTitle}
              </span>
              <span className="inline-flex items-center gap-1 rounded-full bg-blue-500/15 border border-blue-500/30 px-2 py-0.5 text-[10px] font-semibold text-blue-300">
                <Activity className="h-2.5 w-2.5 animate-pulse" />
                <span>{runningAgents.length > 0 ? `${runningAgents.length} Agents Working Concurrently` : "Swarm Synchronized"}</span>
              </span>
            </div>
            <p className="text-[11px] text-white/50">
              Live multi-agent specialization pipeline pooling telemetry in real-time
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-white/40 hidden sm:inline">
            Parallel Workers Pool
          </span>
          <button
            type="button"
            onClick={() => setCollapsed(!collapsed)}
            className="flex h-7 w-7 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-white/70 hover:bg-white/10 hover:text-white transition-colors cursor-pointer"
            title={collapsed ? "Expand agent details" : "Collapse agent details"}
          >
            {collapsed ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronUp className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>

      {/* ── Main Agent Cards Grid ── */}
      <AnimatePresence>
        {!collapsed && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25 }}
            className="p-4 sm:p-5"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
              {displayAgents.map((agent) => {
                const isRunning = agent.status === "running";
                const isDone = agent.status === "completed";
                const isFailed = agent.status === "failed";

                return (
                  <motion.div
                    key={agent.agent_id}
                    layout
                    initial={{ opacity: 0, scale: 0.96 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className={cn(
                      "relative flex flex-col justify-between rounded-xl border p-3.5 transition-all overflow-hidden",
                      isRunning
                        ? "border-blue-500/50 bg-blue-950/20 shadow-[0_0_20px_rgba(59,130,246,0.15)] ring-1 ring-blue-500/30"
                        : isDone
                        ? "border-emerald-500/30 bg-emerald-950/15"
                        : isFailed
                        ? "border-red-500/40 bg-red-950/20"
                        : "border-white/10 bg-white/[0.02]"
                    )}
                  >
                    {/* Top Row: Icon + Name + Status Pill */}
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <div className="flex items-center gap-2 min-w-0">
                          <div
                            className={cn(
                              "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border text-white transition-colors",
                              isRunning
                                ? "border-blue-500 bg-blue-600 shadow-[0_0_10px_rgba(59,130,246,0.5)]"
                                : isDone
                                ? "border-emerald-500 bg-emerald-600"
                                : "border-white/10 bg-white/5 text-white/50"
                            )}
                          >
                            {getAgentIcon(agent.icon)}
                          </div>
                          <div className="min-w-0">
                            <h4 className="text-xs font-bold text-white truncate leading-tight">
                              {agent.name}
                            </h4>
                            <p className="text-[10px] text-white/50 truncate">
                              {agent.role}
                            </p>
                          </div>
                        </div>

                        {/* Status Pill */}
                        <div className="shrink-0">
                          {isRunning && (
                            <span className="flex items-center gap-1 rounded-full bg-blue-500/20 border border-blue-500/40 px-2 py-0.5 text-[10px] font-bold text-blue-300">
                              <span className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-ping" />
                              <span>WORKING</span>
                            </span>
                          )}
                          {isDone && (
                            <span className="flex items-center gap-1 rounded-full bg-emerald-500/20 border border-emerald-500/40 px-2 py-0.5 text-[10px] font-bold text-emerald-300">
                              <CheckCircle2 className="h-3 w-3" />
                              <span>DONE</span>
                            </span>
                          )}
                          {agent.status === "waiting" && (
                            <span className="rounded-full bg-white/10 border border-white/15 px-2 py-0.5 text-[10px] font-medium text-white/50">
                              QUEUED
                            </span>
                          )}
                          {isFailed && (
                            <span className="rounded-full bg-red-500/20 border border-red-500/40 px-2 py-0.5 text-[10px] font-bold text-red-300">
                              ERROR
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Current Active Task */}
                      <p className="text-[11px] text-white/80 leading-relaxed mb-2.5 font-medium line-clamp-2">
                        {agent.current_task || "Executing specialist subtask..."}
                      </p>

                      {/* Live Thought Terminal Box */}
                      {agent.thought && (
                        <div className="rounded-lg border border-white/5 bg-black/50 p-2 text-[10px] font-mono text-sky-200/90 leading-tight mb-2.5">
                          <div className="flex items-center gap-1 text-[9px] text-white/40 mb-1 font-sans uppercase font-bold tracking-wider">
                            <Terminal className="h-2.5 w-2.5" />
                            <span>Specialist Reasoning</span>
                          </div>
                          <span className="italic line-clamp-2">"{agent.thought}"</span>
                        </div>
                      )}
                    </div>

                    {/* Bottom Progress Bar */}
                    <div className="pt-1 border-t border-white/5 mt-1">
                      <div className="flex items-center justify-between text-[10px] text-white/50 mb-1">
                        <span>Phase Execution</span>
                        <span className="font-mono text-white/80 font-bold">
                          {agent.progress_percent}%
                        </span>
                      </div>
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                        <motion.div
                          className={cn(
                            "h-full rounded-full transition-all duration-500",
                            isRunning
                              ? "bg-linear-to-r from-blue-500 via-indigo-400 to-sky-400"
                              : isDone
                              ? "bg-emerald-500"
                              : "bg-white/20"
                          )}
                          initial={{ width: "0%" }}
                          animate={{ width: `${agent.progress_percent}%` }}
                          transition={{ duration: 0.5, ease: "easeOut" }}
                        />
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>

            {/* Micro Live Telemetry Footer Bar */}
            <div className="flex flex-wrap items-center justify-between gap-2 mt-4 pt-3 border-t border-white/10 text-[10px] text-white/40 font-mono">
              <div className="flex items-center gap-2">
                <span className="flex h-1.5 w-1.5 rounded-full bg-emerald-400" />
                <span>Synchronous WebSocket/SSE Telemetry Active</span>
              </div>
              <div>
                <span>Architecture Swarm Orchestrator v2.0</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );

  if (fullscreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-4 sm:p-6 backdrop-blur-md overflow-y-auto">
        <div className="w-full max-w-5xl my-auto">
          {cardContent}
        </div>
      </div>
    );
  }

  return cardContent;
}
