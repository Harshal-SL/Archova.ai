"use client";

import { useState, useEffect } from "react";
import {
  HelpCircle,
  CheckCircle2,
  Sparkles,
  Send,
  Loader2,
  CornerDownLeft,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import { aiEngineApi } from "@/lib/ai-engine-client";
import { parseHldToReactFlow } from "@/lib/graph-parser";
import clsx from "clsx";

interface Props {
  onArchitectureGenerated?: () => void;
}

export default function InterviewCard({ onArchitectureGenerated }: Props) {
  const {
    generationId,
    currentQuestion,
    interviewCompleted,
    addLogEntry,
  } = useAppStore();

  const [selectedOption, setSelectedOption] = useState<string>("");
  const [customAnswer, setCustomAnswer] = useState<string>("");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [generatingArch, setGeneratingArch] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize selected option when current question changes
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
    }
  }, [currentQuestion]);

  // Keyboard shortcut listener (1-5 to select option, Enter to submit)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (document.activeElement?.tagName === "TEXTAREA") return;

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
        handleGenerateArchitecture();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentQuestion, interviewCompleted, customAnswer, selectedOption, generatingArch]);

  const handleSubmit = async () => {
    const answer = (customAnswer || selectedOption).trim();
    if (!answer) {
      setError("Please select or enter an answer before submitting.");
      return;
    }

    if (!generationId) return;

    setSubmitting(true);
    setError(null);

    const now = new Date().toTimeString().split(" ")[0];
    addLogEntry({
      timestamp: now,
      stage: "INTERVIEW",
      message: `Answer submitted: "${answer.slice(0, 40)}${answer.length > 40 ? "..." : ""}"`,
      level: "INFO",
    });

    try {
      const qId = currentQuestion?.question_id || "q1";
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
          message: "✓ All clarifying questions answered. Ready to generate architecture!",
          level: "INFO",
        });
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to submit answer.";
      setError(msg);
      addLogEntry({
        timestamp: new Date().toTimeString().split(" ")[0],
        stage: "CLIENT",
        message: `❌ Submit failed: ${msg}`,
        level: "ERROR",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleGenerateArchitecture = async () => {
    if (!generationId) return;

    setGeneratingArch(true);
    setError(null);

    const now = new Date().toTimeString().split(" ")[0];
    addLogEntry({
      timestamp: now,
      stage: "SAE",
      message: "🚀 Starting full architecture synthesis (ARSRS + HLD)...",
      level: "INFO",
    });

    try {
      const response = await aiEngineApi.generateArchitecture(generationId);

      const hldObj = response.hld as { nodes?: unknown[]; edges?: unknown[] } | undefined;
      const parsedHld = response.hld ? parseHldToReactFlow(response.hld as Record<string, unknown>) : { nodes: [], edges: [] };
      const finalNodes = (hldObj?.nodes && (hldObj.nodes as unknown[]).length > 0) ? hldObj.nodes : parsedHld.nodes;
      const finalEdges = (hldObj?.edges && (hldObj.edges as unknown[]).length > 0) ? hldObj.edges : parsedHld.edges;

      useAppStore.setState({
        arsrsData: response.arsrs || null,
        hldData: response.hld || null,
        hldNodes: finalNodes as any,
        hldEdges: finalEdges as any,
        generationStatus: "COMPLETED",
        activePipelineStep: 2,
      });

      addLogEntry({
        timestamp: new Date().toTimeString().split(" ")[0],
        stage: "SAE",
        message: "✓ ARSRS & HLD generated successfully. Visual graph ready.",
        level: "INFO",
      });

      if (onArchitectureGenerated) {
        onArchitectureGenerated();
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Architecture generation failed.";
      setError(msg);
      addLogEntry({
        timestamp: new Date().toTimeString().split(" ")[0],
        stage: "CLIENT",
        message: `❌ Generation failed: ${msg}`,
        level: "ERROR",
      });
    } finally {
      setGeneratingArch(false);
    }
  };

  if (!generationId) return null;

  // Render interview completed state
  if (interviewCompleted) {
    return (
      <div className="rounded-3xl border border-neutral-300 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-900 p-7 shadow-lg backdrop-blur-xl">
        <div className="flex flex-col items-center text-center">
          <div className="mb-3.5 flex h-14 w-14 items-center justify-center rounded-2xl bg-black text-white dark:bg-white dark:text-black shadow-md">
            <CheckCircle2 className="h-7 w-7" />
          </div>
          <h3 className="font-heading text-xl font-extrabold text-black dark:text-white">
            Requirement Clarification Completed
          </h3>
          <p className="mt-1.5 max-w-md text-xs text-neutral-600 dark:text-neutral-400 leading-relaxed">
            All system boundaries and non-functional requirements have been analyzed. You can now synthesize the formal ARSRS specification and High-Level Design (HLD).
          </p>

          {error && (
            <p className="mt-3 rounded-xl border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-600 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
              {error}
            </p>
          )}

          <div className="mt-6 flex gap-3">
            <button
              onClick={handleGenerateArchitecture}
              disabled={generatingArch}
              className="flex items-center gap-2.5 rounded-full bg-black text-white dark:bg-white dark:text-black px-7 py-3 text-xs sm:text-sm font-bold shadow-md transition-all hover:bg-neutral-800 dark:hover:bg-neutral-200 disabled:opacity-50"
            >
              {generatingArch ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Synthesizing ARSRS + HLD...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Generate Architecture (ARSRS + HLD)
                  <CornerDownLeft className="h-3.5 w-3.5 opacity-75" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Render question card
  if (!currentQuestion) return null;

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

  return (
    <div className="relative rounded-3xl border border-neutral-300 border-t-4 border-t-black bg-white p-6 sm:p-7 shadow-xl dark:border-neutral-800 dark:border-t-white dark:bg-[#0a0a0a] backdrop-blur-xl">
      {/* Header with question badges */}
      <div className="mb-3.5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 rounded-lg border border-neutral-300 bg-neutral-100 px-3 py-1 text-xs font-bold text-black shadow-2xs dark:border-neutral-700 dark:bg-neutral-900 dark:text-white">
            <HelpCircle className="h-3.5 w-3.5" />
            {currentQuestion.question_id || "Requirement Clarification"}
          </span>
          <span className="rounded-lg border border-neutral-300 bg-neutral-100 dark:border-neutral-700 dark:bg-neutral-900 px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wider text-black dark:text-white">
            {(currentQuestion.priority || "Medium").toUpperCase()} Priority
          </span>
        </div>
        <span className="text-[11px] font-mono text-neutral-400 dark:text-neutral-500">
          Keys 1-5 to select • ↵ Enter to submit
        </span>
      </div>

      {/* Question Text */}
      <h3 className="font-heading text-lg font-bold leading-snug text-black dark:text-white">
        {currentQuestion.question}
      </h3>

      {/* Rationale */}
      {currentQuestion.rationale && (
        <p className="mt-1.5 text-xs italic text-neutral-500 dark:text-neutral-400">
          Context: {currentQuestion.rationale}
        </p>
      )}

      {/* Options List */}
      {validOptions.length > 0 && (
        <div className="mt-5 space-y-2">
          <p className="text-[11px] font-bold uppercase tracking-wider text-neutral-500">
            Suggested Architectural Options:
          </p>
          <div className="flex flex-wrap gap-2.5">
            {validOptions.map((opt, idx) => {
              const isSelected = selectedOption === opt;
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setSelectedOption(opt);
                    setCustomAnswer(opt);
                  }}
                  className={clsx(
                    "group flex items-center gap-2.5 rounded-xl border px-3.5 py-2.5 text-left text-xs font-semibold transition-all duration-200",
                    isSelected
                      ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black shadow-sm"
                      : "border-neutral-300 bg-white text-neutral-800 hover:border-black hover:text-black dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-200 dark:hover:border-white dark:hover:text-white"
                  )}
                >
                  <span
                    className={clsx(
                      "flex h-4 w-4 shrink-0 items-center justify-center rounded font-mono text-[10px] font-bold",
                      isSelected
                        ? "bg-white text-black dark:bg-black dark:text-white"
                        : "bg-neutral-200 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300"
                    )}
                  >
                    {idx + 1}
                  </span>
                  <span>{opt}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Custom Answer input with monochrome focus */}
      <div className="mt-5">
        <label className="mb-1.5 block text-[11px] font-bold uppercase tracking-wider text-neutral-600 dark:text-neutral-400">
          Your Answer:
        </label>
        <div className="flex items-center rounded-xl border border-neutral-300 bg-white px-3 shadow-xs transition-all duration-200 focus-within:border-black focus-within:ring-2 focus-within:ring-black/10 dark:border-neutral-800 dark:bg-black dark:focus-within:border-white dark:focus-within:ring-white/10">
          <input
            type="text"
            value={customAnswer}
            onChange={(e) => setCustomAnswer(e.target.value)}
            placeholder="Select an option above or type your custom specification..."
            disabled={submitting}
            className="w-full bg-transparent py-2.5 text-xs text-black placeholder:text-neutral-400 outline-none dark:text-white dark:placeholder:text-neutral-500"
          />
          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitting || !customAnswer.trim()}
            className="flex items-center gap-1.5 rounded-lg bg-black text-white dark:bg-white dark:text-black px-3.5 py-1.5 text-xs font-bold shadow-sm transition-all hover:bg-neutral-800 dark:hover:bg-neutral-200 disabled:opacity-40"
          >
            {submitting ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <>
                <span>Submit</span>
                <Send className="h-3 w-3" />
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <p className="mt-2.5 text-xs font-semibold text-red-600 dark:text-red-400">
          {error}
        </p>
      )}
    </div>
  );
}
