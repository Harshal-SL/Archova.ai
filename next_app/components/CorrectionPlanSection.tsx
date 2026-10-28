"use client";

import React, { useState } from "react";
import {
  Wrench,
  AlertTriangle,
  CheckCircle2,
  FileText,
  Layers,
  ArrowRight,
  Filter,
  Sparkles,
  ShieldAlert,
  Server,
  Database,
  Layout,
  Lock,
  Cloud,
  FileCode,
  Check,
  X,
  RotateCcw,
  Info,
  ShieldCheck,
  Ban,
  Clock,
  XCircle,
  Code2,
  CheckCheck,
  ChevronDown,
  ChevronRight,
  LayoutGrid,
  List,
} from "lucide-react";
import type {
  CorrectionPlan,
  CorrectionItem,
  SupportedArtifact,
  ImpactType,
  CorrectionItemStatus,
} from "@/lib/correction-planner";
import type { TargetedCorrectionResponse } from "@/lib/ai-engine-client";
import { useAppStore } from "@/lib/store";
import clsx from "clsx";

const ARTIFACT_ICONS: Record<SupportedArtifact, React.ReactNode> = {
  ARSRS: <FileCode className="h-3.5 w-3.5 text-purple-400" />,
  HLD: <Layers className="h-3.5 w-3.5 text-indigo-400" />,
  "Backend LLD": <Server className="h-3.5 w-3.5 text-blue-400" />,
  "Database LLD": <Database className="h-3.5 w-3.5 text-amber-400" />,
  "Frontend LLD": <Layout className="h-3.5 w-3.5 text-teal-400" />,
  "Security LLD": <Lock className="h-3.5 w-3.5 text-rose-400" />,
  "Cloud LLD": <Cloud className="h-3.5 w-3.5 text-sky-400" />,
};

const ARTIFACT_ORDER: SupportedArtifact[] = [
  "ARSRS",
  "HLD",
  "Backend LLD",
  "Database LLD",
  "Frontend LLD",
  "Security LLD",
  "Cloud LLD",
];

const ARTIFACT_TITLES: Record<SupportedArtifact, { name: string; subtitle: string }> = {
  ARSRS: { name: "Architecture Requirements (ARSRS)", subtitle: "Functional & Non-Functional Specifications" },
  HLD: { name: "High-Level Architecture (HLD)", subtitle: "Topology, Major Services & Boundaries" },
  "Backend LLD": { name: "Backend Service LLD", subtitle: "API Endpoints, Concurrency & Business Controllers" },
  "Database LLD": { name: "Database & Persistence LLD", subtitle: "Data Models, Indexes & Lock Semantics" },
  "Frontend LLD": { name: "Frontend Architecture LLD", subtitle: "State Management, Routing & Client Contracts" },
  "Security LLD": { name: "Zero-Trust Security LLD", subtitle: "Authentication, RBAC & Security Boundaries" },
  "Cloud LLD": { name: "Cloud Infrastructure LLD", subtitle: "Terraform Manifests, VPC Topology & Scaling" },
};

interface CorrectionPlanSectionProps {
  plan: CorrectionPlan | null | undefined;
}

