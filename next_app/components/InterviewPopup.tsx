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
import ArsrsEditor from "./ArsrsEditor";
import { synthesizeArsrsDocument } from "@/lib/engine/ree";
import { dummyArsrs } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

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
  const effectiveArsrsData = React.useMemo(() => {
    if (arsrsData && Object.keys(arsrsData).length > 0) {
      return arsrsData;
    }
    const session = sessions.find((s) => s.id === activeSessionId);
    const promptText =
      session?.messages.find((m) => m.role === "user")?.content ||
      "Modern Cloud Microservices System";
    try {
      return synthesizeArsrsDocument(promptText, collectedAnswers);
    } catch {
      return dummyArsrs as Record<string, unknown>;
    }
  }, [arsrsData, sessions, activeSessionId, collectedAnswers]);

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
          setArsrsData(dummyArsrs as Record<string, unknown>);
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
      const response = await aiEngineApi.generateArchitecture(generationId);
      const hldObj = response.hld as { nodes?: unknown[]; edges?: unknown[] } | undefined;

      useAppStore.setState({
        arsrsData: finalArsrs,
        hldData: response.hld || null,
        hldNodes: (hldObj?.nodes as any) || [],
        hldEdges: (hldObj?.edges as any) || [],
        generationStatus: "COMPLETED",
        activeView: "hld", // Automatically transition to HLD display as requested!
      });

      setActiveAgent({
        id: "agent-hld",
        name: "HLD Topology Engine",
        role: "Component Layout & Communication Protocols",
        icon: "network",
        task: "High-Level Design (HLD) architecture synthesized successfully. Visual diagram active.",
        status: "completed",
        stage: "HLD",
        progressPercent: 100,
        thought: "Interactive HLD graph ready with microservices, gateway, cache, and database nodes.",
      });

      if (onHldReady) {
        onHldReady();
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to generate HLD architecture.";
      setError(msg);
    } finally {
      setGeneratingArch(false);
    }
  };

  if (!generationId) return null;

  return (
    <>
      {generatingArch && activeAgent && (
        <AiLoader
          fullscreen={true}
          size={180}
          text="Synthesizing"
          agentName={activeAgent.name}
          agentRole={activeAgent.role}
          stage={activeAgent.stage}
          task={activeAgent.task}
          thought={activeAgent.thought}
          progressPercent={activeAgent.progressPercent}
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
        /* ── State 2: Active Animated Pop-out AI Interview Card ── */
        <motion.div
          key={currentQuestion.question_id}
          initial={{ opacity: 0, scale: 0.94, y: 25 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.94, y: -20 }}
          transition={{ type: "spring", stiffness: 260, damping: 22 }}
          className="relative my-4 overflow-hidden rounded-3xl border border-blue-500/30 bg-white/95 dark:bg-neutral-900/95 p-6 sm:p-7 backdrop-blur-2xl shadow-[0_10px_40px_rgba(59,130,246,0.12)] dark:shadow-[0_10px_50px_rgba(0,0,0,0.6)] text-neutral-900 dark:text-white"
        >
          {/* Subtle blue accent bar on top */}
          <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-emerald-500" />

          {/* Header Tag Bar */}
          <div className="flex flex-wrap items-center justify-between gap-2 pb-3 mb-4 border-b border-neutral-200 dark:border-neutral-800">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 px-3 py-1 text-xs font-bold text-blue-600 dark:text-blue-400">
                <Sparkles className="h-3.5 w-3.5" />
                <span>AI Architecture Interview</span>
              </span>
              <span className="text-xs text-neutral-500 dark:text-neutral-400">
                ID: {currentQuestion.question_id}
              </span>
            </div>

            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-md border border-emerald-500/20">
              <Radio className="h-3 w-3 animate-pulse" />
              <span>Architectural Driver</span>
            </span>
          </div>

          {/* The Question */}
          <div className="space-y-2 mb-5">
            <h4 className="text-base sm:text-lg font-bold tracking-tight text-neutral-900 dark:text-white leading-snug">
              {currentQuestion.question}
            </h4>
            {currentQuestion.rationale && (
              <div className="flex items-start gap-2 rounded-xl bg-neutral-100/80 p-3 text-xs text-neutral-600 dark:bg-neutral-800/60 dark:text-neutral-300">
                <Info className="h-4 w-4 shrink-0 text-blue-500 mt-0.5" />
                <p className="leading-relaxed">
                  <strong className="font-semibold text-neutral-800 dark:text-neutral-100">Why this matters: </strong>
                  {currentQuestion.rationale}
                </p>
              </div>
            )}
          </div>

          {/* Radio / Option Cards */}
          {currentQuestion.options && currentQuestion.options.length > 0 && (
            <div className="space-y-2.5 mb-5">
              <span className="text-xs font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
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
                        "group relative flex items-start gap-3 rounded-2xl border p-3.5 text-left text-xs sm:text-sm transition-all cursor-pointer",
                        isSelected
                          ? "border-blue-500 bg-blue-500/10 text-neutral-900 dark:text-white shadow-sm ring-1 ring-blue-500/30 font-medium"
                          : "border-neutral-200 bg-white hover:border-neutral-300 hover:bg-neutral-50 dark:border-neutral-800 dark:bg-neutral-950/60 dark:hover:border-neutral-700 dark:hover:bg-neutral-900 text-neutral-700 dark:text-neutral-300"
                      )}
                    >
                      <div
                        className={cn(
                          "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[11px] font-bold mt-0.5 transition-colors",
                          isSelected
                            ? "border-blue-500 bg-blue-500 text-white"
                            : "border-neutral-300 bg-neutral-100 text-neutral-500 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-400"
                        )}
                      >
                        {idx + 1}
                      </div>
                      <span className="flex-1 leading-relaxed">{opt}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Custom Write-in Input */}
          <div className="space-y-1.5 mb-5">
            <label className="text-[11px] font-semibold text-neutral-500 dark:text-neutral-400">
              Or Customize / Refine Your Answer:
            </label>
            <input
              type="text"
              value={customAnswer}
              onChange={(e) => setCustomAnswer(e.target.value)}
              placeholder="Type custom architectural specification..."
              className="w-full rounded-xl border border-neutral-300 bg-white px-3.5 py-2.5 text-xs sm:text-sm text-neutral-900 placeholder:text-neutral-400 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-neutral-700 dark:bg-black dark:text-white dark:placeholder:text-neutral-500"
            />
          </div>

          {error && (
            <p className="mb-4 rounded-xl border border-red-200 bg-red-50 p-2.5 text-xs text-red-600 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
              {error}
            </p>
          )}

          {/* Action Footer */}
          <div className="flex items-center justify-between pt-2">
            <span className="text-[11px] text-neutral-500 dark:text-neutral-400">
              Press <kbd className="rounded border px-1 font-mono text-[10px]">1-3</kbd> to pick, <kbd className="rounded border px-1 font-mono text-[10px]">Enter ↵</kbd> to submit
            </span>

            <Button
              type="button"
              onClick={handleSubmit}
              disabled={submitting || !(customAnswer || selectedOption).trim()}
              variant="glow"
              size="default"
              neon={true}
              className="px-6 py-2.5 text-xs font-bold cursor-pointer"
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
            </Button>
          </div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  </>
  );
}
