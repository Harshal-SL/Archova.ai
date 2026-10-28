"use client";

import React, { useState } from "react";
import {
  ShieldCheck,
  AlertTriangle,
  XCircle,
  CheckCircle2,
  Clock,
  Layers,
  Cpu,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  TrendingUp,
  Sparkles,
  Info,
  Server,
  Database,
  Cloud,
  Lock,
  Layout,
  ExternalLink,
  RotateCcw,
  BookOpen,
  Filter,
  FileText,
  HelpCircle,
  Globe,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import CorrectionPlanSection from "@/components/CorrectionPlanSection";
import { buildCorrectionPlan } from "@/lib/correction-planner";
import type {
  Report,
  ArtifactResult,
  Finding,
  Correction,
  DimensionScore,
  PatternAssessment,
  RealWorldResult,
  ReferenceSystemUsed,
} from "@/lib/validator-v2-client";
import clsx from "clsx";

const ARTIFACT_ICONS: Record<string, React.ReactNode> = {
  hld: <Layers className="h-4 w-4 text-indigo-400" />,
  backend: <Server className="h-4 w-4 text-blue-400" />,
  database: <Database className="h-4 w-4 text-amber-400" />,
  frontend: <Layout className="h-4 w-4 text-teal-400" />,
  security: <Lock className="h-4 w-4 text-rose-400" />,
  cloud: <Cloud className="h-4 w-4 text-sky-400" />,
};

const ARTIFACT_NAMES: Record<string, string> = {
  hld: "High-Level Architecture (HLD)",
  backend: "Backend Service LLD",
  database: "Database & Persistence LLD",
  frontend: "Frontend Architecture LLD",
  security: "Zero-Trust Security LLD",
  cloud: "Cloud Infrastructure LLD",
};

export default function ValidationReportView() {
  const {
    validationReport,
    correctionPlan,
    validationStatus,
    validationCurrentStep,
    isValidating,
    isValidatingV2,
    validationError,
    validateArchitecture,
    validationIsStale,
    staleReason,
    staleArtifactType,
    activeVersionTag,
    runRevalidation,
  } = useAppStore();

  const [expandedArtifact, setExpandedArtifact] = useState<string | null>("backend");

  const isLoading = isValidating || isValidatingV2;

  if (isLoading) {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center p-8 text-center bg-white/50 dark:bg-black/50">
        <div className="relative mb-4 flex items-center justify-center">
          <RefreshCw className="h-10 w-10 animate-spin text-indigo-500" />
          <ShieldCheck className="absolute h-5 w-5 text-indigo-300" />
        </div>
        <h3 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">
          Validator Engine v2 Running (Port 8002)
        </h3>
        <p className="mt-1.5 max-w-md text-xs text-neutral-600 dark:text-neutral-400">
          {validationCurrentStep || "Evaluating ARSRS, HLD, and all 5 LLDs against verified rubrics and real-world patterns..."}
        </p>
        <span className="mt-3 inline-flex items-center rounded-full bg-indigo-500/10 px-3 py-1 text-xs font-mono text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">
          Status: {validationStatus || "running"}
        </span>
      </div>
    );
  }

  if (!validationReport) {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center p-8 text-center bg-white/50 dark:bg-black/50">
        <div className="mb-4 rounded-2xl bg-neutral-100 p-4 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800">
          <ShieldCheck className="h-10 w-10 text-neutral-400" />
        </div>
        <h3 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">
          No Validation Report Available
        </h3>
        <p className="mt-1 max-w-md text-xs text-neutral-600 dark:text-neutral-400">
          Run the independent Validator Engine v2 on port 8002 to evaluate structural correctness,
          rubrics, anti-hallucination evidence, and real-world architecture grounding.
        </p>

        {validationError && (
          <div className="mt-4 max-w-md rounded-xl border border-rose-500/30 bg-rose-500/10 p-3.5 text-xs text-rose-700 dark:text-rose-300 text-left">
            <div className="flex items-center gap-2 font-bold mb-1">
              <XCircle className="h-4 w-4 text-rose-500 shrink-0" />
              <span>Validator Engine Connection Error</span>
            </div>
            <p>{validationError}</p>
          </div>
        )}

        <button
          onClick={() => validateArchitecture()}
          className="mt-4 inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 shadow-sm transition-colors cursor-pointer"
        >
          <Sparkles className="h-4 w-4" />
          <span>{validationError ? "Retry Validation Audit (Port 8002)" : "Run Validator Engine v2"}</span>
        </button>
      </div>
    );
  }

  const report = validationReport;
  const effectiveCorrectionPlan =
    correctionPlan || (report ? buildCorrectionPlan(report) : null);
  const lastIteration = report.iterations[report.iterations.length - 1];
  const allCorrections: { iterIndex: number; correction: Correction }[] = [];
  report.iterations.forEach((it, idx) => {
    it.corrections.forEach((c) => {
      allCorrections.push({ iterIndex: idx + 1, correction: c });
    });
  });

  // Calculate score trends per artifact
  const scoreHistory: Record<string, number[]> = {};
  report.iterations.forEach((it) => {
    Object.entries(it.results).forEach(([art, res]) => {
      if (!scoreHistory[art]) scoreHistory[art] = [];
      scoreHistory[art].push(res.score);
    });
  });

  return (
    <div className="flex h-full w-full flex-col overflow-y-auto p-4 sm:p-6 space-y-6">
      {/* ── STALE VALIDATION REPORT WARNING BANNER (Part 2.2.2) ── */}
      {validationIsStale && (
        <div className="rounded-2xl border-2 border-amber-500/50 bg-amber-500/10 p-5 dark:border-amber-500/30 dark:bg-amber-950/30 shadow-md">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/30 shrink-0">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-bold text-amber-950 dark:text-amber-100">
                    Validation Report is Stale (Architecture Modified: {activeVersionTag})
                  </h4>
                  <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-mono font-bold text-amber-700 dark:text-amber-300">
                    STALE
                  </span>
                </div>
                <p className="mt-1 text-xs text-amber-800 dark:text-amber-300 leading-relaxed max-w-2xl">
                  {staleReason || `A targeted AI correction was accepted and committed to ${staleArtifactType || "an artifact"}. The validation scores and findings below reflect the previous baseline and do not reflect version ${activeVersionTag}.`}
                </p>
                <div className="mt-2 text-[11px] font-mono text-amber-700/80 dark:text-amber-400/80">
                  Historical validation report preserved for audit comparison. Automatic revalidation is never triggered.
                </div>
              </div>
            </div>

            <button
              onClick={() => runRevalidation()}
              disabled={isLoading}
              className="inline-flex items-center gap-2 rounded-xl bg-amber-600 hover:bg-amber-500 px-4 py-2.5 text-xs font-bold text-white shadow-sm transition-colors cursor-pointer shrink-0 disabled:opacity-50"
              title="Explicitly run Validator Engine v2 on port 8002"
            >
              <RefreshCw className={clsx("h-4 w-4", isLoading && "animate-spin")} />
              <span>Run Revalidation (Port 8002)</span>
            </button>
          </div>
        </div>
      )}

      {/* ── MOCK REVIEWER SAFETY BANNER ── */}
      {report.reviewer_mode === "mock" && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 dark:border-amber-500/20">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
            <div>
              <h4 className="text-sm font-semibold text-amber-900 dark:text-amber-200">
                MOCK reviewer: not a real validation
              </h4>
              <p className="mt-1 text-xs text-amber-700 dark:text-amber-300">
                The validator executed with synthetic mock reviewers. Per Archova safety policy,
                mock reviews cannot produce a production ACCEPTED verdict without live LLM rubric
                and real-world benchmark verification.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ── UNRESOLVED or PROVISIONAL BANNER ── */}
      {report.final_status === "PROVISIONAL" && (
        <div className="rounded-xl border border-purple-500/30 bg-purple-500/10 p-4 dark:border-purple-500/20">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 shrink-0 text-purple-600 dark:text-purple-400 mt-0.5" />
            <div>
              <h4 className="text-sm font-semibold text-purple-900 dark:text-purple-200">
                PROVISIONAL VERDICT — Reviewer LLM Unavailable
              </h4>
              <p className="mt-1 text-xs text-purple-700 dark:text-purple-300">
                The external LLM reviewer could not be reached (offline or rate limited). Scores are
                derived strictly from Layer 0 normalization and Layer 1 executable evidence. In accordance
                with Archova v2 hard constraints, unverified architectures are NEVER silently approved.
              </p>
            </div>
          </div>
        </div>
      )}

      {report.final_status === "UNRESOLVED" && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 dark:border-rose-500/20">
          <div className="flex items-start gap-3">
            <XCircle className="h-5 w-5 shrink-0 text-rose-600 dark:text-rose-400 mt-0.5" />
            <div>
              <h4 className="text-sm font-semibold text-rose-900 dark:text-rose-200">
                UNRESOLVED ARCHITECTURE — Critical Defect Unmitigated
              </h4>
              <p className="mt-1 text-xs text-rose-700 dark:text-rose-300">
                One or more critical or high-severity architectural defects remain unresolved after the
                maximum correction rounds ({report.iterations.length} rounds executed). Inspect the artifact
                cards below for suggested fixes.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ── LAYER 1 SCAFFOLDS STATUS CALLOUT ── */}
      <div className="rounded-xl border border-neutral-200/80 bg-neutral-50/70 p-3.5 text-xs dark:border-neutral-800 dark:bg-neutral-900/40 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-neutral-500 shrink-0" />
          <span className="font-medium text-neutral-700 dark:text-neutral-300">
            Layer 1 Static Evidence (OpenAPI, Dockerfile, Terraform, Alembic Migrations):
          </span>
          <span className="rounded bg-neutral-200/80 px-2 py-0.5 text-[11px] font-mono text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400">
            not evaluated: no scaffold provided
          </span>
        </div>
        <span className="text-[11px] text-neutral-400">
          Zero deductions applied; never falsely marked as passed.
        </span>
      </div>

      {/* ── HEADER ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-2xl border border-neutral-200/80 bg-white/70 p-5 backdrop-blur-md dark:border-neutral-800/80 dark:bg-neutral-900/60 shadow-xs">
        <div>
          <div className="flex flex-wrap items-center gap-2.5">
            <h2 className="text-xl font-bold tracking-tight text-neutral-900 dark:text-neutral-100">
              Validation Report v2
            </h2>
            <StatusBadge status={report.final_status} />
            <span className="rounded-full bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 px-2.5 py-0.5 text-xs font-mono text-neutral-600 dark:text-neutral-400">
              {report.iterations.length} {report.iterations.length === 1 ? "Round" : "Rounds"}
            </span>
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-neutral-500 dark:text-neutral-400">
            <span className="flex items-center gap-1.5">
              <Cpu className="h-3.5 w-3.5" />
              Model: <strong className="font-mono text-neutral-700 dark:text-neutral-300">{report.model_used || "OpenRouter"}</strong>
            </span>
            <span className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5" />
              {new Date(report.created_at).toLocaleString()}
            </span>
            <span className="font-mono text-[11px] text-neutral-400">
              ID: {report.generation_id.slice(0, 16)}...
            </span>
          </div>
        </div>

        <button
          onClick={() => validateArchitecture()}
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-neutral-200 bg-white px-3.5 py-1.5 text-xs font-medium text-neutral-800 hover:bg-neutral-50 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-200 dark:hover:bg-neutral-700 shadow-xs transition-colors cursor-pointer self-start sm:self-auto"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          <span>Re-validate Audit</span>
        </button>
      </div>

      {/* ── OVERALL COMPOSITE SCORECARD (C, R, W, D, S) ── */}
      <div className="rounded-2xl border border-neutral-200/80 bg-white/70 p-5 backdrop-blur-md dark:border-neutral-800/80 dark:bg-neutral-900/60 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-indigo-500" />
            <h3 className="text-sm font-semibold uppercase tracking-wider text-neutral-700 dark:text-neutral-300">
              System Composite Scorecard
            </h3>
          </div>
          <span className="text-xs font-mono text-neutral-400">
            Formula: S = 0.20·C + 0.45·R + 0.35·W − D
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-1">
          {/* C Score */}
          <div className="rounded-xl border border-neutral-200/80 bg-neutral-50/70 p-3 dark:border-neutral-800 dark:bg-neutral-950/40 text-center">
            <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 block mb-1">
              C · Correctness
            </span>
            <span className="text-xl font-black font-mono text-neutral-900 dark:text-neutral-100">
              {report.overall_c ?? report.final_scores?.c ?? 100}
              <span className="text-xs text-neutral-400 font-normal">/100</span>
            </span>
            <span className="text-[10px] text-neutral-400 block mt-0.5">Structural & L1 Evidence</span>
          </div>

          {/* R Score */}
          <div className="rounded-xl border border-neutral-200/80 bg-neutral-50/70 p-3 dark:border-neutral-800 dark:bg-neutral-950/40 text-center">
            <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 block mb-1">
              R · Architecture Review
            </span>
            <span className="text-xl font-black font-mono text-neutral-900 dark:text-neutral-100">
              {report.overall_r ?? report.final_scores?.r ?? 0}
              <span className="text-xs text-neutral-400 font-normal">/100</span>
            </span>
            <span className="text-[10px] text-neutral-400 block mt-0.5">Rubric Dimensions</span>
          </div>

          {/* W Score */}
          <div className="rounded-xl border border-neutral-200/80 bg-neutral-50/70 p-3 dark:border-neutral-800 dark:bg-neutral-950/40 text-center">
            <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 block mb-1">
              W · Real-World Suitability
            </span>
            <span className="text-xl font-black font-mono text-neutral-900 dark:text-neutral-100">
              {report.overall_w !== null && report.overall_w !== undefined ? (
                <>
                  {report.overall_w}
                  <span className="text-xs text-neutral-400 font-normal">/100</span>
                </>
              ) : (
                <span className="text-sm font-semibold text-purple-500">PROVISIONAL</span>
              )}
            </span>
            <span className="text-[10px] text-neutral-400 block mt-0.5">Benchmark Patterns</span>
          </div>

          {/* D Penalty */}
          <div className="rounded-xl border border-neutral-200/80 bg-neutral-50/70 p-3 dark:border-neutral-800 dark:bg-neutral-950/40 text-center">
            <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 block mb-1">
              D · Penalty Deductions
            </span>
            <span className="text-xl font-black font-mono text-rose-500">
              -{report.overall_d ?? report.final_scores?.d ?? 0}
            </span>
            <span className="text-[10px] text-neutral-400 block mt-0.5">Verified Defect Points</span>
          </div>

          {/* Final S Composite Score */}
          <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/5 p-3 dark:border-indigo-500/30 dark:bg-indigo-950/20 text-center col-span-2 sm:col-span-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400 block mb-1">
              Final Composite S
            </span>
            <span className="text-2xl font-black font-mono text-indigo-600 dark:text-indigo-400">
              {report.final_scores?.overall ?? 0}
              <span className="text-xs text-neutral-400 font-normal">/100</span>
            </span>
            <span className="text-[10px] font-bold text-neutral-600 dark:text-neutral-300 block mt-0.5">
              {report.final_status}
            </span>
          </div>
        </div>
      </div>

      {/* ── REFERENCED REAL-WORLD SYSTEMS PANEL ── */}
      {report.references_used && report.references_used.length > 0 && (
        <div className="rounded-2xl border border-neutral-200/80 bg-white/70 p-5 backdrop-blur-md dark:border-neutral-800/80 dark:bg-neutral-900/60 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Globe className="h-4 w-4 text-indigo-500" />
              <h3 className="text-sm font-semibold uppercase tracking-wider text-neutral-700 dark:text-neutral-300">
                Grounding Reference Systems (Real-World Corpus)
              </h3>
            </div>
            <span className="rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-xs font-medium text-indigo-600 dark:text-indigo-400">
              {report.references_used.length} Reference Systems Selected
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {report.references_used.map((ref) => (
              <div
                key={ref.id}
                className="rounded-xl border border-neutral-200/80 bg-neutral-50/70 p-3.5 dark:border-neutral-800 dark:bg-neutral-950/40 text-xs space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-neutral-900 dark:text-neutral-100">
                    {ref.system_name}
                  </span>
                  <span className="font-mono text-[10px] text-neutral-400">{ref.id}</span>
                </div>

                {ref.match_reasons.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {ref.match_reasons.map((r, i) => (
                      <span
                        key={i}
                        className="rounded bg-neutral-200/80 px-1.5 py-0.2 text-[10px] text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300"
                      >
                        {r}
                      </span>
                    ))}
                  </div>
                )}

                {ref.scale_note && (
                  <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-2 text-[11px] text-amber-800 dark:text-amber-300">
                    <strong>Scale Note:</strong> {ref.scale_note}
                  </div>
                )}

                <div className="pt-1">
                  <span className="text-[10px] font-semibold uppercase text-neutral-400 block mb-1">
                    Sources / Citations:
                  </span>
                  {ref.sources && ref.sources.length > 0 ? (
                    <div className="space-y-1">
                      {ref.sources.map((src, i) => (
                        <div key={i} className="text-[11px] text-indigo-600 dark:text-indigo-400 truncate">
                          {src}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <span className="text-[11px] text-neutral-400 italic">no source cited</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── ARCHITECTURE CORRECTION PLAN (PART 2.1) ── */}
      <CorrectionPlanSection plan={effectiveCorrectionPlan} />

      {/* ── ARTIFACT BLUEPRINT CARDS (HLD + 5 LLDs) ── */}
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
            Artifact Evaluations & Evidence Scorecards
          </h3>
          <span className="text-xs text-neutral-400">
            Layer 0 Normalizer + L1 Tools + Rubric LLM + Real-World Benchmark
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(lastIteration.results).map(([artKey, res]) => (
            <ArtifactCard
              key={artKey}
              artifactKey={artKey}
              result={res}
              history={scoreHistory[artKey] || [res.score]}
              isExpanded={expandedArtifact === artKey}
              onToggle={() =>
                setExpandedArtifact(expandedArtifact === artKey ? null : artKey)
              }
            />
          ))}
        </div>
      </div>

      {/* ── CORRECTIONS TIMELINE ── */}
      {allCorrections.length > 0 && (
        <div className="rounded-2xl border border-neutral-200/80 bg-white/70 p-5 backdrop-blur-md dark:border-neutral-800/80 dark:bg-neutral-900/60 shadow-xs">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-indigo-500" />
              <h3 className="text-sm font-semibold uppercase tracking-wider text-neutral-700 dark:text-neutral-300">
                Autonomous Correction Timeline
              </h3>
            </div>
            <span className="rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-xs font-medium text-indigo-600 dark:text-indigo-400">
              {allCorrections.length} {allCorrections.length === 1 ? "Action" : "Actions"}
            </span>
          </div>

          <div className="space-y-3">
            {allCorrections.map(({ iterIndex, correction }, idx) => (
              <div
                key={idx}
                className="rounded-xl border border-neutral-200/80 bg-neutral-50/70 p-4 dark:border-neutral-800 dark:bg-neutral-950/40"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="rounded-md bg-neutral-200 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">
                      Round {iterIndex}
                    </span>
                    <span className="font-semibold text-sm text-neutral-900 dark:text-neutral-100">
                      {ARTIFACT_NAMES[correction.artifact] || correction.artifact}
                    </span>
                    <span
                      className={clsx(
                        "rounded-full px-2 py-0.5 text-[10px] font-bold border",
                        correction.regenerated_with_feedback
                          ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/30 dark:text-emerald-400"
                          : "bg-amber-500/10 text-amber-600 border-amber-500/30 dark:text-amber-400"
                      )}
                    >
                      {correction.regenerated_with_feedback
                        ? "Feedback-Driven"
                        : "Regenerated Without Feedback (Fallback)"}
                    </span>
                  </div>

                  {/* Score Transition */}
                  <div className="flex items-center gap-1.5 text-xs font-mono">
                    <span className="text-neutral-500">{correction.score_before}</span>
                    <span className="text-neutral-400">→</span>
                    <span
                      className={clsx(
                        "font-bold",
                        correction.score_after > correction.score_before
                          ? "text-emerald-500"
                          : "text-neutral-400"
                      )}
                    >
                      {correction.score_after}
                    </span>
                    <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold">
                      (+{correction.score_after - correction.score_before})
                    </span>
                  </div>
                </div>

                <p className="mt-2 text-xs text-neutral-600 dark:text-neutral-400 leading-relaxed">
                  {correction.action_summary}
                </p>

                {/* Diff stats */}
                <div className="mt-3 flex flex-wrap items-center gap-3 text-[11px]">
                  {correction.resolved.length > 0 && (
                    <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
                      <CheckCircle2 className="h-3 w-3" />
                      {correction.resolved.length} Findings Resolved
                    </span>
                  )}
                  {correction.unresolved.length > 0 && (
                    <span className="flex items-center gap-1 text-amber-600 dark:text-amber-400 font-medium">
                      <AlertTriangle className="h-3 w-3" />
                      {correction.unresolved.length} Findings Unresolved
                    </span>
                  )}
                  {correction.new_findings.length > 0 && (
                    <span className="flex items-center gap-1 text-rose-500 font-medium">
                      <XCircle className="h-3 w-3" />
                      {correction.new_findings.length} New Findings
                    </span>
                  )}
                  {correction.patterns_resolved && correction.patterns_resolved.length > 0 && (
                    <span className="flex items-center gap-1 text-indigo-600 dark:text-indigo-400 font-medium">
                      <CheckCircle2 className="h-3 w-3" />
                      {correction.patterns_resolved.length} Patterns Resolved: {correction.patterns_resolved.join(", ")}
                    </span>
                  )}
                  {correction.patterns_still_missing && correction.patterns_still_missing.length > 0 && (
                    <span className="flex items-center gap-1 text-orange-600 dark:text-orange-400 font-medium">
                      <AlertTriangle className="h-3 w-3" />
                      {correction.patterns_still_missing.length} Patterns Still Missing: {correction.patterns_still_missing.join(", ")}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── SUBCOMPONENTS ──

function StatusBadge({ status }: { status: string }) {
  switch (status) {
    case "ACCEPTED":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-3 py-0.5 text-xs font-bold text-emerald-600 border border-emerald-500/30 dark:text-emerald-400">
          <CheckCircle2 className="h-3.5 w-3.5" />
          ACCEPTED
        </span>
      );
    case "ACCEPTED_WITH_WARNINGS":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-3 py-0.5 text-xs font-bold text-amber-600 border border-amber-500/30 dark:text-amber-400">
          <AlertTriangle className="h-3.5 w-3.5" />
          ACCEPTED WITH WARNINGS
        </span>
      );
    case "PROVISIONAL":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-purple-500/10 px-3 py-0.5 text-xs font-bold text-purple-600 border border-purple-500/30 dark:text-purple-400">
          <Info className="h-3.5 w-3.5" />
          PROVISIONAL
        </span>
      );
    case "REJECTED":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-500/10 px-3 py-0.5 text-xs font-bold text-rose-600 border border-rose-500/30 dark:text-rose-400">
          <XCircle className="h-3.5 w-3.5" />
          REJECTED
        </span>
      );
    case "UNRESOLVED":
    default:
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-500/10 px-3 py-0.5 text-xs font-bold text-rose-600 border border-rose-500/30 dark:text-rose-400">
          <XCircle className="h-3.5 w-3.5" />
          UNRESOLVED
        </span>
      );
  }
}

function ArtifactCard({
  artifactKey,
  result,
  history,
  isExpanded,
  onToggle,
}: {
  artifactKey: string;
  result: ArtifactResult;
  history: number[];
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const missingComponents = result.dimensions.flatMap((d) => d.missing || []);
  const [patternFilter, setPatternFilter] = useState<string>("ALL");

  const rw = result.real_world;
  const filteredAssessments = rw?.assessments.filter((a) => {
    if (patternFilter === "ALL") return true;
    return a.status === patternFilter;
  }) || [];

  const missingAtScale = rw?.assessments.filter(
    (a) => a.status === "MISSING" || a.status === "PARTIAL"
  ) || [];

  return (
    <div
      className={clsx(
        "flex flex-col rounded-2xl border transition-all duration-200 bg-white/70 backdrop-blur-md dark:bg-neutral-900/60 shadow-xs",
        isExpanded
          ? "border-indigo-500/50 dark:border-indigo-500/50 ring-1 ring-indigo-500/20 md:col-span-2 lg:col-span-3"
          : "border-neutral-200/80 dark:border-neutral-800/80 hover:border-neutral-300 dark:hover:border-neutral-700"
      )}
    >
      {/* Card Header */}
      <div className="p-4 flex items-start justify-between gap-3 border-b border-neutral-100 dark:border-neutral-800/60">
        <div className="flex items-center gap-2.5">
          <div className="rounded-xl bg-neutral-100 p-2 dark:bg-neutral-800">
            {ARTIFACT_ICONS[artifactKey] || <Layers className="h-4 w-4" />}
          </div>
          <div>
            <h4 className="text-sm font-bold text-neutral-900 dark:text-neutral-100">
              {ARTIFACT_NAMES[artifactKey] || artifactKey.toUpperCase()}
            </h4>
            <div className="flex items-center gap-2 mt-0.5">
              <span
                className={clsx(
                  "rounded-full px-2 py-0.2 text-[10px] font-bold uppercase border",
                  result.verdict === "ACCEPTED"
                    ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/30 dark:text-emerald-400"
                    : result.verdict === "PROVISIONAL"
                    ? "bg-purple-500/10 text-purple-600 border-purple-500/30 dark:text-purple-400"
                    : "bg-rose-500/10 text-rose-600 border-rose-500/30 dark:text-rose-400"
                )}
              >
                {result.verdict}
              </span>

              {history.length > 1 && (
                <span className="text-[11px] font-mono text-neutral-400">
                  {history.join(" → ")}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Score pill */}
        <div className="flex flex-col items-end">
          <span
            className={clsx(
              "text-xl font-black font-mono tracking-tight",
              result.score >= 80
                ? "text-emerald-600 dark:text-emerald-400"
                : result.score >= 60
                ? "text-amber-500"
                : "text-rose-500"
            )}
          >
            {result.score}
            <span className="text-xs text-neutral-400 font-normal">/100</span>
          </span>
          {result.reviewer_status !== "ok" && (
            <span className="text-[9px] font-semibold text-purple-500 uppercase tracking-wider">
              {result.reviewer_status}
            </span>
          )}
        </div>
      </div>

      {/* Reviewer Status Warning if unavailable */}
      {result.reviewer_status !== "ok" && (
        <div className="bg-purple-500/10 border-b border-purple-500/20 px-4 py-1.5 text-[11px] text-purple-700 dark:text-purple-300 flex items-center gap-1.5">
          <Info className="h-3.5 w-3.5 shrink-0" />
          <span>Reviewer LLM unavailable. Scored via Layer 0 & 1 Evidence.</span>
        </div>
      )}

      {/* Body: Dimension Bars & Highlights */}
      <div className="p-4 space-y-4 flex-1">
        {/* Composite Score Breakdown */}
        <div className="rounded-xl border border-neutral-200/80 bg-neutral-50/70 p-2.5 text-xs dark:border-neutral-800 dark:bg-neutral-950/40">
          <div className="flex flex-wrap items-center justify-between text-[11px] font-mono text-neutral-600 dark:text-neutral-400">
            <span>C (Correctness): <strong>{result.c_score ?? 100}/100</strong></span>
            <span>•</span>
            <span>R (Rubric): <strong>{result.r_score ?? result.rubric_score ?? result.score}/100</strong></span>
            <span>•</span>
            <span>W (Real-World): <strong>{rw?.score !== null && rw?.score !== undefined ? `${rw.score}/100` : "N/A"}</strong></span>
            <span>•</span>
            <span>Final S: <strong className="text-indigo-600 dark:text-indigo-400 font-bold">{result.score}/100</strong></span>
          </div>
        </div>

        {/* Dimension Bars */}
        <div className="space-y-2">
          {result.dimensions.map((dim) => {
            const isBest = result.best_dimension === dim.id;
            const isWeakest = result.weakest_dimension === dim.id && result.score < 100;
            const pct = Math.round((dim.score / 5) * 100);

            return (
              <div key={dim.id} className="text-xs">
                <div className="flex items-center justify-between mb-1">
                  <span className="flex items-center gap-1.5 font-medium text-neutral-700 dark:text-neutral-300">
                    {dim.label}
                    {isBest && (
                      <span className="rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 px-1.5 py-0.2 text-[9px] font-bold">
                        Best
                      </span>
                    )}
                    {isWeakest && (
                      <span className="rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30 px-1.5 py-0.2 text-[9px] font-bold">
                        Weakest
                      </span>
                    )}
                  </span>
                  <span className="font-mono text-neutral-500 text-[11px]">
                    {dim.score}/5
                  </span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-neutral-100 dark:bg-neutral-800 overflow-hidden">
                  <div
                    className={clsx(
                      "h-full rounded-full transition-all duration-300",
                      dim.score >= 4
                        ? "bg-emerald-500"
                        : dim.score >= 3
                        ? "bg-indigo-500"
                        : dim.score >= 2
                        ? "bg-amber-500"
                        : "bg-rose-500"
                    )}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>

        {/* ── REAL-WORLD BENCHMARK PANEL ── */}
        <div className="rounded-xl border border-indigo-500/20 bg-indigo-500/5 p-3.5 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-1.5">
              <BookOpen className="h-4 w-4 text-indigo-500" />
              <h5 className="text-xs font-bold uppercase tracking-wider text-neutral-800 dark:text-neutral-200">
                Real-World Benchmark
              </h5>
              <div
                className="group relative cursor-help text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300"
                title="Measures alignment with transferable practices from reference systems, not similarity to their architecture."
              >
                <HelpCircle className="h-3.5 w-3.5" />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span
                className={clsx(
                  "rounded-full px-2 py-0.5 text-[10px] font-bold border capitalize",
                  rw?.confidence === "normal"
                    ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/30 dark:text-emerald-400"
                    : rw?.confidence === "low"
                    ? "bg-amber-500/10 text-amber-600 border-amber-500/30 dark:text-amber-400"
                    : "bg-neutral-500/10 text-neutral-600 border-neutral-500/30 dark:text-neutral-400"
                )}
              >
                {rw?.confidence || "unavailable"} confidence
              </span>
              <span className="font-mono text-xs font-bold text-indigo-600 dark:text-indigo-400">
                {rw?.score !== null && rw?.score !== undefined ? `${rw.score}/100` : "Unavailable"}
              </span>
            </div>
          </div>

          <p className="text-[11px] text-neutral-600 dark:text-neutral-400 leading-relaxed italic">
            Measures alignment with transferable practices from reference systems, not similarity to their architecture.
          </p>

          {/* Counts pill row */}
          {rw && (
            <div className="flex flex-wrap gap-1.5 text-[10px] font-medium">
              <span className="rounded bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 px-2 py-0.5 border border-emerald-500/20">
                {rw.counts.aligned} Aligned
              </span>
              <span className="rounded bg-amber-500/10 text-amber-700 dark:text-amber-400 px-2 py-0.5 border border-amber-500/20">
                {rw.counts.partial} Partial
              </span>
              <span className="rounded bg-rose-500/10 text-rose-700 dark:text-rose-400 px-2 py-0.5 border border-rose-500/20">
                {rw.counts.missing} Missing
              </span>
              <span className="rounded bg-purple-500/10 text-purple-700 dark:text-purple-400 px-2 py-0.5 border border-purple-500/20">
                {rw.counts.justified_divergence} Justified Divergence
              </span>
              <span className="rounded bg-neutral-200 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 px-2 py-0.5">
                {rw.counts.not_applicable} Not Applicable
              </span>
              {rw.counts.downgraded_unverified > 0 && (
                <span className="rounded bg-orange-500/10 text-orange-700 dark:text-orange-400 px-2 py-0.5 border border-orange-500/20">
                  {rw.counts.downgraded_unverified} Unverified Downgraded
                </span>
              )}
            </div>
          )}

          {/* Missing at your scale callout */}
          {missingAtScale.length > 0 && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-2.5 text-xs space-y-1.5">
              <div className="font-bold text-amber-900 dark:text-amber-200 text-[11px] uppercase tracking-wider flex items-center gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5" />
                Missing At Your System Scale ({missingAtScale.length})
              </div>
              <ul className="list-disc pl-4 space-y-1 text-[11px] text-amber-800 dark:text-amber-300">
                {missingAtScale.map((p) => (
                  <li key={p.pattern_id}>
                    <strong>{p.pattern_name}</strong> ({p.system_name}, Priority P{p.priority}): {p.justification}{" "}
                    <span className="italic text-neutral-500 dark:text-neutral-400">
                      (Address at this system's scale; do not copy the reference architecture).
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Pattern Table with Filters */}
          {isExpanded && rw && rw.assessments.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-indigo-500/10">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-neutral-700 dark:text-neutral-300">
                  Evaluated Patterns ({rw.assessments.length})
                </span>
                <div className="flex flex-wrap gap-1">
                  {["ALL", "ALIGNED", "PARTIAL", "MISSING", "JUSTIFIED_DIVERGENCE", "NOT_APPLICABLE"].map((f) => (
                    <button
                      key={f}
                      onClick={() => setPatternFilter(f)}
                      className={clsx(
                        "rounded px-1.5 py-0.5 text-[10px] font-mono transition-colors cursor-pointer",
                        patternFilter === f
                          ? "bg-indigo-600 text-white"
                          : "bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-neutral-600 dark:text-neutral-400"
                      )}
                    >
                      {f}
                    </button>
                  ))}
                </div>
              </div>

              <div className="overflow-x-auto rounded-lg border border-neutral-200 dark:border-neutral-800">
                <table className="w-full text-left text-[11px] divide-y divide-neutral-200 dark:divide-neutral-800">
                  <thead className="bg-neutral-100/60 dark:bg-neutral-800/60 text-neutral-600 dark:text-neutral-400 font-semibold">
                    <tr>
                      <th className="p-2">Pattern</th>
                      <th className="p-2">Reference</th>
                      <th className="p-2">Category</th>
                      <th className="p-2">Priority</th>
                      <th className="p-2">Status</th>
                      <th className="p-2">Evidence / Rationale</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800/60 font-mono">
                    {filteredAssessments.map((a) => (
                      <tr key={a.pattern_id} className="hover:bg-neutral-50 dark:hover:bg-neutral-800/30">
                        <td className="p-2 font-medium font-sans text-neutral-900 dark:text-neutral-100">
                          {a.pattern_name}
                          <span className="block text-[10px] text-neutral-400 font-mono">{a.pattern_id}</span>
                        </td>
                        <td className="p-2 text-neutral-600 dark:text-neutral-400 font-sans">{a.system_name}</td>
                        <td className="p-2 uppercase text-[10px] text-neutral-500">{a.category}</td>
                        <td className="p-2 text-neutral-500">P{a.priority}</td>
                        <td className="p-2">
                          <PatternStatusChip status={a.status} />
                        </td>
                        <td className="p-2 font-sans text-neutral-700 dark:text-neutral-300">
                          <p className="text-[11px] leading-tight">{a.justification}</p>
                          {a.evidence_path && (
                            <span className="block text-[10px] font-mono text-indigo-600 dark:text-indigo-400 mt-0.5 truncate">
                              Evidence: {a.evidence_path}
                            </span>
                          )}
                          {a.requirement_refs && a.requirement_refs.length > 0 && (
                            <span className="block text-[10px] text-neutral-400 mt-0.5">
                              Refs: {a.requirement_refs.join(", ")}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Missing Components */}
        {missingComponents.length > 0 && (
          <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-3">
            <h5 className="text-[11px] font-bold uppercase tracking-wider text-amber-700 dark:text-amber-400 mb-1.5">
              Missing Components ({missingComponents.length})
            </h5>
            <div className="flex flex-wrap gap-1.5">
              {missingComponents.map((item, i) => (
                <span
                  key={i}
                  className="rounded-md bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 text-[11px] text-amber-800 dark:text-amber-300"
                >
                  {item}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Why the Score is Low / Top Findings */}
        {result.findings.length > 0 && (
          <div className="space-y-2 pt-1">
            <h5 className="text-[11px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
              Why the score is low ({result.findings.length} Findings)
            </h5>
            <div className="space-y-2">
              {result.findings.slice(0, isExpanded ? 15 : 2).map((f) => (
                <div
                  key={f.id}
                  className="rounded-lg border border-neutral-200/80 bg-neutral-50/70 p-2.5 text-xs dark:border-neutral-800 dark:bg-neutral-950/40"
                >
                  <div className="flex flex-wrap items-center gap-1.5 mb-1">
                    <SeverityBadge severity={f.severity} />
                    <span className="rounded bg-neutral-200 dark:bg-neutral-800 px-1.5 py-0.2 text-[10px] font-mono text-neutral-700 dark:text-neutral-300">
                      {f.source}
                    </span>
                    <span className="font-mono text-[10px] text-neutral-400">
                      {f.rule_id}
                    </span>
                  </div>
                  <p className="text-neutral-800 dark:text-neutral-200 font-medium">
                    {f.message}
                  </p>
                  {f.evidence_path && (
                    <div className="mt-1 text-[10px] font-mono text-neutral-500 dark:text-neutral-400 truncate">
                      Evidence: {f.evidence_path}
                    </div>
                  )}
                  {f.suggested_fix && (
                    <div className="mt-1 text-[11px] text-indigo-600 dark:text-indigo-400 bg-indigo-500/5 rounded p-1.5 border border-indigo-500/10">
                      <strong>Fix:</strong> {f.suggested_fix}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Card Footer toggle */}
      <div className="border-t border-neutral-100 p-3 text-center dark:border-neutral-800/60">
        <button
          onClick={onToggle}
          className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline cursor-pointer"
        >
          {isExpanded ? "Collapse Details" : "Inspect All Findings, Rubric & Real-World Benchmark"}
          {isExpanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        </button>
      </div>
    </div>
  );
}

function PatternStatusChip({ status }: { status: string }) {
  switch (status) {
    case "ALIGNED":
      return (
        <span className="rounded-full bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 text-[10px] font-bold text-emerald-600 dark:text-emerald-400">
          ALIGNED
        </span>
      );
    case "PARTIAL":
      return (
        <span className="rounded-full bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 text-[10px] font-bold text-amber-600 dark:text-amber-400">
          PARTIAL
        </span>
      );
    case "JUSTIFIED_DIVERGENCE":
      return (
        <span className="rounded-full bg-purple-500/10 border border-purple-500/30 px-2 py-0.5 text-[10px] font-bold text-purple-600 dark:text-purple-400">
          JUSTIFIED
        </span>
      );
    case "NOT_APPLICABLE":
      return (
        <span className="rounded-full bg-neutral-200 dark:bg-neutral-800 px-2 py-0.5 text-[10px] font-bold text-neutral-600 dark:text-neutral-400">
          N/A
        </span>
      );
    case "MISSING":
    default:
      return (
        <span className="rounded-full bg-rose-500/10 border border-rose-500/30 px-2 py-0.5 text-[10px] font-bold text-rose-600 dark:text-rose-400">
          MISSING
        </span>
      );
  }
}

function SeverityBadge({ severity }: { severity: string }) {
  switch (severity) {
    case "critical":
      return (
        <span className="rounded-full bg-rose-500/10 border border-rose-500/30 px-2 py-0.2 text-[10px] font-bold uppercase text-rose-600 dark:text-rose-400">
          Critical
        </span>
      );
    case "high":
      return (
        <span className="rounded-full bg-orange-500/10 border border-orange-500/30 px-2 py-0.2 text-[10px] font-bold uppercase text-orange-600 dark:text-orange-400">
          High
        </span>
      );
    case "medium":
      return (
        <span className="rounded-full bg-amber-500/10 border border-amber-500/30 px-2 py-0.2 text-[10px] font-bold uppercase text-amber-600 dark:text-amber-400">
          Medium
        </span>
      );
    case "low":
    default:
      return (
        <span className="rounded-full bg-blue-500/10 border border-blue-500/30 px-2 py-0.2 text-[10px] font-bold uppercase text-blue-600 dark:text-blue-400">
          Low
        </span>
      );
  }
}
