"use client";

import React, { useState } from "react";
import {
  X,
  Cpu,
  Globe,
  Server,
  Database,
  ShieldCheck,
  Cloud,
  CheckCircle2,
  XCircle,
  Trophy,
  Copy,
  Check,
  Scale,
  Sparkles,
  ArrowRight,
  Code2,
  Sliders,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import { getTechRationale, type TechRationale, type AlternativeEvaluation } from "@/lib/tech-rationale";

export default function ExplainModal() {
  const {
    explainOpen,
    explainNode,
    explainTitle,
    explainContent,
    explainNodeData,
    closeExplain,
    activeModelId,
  } = useAppStore();

  const isArchova = !activeModelId || activeModelId === "archova";
  const [activeTab, setActiveTab] = useState<"rationale" | "alternatives" | "spec">(
    isArchova ? "rationale" : "spec"
  );
  const [copied, setCopied] = useState(false);

  React.useEffect(() => {
    if (!isArchova) {
      setActiveTab("spec");
    }
  }, [isArchova, explainOpen]);

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeExplain();
    };
    if (explainOpen) {
      window.addEventListener("keydown", handleKeyDown);
      return () => window.removeEventListener("keydown", handleKeyDown);
    }
  }, [explainOpen, closeExplain]);

  if (!explainOpen || !explainNode) return null;

  // Resolve rich architectural rationale using tech-rationale engine
  const nodeContext = {
    id: explainNode,
    label: explainTitle || explainNode.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
    description: explainContent || "",
    ...((explainNodeData || {}) as Record<string, unknown>),
  };

  const rationale: TechRationale = getTechRationale(nodeContext);

  const rawContent =
    explainContent ||
    (nodeContext.description as string) ||
    "Component synthesized by the AI Architecture Engine (REE + SAE).";

  const isJson = rawContent.trim().startsWith("{") || rawContent.trim().startsWith("[");

  // Determine icon based on category
  const lowerCat = `${rationale.category} ${rationale.componentName} ${rationale.techName}`.toLowerCase();
  const IconComponent =
    lowerCat.includes("frontend") || lowerCat.includes("client")
      ? Globe
      : lowerCat.includes("gateway") || lowerCat.includes("ingress")
      ? ShieldCheck
      : lowerCat.includes("database") || lowerCat.includes("cache")
      ? Database
      : lowerCat.includes("cloud") || lowerCat.includes("docker") || lowerCat.includes("kubernetes")
      ? Cloud
      : lowerCat.includes("security") || lowerCat.includes("auth")
      ? ShieldCheck
      : Server;

  const handleCopyMarkdown = () => {
    const text = `### Architecture Decision Record (ADR): ${rationale.componentName}
**Selected Technology:** ${rationale.techName}
**Category:** ${rationale.category}

#### Why Selected:
${rationale.whySelected}

#### Key Capabilities:
${rationale.keyCapabilities.map((c) => `- ${c}`).join("\n")}

#### Why It Is Best for This Application:
${rationale.whyBestFit}

#### Alternatives Evaluated:
${rationale.alternatives
  .map(
    (a) =>
      `##### ${a.name}
- **Pros:** ${a.pros.join(", ")}
- **Cons:** ${a.cons.join(", ")}
- **Verdict:** ${a.verdict}`
  )
  .join("\n\n")}

#### Accepted Trade-offs:
${rationale.tradeoffs.map((t) => `- **Trade-off:** ${t.acceptedTradeoff}\n  - **Mitigation:** ${t.mitigationStrategy}`).join("\n")}
`;

    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      onClick={(e) => {
        if (e.target === e.currentTarget) closeExplain();
      }}
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/75 backdrop-blur-md p-4 animate-in fade-in duration-150"
    >
      <div className="relative mx-auto flex h-[88vh] max-h-[780px] w-full max-w-3xl flex-col rounded-3xl border border-neutral-300 bg-white shadow-2xl dark:border-neutral-800 dark:bg-neutral-950 text-neutral-900 dark:text-neutral-100 overflow-hidden">
        {/* Top Gradient Accent Banner */}
        <div className="h-1.5 w-full bg-gradient-to-r from-blue-600 via-indigo-500 to-purple-600 shrink-0" />

        {/* ── Modal Header ── */}
        <div className="flex items-start justify-between border-b border-neutral-200/80 px-6 py-4.5 dark:border-neutral-800/80 shrink-0 bg-neutral-50/50 dark:bg-neutral-900/40">
          <div className="flex items-start gap-3.5 min-w-0">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-neutral-900 to-neutral-800 text-white shadow-md dark:from-neutral-100 dark:to-neutral-300 dark:text-neutral-900">
              <IconComponent className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <span className="rounded-md bg-blue-500/10 px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wider text-blue-600 dark:bg-blue-400/15 dark:text-blue-400 border border-blue-500/20">
                  {rationale.category}
                </span>
                {isArchova ? (
                  <span className="flex items-center gap-1 rounded-md bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-600 dark:bg-emerald-400/15 dark:text-emerald-400 border border-emerald-500/20">
                    <CheckCircle2 className="h-3 w-3" />
                    <span>Architecture Decision (ADR)</span>
                  </span>
                ) : (
                  <span className="flex items-center gap-1 rounded-md bg-neutral-500/10 px-2 py-0.5 text-[10px] font-bold text-neutral-600 dark:bg-neutral-400/15 dark:text-neutral-400 border border-neutral-500/20">
                    <Cpu className="h-3 w-3" />
                    <span>Direct LLM Model Spec</span>
                  </span>
                )}
              </div>
              <h2 className="font-heading text-lg font-black tracking-tight text-neutral-950 dark:text-white truncate">
                {rationale.componentName}
              </h2>
              <p className="text-xs font-semibold text-neutral-600 dark:text-neutral-400 font-mono mt-0.5">
                {rationale.techName}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0 ml-3">
            {isArchova && (
              <button
                type="button"
                onClick={handleCopyMarkdown}
                className="flex items-center gap-1.5 rounded-xl border border-neutral-200 bg-white px-3 py-1.5 text-xs font-semibold text-neutral-700 shadow-2xs hover:bg-neutral-100 dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-300 dark:hover:bg-neutral-800 transition-all cursor-pointer"
                title="Copy ADR Rationale (Markdown)"
              >
                {copied ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
                <span className="hidden sm:inline">{copied ? "Copied ADR" : "Copy Rationale"}</span>
              </button>
            )}

            <button
              type="button"
              onClick={closeExplain}
              className="rounded-xl p-2 text-neutral-400 transition-colors hover:bg-neutral-100 hover:text-black dark:hover:bg-neutral-900 dark:hover:text-white cursor-pointer"
              title="Close Dialog"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Notice for non-Archova LLM models */}
        {!isArchova && (
          <div className="mx-6 mt-3.5 mb-1 rounded-xl border border-amber-500/25 bg-amber-50/70 dark:border-amber-500/20 dark:bg-amber-950/25 px-4 py-2.5 text-xs text-amber-900 dark:text-amber-200 flex items-center gap-2.5 shrink-0">
            <Sparkles className="h-4 w-4 text-amber-500 shrink-0" />
            <span>
              <strong>Note:</strong> In-detail architectural justification, ADR decisions, and trade-offs are available exclusively for <strong>Archova AI Engine</strong> designs. Baseline LLM designs display component specifications only.
            </span>
          </div>
        )}

        {/* ── Navigation Tabs ── */}
        <div className="flex items-center gap-2 border-b border-neutral-200/80 px-6 py-2.5 bg-neutral-100/60 dark:border-neutral-800/80 dark:bg-neutral-900/60 shrink-0">
          {isArchova && (
            <>
              <button
                type="button"
                onClick={() => setActiveTab("rationale")}
                className={`flex items-center gap-2 rounded-xl px-3.5 py-1.5 text-xs font-bold transition-all cursor-pointer ${
                  activeTab === "rationale"
                    ? "bg-white text-black shadow-xs dark:bg-neutral-800 dark:text-white"
                    : "text-neutral-600 hover:text-black dark:text-neutral-400 dark:hover:text-white"
                }`}
              >
                <Trophy className="h-3.5 w-3.5 text-amber-500" />
                <span>Why This Tech & Fit</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab("alternatives")}
                className={`flex items-center gap-2 rounded-xl px-3.5 py-1.5 text-xs font-bold transition-all cursor-pointer ${
                  activeTab === "alternatives"
                    ? "bg-white text-black shadow-xs dark:bg-neutral-800 dark:text-white"
                    : "text-neutral-600 hover:text-black dark:text-neutral-400 dark:hover:text-white"
                }`}
              >
                <Scale className="h-3.5 w-3.5 text-blue-500" />
                <span>Alternatives Evaluated ({rationale.alternatives.length})</span>
              </button>
            </>
          )}

          <button
            type="button"
            onClick={() => setActiveTab("spec")}
            className={`flex items-center gap-2 rounded-xl px-3.5 py-1.5 text-xs font-bold transition-all cursor-pointer ${
              activeTab === "spec"
                ? "bg-white text-black shadow-xs dark:bg-neutral-800 dark:text-white"
                : "text-neutral-600 hover:text-black dark:text-neutral-400 dark:hover:text-white"
            }`}
          >
            <Code2 className="h-3.5 w-3.5 text-emerald-500" />
            <span>Technical Spec & Metadata</span>
          </button>
        </div>

        {/* ── Tab Content Area (Scrollable) ── */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5 min-h-0 text-sm">
          {/* ════ TAB 1: WHY SELECTED & BEST FIT (ARCHOVA ONLY) ════ */}
          {isArchova && activeTab === "rationale" && (
            <div className="space-y-5 animate-in fade-in duration-100">
              {/* Primary Architectural Justification Callout */}
              <div className="rounded-2xl border border-blue-500/20 bg-blue-50/50 p-4.5 dark:border-blue-500/20 dark:bg-blue-950/20">
                <div className="flex items-center gap-2 text-blue-700 dark:text-blue-300 font-bold text-xs uppercase tracking-wider mb-2">
                  <Sparkles className="h-4 w-4 text-blue-500" />
                  <span>Strategic Architectural Rationale</span>
                </div>
                <p className="text-xs sm:text-sm leading-relaxed text-neutral-800 dark:text-neutral-200">
                  {rationale.whySelected}
                </p>
              </div>

              {/* Core Capabilities */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400 mb-2.5">
                  Key Capabilities Provided
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {rationale.keyCapabilities.map((cap, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-2.5 rounded-xl border border-neutral-200/80 bg-neutral-50/70 p-3 text-xs dark:border-neutral-800/80 dark:bg-neutral-900/40"
                    >
                      <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-500 mt-0.5" />
                      <span className="font-medium text-neutral-700 dark:text-neutral-300 leading-snug">
                        {cap}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Decisive Reason: Why It's Best for This Application */}
              <div className="rounded-2xl border border-amber-500/20 bg-amber-50/50 p-4.5 dark:border-amber-500/20 dark:bg-amber-950/20">
                <div className="flex items-center gap-2 text-amber-700 dark:text-amber-300 font-bold text-xs uppercase tracking-wider mb-2">
                  <Trophy className="h-4 w-4 text-amber-500" />
                  <span>Why This is the Best Fit for This Specific System</span>
                </div>
                <p className="text-xs sm:text-sm leading-relaxed text-neutral-800 dark:text-neutral-200">
                  {rationale.whyBestFit}
                </p>
              </div>

              {/* Architectural Quality Scorecards */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400 mb-2.5">
                  Architectural Fitness Scorecard
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="rounded-2xl border border-neutral-200 bg-neutral-50/60 p-3 text-center dark:border-neutral-800 dark:bg-neutral-900/40">
                    <span className="text-[10px] font-semibold uppercase text-neutral-400">Performance</span>
                    <p className="font-heading text-lg font-black text-emerald-600 dark:text-emerald-400 mt-0.5">
                      {rationale.scorecard.performance}%
                    </p>
                    <span className="text-[10px] text-neutral-500">Sub-100ms I/O</span>
                  </div>

                  <div className="rounded-2xl border border-neutral-200 bg-neutral-50/60 p-3 text-center dark:border-neutral-800 dark:bg-neutral-900/40">
                    <span className="text-[10px] font-semibold uppercase text-neutral-400">Scalability</span>
                    <p className="font-heading text-lg font-black text-blue-600 dark:text-blue-400 mt-0.5">
                      {rationale.scorecard.scalability}%
                    </p>
                    <span className="text-[10px] text-neutral-500">Auto-Scaling</span>
                  </div>

                  <div className="rounded-2xl border border-neutral-200 bg-neutral-50/60 p-3 text-center dark:border-neutral-800 dark:bg-neutral-900/40">
                    <span className="text-[10px] font-semibold uppercase text-neutral-400">Reliability</span>
                    <p className="font-heading text-lg font-black text-purple-600 dark:text-purple-400 mt-0.5">
                      {rationale.scorecard.reliability}%
                    </p>
                    <span className="text-[10px] text-neutral-500">99.99% SLA</span>
                  </div>

                  <div className="rounded-2xl border border-neutral-200 bg-neutral-50/60 p-3 text-center dark:border-neutral-800 dark:bg-neutral-900/40">
                    <span className="text-[10px] font-semibold uppercase text-neutral-400">Dev Velocity</span>
                    <p className="font-heading text-lg font-black text-indigo-600 dark:text-indigo-400 mt-0.5">
                      {rationale.scorecard.developerVelocity}%
                    </p>
                    <span className="text-[10px] text-neutral-500">Ecosystem Size</span>
                  </div>
                </div>
              </div>

              {/* Trade-offs & Mitigations */}
              {rationale.tradeoffs.length > 0 && (
                <div className="rounded-2xl border border-neutral-200 bg-neutral-50/60 p-4 dark:border-neutral-800 dark:bg-neutral-900/40">
                  <div className="flex items-center gap-2 text-neutral-700 dark:text-neutral-300 font-bold text-xs uppercase tracking-wider mb-2">
                    <Sliders className="h-4 w-4 text-neutral-500" />
                    <span>Accepted Trade-off & Mitigation</span>
                  </div>
                  {rationale.tradeoffs.map((t, idx) => (
                    <div key={idx} className="space-y-1.5 text-xs">
                      <p className="text-neutral-600 dark:text-neutral-400">
                        <strong className="text-neutral-900 dark:text-neutral-200">Trade-off:</strong>{" "}
                        {t.acceptedTradeoff}
                      </p>
                      <p className="text-emerald-700 dark:text-emerald-400">
                        <strong>Mitigation Strategy:</strong> {t.mitigationStrategy}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ════ TAB 2: ALTERNATIVES EVALUATED (ARCHOVA ONLY) ════ */}
          {isArchova && activeTab === "alternatives" && (
            <div className="space-y-4 animate-in fade-in duration-100">
              <p className="text-xs text-neutral-500 dark:text-neutral-400">
                The AI Architecture Engine rigorously analyzed {rationale.alternatives.length} candidate technologies before selecting{" "}
                <strong className="text-neutral-900 dark:text-neutral-100">{rationale.techName}</strong>. Below is the comparative trade-off breakdown:
              </p>

              <div className="space-y-3.5">
                {rationale.alternatives.map((alt: AlternativeEvaluation, idx) => (
                  <div
                    key={idx}
                    className="rounded-2xl border border-neutral-200 bg-neutral-50/80 p-4 transition-all hover:border-neutral-300 dark:border-neutral-800 dark:bg-neutral-900/60 dark:hover:border-neutral-700"
                  >
                    <div className="flex items-center justify-between pb-2 mb-2.5 border-b border-neutral-200/80 dark:border-neutral-800/80">
                      <div className="flex items-center gap-2">
                        <span className="font-heading text-sm font-bold text-neutral-900 dark:text-white">
                          {alt.name}
                        </span>
                        {alt.category && (
                          <span className="text-[10px] font-semibold text-neutral-500">
                            · {alt.category}
                          </span>
                        )}
                      </div>
                      <span className="rounded-md bg-neutral-200/70 px-2 py-0.5 text-[10px] font-bold text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">
                        Alternative #{idx + 1}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3 text-xs">
                      {/* Pros */}
                      <div className="space-y-1">
                        <span className="flex items-center gap-1 font-bold text-emerald-600 dark:text-emerald-400 text-[11px]">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          <span>Pros</span>
                        </span>
                        <ul className="space-y-1 pl-4 list-disc text-neutral-600 dark:text-neutral-400 text-[11.5px]">
                          {alt.pros.map((p, pi) => (
                            <li key={pi}>{p}</li>
                          ))}
                        </ul>
                      </div>

                      {/* Cons */}
                      <div className="space-y-1">
                        <span className="flex items-center gap-1 font-bold text-red-600 dark:text-red-400 text-[11px]">
                          <XCircle className="h-3.5 w-3.5" />
                          <span>Cons</span>
                        </span>
                        <ul className="space-y-1 pl-4 list-disc text-neutral-600 dark:text-neutral-400 text-[11.5px]">
                          {alt.cons.map((c, ci) => (
                            <li key={ci}>{c}</li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {/* Verdict */}
                    <div className="rounded-xl border border-neutral-200/60 bg-white/70 p-2.5 text-xs dark:border-neutral-800/80 dark:bg-neutral-950/60">
                      <span className="font-bold text-neutral-800 dark:text-neutral-200">
                        Why Not Selected:
                      </span>{" "}
                      <span className="text-neutral-600 dark:text-neutral-400">{alt.verdict}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ════ TAB 3: SPECIFICATION & METADATA ════ */}
          {activeTab === "spec" && (
            <div className="space-y-4 animate-in fade-in duration-100">
              <div className="rounded-2xl border border-neutral-200 bg-neutral-50 p-4 dark:border-neutral-800 dark:bg-neutral-900/60 space-y-2 font-mono text-xs">
                <div className="flex items-center justify-between pb-2 border-b border-neutral-200 dark:border-neutral-800">
                  <span className="text-neutral-500">Component Identifier:</span>
                  <span className="font-bold text-neutral-900 dark:text-neutral-200">{rationale.componentId}</span>
                </div>
                <div className="flex items-center justify-between pb-2 border-b border-neutral-200 dark:border-neutral-800">
                  <span className="text-neutral-500">Component Name:</span>
                  <span className="font-bold text-neutral-900 dark:text-neutral-200">{rationale.componentName}</span>
                </div>
                <div className="flex items-center justify-between pb-2 border-b border-neutral-200 dark:border-neutral-800">
                  <span className="text-neutral-500">Technology Stack:</span>
                  <span className="font-bold text-neutral-900 dark:text-neutral-200">{rationale.techName}</span>
                </div>
                <div className="flex items-center justify-between pb-2 border-b border-neutral-200 dark:border-neutral-800">
                  <span className="text-neutral-500">Architectural Tier:</span>
                  <span className="font-bold text-neutral-900 dark:text-neutral-200">{rationale.category}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-neutral-500">Synthesis Engine:</span>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400">SAE Topology Synthesizer</span>
                </div>
              </div>

              {/* Raw JSON or description payload */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400 mb-2">
                  Node Specification Payload
                </h4>
                {isJson ? (
                  <pre className="max-h-60 overflow-y-auto rounded-xl border border-neutral-200 bg-neutral-950 p-4 font-mono text-xs text-emerald-400 dark:border-neutral-800">
                    {rawContent}
                  </pre>
                ) : (
                  <div className="rounded-xl border border-neutral-200 bg-neutral-50 p-3.5 text-xs text-neutral-700 dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-300">
                    {rawContent}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* ── Modal Footer ── */}
        <div className="flex items-center justify-between border-t border-neutral-200/80 px-6 py-3.5 bg-neutral-50/70 dark:border-neutral-800/80 dark:bg-neutral-900/50 shrink-0">
          <span className="text-[11px] text-neutral-500 dark:text-neutral-400 hidden sm:inline">
            Architecture Decision Record (ADR) backed by AI Engine Multi-Agent Verification
          </span>
          <button
            type="button"
            onClick={closeExplain}
            className="rounded-xl bg-neutral-900 px-5 py-2 text-xs font-bold text-white transition-all hover:bg-neutral-800 dark:bg-neutral-100 dark:text-neutral-900 dark:hover:bg-neutral-200 cursor-pointer shadow-xs ml-auto"
          >
            Close Dialog
          </button>
        </div>
      </div>
    </div>
  );
}
