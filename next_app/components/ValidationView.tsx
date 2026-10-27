"use client";

import { useState, useMemo } from "react";
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Download,
  Copy,
  Check,
  RefreshCw,
  Search,
  Server,
  Database,
  Cloud,
  ChevronDown,
  ChevronRight,
  Layers,
  FileCheck2,
  Lock,
  Compass,
  ArrowLeft,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import type { Finding } from "@/lib/validator-client";
import clsx from "clsx";

export default function ValidationView() {
  const {
    validationData,
    isValidating,
    validationError,
    validateArchitecture,
    setHldWorkspaceTab,
  } = useAppStore();

  const [copied, setCopied] = useState(false);
  const [findingSeverityFilter, setFindingSeverityFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedFindings, setExpandedFindings] = useState<Record<string, boolean>>({});
  const [showDetailsSection, setShowDetailsSection] = useState(false);

  const handleCopyJson = () => {
    if (!validationData) return;
    navigator.clipboard.writeText(JSON.stringify(validationData, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadJson = () => {
    if (!validationData) return;
    const blob = new Blob([JSON.stringify(validationData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `validated_architecture_${validationData.metadata?.package_id || "export"}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const toggleFindingExpand = (id: string) => {
    setExpandedFindings((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  // Resolved issue IDs from correction history
  const resolvedIssueIds = useMemo(() => {
    if (!validationData?.correction_history) return new Set<string>();
    const ids = new Set<string>();
    validationData.correction_history.forEach((attempt) => {
      attempt.resolved_issue_ids?.forEach((id) => ids.add(id));
    });
    return ids;
  }, [validationData]);

  if (isValidating) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-6 text-center bg-white/50 dark:bg-black/50">
        <div className="relative mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-500 shadow-lg shadow-indigo-500/10">
          <ShieldCheck className="h-8 w-8 animate-pulse" />
          <div className="absolute inset-0 rounded-2xl border-2 border-indigo-500/40 animate-ping opacity-30" />
        </div>
        <h3 className="text-base font-bold text-gray-900 dark:text-white">
          Architectural Verification in Progress
        </h3>
        <p className="mt-1.5 max-w-sm text-xs text-neutral-500 dark:text-neutral-400">
          Auditing ARSRS alignment, cross-artifact consistency, and running closed-loop AI correction cycles...
        </p>
        <div className="mt-4 flex items-center gap-2 text-xs font-semibold text-indigo-600 dark:text-indigo-400">
          <RefreshCw className="h-3.5 w-3.5 animate-spin" />
          <span>Standalone Validator Engine Active (Port 8001)</span>
        </div>
      </div>
    );
  }

  if (!validationData) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-6 text-center bg-white/50 dark:bg-black/50">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-500">
          <ShieldCheck className="h-7 w-7" />
        </div>
        <h3 className="text-base font-bold text-gray-900 dark:text-white">
          No Validation Report Available
        </h3>
        <p className="mt-1 max-w-sm text-xs text-neutral-500 dark:text-neutral-400">
          Run the independent Validator Engine against the architecture package to evaluate consistency, NFRs, and RAG benchmarks.
        </p>
        {validationError && (
          <div className="mt-3 max-w-md rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-600 dark:text-red-400">
            {validationError}
          </div>
        )}
        <div className="mt-5 flex items-center gap-3">
          <button
            onClick={() => validateArchitecture()}
            className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-500 transition-all cursor-pointer"
          >
            <ShieldCheck className="h-4 w-4" />
            <span>Validate Architecture Package</span>
          </button>
          <button
            onClick={() => setHldWorkspaceTab("hld")}
            className="flex items-center gap-1.5 rounded-xl border border-neutral-300 px-3 py-2 text-xs font-semibold text-neutral-700 hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800 transition-all cursor-pointer"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Back to Topology</span>
          </button>
        </div>
      </div>
    );
  }

  // ── Extract real fields from ValidatedArchitectureResponse ──
  const summary = validationData.validation?.summary;
  const scorecard = validationData.validation?.scorecard;
  const structural = validationData.validation?.structural_validation;
  const reqAlignment = validationData.validation?.requirement_alignment;
  const consistency = validationData.validation?.cross_artifact_consistency;
  const nfrValidation = validationData.validation?.nfr_validation;
  const redTeam = validationData.validation?.red_team_review;
  const evidence = validationData.evidence;

  // Real composite score (0-100%)
  const rawScore = summary?.overall_score ?? scorecard?.overall_composite_score ?? 0;
  const scorePercent = Math.round(rawScore * 100);

  // Verdict and validation status
  const verdict = summary?.verdict || "NEEDS_REMEDIATION";
  const isFullyValidated = Boolean(validationData.is_fully_validated);

  // Findings
  const allFindings = validationData.validation?.findings || [];
  const criticalCount = summary?.critical_findings_count ?? allFindings.filter((f) => f.severity === "CRITICAL").length;
  const highCount = summary?.high_findings_count ?? allFindings.filter((f) => f.severity === "HIGH").length;
  const mediumCount = summary?.medium_findings_count ?? allFindings.filter((f) => f.severity === "MEDIUM").length;
  const lowCount = summary?.low_findings_count ?? allFindings.filter((f) => f.severity === "LOW").length;

  // Attempts count
  const attempt = validationData.attempt || (validationData.correction_history?.length ? validationData.correction_history.length + 1 : 1);
  const maxRetries = validationData.max_retries || 2;

  // Filtered findings list
  const filteredFindings = allFindings.filter((f) => {
    const matchesSeverity = findingSeverityFilter === "ALL" ? true : f.severity === findingSeverityFilter;
    const matchesSearch = searchQuery
      ? f.explanation.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.affected_component?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.id.toLowerCase().includes(searchQuery.toLowerCase())
      : true;
    return matchesSeverity && matchesSearch;
  });

  return (
    <div className="flex h-full flex-col overflow-y-auto bg-neutral-50/60 dark:bg-black/60 text-neutral-900 dark:text-neutral-100 transition-colors">
      {/* ── Compact Header Bar: Scorecard Summary & Actions ── */}
      <div className="border-b border-neutral-200/80 bg-white/90 px-4 py-3 dark:border-neutral-800/80 dark:bg-neutral-950/90 backdrop-blur-md sticky top-0 z-20 shadow-2xs">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Left: Overall Score + Status Badges */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setHldWorkspaceTab("hld")}
              title="Return to Topology"
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-neutral-200 bg-neutral-100 text-neutral-700 hover:bg-neutral-200 dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-300 dark:hover:bg-neutral-800 transition-colors cursor-pointer"
            >
              <ArrowLeft className="h-4 w-4" />
            </button>

            {/* Overall Score Badge */}
            <div className="flex items-center gap-2">
              <div
                className={clsx(
                  "flex h-9 min-w-14 items-center justify-center rounded-xl font-black text-sm px-2.5 shadow-2xs border",
                  scorePercent >= 80
                    ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/30 dark:bg-emerald-950/40 dark:text-emerald-400"
                    : scorePercent >= 60
                    ? "bg-amber-500/10 text-amber-600 border-amber-500/30 dark:bg-amber-950/40 dark:text-amber-400"
                    : "bg-rose-500/10 text-rose-600 border-rose-500/30 dark:bg-rose-950/40 dark:text-rose-400"
                )}
              >
                {scorePercent}%
              </div>

              <div>
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span
                    className={clsx(
                      "rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider border",
                      verdict.startsWith("APPROVED")
                        ? "bg-emerald-500/10 text-emerald-700 border-emerald-500/30 dark:text-emerald-300"
                        : "bg-amber-500/10 text-amber-700 border-amber-500/30 dark:text-amber-300"
                    )}
                  >
                    {verdict.replace(/_/g, " ")}
                  </span>

                  <span
                    className={clsx(
                      "rounded-full px-2 py-0.5 text-[10px] font-semibold border",
                      isFullyValidated
                        ? "bg-emerald-500/10 text-emerald-700 border-emerald-500/30 dark:text-emerald-300"
                        : "bg-rose-500/10 text-rose-700 border-rose-500/30 dark:text-rose-300"
                    )}
                  >
                    {isFullyValidated ? "✓ Fully Validated" : "⚠️ Remediation Needed"}
                  </span>

                  <span className="rounded-full bg-neutral-200/80 px-2 py-0.5 text-[10px] font-medium text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">
                    Attempt {attempt} / {maxRetries}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Center/Right: Finding Counts Pill Counters */}
          <div className="flex items-center gap-1.5 text-[11px] font-semibold">
            <span
              onClick={() => setFindingSeverityFilter(findingSeverityFilter === "CRITICAL" ? "ALL" : "CRITICAL")}
              className={clsx(
                "rounded-md px-2 py-1 cursor-pointer transition-all border",
                criticalCount > 0
                  ? "bg-rose-500/10 text-rose-600 border-rose-500/30 dark:text-rose-400"
                  : "bg-neutral-100 text-neutral-400 border-neutral-200 dark:bg-neutral-900 dark:border-neutral-800"
              )}
            >
              {criticalCount} Critical
            </span>

            <span
              onClick={() => setFindingSeverityFilter(findingSeverityFilter === "HIGH" ? "ALL" : "HIGH")}
              className={clsx(
                "rounded-md px-2 py-1 cursor-pointer transition-all border",
                highCount > 0
                  ? "bg-orange-500/10 text-orange-600 border-orange-500/30 dark:text-orange-400"
                  : "bg-neutral-100 text-neutral-400 border-neutral-200 dark:bg-neutral-900 dark:border-neutral-800"
              )}
            >
              {highCount} High
            </span>

            <span
              onClick={() => setFindingSeverityFilter(findingSeverityFilter === "MEDIUM" ? "ALL" : "MEDIUM")}
              className={clsx(
                "rounded-md px-2 py-1 cursor-pointer transition-all border",
                mediumCount > 0
                  ? "bg-amber-500/10 text-amber-600 border-amber-500/30 dark:text-amber-400"
                  : "bg-neutral-100 text-neutral-400 border-neutral-200 dark:bg-neutral-900 dark:border-neutral-800"
              )}
            >
              {mediumCount} Med
            </span>

            <span
              onClick={() => setFindingSeverityFilter(findingSeverityFilter === "LOW" ? "ALL" : "LOW")}
              className={clsx(
                "rounded-md px-2 py-1 cursor-pointer transition-all border",
                lowCount > 0
                  ? "bg-blue-500/10 text-blue-600 border-blue-500/30 dark:text-blue-400"
                  : "bg-neutral-100 text-neutral-400 border-neutral-200 dark:bg-neutral-900 dark:border-neutral-800"
              )}
            >
              {lowCount} Low
            </span>
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => validateArchitecture()}
              title="Re-validate current architecture"
              className="flex items-center gap-1 rounded-lg border border-neutral-200/80 bg-white/70 backdrop-blur-md px-2.5 py-1.5 text-xs font-semibold text-neutral-700 hover:border-black hover:text-black dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-300 dark:hover:bg-[#161619] dark:hover:border-white/20 dark:hover:text-white transition-colors cursor-pointer"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Re-Validate</span>
            </button>

            <button
              onClick={handleCopyJson}
              title="Copy validated architecture JSON"
              className="flex items-center gap-1 rounded-lg border border-neutral-200/80 bg-white/70 backdrop-blur-md px-2.5 py-1.5 text-xs font-semibold text-neutral-700 hover:border-black hover:text-black dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-300 dark:hover:bg-[#161619] dark:hover:border-white/20 dark:hover:text-white transition-colors cursor-pointer"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
              <span className="hidden sm:inline">{copied ? "Copied" : "Copy"}</span>
            </button>

            <button
              onClick={handleDownloadJson}
              title="Export validated architecture JSON"
              className="flex items-center gap-1 rounded-lg bg-neutral-900 text-white px-2.5 py-1.5 text-xs font-semibold hover:bg-neutral-800 dark:bg-neutral-100 dark:text-neutral-900 dark:hover:bg-neutral-200 transition-colors cursor-pointer"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Export</span>
            </button>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4 max-w-7xl mx-auto w-full">
        {/* ── 6-Dimension Architectural Quality Grid ── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {/* 1. Structural Completeness */}
          <div className="rounded-xl border border-neutral-200/80 bg-white p-3.5 dark:border-neutral-800/80 dark:bg-neutral-950 shadow-2xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-500/10 text-blue-500">
                  <FileCheck2 className="h-4 w-4" />
                </div>
                <span className="text-xs font-bold">Structural Completeness</span>
              </div>
              {scorecard?.structural_completeness != null ? (
                <span className="text-xs font-black text-blue-600 dark:text-blue-400">
                  {Math.round(scorecard.structural_completeness * 100)}%
                </span>
              ) : (
                <span className={clsx("text-[10px] font-bold uppercase", structural?.is_valid ? "text-emerald-500" : "text-amber-500")}>
                  {structural?.is_valid ? "Valid" : "Deficient"}
                </span>
              )}
            </div>
            <div className="mt-2.5 flex items-center justify-between text-[11px] text-neutral-500 dark:text-neutral-400">
              <span>Missing Sections</span>
              <span className="font-semibold text-neutral-800 dark:text-neutral-200">
                {structural?.missing_sections?.length || 0}
              </span>
            </div>
          </div>

          {/* 2. Requirement Alignment */}
          <div className="rounded-xl border border-neutral-200/80 bg-white p-3.5 dark:border-neutral-800/80 dark:bg-neutral-950 shadow-2xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-500">
                  <CheckCircle2 className="h-4 w-4" />
                </div>
                <span className="text-xs font-bold">Requirement Alignment</span>
              </div>
              {(scorecard?.requirement_alignment_score ?? reqAlignment?.alignment_score) != null ? (
                <span className="text-xs font-black text-emerald-600 dark:text-emerald-400">
                  {Math.round((scorecard?.requirement_alignment_score ?? reqAlignment?.alignment_score ?? 1) * 100)}%
                </span>
              ) : (
                <span className={clsx("text-[10px] font-bold uppercase", reqAlignment?.is_aligned ? "text-emerald-500" : "text-amber-500")}>
                  {reqAlignment?.is_aligned ? "Aligned" : "Gaps"}
                </span>
              )}
            </div>
            <div className="mt-2.5 flex items-center justify-between text-[11px] text-neutral-500 dark:text-neutral-400">
              <span>Requirements Covered</span>
              <span className="font-semibold text-neutral-800 dark:text-neutral-200">
                {reqAlignment?.covered_requirements_count ?? 0} / {reqAlignment?.total_requirements ?? 0}
              </span>
            </div>
          </div>

          {/* 3. Cross-Artifact Consistency */}
          <div className="rounded-xl border border-neutral-200/80 bg-white p-3.5 dark:border-neutral-800/80 dark:bg-neutral-950 shadow-2xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-purple-500/10 text-purple-500">
                  <Layers className="h-4 w-4" />
                </div>
                <span className="text-xs font-bold">Cross-Artifact Consistency</span>
              </div>
              {(scorecard?.consistency_score ?? consistency?.consistency_score) != null ? (
                <span className="text-xs font-black text-purple-600 dark:text-purple-400">
                  {Math.round((scorecard?.consistency_score ?? consistency?.consistency_score ?? 1) * 100)}%
                </span>
              ) : (
                <span className={clsx("text-[10px] font-bold uppercase", consistency?.is_consistent ? "text-emerald-500" : "text-amber-500")}>
                  {consistency?.is_consistent ? "Consistent" : "Discrepancy"}
                </span>
              )}
            </div>
            <div className="mt-2.5 flex items-center justify-between text-[11px] text-neutral-500 dark:text-neutral-400">
              <span>HLD ↔ Backend Alignment</span>
              <span className="font-semibold text-neutral-800 dark:text-neutral-200">
                {Math.round((consistency?.hld_to_backend_alignment ?? 1) * 100)}%
              </span>
            </div>
          </div>

          {/* 4. NFR Feasibility & Quality */}
          <div className="rounded-xl border border-neutral-200/80 bg-white p-3.5 dark:border-neutral-800/80 dark:bg-neutral-950 shadow-2xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-500">
                  <Server className="h-4 w-4" />
                </div>
                <span className="text-xs font-bold">NFR Quality & Feasibility</span>
              </div>
              {nfrValidation?.feasibility_score != null ? (
                <span className="text-xs font-black text-cyan-600 dark:text-cyan-400">
                  {Math.round(nfrValidation.feasibility_score * 100)}%
                </span>
              ) : (
                <span className="text-[10px] font-bold text-neutral-500 uppercase">
                  {nfrValidation?.is_valid ? "Evaluated" : "At Risk"}
                </span>
              )}
            </div>
            <div className="mt-2.5 flex items-center justify-between text-[11px] text-neutral-500 dark:text-neutral-400">
              <span>Supported Attributes</span>
              <span className="font-semibold text-neutral-800 dark:text-neutral-200">
                {nfrValidation?.supported_nfrs_count ?? 0} / {nfrValidation?.total_nfrs ?? 0}
              </span>
            </div>
          </div>

          {/* 5. Red-Team & Security Review */}
          <div className="rounded-xl border border-neutral-200/80 bg-white p-3.5 dark:border-neutral-800/80 dark:bg-neutral-950 shadow-2xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-rose-500/10 text-rose-500">
                  <Lock className="h-4 w-4" />
                </div>
                <span className="text-xs font-bold">Red-Team Adversarial Audit</span>
              </div>
              <span
                className={clsx(
                  "rounded-full px-2 py-0.5 text-[9px] font-bold uppercase border",
                  (redTeam?.review_status || redTeam?.verdict || "PASSED").startsWith("PASSED")
                    ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/30"
                    : "bg-rose-500/10 text-rose-600 border-rose-500/30"
                )}
              >
                {redTeam?.review_status || redTeam?.verdict || "PASSED"}
              </span>
            </div>
            <div className="mt-2.5 flex items-center justify-between text-[11px] text-neutral-500 dark:text-neutral-400">
              <span>SPOFs Identified</span>
              <span className="font-semibold text-neutral-800 dark:text-neutral-200">
                {redTeam?.single_points_of_failure?.length || 0}
              </span>
            </div>
          </div>

          {/* 6. Real-World Evidence Support */}
          <div className="rounded-xl border border-neutral-200/80 bg-white p-3.5 dark:border-neutral-800/80 dark:bg-neutral-950 shadow-2xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-500">
                  <Compass className="h-4 w-4" />
                </div>
                <span className="text-xs font-bold">Real-World Evidence Support</span>
              </div>
              {(evidence?.evidence_quality_score ?? scorecard?.evidence_support_score) != null ? (
                <span className="text-xs font-black text-indigo-600 dark:text-indigo-400">
                  {Math.round((evidence?.evidence_quality_score ?? scorecard?.evidence_support_score ?? 0.85) * 100)}%
                </span>
              ) : (
                <span className="text-[10px] font-bold text-neutral-500 uppercase">
                  {evidence?.has_evidence ? "Supported" : "Gaps"}
                </span>
              )}
            </div>
            <div className="mt-2.5 flex items-center justify-between text-[11px] text-neutral-500 dark:text-neutral-400">
              <span className="truncate max-w-[150px]">{evidence?.primary_archetype || "Production Precedent"}</span>
              <span className="font-semibold text-neutral-800 dark:text-neutral-200">
                {(evidence?.matched_archetypes?.length || evidence?.matched_systems?.length || 0)} Systems
              </span>
            </div>
          </div>
        </div>

        {/* ── Findings Section with Severity & Resolution Status ── */}
        <div className="rounded-xl border border-neutral-200/80 bg-white p-4 dark:border-neutral-800/80 dark:bg-neutral-950 shadow-2xs space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-neutral-100 pb-3 dark:border-neutral-900">
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                Findings & Architectural Defects ({filteredFindings.length})
              </h3>
            </div>

            {/* Search Filter */}
            <div className="relative flex items-center">
              <Search className="absolute left-2.5 h-3.5 w-3.5 text-neutral-400" />
              <input
                type="text"
                placeholder="Search findings..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-7 w-44 rounded-lg border border-neutral-200 bg-neutral-50 pl-8 pr-2.5 text-xs text-neutral-900 placeholder:text-neutral-400 dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-1 focus:ring-neutral-400"
              />
            </div>
          </div>

          {filteredFindings.length === 0 ? (
            <div className="py-8 text-center text-xs text-neutral-400 dark:text-neutral-500">
              No findings matching the selected filter.
            </div>
          ) : (
            <div className="space-y-2">
              {filteredFindings.map((finding) => {
                const isExpanded = Boolean(expandedFindings[finding.id]);
                const isResolved =
                  finding.status === "RESOLVED" ||
                  finding.resolution_status === "RESOLVED" ||
                  resolvedIssueIds.has(finding.id);

                return (
                  <div
                    key={finding.id}
                    className="rounded-lg border border-neutral-200/60 bg-neutral-50/50 dark:border-neutral-800/60 dark:bg-neutral-900/30 overflow-hidden transition-all text-xs"
                  >
                    {/* Header item row */}
                    <div
                      onClick={() => toggleFindingExpand(finding.id)}
                      className="flex items-start justify-between p-3 cursor-pointer hover:bg-neutral-100/50 dark:hover:bg-neutral-800/30 gap-2"
                    >
                      <div className="flex items-start gap-2.5 min-w-0">
                        {/* Severity Pill */}
                        <span
                          className={clsx(
                            "rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider shrink-0 border",
                            finding.severity === "CRITICAL"
                              ? "bg-rose-500/10 text-rose-600 border-rose-500/30 dark:text-rose-400"
                              : finding.severity === "HIGH"
                              ? "bg-orange-500/10 text-orange-600 border-orange-500/30 dark:text-orange-400"
                              : finding.severity === "MEDIUM"
                              ? "bg-amber-500/10 text-amber-600 border-amber-500/30 dark:text-amber-400"
                              : "bg-blue-500/10 text-blue-600 border-blue-500/30 dark:text-blue-400"
                          )}
                        >
                          {finding.severity}
                        </span>

                        <div className="min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-semibold text-neutral-900 dark:text-white">
                              {finding.affected_component || finding.id}
                            </span>
                            {finding.affected_artifact && (
                              <span className="rounded bg-neutral-200/70 px-1.5 py-0.5 text-[9px] font-mono text-neutral-600 dark:bg-neutral-800 dark:text-neutral-300">
                                {finding.affected_artifact.replace("_", " ")}
                              </span>
                            )}
                          </div>
                          <p className="mt-1 text-neutral-600 dark:text-neutral-300 line-clamp-2">
                            {finding.explanation}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        {/* Resolution Status Badge */}
                        <span
                          className={clsx(
                            "rounded-full px-2 py-0.5 text-[9px] font-bold uppercase border",
                            isResolved
                              ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/30 dark:text-emerald-400"
                              : "bg-rose-500/10 text-rose-600 border-rose-500/30 dark:text-rose-400"
                          )}
                        >
                          {isResolved ? "✓ Resolved" : "Open"}
                        </span>
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4 text-neutral-400" />
                        ) : (
                          <ChevronRight className="h-4 w-4 text-neutral-400" />
                        )}
                      </div>
                    </div>

                    {/* Expanded Detail */}
                    {isExpanded && (
                      <div className="border-t border-neutral-200/60 bg-white p-3.5 dark:border-neutral-800/60 dark:bg-neutral-950 space-y-2">
                        {finding.recommendation && (
                          <div className="rounded-lg bg-indigo-50/60 p-2.5 dark:bg-indigo-950/20 border border-indigo-200/40 dark:border-indigo-800/40">
                            <span className="block text-[10px] font-bold text-indigo-700 dark:text-indigo-300 uppercase tracking-wider">
                              Actionable Recommendation:
                            </span>
                            <p className="mt-0.5 text-indigo-950 dark:text-indigo-200 text-[11px] leading-relaxed">
                              {finding.recommendation}
                            </p>
                          </div>
                        )}

                        {finding.evidence && (
                          <div className="text-[11px] text-neutral-500 dark:text-neutral-400">
                            <span className="font-semibold text-neutral-700 dark:text-neutral-300">Supporting Evidence: </span>
                            {finding.evidence}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* ── Collapsible History & Evidence Section ── */}
        <div className="rounded-xl border border-neutral-200/80 bg-white dark:border-neutral-800/80 dark:bg-neutral-950 overflow-hidden shadow-2xs">
          <button
            onClick={() => setShowDetailsSection(!showDetailsSection)}
            className="flex w-full items-center justify-between p-3.5 text-xs font-bold text-neutral-700 hover:bg-neutral-50 dark:text-neutral-300 dark:hover:bg-neutral-900 transition-colors cursor-pointer"
          >
            <span>
              Correction History & Reference Precedents (
              {validationData.correction_history?.length || 0} attempts ·{" "}
              {evidence?.matched_archetypes?.length || evidence?.matched_systems?.length || 0} benchmarks)
            </span>
            {showDetailsSection ? (
              <ChevronDown className="h-4 w-4 text-neutral-400" />
            ) : (
              <ChevronRight className="h-4 w-4 text-neutral-400" />
            )}
          </button>

          {showDetailsSection && (
            <div className="border-t border-neutral-200/80 p-4 space-y-4 dark:border-neutral-800/80 text-xs">
              {/* Correction History Records */}
              <div>
                <h4 className="text-[11px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400 mb-2">
                  Closed-Loop AI Correction Attempts
                </h4>
                {(!validationData.correction_history || validationData.correction_history.length === 0) ? (
                  <p className="text-neutral-500 text-[11px]">
                    No intermediate correction cycles required; initial generation cleared validation gates.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {validationData.correction_history.map((record) => (
                      <div
                        key={record.attempt}
                        className="rounded-lg border border-neutral-200/70 p-3 bg-neutral-50 dark:border-neutral-800/70 dark:bg-neutral-900/50"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-neutral-900 dark:text-white">
                            Attempt #{record.attempt}
                          </span>
                          <span className="text-[10px] text-neutral-400">
                            {record.timestamp ? new Date(record.timestamp).toLocaleTimeString() : ""}
                          </span>
                        </div>
                        <p className="mt-1 text-neutral-600 dark:text-neutral-300">{record.summary}</p>
                        {record.regenerated_artifacts && record.regenerated_artifacts.length > 0 && (
                          <div className="mt-1.5 flex items-center gap-1.5 flex-wrap">
                            <span className="text-[10px] font-semibold text-neutral-500">Regenerated:</span>
                            {record.regenerated_artifacts.map((art) => (
                              <span
                                key={art}
                                className="rounded bg-neutral-200/70 px-1.5 py-0.5 text-[9px] font-mono text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300"
                              >
                                {art}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Matched Precedents */}
              {evidence?.matched_archetypes && evidence.matched_archetypes.length > 0 && (
                <div>
                  <h4 className="text-[11px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400 mb-2">
                    Matched Production Precedents (Category 10)
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {evidence.matched_archetypes.map((arch: any, idx: number) => (
                      <div
                        key={idx}
                        className="rounded-lg border border-neutral-200/70 p-3 bg-neutral-50 dark:border-neutral-800/70 dark:bg-neutral-900/50 text-[11px]"
                      >
                        <span className="font-bold text-neutral-900 dark:text-white">
                          {arch.reference_system || arch.domain}
                        </span>
                        <p className="mt-1 text-neutral-600 dark:text-neutral-300">
                          {arch.relevance_reason || arch.structural_comparison}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
