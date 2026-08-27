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
import clsx from "clsx";

interface Props {
  onArchitectureGenerated?: () => void;
}

export default function InterviewCard({ onArchitectureGenerated }: Props) {
  const {
    generationId,
    generationStatus,
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
    if (!generationId || !currentQuestion) {
      setError("No active session found.");
      return;
    }

    setError(null);
    setSubmitting(true);

    const now = new Date().toTimeString().split(" ")[0];
    addLogEntry({
      timestamp: now,
      stage: "INTERVIEW",
      message: `Submitted answer for '${currentQuestion.question_id}': "${answer.slice(0, 60)}..."`,
      level: "INFO",
    });

    try {
      const response = await aiEngineApi.submitAnswer(
        generationId,
        currentQuestion.question_id,
        answer
      );

      if (response.status === "INTERVIEW_IN_PROGRESS" && response.next_question) {
        useAppStore.setState({
          currentQuestion: response.next_question,
          interviewCompleted: false,
        });
      } else {
        useAppStore.setState({
          currentQuestion: null,
          interviewCompleted: true,
          generationStatus: "INTERVIEW_COMPLETED",
        });
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to submit answer.";
      setError(msg);
      addLogEntry({
        timestamp: new Date().toTimeString().split(" ")[0],
        stage: "CLIENT",
        message: `❌ Submit error: ${msg}`,
        level: "ERROR",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleGenerateArchitecture = async () => {
    if (!generationId) return;

    setError(null);
    setGeneratingArch(true);

    const now = new Date().toTimeString().split(" ")[0];
    addLogEntry({
      timestamp: now,
      stage: "CLIENT",
      message: "⚙️ Triggering Architecture Generation (ARSRS + HLD)...",
      level: "INFO",
    });

    try {
      useAppStore.setState({ generationStatus: "GENERATING_ARCH" });
      const response = await aiEngineApi.generateArchitecture(generationId);

      // Parse HLD to ReactFlow graph
      const { nodes, edges } = await import("@/lib/graph-parser").then((m) =>
        m.parseHldToReactFlow(response.hld)
      );

      useAppStore.setState({
        arsrsData: response.arsrs || {},
        hldData: response.hld || {},
        hldNodes: nodes,
        hldEdges: edges,
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
      <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-5 backdrop-blur-md dark:border-emerald-500/20 dark:bg-emerald-950/20">
        <div className="flex flex-col items-center text-center">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400">
            <CheckCircle2 className="h-6 w-6" />
          </div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">
            Interview Completed!
          </h3>
          <p className="mt-1 max-w-md text-xs text-gray-600 dark:text-gray-300">
            All clarifying requirements have been captured. You are ready to generate
            the formal ARSRS specification and High-Level Design (HLD).
          </p>

          {error && (
            <p className="mt-3 rounded-lg bg-red-500/10 px-3 py-1.5 text-xs text-red-600 dark:text-red-400">
              {error}
            </p>
          )}

          <div className="mt-5 flex gap-3">
            <button
              onClick={handleGenerateArchitecture}
              disabled={generatingArch}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-emerald-500/25 transition-all hover:opacity-95 hover:shadow-xl disabled:opacity-60"
            >
              {generatingArch ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Generating ARSRS + HLD...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Generate Architecture (ARSRS + HLD)
                  <CornerDownLeft className="h-3.5 w-3.5 opacity-70" />
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

  const priorityColor =
    currentQuestion.priority === "high"
      ? "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30"
      : currentQuestion.priority === "low"
      ? "bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/30"
      : "bg-purple-500/15 text-purple-600 dark:text-purple-400 border-purple-500/30";

  return (
    <div className="rounded-2xl border border-indigo-500/30 bg-white/90 p-5 shadow-lg backdrop-blur-md dark:border-indigo-500/20 dark:bg-gray-900/90">
      {/* Header with question badges */}
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1 rounded-lg bg-indigo-500/10 px-2.5 py-1 text-xs font-bold text-indigo-600 dark:text-indigo-400">
            <HelpCircle className="h-3.5 w-3.5" />
            {currentQuestion.question_id || "Requirement Clarification"}
          </span>
          <span
            className={clsx(
              "rounded-lg border px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider",
              priorityColor
            )}
          >
            {(currentQuestion.priority || "Medium").toUpperCase()} Priority
          </span>
        </div>
        <span className="text-[11px] text-gray-400 font-mono">
          Press 1-5 to pick option ↵ Enter to submit
        </span>
      </div>

      {/* Question Text */}
      <h3 className="text-base font-semibold leading-snug text-gray-900 dark:text-white">
        {currentQuestion.question}
      </h3>

      {/* Rationale */}
      {currentQuestion.rationale && (
        <p className="mt-1 text-xs italic text-gray-500 dark:text-gray-400">
          Context: {currentQuestion.rationale}
        </p>
      )}

      {/* Options List */}
      {validOptions.length > 0 && (
        <div className="mt-4 space-y-1.5">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-400">
            Suggested Options:
          </p>
          <div className="flex flex-wrap gap-2">
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
                    "group flex items-center gap-2 rounded-xl border px-3 py-2 text-left text-xs transition-all",
                    isSelected
                      ? "border-indigo-500 bg-indigo-500/15 font-semibold text-indigo-600 shadow-sm dark:border-indigo-400 dark:bg-indigo-950/50 dark:text-indigo-300"
                      : "border-gray-200 bg-gray-50 text-gray-700 hover:border-indigo-300 hover:bg-indigo-50/50 dark:border-gray-800 dark:bg-gray-800/60 dark:text-gray-300 dark:hover:border-indigo-800 dark:hover:bg-gray-800"
                  )}
                >
                  <span
                    className={clsx(
                      "flex h-4 w-4 shrink-0 items-center justify-center rounded font-mono text-[10px] font-bold",
                      isSelected
                        ? "bg-indigo-500 text-white"
                        : "bg-gray-200 text-gray-600 dark:bg-gray-700 dark:text-gray-300 group-hover:bg-indigo-100 dark:group-hover:bg-indigo-900"
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

      {/* Custom Answer input */}
      <div className="mt-4">
        <label className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-gray-400">
          Your Answer:
        </label>
        <div className="flex items-center rounded-xl border border-gray-300 bg-white px-3 transition-colors focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/20 dark:border-gray-700 dark:bg-gray-800">
          <input
            type="text"
            value={customAnswer}
            onChange={(e) => setCustomAnswer(e.target.value)}
            placeholder="Select an option above or type your custom answer..."
            disabled={submitting}
            className="w-full bg-transparent py-2.5 text-xs outline-none placeholder:text-gray-400 dark:text-white"
          />
          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitting || !customAnswer.trim()}
            className="flex items-center gap-1 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition-opacity hover:opacity-95 disabled:opacity-40"
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
        <p className="mt-2 text-xs font-medium text-red-600 dark:text-red-400">
          {error}
        </p>
      )}
    </div>
  );
}