export default function CorrectionPlanSection({ plan }: CorrectionPlanSectionProps) {
  const [activeFilter, setActiveFilter] = useState<
    "ALL" | "ACTIONABLE" | "CRITICAL_HIGH" | "REVIEW" | "APPROVED" | "DISMISSED"
  >("ALL");
  const [selectedArtifact, setSelectedArtifact] = useState<string>("ALL");
  const [viewMode, setViewMode] = useState<"GROUPED" | "LIST">("GROUPED");
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({});

  const toggleGroupCollapse = (artifact: string) => {
    setCollapsedGroups((prev) => ({
      ...prev,
      [artifact]: !prev[artifact],
    }));
  };

  const {
    approveCorrectionPlanItem,
    markCorrectionForManualReview,
    dismissCorrectionPlanItem,
    resetCorrectionDecision,
    isProcessingCorrectionAction,
    correctionActionMessage,
    clearCorrectionActionMessage,
    activeCorrectionDraft,
    isExecutingAiCorrection,
    acceptCorrectionDraft,
    rejectCorrectionDraft,
    dismissCorrectionDraftModal,
  } = useAppStore();

  if (!plan) {
    return null;
  }

  const items = plan.items || [];

  const approvedCount = items.filter((i) => i.status === "APPROVED_FOR_CORRECTION").length;
  const dismissedCount = items.filter((i) => i.status === "DISMISSED").length;

  const statusFiltered = items.filter((item) => {
    if (activeFilter === "ACTIONABLE") return item.is_actionable && item.status !== "DISMISSED";
    if (activeFilter === "CRITICAL_HIGH")
      return (item.severity === "critical" || item.severity === "high") && item.status !== "DISMISSED";
    if (activeFilter === "REVIEW")
      return item.status === "MANUAL_REVIEW_REQUIRED" || item.requires_manual_review || !item.is_supported_by_evidence;
    if (activeFilter === "APPROVED") return item.status === "APPROVED_FOR_CORRECTION";
    if (activeFilter === "DISMISSED") return item.status === "DISMISSED";
    return true;
  });

  const filteredItems = statusFiltered.filter((item) => {
    if (selectedArtifact === "ALL") return true;
    return item.affected_artifact === selectedArtifact;
  });

  const presentArtifacts = ARTIFACT_ORDER.filter((art) =>
    items.some((i) => i.affected_artifact === art)
  );

  const itemsByArtifact: Record<SupportedArtifact, CorrectionItem[]> = {
    ARSRS: [],
    HLD: [],
    "Backend LLD": [],
    "Database LLD": [],
    "Frontend LLD": [],
    "Security LLD": [],
    "Cloud LLD": [],
  };

  filteredItems.forEach((item) => {
    if (itemsByArtifact[item.affected_artifact]) {
      itemsByArtifact[item.affected_artifact].push(item);
    }
  });

  const activeGroupedArtifacts = ARTIFACT_ORDER.filter(
    (art) => itemsByArtifact[art] && itemsByArtifact[art].length > 0
  );

  const handleApproveAllForArtifact = (artifactItems: CorrectionItem[]) => {
    const pendingActionable = artifactItems.filter(
      (i) => i.is_actionable && i.status !== "APPROVED_FOR_CORRECTION" && i.status !== "DISMISSED"
    );
    pendingActionable.forEach((item) => {
      approveCorrectionPlanItem(item.id);
    });
  };

  return (
    <div className="rounded-2xl border border-neutral-200/80 bg-white/70 p-5 backdrop-blur-md dark:border-neutral-800/80 dark:bg-neutral-900/60 shadow-xs space-y-4">
      {/* ── HEADER ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-neutral-200/60 pb-4 dark:border-neutral-800/60">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">
            <Wrench className="h-4.5 w-4.5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-neutral-900 dark:text-neutral-100">
                Evidence-Based Architecture Correction Plan
              </h3>
              <span className="rounded-full bg-neutral-100 px-2 py-0.5 text-[10px] font-mono font-bold text-neutral-500 dark:bg-neutral-800 dark:text-neutral-400">
                Part 2.2.1 Review Workflow
              </span>
            </div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">
              Review findings, approve proposed corrections, understand dependencies, and manage architectural review decisions safely.
            </p>
          </div>
        </div>

        <div>
          <PlanStatusBadge status={plan.status} />
        </div>
      </div>

      {/* ── API CAPABILITY & TRANSPARENCY NOTICE ── */}
      <div className="rounded-xl border border-blue-500/25 bg-blue-500/5 p-3 text-xs dark:border-blue-500/20 dark:bg-blue-950/20 flex items-start gap-2.5">
        <Info className="h-4 w-4 text-blue-500 shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <span className="font-semibold text-blue-900 dark:text-blue-200">
            Targeted AI Correction Capability Status: Safe Review Mode
          </span>
          <p className="text-blue-800/80 dark:text-blue-300/80 text-[11px] leading-relaxed">
            The current AI Engine API supports full architecture generation and additive feature evolution, but does not provide an isolated single-finding correction endpoint. Approved correction plans are recorded for review without modifying architecture artifacts or creating false versions.
          </p>
        </div>
      </div>

      {/* ── ACTION NOTIFICATION BANNER ── */}
      {correctionActionMessage && (
        <div
          className={clsx(
            "rounded-xl border p-3 text-xs flex items-center justify-between gap-2",
            correctionActionMessage.type === "warning"
              ? "border-amber-500/30 bg-amber-500/10 text-amber-800 dark:text-amber-300"
              : correctionActionMessage.type === "error"
              ? "border-rose-500/30 bg-rose-500/10 text-rose-800 dark:text-rose-300"
              : "border-indigo-500/30 bg-indigo-500/10 text-indigo-800 dark:text-indigo-300"
          )}
        >
          <div className="flex items-center gap-2">
            {correctionActionMessage.type === "warning" ? (
              <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />
            ) : correctionActionMessage.type === "error" ? (
              <Ban className="h-4 w-4 text-rose-500 shrink-0" />
            ) : (
              <CheckCircle2 className="h-4 w-4 text-indigo-500 shrink-0" />
            )}
            <span className="font-medium">{correctionActionMessage.text}</span>
          </div>
          <button
            onClick={clearCorrectionActionMessage}
            className="text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200 cursor-pointer p-1"
            title="Dismiss message"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* ── AI CORRECTION GENERATING INDICATOR (Part 2.2.2) ── */}
      {isExecutingAiCorrection && (
        <div className="rounded-xl border border-indigo-500/40 bg-indigo-500/10 p-4 dark:border-indigo-500/30 dark:bg-indigo-950/40 animate-pulse flex items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-sm shrink-0">
              <Sparkles className="h-4.5 w-4.5 animate-spin" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-indigo-950 dark:text-indigo-100 flex items-center gap-2">
                Synthesizing Targeted AI Architecture Correction
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-700 dark:text-indigo-300">
                  OpenRouter Free Tier
                </span>
              </h4>
              <p className="text-xs text-indigo-800 dark:text-indigo-300 mt-0.5">
                Executing isolated model inference on the approved defect. Baseline architecture invariants and unrelated decisions are strictly preserved.
              </p>
            </div>
          </div>
          <span className="text-xs font-mono font-bold text-indigo-600 dark:text-indigo-400 animate-pulse shrink-0">
            IN_PROGRESS...
          </span>
        </div>
      )}

      {/* ── TARGETED CORRECTION DRAFT REVIEW PANEL (Part 2.2.2) ── */}
      {activeCorrectionDraft && (
        <CorrectionDraftReviewCard
          draft={activeCorrectionDraft}
          onAccept={() => acceptCorrectionDraft(activeCorrectionDraft.operation_id)}
          onReject={() => rejectCorrectionDraft(activeCorrectionDraft.operation_id)}
          onDismiss={dismissCorrectionDraftModal}
          isProcessing={isProcessingCorrectionAction}
        />
      )}

      {/* ── SUMMARY BANNER ── */}
      <div
        className={clsx(
          "rounded-xl border p-3.5 text-xs",
          plan.status === "NO_ACTION_REQUIRED"
            ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-800 dark:text-emerald-300"
            : plan.status === "MANUAL_REVIEW_REQUIRED"
            ? "border-rose-500/30 bg-rose-500/10 text-rose-800 dark:text-rose-300"
            : plan.status === "PROVISIONAL_STAGE_UNAVAILABLE"
            ? "border-purple-500/30 bg-purple-500/10 text-purple-800 dark:text-purple-300"
            : "border-indigo-500/30 bg-indigo-500/10 text-indigo-800 dark:text-indigo-300"
        )}
      >
        <p className="font-medium leading-relaxed">{plan.summary}</p>
      </div>

      {/* ── METRIC TILES BAR ── */}
      <div className="grid grid-cols-2 sm:grid-cols-6 gap-2.5">
        <div className="rounded-xl border border-neutral-200/70 bg-neutral-50/60 p-2.5 dark:border-neutral-800 dark:bg-neutral-950/40 text-center">
          <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 block">
            Actionable
          </span>
          <span className="text-lg font-black font-mono text-indigo-600 dark:text-indigo-400">
            {plan.actionable_count}
          </span>
        </div>

        <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-2.5 dark:border-rose-500/20 dark:bg-rose-950/20 text-center">
          <span className="text-[10px] font-bold uppercase tracking-wider text-rose-500 block">
            Critical
          </span>
          <span className="text-lg font-black font-mono text-rose-600 dark:text-rose-400">
            {plan.items_by_severity.critical}
          </span>
        </div>

        <div className="rounded-xl border border-orange-500/20 bg-orange-500/5 p-2.5 dark:border-orange-500/20 dark:bg-orange-950/20 text-center">
          <span className="text-[10px] font-bold uppercase tracking-wider text-orange-500 block">
            High
          </span>
          <span className="text-lg font-black font-mono text-orange-600 dark:text-orange-400">
            {plan.items_by_severity.high}
          </span>
        </div>

        <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-2.5 dark:border-amber-500/20 dark:bg-amber-950/20 text-center">
          <span className="text-[10px] font-bold uppercase tracking-wider text-amber-500 block">
            Medium
          </span>
          <span className="text-lg font-black font-mono text-amber-600 dark:text-amber-400">
            {plan.items_by_severity.medium}
          </span>
        </div>

        <div className="rounded-xl border border-purple-500/20 bg-purple-500/5 p-2.5 dark:border-purple-500/20 dark:bg-purple-950/20 text-center">
          <span className="text-[10px] font-bold uppercase tracking-wider text-purple-500 block">
            Approved
          </span>
          <span className="text-lg font-black font-mono text-purple-600 dark:text-purple-400">
            {approvedCount}
          </span>
        </div>

        <div className="rounded-xl border border-neutral-300/40 bg-neutral-100/50 p-2.5 dark:border-neutral-800 dark:bg-neutral-900/40 text-center">
          <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-500 block">
            Total Items
          </span>
          <span className="text-lg font-black font-mono text-neutral-700 dark:text-neutral-300">
            {items.length}
          </span>
        </div>
      </div>

      {/* ── FILTER CHIPS BAR & VIEW MODE TOGGLE ── */}
      {items.length > 0 && (
        <div className="space-y-2.5 pt-1 border-t border-neutral-100 dark:border-neutral-800/60">
          <div className="flex flex-wrap items-center justify-between gap-2.5">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="text-xs font-semibold text-neutral-500 dark:text-neutral-400 flex items-center gap-1.5 mr-1">
                <Filter className="h-3.5 w-3.5 text-neutral-400" />
                Filter:
              </span>
              <button
                onClick={() => setActiveFilter("ALL")}
                className={clsx(
                  "rounded-lg px-2.5 py-1 text-xs font-medium transition-colors cursor-pointer",
                  activeFilter === "ALL"
                    ? "bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900"
                    : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200 dark:bg-neutral-800 dark:text-neutral-300 dark:hover:bg-neutral-700"
                )}
              >
                All ({items.length})
              </button>
              <button
                onClick={() => setActiveFilter("ACTIONABLE")}
                className={clsx(
                  "rounded-lg px-2.5 py-1 text-xs font-medium transition-colors cursor-pointer",
                  activeFilter === "ACTIONABLE"
                    ? "bg-indigo-600 text-white"
                    : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200 dark:bg-neutral-800 dark:text-neutral-300 dark:hover:bg-neutral-700"
                )}
              >
                Actionable ({plan.actionable_count})
              </button>
              <button
                onClick={() => setActiveFilter("CRITICAL_HIGH")}
                className={clsx(
                  "rounded-lg px-2.5 py-1 text-xs font-medium transition-colors cursor-pointer",
                  activeFilter === "CRITICAL_HIGH"
                    ? "bg-rose-600 text-white"
                    : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200 dark:bg-neutral-800 dark:text-neutral-300 dark:hover:bg-neutral-700"
                )}
              >
                Critical & High ({plan.items_by_severity.critical + plan.items_by_severity.high})
              </button>
              <button
                onClick={() => setActiveFilter("REVIEW")}
                className={clsx(
                  "rounded-lg px-2.5 py-1 text-xs font-medium transition-colors cursor-pointer",
                  activeFilter === "REVIEW"
                    ? "bg-purple-600 text-white"
                    : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200 dark:bg-neutral-800 dark:text-neutral-300 dark:hover:bg-neutral-700"
                )}
              >
                Manual Review ({plan.requires_review_count})
              </button>
              {approvedCount > 0 && (
                <button
                  onClick={() => setActiveFilter("APPROVED")}
                  className={clsx(
                    "rounded-lg px-2.5 py-1 text-xs font-medium transition-colors cursor-pointer",
                    activeFilter === "APPROVED"
                      ? "bg-teal-600 text-white"
                      : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200 dark:bg-neutral-800 dark:text-neutral-300 dark:hover:bg-neutral-700"
                  )}
                >
                  Approved ({approvedCount})
                </button>
              )}
              {dismissedCount > 0 && (
                <button
                  onClick={() => setActiveFilter("DISMISSED")}
                  className={clsx(
                    "rounded-lg px-2.5 py-1 text-xs font-medium transition-colors cursor-pointer",
                    activeFilter === "DISMISSED"
                      ? "bg-neutral-700 text-white"
                      : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200 dark:bg-neutral-800 dark:text-neutral-300 dark:hover:bg-neutral-700"
                  )}
                >
                  Dismissed ({dismissedCount})
                </button>
              )}
            </div>

            {/* View Mode Toggle */}
            <div className="flex items-center gap-1 bg-neutral-100 dark:bg-neutral-800/80 p-0.5 rounded-lg border border-neutral-200/60 dark:border-neutral-700/60">
              <button
                onClick={() => setViewMode("GROUPED")}
                className={clsx(
                  "flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors cursor-pointer",
                  viewMode === "GROUPED"
                    ? "bg-white text-neutral-900 shadow-xs dark:bg-neutral-900 dark:text-neutral-100 font-semibold"
                    : "text-neutral-500 hover:text-neutral-800 dark:text-neutral-400 dark:hover:text-neutral-200"
                )}
                title="Group corrections by architecture artifact"
              >
                <LayoutGrid className="h-3.5 w-3.5" />
                <span>Group by Artifact</span>
              </button>
              <button
                onClick={() => setViewMode("LIST")}
                className={clsx(
                  "flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors cursor-pointer",
                  viewMode === "LIST"
                    ? "bg-white text-neutral-900 shadow-xs dark:bg-neutral-900 dark:text-neutral-100 font-semibold"
                    : "text-neutral-500 hover:text-neutral-800 dark:text-neutral-400 dark:hover:text-neutral-200"
                )}
                title="Show all corrections in a flat list"
              >
                <List className="h-3.5 w-3.5" />
                <span>List View</span>
              </button>
            </div>
          </div>

          {/* Artifact Filter Bar (Quick Select) */}
          {presentArtifacts.length > 1 && (
            <div className="flex flex-wrap items-center gap-1.5 pt-1">
              <span className="text-[11px] font-semibold text-neutral-400 dark:text-neutral-500 mr-1">
                Artifact:
              </span>
              <button
                onClick={() => setSelectedArtifact("ALL")}
                className={clsx(
                  "rounded-md px-2 py-0.5 text-xs font-medium transition-colors cursor-pointer",
                  selectedArtifact === "ALL"
                    ? "bg-indigo-600 text-white"
                    : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200 dark:bg-neutral-800 dark:text-neutral-300 dark:hover:bg-neutral-700"
                )}
              >
                All Artifacts ({statusFiltered.length})
              </button>
              {presentArtifacts.map((art) => {
                const count = statusFiltered.filter((i) => i.affected_artifact === art).length;
                if (count === 0 && selectedArtifact !== art) return null;
                return (
                  <button
                    key={art}
                    onClick={() => setSelectedArtifact(selectedArtifact === art ? "ALL" : art)}
                    className={clsx(
                      "flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium transition-colors cursor-pointer border",
                      selectedArtifact === art
                        ? "bg-indigo-50 border-indigo-300 text-indigo-700 dark:bg-indigo-950/60 dark:border-indigo-700 dark:text-indigo-200 font-bold"
                        : "bg-white border-neutral-200 text-neutral-700 hover:bg-neutral-50 dark:bg-neutral-900/60 dark:border-neutral-800 dark:text-neutral-300 dark:hover:bg-neutral-800"
                    )}
                  >
                    {ARTIFACT_ICONS[art]}
                    <span>{art}</span>
                    <span className="rounded-full bg-neutral-200/80 dark:bg-neutral-800 px-1.5 py-0.2 text-[10px] font-mono">
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ── ITEMS LIST / EMPTY STATE ── */}
      {items.length === 0 ? (
        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-6 text-center dark:border-emerald-500/10">
          <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-500 mb-2" />
          <h4 className="text-sm font-bold text-neutral-900 dark:text-neutral-100">
            No Architecture Corrections Required
          </h4>
          <p className="mt-1 text-xs text-neutral-500 dark:text-neutral-400 max-w-md mx-auto">
            All evaluated architecture artifacts comply with deterministic Layer 0/1 rules and architectural rubrics.
          </p>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="rounded-xl border border-neutral-200/80 bg-neutral-50/50 p-6 text-center dark:border-neutral-800 dark:bg-neutral-900/30">
          <p className="text-xs text-neutral-500">No correction items match the selected filter criteria.</p>
        </div>
      ) : viewMode === "GROUPED" ? (
        /* ── GROUPED BY ARTIFACT (Clean Hierarchy: Artifact rendered ONCE per section) ── */
        <div className="space-y-4 pt-1">
          {activeGroupedArtifacts.map((art) => {
            const groupItems = itemsByArtifact[art] || [];
            if (groupItems.length === 0) return null;
            const isCollapsed = collapsedGroups[art] || false;
            const meta = ARTIFACT_TITLES[art] || { name: art, subtitle: "Architecture Artifact" };

            const actionablePending = groupItems.filter(
              (i) => i.is_actionable && i.status !== "APPROVED_FOR_CORRECTION" && i.status !== "DISMISSED"
            );
            const critCount = groupItems.filter((i) => i.severity === "critical").length;
            const highCount = groupItems.filter((i) => i.severity === "high").length;

            return (
              <div
                key={art}
                className="rounded-2xl border border-neutral-200/90 bg-neutral-50/40 dark:border-neutral-800/90 dark:bg-neutral-950/40 overflow-hidden shadow-2xs"
              >
                {/* ── ARTIFACT GROUP HEADER (Rendered ONCE for all items in this artifact) ── */}
                <div
                  onClick={() => toggleGroupCollapse(art)}
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 bg-white/80 dark:bg-neutral-900/80 border-b border-neutral-200/70 dark:border-neutral-800/70 cursor-pointer hover:bg-neutral-50/90 dark:hover:bg-neutral-800/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 shadow-2xs shrink-0">
                      {ARTIFACT_ICONS[art]}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-bold text-neutral-900 dark:text-neutral-100">
                          {meta.name}
                        </h4>
                        <span className="rounded-full bg-neutral-200/80 dark:bg-neutral-800 px-2 py-0.5 text-[10px] font-mono font-bold text-neutral-700 dark:text-neutral-300">
                          {groupItems.length} {groupItems.length === 1 ? "Item" : "Items"}
                        </span>
                        {critCount > 0 && (
                          <span className="rounded-full bg-rose-500/15 border border-rose-500/30 px-2 py-0.2 text-[10px] font-bold text-rose-600 dark:text-rose-400">
                            {critCount} Critical
                          </span>
                        )}
                        {highCount > 0 && (
                          <span className="rounded-full bg-orange-500/15 border border-orange-500/30 px-2 py-0.2 text-[10px] font-bold text-orange-600 dark:text-orange-400">
                            {highCount} High
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-neutral-500 dark:text-neutral-400 mt-0.5">
                        {meta.subtitle}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-auto" onClick={(e) => e.stopPropagation()}>
                    {actionablePending.length > 0 && (
                      <button
                        onClick={() => handleApproveAllForArtifact(groupItems)}
                        disabled={isProcessingCorrectionAction}
                        className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800/50 px-2.5 py-1 text-xs font-semibold text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-900/40 transition-colors cursor-pointer"
                        title={`Approve all ${actionablePending.length} pending actionable items for ${art}`}
                      >
                        <CheckCheck className="h-3.5 w-3.5" />
                        <span>Approve All ({actionablePending.length})</span>
                      </button>
                    )}
                    <button
                      onClick={() => toggleGroupCollapse(art)}
                      className="p-1 rounded-lg text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
                      title={isCollapsed ? "Expand section" : "Collapse section"}
                    >
                      {isCollapsed ? (
                        <ChevronRight className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>

                {/* ── ARTIFACT GROUP ITEMS ── */}
                {!isCollapsed && (
                  <div className="p-3.5 space-y-3">
                    {groupItems.map((item) => (
                      <CorrectionItemCard
                        key={item.id}
                        item={item}
                        inGroupedView={true}
                        onApprove={() => approveCorrectionPlanItem(item.id)}
                        onMarkReview={() => markCorrectionForManualReview(item.id)}
                        onDismiss={() => dismissCorrectionPlanItem(item.id)}
                        onReset={() => resetCorrectionDecision(item.id)}
                        isProcessing={isProcessingCorrectionAction}
                      />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        /* ── FLAT LIST VIEW ── */
        <div className="space-y-3.5 pt-1">
          {filteredItems.map((item) => (
            <CorrectionItemCard
              key={item.id}
              item={item}
              inGroupedView={false}
              onApprove={() => approveCorrectionPlanItem(item.id)}
              onMarkReview={() => markCorrectionForManualReview(item.id)}
              onDismiss={() => dismissCorrectionPlanItem(item.id)}
              onReset={() => resetCorrectionDecision(item.id)}
              isProcessing={isProcessingCorrectionAction}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface CorrectionItemCardProps {
  item: CorrectionItem;
  inGroupedView?: boolean;
  onApprove: () => void;
  onMarkReview: () => void;
  onDismiss: () => void;
  onReset: () => void;
  isProcessing: boolean;
}

function CorrectionItemCard({
  item,
  inGroupedView = false,
  onApprove,
  onMarkReview,
  onDismiss,
  onReset,
  isProcessing,
}: CorrectionItemCardProps) {
  const isApproved = item.status === "APPROVED_FOR_CORRECTION";
  const isDismissed = item.status === "DISMISSED";
  const isApplied = item.status === "APPLIED";
  const isManualReview = item.status === "MANUAL_REVIEW_REQUIRED" || item.requires_manual_review;
  const isActionable = item.is_actionable && item.is_supported_by_evidence && !item.requires_manual_review;

  const hasHldDependencies =
    item.affected_artifact === "HLD" && item.dependencies && item.dependencies.length > 0;

  return (
    <div
      className={clsx(
        "rounded-xl border p-4 shadow-xs space-y-3 transition-colors",
        isApplied
          ? "border-emerald-500/40 bg-emerald-50/20 dark:border-emerald-900/50 dark:bg-emerald-950/20"
          : isDismissed
          ? "border-neutral-200 bg-neutral-50/60 dark:border-neutral-800 dark:bg-neutral-950/30 opacity-75"
          : isApproved
          ? "border-indigo-300/70 bg-indigo-50/20 dark:border-indigo-900/50 dark:bg-indigo-950/15"
          : "border-neutral-200/90 bg-white dark:border-neutral-800 dark:bg-neutral-950/60"
      )}
    >
      {/* ── CARD HEADER ── */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-neutral-100 pb-2.5 dark:border-neutral-800/60">
        <div className="flex flex-wrap items-center gap-2">
          <ItemSeverityBadge severity={item.severity} />
          {/* Only show artifact pill if in flat list mode; in grouped view, artifact header is already shown above */}
          {!inGroupedView && (
            <span className="flex items-center gap-1.5 rounded-md bg-neutral-100 px-2 py-0.5 text-xs font-semibold text-neutral-800 dark:bg-neutral-800 dark:text-neutral-200 border border-neutral-200 dark:border-neutral-700">
              {ARTIFACT_ICONS[item.affected_artifact]}
              {item.affected_artifact}
            </span>
          )}
          {item.affected_target && (
            <span className="rounded bg-indigo-50 px-2 py-0.5 text-[11px] font-mono font-medium text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800/40">
              {item.affected_target}
            </span>
          )}
          {item.reference_systems && item.reference_systems.length > 1 && (
            <span className="rounded-full bg-blue-500/10 px-2 py-0.5 text-[10px] font-semibold text-blue-600 dark:text-blue-400 border border-blue-500/20">
              {item.reference_systems.length} Benchmark Systems
            </span>
          )}
          {item.consolidated_count && item.consolidated_count > 1 && (
            <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
              Consolidated ({item.consolidated_count})
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <ItemWorkflowStatusBadge status={item.status} />
          <span className="font-mono text-[10px] text-neutral-400">{item.finding_id}</span>
        </div>
      </div>

      {/* ── ORIGINAL FINDING & EVIDENCE ── */}
      <div className="space-y-1.5">
        <div className="text-xs font-semibold text-neutral-900 dark:text-neutral-100 flex items-start gap-1.5">
          <span className="font-mono text-neutral-500 shrink-0">
            [{inGroupedView ? item.finding_id : item.title}]
          </span>
          <span>{item.description}</span>
        </div>

        {item.evidence && (
          <div className="rounded-md bg-neutral-50 p-2 font-mono text-[11px] text-neutral-600 dark:bg-neutral-900/60 dark:text-neutral-400 border border-neutral-200/60 dark:border-neutral-800/60 flex items-center gap-2 truncate">
            <FileText className="h-3.5 w-3.5 text-neutral-400 shrink-0" />
            <span className="truncate">Evidence: {item.evidence}</span>
          </div>
        )}
      </div>

      {/* ── PROPOSED CORRECTION INSTRUCTION ── */}
      <div className="rounded-lg border border-indigo-500/20 bg-indigo-500/5 p-3 text-xs dark:border-indigo-500/20 dark:bg-indigo-950/20 space-y-1.5">
        <div className="flex items-center gap-1.5 font-bold text-indigo-900 dark:text-indigo-200">
          <Sparkles className="h-3.5 w-3.5 text-indigo-500" />
          <span>Proposed AI Engine Correction Instruction:</span>
        </div>
        <p className="text-neutral-800 dark:text-neutral-200 leading-relaxed font-sans">
          {item.correction_instruction}
        </p>
        <p className="text-[11px] text-neutral-500 dark:text-neutral-400 italic">
          Reason: {item.reason}
        </p>
      </div>

      {/* ── DEPENDENCIES ── */}
      <div className="pt-0.5">
        <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 block mb-1.5">
          Architectural Dependencies ({item.dependencies.length}):
        </span>

        {item.dependencies.length === 0 ? (
          <p className="text-[11px] text-neutral-400 italic">
            Localized change; no external artifact dependencies detected.
          </p>
        ) : (
          <div className="space-y-1.5">
            {item.dependencies.map((dep, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2 rounded-md bg-neutral-50 px-2.5 py-1.5 text-[11px] dark:bg-neutral-900/40 border border-neutral-200/50 dark:border-neutral-800/50"
              >
                <ArrowRight className="h-3.5 w-3.5 text-indigo-500 shrink-0 mt-0.5" />
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-semibold text-neutral-800 dark:text-neutral-200">
                      {dep.artifact}
                    </span>
                    <ImpactTypeBadge impact={dep.impact_type} />
                  </div>
                  <p className="text-neutral-600 dark:text-neutral-400 text-[10px] mt-0.5">
                    {dep.reason}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── HLD INTERFACE / BOUNDARY ADVISORY CALLOUT ── */}
      {hasHldDependencies && (
        <div className="rounded-lg border border-amber-500/25 bg-amber-500/10 p-2.5 text-[11px] text-amber-900 dark:text-amber-200 space-y-1">
          <div className="flex items-center gap-1.5 font-bold">
            <AlertTriangle className="h-3.5 w-3.5 text-amber-600 shrink-0" />
            <span>HLD Boundary Change Advisory</span>
          </div>
          <p className="text-[11px] leading-relaxed">
            This correction modifies high-level service boundaries or interfaces. Downstream dependent LLDs (
            <strong>{item.dependencies.map((d) => d.artifact).join(", ")}</strong>) require manual review before implementation. Dependent LLDs are not automatically rewritten.
          </p>
        </div>
      )}

      {/* ── MANUAL REVIEW WARNING CALLOUT ── */}
      {item.requires_manual_review && (
        <div className="rounded-lg border border-purple-500/30 bg-purple-500/10 p-2.5 text-[11px] text-purple-900 dark:text-purple-200 flex items-start gap-2">
          <AlertTriangle className="h-3.5 w-3.5 text-purple-500 shrink-0 mt-0.5" />
          <div>
            <strong>Manual Clarification Required:</strong>{" "}
            {item.clarification_needed ||
              "Insufficient concrete evidence exists to formulate an automated correction without ambiguity. Stakeholder architectural clarification is required."}
          </div>
        </div>
      )}

      {/* ── APPLIED / COMMITTED BANNER (Part 2.2.2) ── */}
      {isApplied && (
        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-900 dark:text-emerald-200 space-y-1">
          <div className="flex items-center gap-1.5 font-bold text-emerald-700 dark:text-emerald-300">
            <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
            <span>Correction Accepted & Committed</span>
          </div>
          <p className="text-[11px] leading-relaxed text-emerald-800 dark:text-emerald-300">
            Targeted AI correction has been accepted and committed as a new artifact version. Validation report is marked as stale until explicit revalidation is performed.
          </p>
          <div className="pt-1 flex items-center justify-between">
            <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400">
              Status: Verified & Stored
            </span>
          </div>
        </div>
      )}

      {/* ── APPROVED FOR CORRECTION BANNER ── */}
      {isApproved && !isApplied && (
        <div className="rounded-lg border border-indigo-500/30 bg-indigo-500/10 p-3 text-xs text-indigo-900 dark:text-indigo-200 space-y-1">
          <div className="flex items-center gap-1.5 font-bold">
            <CheckCircle2 className="h-4 w-4 text-indigo-600 shrink-0" />
            <span>Correction Approved — Targeted AI Request Dispatched</span>
          </div>
          <p className="text-[11px] leading-relaxed text-indigo-800 dark:text-indigo-300">
            Correction has been approved. The AI Engine performs targeted correction on the affected artifact, preserving unrelated decisions and invariants.
          </p>
          <div className="pt-1 flex items-center justify-between">
            <span className="text-[10px] font-mono text-indigo-500 dark:text-indigo-400">
              Decision Recorded: {item.review_decision?.decided_at ? new Date(item.review_decision.decided_at).toLocaleTimeString() : "Active"}
            </span>
            <button
              onClick={onReset}
              disabled={isProcessing}
              className="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 dark:text-indigo-300 dark:hover:text-indigo-100 cursor-pointer"
            >
              <RotateCcw className="h-3 w-3" />
              Reset Decision
            </button>
          </div>
        </div>
      )}

      {/* ── DISMISSED STATE NOTICE ── */}
      {isDismissed && (
        <div className="rounded-lg border border-neutral-300 bg-neutral-100/70 p-2.5 text-xs text-neutral-600 dark:border-neutral-800 dark:bg-neutral-900/50 dark:text-neutral-400 flex items-center justify-between">
          <span className="text-[11px] italic">
            Proposal dismissed by user. Excluded from active review.
          </span>
          <button
            onClick={onReset}
            disabled={isProcessing}
            className="inline-flex items-center gap-1 text-[11px] font-semibold text-neutral-700 hover:text-neutral-900 dark:text-neutral-300 dark:hover:text-white cursor-pointer"
          >
            <RotateCcw className="h-3 w-3" />
            Restore Proposal
          </button>
        </div>
      )}

      {/* ── USER CONTROLS BAR ── */}
      {!isApproved && !isDismissed && !isApplied && (
        <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-neutral-100 dark:border-neutral-800/60">
          <div className="text-[11px] text-neutral-400">
            {isActionable ? (
              <span className="text-emerald-600 dark:text-emerald-400 font-medium">
                ✓ Ready for review & approval
              </span>
            ) : isManualReview ? (
              <span className="text-purple-600 dark:text-purple-400 font-medium">
                ⚠️ Requires manual review / clarification
              </span>
            ) : (
              <span className="text-neutral-500">Advisory notice</span>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* 1. APPROVE ACTION */}
            {isActionable && (
              <button
                onClick={onApprove}
                disabled={isProcessing}
                className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 transition-colors shadow-xs cursor-pointer"
                title="Approve proposed correction plan"
              >
                <Check className="h-3.5 w-3.5" />
                <span>Approve Proposed Correction</span>
              </button>
            )}

            {/* 2. MARK FOR MANUAL REVIEW ACTION */}
            {!isManualReview && (
              <button
                onClick={onMarkReview}
                disabled={isProcessing}
                className="inline-flex items-center gap-1.5 rounded-lg border border-purple-500/30 bg-purple-500/10 px-2.5 py-1.5 text-xs font-medium text-purple-700 hover:bg-purple-500/20 dark:text-purple-300 disabled:opacity-50 transition-colors cursor-pointer"
                title="Flag for manual architectural review"
              >
                <AlertTriangle className="h-3.5 w-3.5" />
                <span>Mark for Manual Review</span>
              </button>
            )}

            {/* 3. DISMISS ACTION */}
            <button
              onClick={onDismiss}
              disabled={isProcessing}
              className="inline-flex items-center gap-1 rounded-lg border border-neutral-200 bg-neutral-50 px-2.5 py-1.5 text-xs font-medium text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900 dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-400 dark:hover:bg-neutral-800 disabled:opacity-50 transition-colors cursor-pointer"
              title="Dismiss proposal"
            >
              <X className="h-3.5 w-3.5" />
              <span>Dismiss</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function ItemWorkflowStatusBadge({ status }: { status?: CorrectionItemStatus }) {
  switch (status) {
    case "APPROVED_FOR_CORRECTION":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-indigo-500/15 border border-indigo-500/30 px-2 py-0.5 text-[10px] font-bold text-indigo-700 dark:text-indigo-300">
          <CheckCircle2 className="h-3 w-3" />
          APPROVED FOR REVIEW
        </span>
      );
    case "MANUAL_REVIEW_REQUIRED":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-purple-500/15 border border-purple-500/30 px-2 py-0.5 text-[10px] font-bold text-purple-700 dark:text-purple-300">
          <AlertTriangle className="h-3 w-3" />
          MANUAL REVIEW
        </span>
      );
    case "DISMISSED":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-neutral-200 dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 px-2 py-0.5 text-[10px] font-medium text-neutral-600 dark:text-neutral-400">
          <X className="h-3 w-3" />
          DISMISSED
        </span>
      );
    case "CORRECTION_UNAVAILABLE":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/15 border border-amber-500/30 px-2 py-0.5 text-[10px] font-bold text-amber-700 dark:text-amber-300">
          <Ban className="h-3 w-3" />
          CORRECTION UNAVAILABLE
        </span>
      );
    case "CORRECTION_FAILED":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-rose-500/15 border border-rose-500/30 px-2 py-0.5 text-[10px] font-bold text-rose-700 dark:text-rose-300">
          <AlertTriangle className="h-3 w-3" />
          FAILED
        </span>
      );
    case "APPLIED":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 text-[10px] font-bold text-emerald-700 dark:text-emerald-300">
          <Check className="h-3 w-3" />
          APPLIED
        </span>
      );
    case "PENDING_REVIEW":
    default:
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-blue-500/10 border border-blue-500/30 px-2 py-0.5 text-[10px] font-bold text-blue-700 dark:text-blue-300">
          <Clock className="h-3 w-3" />
          PENDING REVIEW
        </span>
      );
  }
}

function PlanStatusBadge({ status }: { status: string }) {
  switch (status) {
    case "NO_ACTION_REQUIRED":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 px-3 py-1 text-xs font-bold text-emerald-600 dark:text-emerald-400">
          <CheckCircle2 className="h-3.5 w-3.5" />
          NO ACTION REQUIRED
        </span>
      );
    case "MANUAL_REVIEW_REQUIRED":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-rose-500/15 border border-rose-500/30 px-3 py-1 text-xs font-bold text-rose-600 dark:text-rose-400">
          <ShieldAlert className="h-3.5 w-3.5" />
          MANUAL REVIEW REQUIRED
        </span>
      );
    case "PROVISIONAL_STAGE_UNAVAILABLE":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-purple-500/15 border border-purple-500/30 px-3 py-1 text-xs font-bold text-purple-600 dark:text-purple-400">
          <AlertTriangle className="h-3.5 w-3.5" />
          STAGE UNAVAILABLE
        </span>
      );
    case "CORRECTION_NEEDED":
    default:
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/15 border border-amber-500/30 px-3 py-1 text-xs font-bold text-amber-600 dark:text-amber-400">
          <Wrench className="h-3.5 w-3.5" />
          CORRECTION NEEDED
        </span>
      );
  }
}

function ItemSeverityBadge({ severity }: { severity: string }) {
  switch (severity) {
    case "critical":
      return (
        <span className="rounded-full bg-rose-500/15 border border-rose-500/30 px-2 py-0.5 text-[10px] font-bold uppercase text-rose-600 dark:text-rose-400">
          Critical
        </span>
      );
    case "high":
      return (
        <span className="rounded-full bg-orange-500/15 border border-orange-500/30 px-2 py-0.5 text-[10px] font-bold uppercase text-orange-600 dark:text-orange-400">
          High
        </span>
      );
    case "medium":
      return (
        <span className="rounded-full bg-amber-500/15 border border-amber-500/30 px-2 py-0.5 text-[10px] font-bold uppercase text-amber-600 dark:text-amber-400">
          Medium
        </span>
      );
    case "low":
    default:
      return (
        <span className="rounded-full bg-blue-500/15 border border-blue-500/30 px-2 py-0.5 text-[10px] font-bold uppercase text-blue-600 dark:text-blue-400">
          Low
        </span>
      );
  }
}

function ImpactTypeBadge({ impact }: { impact: ImpactType }) {
  return (
    <span className="rounded bg-neutral-200/80 px-1.5 py-0.5 text-[9px] font-mono uppercase text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400">
      {impact}
    </span>
  );
}

interface CorrectionDraftReviewCardProps {
  draft: TargetedCorrectionResponse;
  onAccept: () => void;
  onReject: () => void;
  onDismiss: () => void;
  isProcessing: boolean;
}

export function CorrectionDraftReviewCard({
  draft,
  onAccept,
  onReject,
  onDismiss,
  isProcessing,
}: CorrectionDraftReviewCardProps) {
  const [activeTab, setActiveTab] = useState<"side_by_side" | "original" | "corrected">("side_by_side");

  const isVerified = draft.status === "CORRECTION_VERIFIED";
  const isFailed = draft.status === "CORRECTION_FAILED";
  const isManualReview = draft.status === "MANUAL_REVIEW_REQUIRED";
  const preservationScore = Math.round((draft.verification_result?.baseline_preservation_score ?? 1.0) * 100);
  const resultingVersion = "v" + (parseFloat((draft.source_version || "v1.0").replace("v", "")) + 0.1).toFixed(1);

  return (
    <div className="rounded-2xl border-2 border-indigo-500/40 bg-white/95 dark:bg-neutral-900/95 shadow-xl p-5 space-y-4 backdrop-blur-md">
      {/* ── CARD HEADER ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-neutral-200 dark:border-neutral-800 pb-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 rounded-lg bg-indigo-600 text-white px-2.5 py-1 text-xs font-bold tracking-wide">
              <Sparkles className="h-3.5 w-3.5" />
              PROPOSED TARGETED CORRECTION
            </span>
            <span className="font-mono text-xs px-2 py-0.5 rounded-md bg-neutral-100 dark:bg-neutral-800 font-semibold text-neutral-700 dark:text-neutral-300">
              {draft.artifact_type} ({draft.source_version} → {resultingVersion})
            </span>
            <span className="font-mono text-[10px] text-neutral-400">
              Op: {draft.operation_id.slice(0, 10)}...
            </span>
          </div>
          <h4 className="text-sm font-bold text-neutral-900 dark:text-neutral-100 flex items-center gap-2">
            Finding: <span className="font-mono text-indigo-600 dark:text-indigo-400">[{draft.finding_id}]</span>
          </h4>
        </div>

        <div className="flex items-center gap-2">
          {/* Status Badge */}
          {isVerified ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 px-3 py-1 text-xs font-bold text-emerald-600 dark:text-emerald-400">
              <ShieldCheck className="h-3.5 w-3.5" />
              VERIFIED
            </span>
          ) : isFailed ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-rose-500/15 border border-rose-500/30 px-3 py-1 text-xs font-bold text-rose-600 dark:text-rose-400">
              <XCircle className="h-3.5 w-3.5" />
              CORRECTION FAILED
            </span>
          ) : isManualReview ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-purple-500/15 border border-purple-500/30 px-3 py-1 text-xs font-bold text-purple-600 dark:text-purple-400">
              <AlertTriangle className="h-3.5 w-3.5" />
              MANUAL REVIEW REQUIRED
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 rounded-full bg-indigo-500/15 border border-indigo-500/30 px-3 py-1 text-xs font-bold text-indigo-600 dark:text-indigo-400">
              <Sparkles className="h-3.5 w-3.5" />
              PROPOSED
            </span>
          )}

          <button
            onClick={onDismiss}
            className="p-1 rounded-lg text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
            title="Close review modal"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* ── CHANGE SUMMARY & RATIONALE ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
        <div className="rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50/50 dark:bg-neutral-950/40 p-3 space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 block">
            Correction Rationale
          </span>
          <p className="text-neutral-700 dark:text-neutral-300 leading-relaxed font-sans">
            {draft.explanation}
          </p>
        </div>
        <div className="rounded-xl border border-indigo-500/20 bg-indigo-50/30 dark:bg-indigo-950/20 p-3 space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-500 dark:text-indigo-400 block">
            Change Summary
          </span>
          <p className="text-neutral-700 dark:text-neutral-300 leading-relaxed font-sans">
            {draft.change_summary}
          </p>
        </div>
      </div>

      {/* ── VERIFICATION METRICS & CHECKS ── */}
      <div className="rounded-xl border border-neutral-200/80 dark:border-neutral-800/80 bg-neutral-50/40 dark:bg-neutral-900/40 p-3 space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-neutral-200/60 dark:border-neutral-800/60 pb-2">
          <span className="text-xs font-bold text-neutral-800 dark:text-neutral-200 flex items-center gap-1.5">
            <ShieldCheck className="h-4 w-4 text-emerald-500" />
            Backend Verification Checks
          </span>
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-neutral-500">Baseline Content Preservation:</span>
            <span className="font-mono text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30">
              {preservationScore}% Preserved
            </span>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 pt-1">
          {draft.verification_result?.checks_passed?.map((chk: string, i: number) => (
            <span
              key={`pass-${i}`}
              className="inline-flex items-center gap-1 rounded-md bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 text-[10px] font-mono text-emerald-700 dark:text-emerald-300"
            >
              <Check className="h-3 w-3 text-emerald-600" />
              {chk}
            </span>
          ))}
          {draft.verification_result?.checks_failed?.map((chk: string, i: number) => (
            <span
              key={`fail-${i}`}
              className="inline-flex items-center gap-1 rounded-md bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 text-[10px] font-mono text-rose-700 dark:text-rose-300"
            >
              <X className="h-3 w-3 text-rose-600" />
              {chk}
            </span>
          ))}
          {draft.unresolved_issues?.map((warn: string, i: number) => (
            <span
              key={`warn-${i}`}
              className="inline-flex items-center gap-1 rounded-md bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 text-[10px] font-mono text-amber-700 dark:text-amber-300"
            >
              <AlertTriangle className="h-3 w-3 text-amber-600" />
              {warn}
            </span>
          ))}
        </div>
      </div>

      {/* ── ARTIFACT CONTENT INSPECTION / COMPARISON ── */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <Code2 className="h-4 w-4 text-neutral-500" />
            <span className="text-xs font-bold text-neutral-700 dark:text-neutral-300">
              Artifact Content Comparison
            </span>
          </div>
          <div className="flex items-center gap-1 rounded-lg bg-neutral-100 dark:bg-neutral-800 p-0.5 text-xs">
            <button
              onClick={() => setActiveTab("side_by_side")}
              className={clsx(
                "px-2.5 py-1 rounded-md font-medium transition-colors cursor-pointer text-[11px]",
                activeTab === "side_by_side"
                  ? "bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-100 shadow-xs"
                  : "text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200"
              )}
            >
              Side-by-Side
            </button>
            <button
              onClick={() => setActiveTab("original")}
              className={clsx(
                "px-2.5 py-1 rounded-md font-medium transition-colors cursor-pointer text-[11px]",
                activeTab === "original"
                  ? "bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-100 shadow-xs"
                  : "text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200"
              )}
            >
              Original ({draft.source_version})
            </button>
            <button
              onClick={() => setActiveTab("corrected")}
              className={clsx(
                "px-2.5 py-1 rounded-md font-medium transition-colors cursor-pointer text-[11px]",
                activeTab === "corrected"
                  ? "bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-100 shadow-xs"
                  : "text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200"
              )}
            >
              Proposed ({resultingVersion})
            </button>
          </div>
        </div>

        {/* Tab views */}
        {activeTab === "side_by_side" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            <div className="rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-950 p-3 font-mono text-[11px] text-neutral-300 overflow-auto max-h-80 shadow-inner">
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-neutral-800 text-[10px] text-neutral-400 uppercase tracking-wider">
                <span>Original Artifact ({draft.source_version})</span>
                <span className="text-neutral-500">Read-Only</span>
              </div>
              <pre className="whitespace-pre-wrap leading-relaxed">
                {draft.original_artifact ? JSON.stringify(draft.original_artifact, null, 2) : "// No original snapshot available"}
              </pre>
            </div>
            <div className="rounded-xl border border-indigo-500/30 bg-neutral-950 p-3 font-mono text-[11px] text-emerald-300 overflow-auto max-h-80 shadow-inner">
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-neutral-800 text-[10px] text-indigo-400 uppercase tracking-wider">
                <span>Proposed Corrected Artifact ({resultingVersion})</span>
                <span className="text-indigo-400">AI Target</span>
              </div>
              <pre className="whitespace-pre-wrap leading-relaxed">
                {draft.corrected_artifact ? JSON.stringify(draft.corrected_artifact, null, 2) : "// No proposed artifact"}
              </pre>
            </div>
          </div>
        )}

        {activeTab === "original" && (
          <div className="rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-950 p-3 font-mono text-[11px] text-neutral-300 overflow-auto max-h-96 shadow-inner">
            <pre className="whitespace-pre-wrap leading-relaxed">
              {draft.original_artifact ? JSON.stringify(draft.original_artifact, null, 2) : "// No original snapshot available"}
            </pre>
          </div>
        )}

        {activeTab === "corrected" && (
          <div className="rounded-xl border border-indigo-500/30 bg-neutral-950 p-3 font-mono text-[11px] text-emerald-300 overflow-auto max-h-96 shadow-inner">
            <pre className="whitespace-pre-wrap leading-relaxed">
              {draft.corrected_artifact ? JSON.stringify(draft.corrected_artifact, null, 2) : "// No proposed artifact"}
            </pre>
          </div>
        )}
      </div>

      {/* ── SAFETY ADVISORY ── */}
      <div className="rounded-lg bg-neutral-100/80 dark:bg-neutral-800/60 p-2.5 text-[11px] text-neutral-600 dark:text-neutral-400 flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <Info className="h-3.5 w-3.5 text-neutral-400 shrink-0" />
          <span>
            Rejecting this draft leaves the original version untouched. Accepting commits version <strong>{resultingVersion}</strong> and marks validation stale.
          </span>
        </div>
        <span className="font-mono text-[10px] text-neutral-400 shrink-0">
          Revalidation is strictly user-controlled.
        </span>
      </div>

      {/* ── ACTIONS BAR ── */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-neutral-200 dark:border-neutral-800">
        <button
          onClick={onReject}
          disabled={isProcessing}
          className="inline-flex items-center gap-1.5 rounded-xl border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-900 px-4 py-2 text-xs font-semibold text-neutral-700 dark:text-neutral-200 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/30 dark:hover:text-rose-400 disabled:opacity-50 transition-colors cursor-pointer shadow-xs"
          title="Reject proposed correction and discard draft"
        >
          <X className="h-4 w-4" />
          <span>Reject Correction (Discard)</span>
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={onAccept}
            disabled={isProcessing || isFailed}
            className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-5 py-2 text-xs font-bold text-white hover:bg-indigo-500 disabled:opacity-50 transition-colors shadow-sm cursor-pointer"
            title="Accept correction and persist as new artifact version"
          >
            <Check className="h-4 w-4" />
            <span>Accept Correction & Create {resultingVersion}</span>
          </button>
        </div>
      </div>
    </div>
  );
}

