"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  HelpCircle,
  CheckCircle2,
  Sparkles,
  Send,
  Loader2,
  CornerDownLeft,
  Radio,
  Layers,
  ArrowRight,
  Info,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import { aiEngineApi } from "@/lib/ai-engine-client";
import { Button } from "@/components/ui/Button";
import { AiLoader } from "@/components/ui/ai-loader";
import MultiAgentSwarmLoader from "./MultiAgentSwarmLoader";
import ArsrsEditor from "./ArsrsEditor";
import { synthesizeArsrsDocument } from "@/lib/engine/ree";
import { parseHldToReactFlow } from "@/lib/graph-parser";
import { cn } from "@/lib/utils";
import Avatar from "@/components/ui/components-primitives-avatar";

interface InterviewPopupProps {
  onHldReady?: () => void;
}

export default function InterviewPopup({ onHldReady }: InterviewPopupProps) {
  const {
    generationId,
    currentQuestion,
    interviewCompleted,
    addLogEntry,
    activeAgent,
    setActiveAgent,
    setActiveView,
    arsrsData,
    setArsrsData,
    sessions,
    activeSessionId,
  } = useAppStore();

  const [selectedOption, setSelectedOption] = useState<string>("");
  const [customAnswer, setCustomAnswer] = useState<string>("");
  const [collectedAnswers, setCollectedAnswers] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [generatingArch, setGeneratingArch] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Derive synthesized or loaded ARSRS document
  const effectiveArsrsData = React.useMemo<Record<string, unknown>>(() => {
    if (arsrsData && Object.keys(arsrsData).length > 0) {
      return arsrsData;
    }
    const session = sessions.find((s) => s.id === activeSessionId);
    const promptText =
      session?.messages.find((m) => m.role === "user")?.content ||
      "Modern Cloud Microservices System";
    try {
      return (synthesizeArsrsDocument(promptText, collectedAnswers) as Record<string, unknown>) || {};
    } catch {
      return {};
    }
  }, [arsrsData, sessions, activeSessionId, collectedAnswers]);

  useEffect(() => {
    return () => {
      useAppStore.getState().stopAgentTelemetryPolling();
    };
  }, []);

  // Sync selected option when question changes
  useEffect(() => {
    if (currentQuestion) {
      const validOptions = (currentQuestion.options || []).filter((opt) => {
        const s = String(opt).trim().toLowerCase();
        return (
          s &&
          ![
            "option a",
            "option b",
            "option c",
            "option 1",
            "option 2",
            "placeholder",
            "none",
          ].includes(s)
        );
      });

      const defaultOpt =
        currentQuestion.default_option ||
        validOptions.find(
          (o) =>
            o.toLowerCase().includes("recommended") ||
            o.toLowerCase().includes("default")
        ) ||
        validOptions[0] ||
        "";

      setSelectedOption(defaultOpt);
      setCustomAnswer(defaultOpt);
      setError(null);

      // Update active agent to Interviewer
      setActiveAgent({
        id: "agent-interviewer",
        name: "Architectural Interviewer Agent",
        role: "Requirement Clarification & Constraints Discovery",
        icon: "mic",
        task: `Asking clarifying question: ${currentQuestion.question.slice(0, 60)}...`,
        status: "working",
        stage: "INTERVIEW",
        progressPercent: 50,
        thought: currentQuestion.rationale || "Formulating targeted architectural questions to eliminate ambiguity.",
      });
    }
  }, [currentQuestion, setActiveAgent]);

  // Keyboard shortcut listener (1-3 for options, Enter to submit)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (document.activeElement?.tagName === "TEXTAREA" || document.activeElement?.tagName === "INPUT") return;

      if (currentQuestion && !interviewCompleted) {
        const validOptions = (currentQuestion.options || []).filter(Boolean);
        if (["1", "2", "3", "4", "5"].includes(e.key)) {
          const idx = parseInt(e.key, 10) - 1;
          if (validOptions[idx]) {
            e.preventDefault();
            setSelectedOption(validOptions[idx]);
            setCustomAnswer(validOptions[idx]);
          }
        } else if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          handleSubmit();
        }
      } else if (interviewCompleted && !generatingArch && e.key === "Enter") {
        e.preventDefault();
        handleGenerateHld();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentQuestion, interviewCompleted, customAnswer, selectedOption, generatingArch]);

  const handleSubmit = async () => {
    const answer = (customAnswer || selectedOption).trim();
    if (!answer) {
      setError("Please select or enter an answer before proceeding.");
      return;
    }

    if (!generationId) return;

    setSubmitting(true);
    setError(null);

    const now = new Date().toTimeString().split(" ")[0];
    addLogEntry({
      timestamp: now,
      stage: "INTERVIEW",
      message: `Answer submitted: "${answer.slice(0, 45)}${answer.length > 45 ? "..." : ""}"`,
      level: "INFO",
    });

    try {
      const qId = currentQuestion?.question_id || "q1";
      const updatedAnswers = { ...collectedAnswers, [qId]: answer };
      setCollectedAnswers(updatedAnswers);

      const response = await aiEngineApi.submitAnswer(generationId, qId, answer);

      useAppStore.setState({
        interviewCompleted: response.status === "INTERVIEW_COMPLETED",
        currentQuestion: response.next_question || null,
        generationStatus: response.status,
      });

      if (response.status === "INTERVIEW_COMPLETED") {
        addLogEntry({
          timestamp: new Date().toTimeString().split(" ")[0],
          stage: "INTERVIEW",
          message: "✓ All architectural questions answered. Synthesizing formal ARSRS specification document...",
          level: "INFO",
        });

        // Automatically synthesize the formal ARSRS document
        const session = sessions.find((s) => s.id === activeSessionId);
        const promptText =
          session?.messages.find((m) => m.role === "user")?.content ||
          "Modern Cloud Microservices Architecture";

        try {
          const synthesized = synthesizeArsrsDocument(promptText, updatedAnswers);
          setArsrsData(synthesized);
        } catch {
          // Keep null if synthesis fails
        }

        setActiveAgent({
          id: "agent-ree",
          name: "Requirements Engineering Agent (REE)",
          role: "Formal Specification & Requirements Review",
          icon: "brain",
          task: "ARSRS specification synthesized. Ready for human review and requirements customization.",
          status: "completed",
          stage: "REE",
          progressPercent: 85,
          thought: "Synthesized ARSRS specification containing problem scope, stakeholder actors, functional requirements, and non-functional SLAs.",
        });
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to record answer.";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleGenerateHld = async (customArsrs?: Record<string, unknown>) => {
    if (!generationId) return;

    setGeneratingArch(true);
    setError(null);

    const finalArsrs = customArsrs || effectiveArsrsData;
    setArsrsData(finalArsrs);

    setActiveAgent({
      id: "agent-hld",
      name: "HLD Topology Engine",
      role: "Component Layout & Communication Protocols",
      icon: "network",
      task: "Generating High-Level Design (HLD) interactive architecture diagram from confirmed requirements...",
      status: "working",
      stage: "HLD",
      progressPercent: 95,
      thought: "Calculating topological component layout, React Flow edges, and protocol routes based on confirmed ARSRS specification.",
    });

    try {
      // Start live swarm telemetry polling
      useAppStore.getState().startAgentTelemetryPolling(generationId);

      // 1. Initial AI generation
      const response = await aiEngineApi.generateArchitecture(generationId);
      const parsedHld = response.hld ? parseHldToReactFlow(response.hld as Record<string, unknown>) : { nodes: [], edges: [] };
      const initialNodes = parsedHld.nodes;
      const initialEdges = parsedHld.edges;

      // Keep generation and validation progress distinct - do not mark as COMPLETED yet!
      useAppStore.setState({
        arsrsData: response.arsrs || finalArsrs,
        hldData: response.hld || null,
        hldNodes: initialNodes as any,
        hldEdges: initialEdges as any,
        generationStatus: "VALIDATING_ARCH",
      });

      setActiveAgent({
        id: "agent-validator",
        name: "Architectural Validator Engine",
        role: "Automated Verification & AI Correction",
        icon: "shield",
        task: "Executing automated Validator Engine verification and AI correction loop (max 2 retries)...",
        status: "working",
        stage: "VALIDATOR",
        progressPercent: 90,
        thought: "Auditing ARSRS alignment, cross-artifact consistency, and NFR feasibility across all 6 architecture artifacts.",
      });

      // 2. Automated Validation & AI Correction Workflow (calls POST /api/v1/generations/{id}/validate-and-correct?max_retries=2)
      const validatedResult = await useAppStore.getState().runCorrectionWorkflow(2);

      setActiveAgent({
        id: "agent-validator",
        name: "Architectural Validator Engine",
        role: "Multi-Artifact Closed-Loop Verification",
        icon: "shield",
        task: validatedResult?.is_fully_validated
          ? "Architecture verified and fully validated! Visual diagram active."
          : "Architecture generation complete with validation findings.",
        status: "completed",
        stage: "VALIDATOR",
        progressPercent: 100,
        thought: "Final validated architecture package loaded into HLD and LLD visualization.",
      });

      if (onHldReady) {
        onHldReady();
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to generate and validate architecture.";
      await useAppStore.getState().saveCurrentArchitecture().catch(() => {});
      setError(msg);
    } finally {
      setGeneratingArch(false);
      useAppStore.getState().stopAgentTelemetryPolling();
    }
  };

  if (!generationId) return null;

  return (
    <>
      {/* Synthesizing Architecture AI Loader (SAE Engine) */}
      {generatingArch && (
        <AiLoader
          fullscreen={true}
          size={180}
          text="Synthesizing"
          stage="SAE"
          agentName="SAE Engine"
          agentRole="Systems Architecture Engine"
          task={activeAgent?.task || "Synthesizing High-Level Design topology, 5 LLD specifications & automated validation..."}
          thought={activeAgent?.thought}
          progressPercent={activeAgent?.progressPercent ?? 85}
        />
      )}

      <AnimatePresence mode="wait">
      {/* ── State 1: Completed Interview -> ARSRS Document Specification Editor (Normal & Text JSON) ── */}
      {interviewCompleted ? (
        <motion.div
          key="arsrs-editor-wrapper"
          initial={{ opacity: 0, scale: 0.97, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.97, y: -15 }}
          transition={{ type: "spring", stiffness: 240, damping: 20 }}
        >
          <ArsrsEditor
            initialData={effectiveArsrsData}
            onProceed={(editedArsrs) => handleGenerateHld(editedArsrs)}
            isGenerating={generatingArch}
          />
        </motion.div>
      ) : currentQuestion ? (
        /* ── State 2: Active Animated Pop-out AI Interview Card (Compact Layout) ── */
        <motion.div
          key={currentQuestion.question_id}
          initial={{ opacity: 0, scale: 0.96, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: -15 }}
          transition={{ type: "spring", stiffness: 280, damping: 24 }}
          className="relative my-3.5 overflow-hidden rounded-2xl border border-[#005dff]/30 bg-white/95 dark:bg-neutral-900/95 p-4 sm:p-5 backdrop-blur-2xl shadow-[0_10px_40px_rgba(0,93,255,0.08)] dark:shadow-[0_10px_45px_rgba(0,0,0,0.55)] text-neutral-900 dark:text-white"
        >
          {/* Subtle accent bar on top in dark blue */}
          <div className="absolute top-0 inset-x-0 h-0.5 bg-[#005dff]" />

          {/* Two-Column Grid: Left = Question & Options, Right = AI Bot Box */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-stretch">
            {/* ══ Left Column: Interaction (Question, Rationale, Options, Custom Input, Submit) ══ */}
            <div className="md:col-span-8 lg:col-span-8 flex flex-col justify-between space-y-4">
              <div className="space-y-3.5">
                {/* The Question */}
                <div className="space-y-1.5">
                  <h4 className="text-base sm:text-lg font-bold tracking-tight text-neutral-900 dark:text-white leading-snug">
                    {currentQuestion.question}
                  </h4>
                  {currentQuestion.rationale && (
                    <div className="flex items-start gap-2 rounded-xl bg-neutral-100/80 px-3 py-2 text-xs text-neutral-600 dark:bg-neutral-800/60 dark:text-neutral-300">
                      <Info className="h-4 w-4 shrink-0 text-[#005dff] mt-0.5" />
                      <p className="leading-relaxed">
                        <strong className="font-semibold text-neutral-800 dark:text-neutral-100">Why this matters: </strong>
                        {currentQuestion.rationale}
                      </p>
                    </div>
                  )}
                </div>

                {/* Radio / Option Cards */}
                {currentQuestion.options && currentQuestion.options.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                      Choose Recommended Architectural Pattern:
                    </span>
                    <div className="grid grid-cols-1 gap-2">
                      {currentQuestion.options.map((opt, idx) => {
                        const isSelected = selectedOption === opt;
                        return (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => {
                              setSelectedOption(opt);
                              setCustomAnswer(opt);
                            }}
                            className={cn(
                              "group relative flex items-center gap-3 rounded-xl border px-3.5 py-2.5 text-left text-xs sm:text-sm transition-all cursor-pointer",
                              isSelected
                                ? "border-[#005dff] bg-[#005dff]/10 text-neutral-900 dark:text-white shadow-xs ring-1 ring-[#005dff]/30 font-medium"
                                : "border-neutral-200/80 bg-white/70 backdrop-blur-md hover:border-black dark:border-[#262626] dark:bg-[#0D0D0F] dark:hover:border-white/20 dark:hover:bg-[#161619] text-neutral-700 dark:text-neutral-300"
                            )}
                          >
                            <div
                              className={cn(
                                "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[11px] font-bold transition-colors",
                                isSelected
                                  ? "border-[#005dff] bg-[#005dff] text-white"
                                  : "border-neutral-300 bg-neutral-100 text-neutral-500 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-400"
                              )}
                            >
                              {idx + 1}
                            </div>
                            <span className="flex-1 leading-normal">{opt}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Custom Write-in Input */}
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-neutral-500 dark:text-neutral-400">
                    Or Customize / Refine Your Answer:
                  </label>
                  <input
                    type="text"
                    value={customAnswer}
                    onChange={(e) => setCustomAnswer(e.target.value)}
                    placeholder="Type custom architectural specification..."
                    className="w-full rounded-xl border border-neutral-300 bg-white px-3.5 py-2 text-xs sm:text-sm text-neutral-900 placeholder:text-neutral-400 outline-none transition-all focus:border-[#005dff] focus:ring-1 focus:ring-[#005dff]/20 dark:border-neutral-700 dark:bg-black dark:text-white dark:placeholder:text-neutral-500"
                  />
                </div>

                {error && (
                  <p className="rounded-xl border border-neutral-300 bg-neutral-100 px-3 py-2 text-xs font-semibold text-neutral-800 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-200">
                    {error}
                  </p>
                )}
              </div>

              {/* Action Footer */}
              <div className="flex flex-wrap items-center justify-between gap-2 pt-3 border-t border-neutral-200/60 dark:border-neutral-800/60">
                <span className="text-[11px] text-neutral-500 dark:text-neutral-400">
                  Press <kbd className="rounded border px-1 font-mono text-[10px]">1-3</kbd> to pick, <kbd className="rounded border px-1 font-mono text-[10px]">Enter ↵</kbd> to submit
                </span>

                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={submitting || !(customAnswer || selectedOption).trim()}
                  className="flex items-center gap-2 rounded-xl bg-[#005dff] hover:bg-[#004ad0] text-white px-5 py-2.5 text-xs font-bold transition-all disabled:opacity-40 cursor-pointer shadow-sm"
                >
                  {submitting ? (
                    <span className="flex items-center gap-1.5">
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      <span>Recording Answer...</span>
                    </span>
                  ) : (
                    <span className="flex items-center gap-1.5">
                      <span>Submit Answer</span>
                      <Send className="h-3.5 w-3.5" />
                    </span>
                  )}
                </button>
              </div>
            </div>

            {/* ══ Right Column: AI Bot Box (Enlarged Avatar Display in Black/White/Dark Blue) ══ */}
            <div className="md:col-span-4 lg:col-span-4 flex flex-col items-center justify-center rounded-2xl border border-[#005dff]/20 bg-white dark:bg-black/60 p-6 relative overflow-hidden self-stretch min-h-[220px]">
              {/* Soft ambient dark blue glow */}
              <div className="pointer-events-none absolute -top-8 -right-8 h-36 w-36 rounded-full bg-[#005dff]/10 blur-2xl" />
              <div className="pointer-events-none absolute -bottom-8 -left-8 h-36 w-36 rounded-full bg-[#005dff]/10 blur-2xl" />

              <div className="relative flex flex-col items-center justify-center my-auto">
                <div className="relative flex items-center justify-center">
                  {/* Subtle soft pulsing halo in dark blue */}
                  <div
                    className={cn(
                      "absolute -inset-4 rounded-full blur-xl transition-all duration-700 bg-[#005dff]/20",
                      submitting ? "scale-110 opacity-100" : "scale-100 opacity-60"
                    )}
                  />
                  <Avatar
                    color="blue"
                    size="xl"
                    shape="circle"
                    blinking={true}
                  />
                </div>

                {/* Animated telemetry audio bars in dark blue */}
                <div className="flex items-center gap-1.5 mt-4 h-5">
                  {[8, 16, 11, 22, 14, 18, 10, 15, 7].map((h, i) => (
                    <motion.span
                      key={i}
                      animate={{
                        scaleY: submitting ? [0.3, 1.4, 0.4, 1.2, 0.3] : [0.4, 0.9, 0.5, 1, 0.4],
                        opacity: submitting ? [0.7, 1, 0.6, 1, 0.7] : [0.4, 0.85, 0.5, 0.9, 0.4],
                      }}
                      transition={{
                        repeat: Infinity,
                        duration: submitting ? 0.75 : 1.5,
                        delay: i * 0.08,
                        ease: "easeInOut",
                      }}
                      className="w-1 rounded-full bg-[#005dff]"
                      style={{ height: `${h}px` }}
                    />
                  ))}
                </div>

                <p className="mt-2 text-[10px] text-neutral-400 dark:text-neutral-500 font-medium">
                  Tap avatar to interact
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  </>
  );
}
