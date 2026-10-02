"use client";

import React, { useState, useEffect } from "react";
import {
  FileText,
  Code2,
  Copy,
  Check,
  RotateCcw,
  Plus,
  Trash2,
  Sparkles,
  ArrowRight,
  ShieldAlert,
  Sliders,
  Users,
  CheckCircle2,
  Loader2,
  AlertCircle,
  Cpu,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

interface FunctionalRequirement {
  id: string;
  title: string;
  description: string;
  priority?: "P0" | "P1" | "P2" | string;
  compliance?: string;
}

interface ArsrsStructure {
  metadata?: {
    document_type?: string;
    version?: string;
    system_name?: string;
    domain?: string;
    status?: string;
    generated_at?: string;
    [key: string]: unknown;
  };
  system_overview?: {
    problem_statement?: string;
    architecture_pattern?: string;
    primary_actors?: string[];
    clarified_specifications?: Record<string, string>;
    [key: string]: unknown;
  };
  functional_requirements?: FunctionalRequirement[];
  non_functional_requirements?: {
    availability?: string;
    latency?: string;
    scalability?: string;
    security?: string;
    compliance?: string;
    [key: string]: unknown;
  };
  data_model_overview?: {
    primary_entities?: string[];
    database_strategy?: string;
    caching_strategy?: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

interface ArsrsEditorProps {
  initialData: Record<string, unknown>;
  onProceed: (editedArsrs: Record<string, unknown>) => void;
  isGenerating?: boolean;
}

export default function ArsrsEditor({
  initialData,
  onProceed,
  isGenerating = false,
}: ArsrsEditorProps) {
  // View mode: "normal" (Formatted interactive UI) or "json" (Text JSON editor)
  const [viewMode, setViewMode] = useState<"normal" | "json">("normal");

  // Local structured document state
  const [doc, setDoc] = useState<ArsrsStructure>(() => {
    try {
      return JSON.parse(JSON.stringify(initialData));
    } catch {
      return {};
    }
  });

  // Text JSON state with live validation
  const [jsonString, setJsonString] = useState<string>(() =>
    JSON.stringify(initialData, null, 2)
  );
  const [jsonError, setJsonError] = useState<string | null>(null);

  // Actor tag input state
  const [newActor, setNewActor] = useState("");
  const [copied, setCopied] = useState(false);

  // Sync to doc whenever initialData changes externally
  useEffect(() => {
    try {
      const cloned = JSON.parse(JSON.stringify(initialData));
      setDoc(cloned);
      setJsonString(JSON.stringify(cloned, null, 2));
      setJsonError(null);
    } catch {
      // ignore
    }
  }, [initialData]);

  // Handle switching between Normal and JSON views
  const handleSwitchTab = (newMode: "normal" | "json") => {
    if (newMode === "json") {
      // Serialize current normal doc to JSON
      setJsonString(JSON.stringify(doc, null, 2));
      setJsonError(null);
      setViewMode("json");
    } else {
      // Parse JSON back to doc
      try {
        const parsed = JSON.parse(jsonString);
        setDoc(parsed);
        setJsonError(null);
        setViewMode("normal");
      } catch (err) {
        setJsonError(
          err instanceof Error
            ? `Cannot switch: ${err.message}`
            : "Invalid JSON format"
        );
      }
    }
  };

  // Text JSON onChange with on-the-fly validation
  const handleJsonTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setJsonString(val);
    try {
      const parsed = JSON.parse(val);
      setDoc(parsed);
      setJsonError(null);
    } catch (err) {
      setJsonError(err instanceof Error ? err.message : "Invalid JSON syntax");
    }
  };

  const handlePrettifyJson = () => {
    try {
      const parsed = JSON.parse(jsonString);
      const pretty = JSON.stringify(parsed, null, 2);
      setJsonString(pretty);
      setDoc(parsed);
      setJsonError(null);
    } catch (err) {
      setJsonError(err instanceof Error ? err.message : "Syntax error");
    }
  };

  const handleCopyJson = () => {
    const textToCopy =
      viewMode === "json" ? jsonString : JSON.stringify(doc, null, 2);
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleReset = () => {
    const orig = JSON.parse(JSON.stringify(initialData));
    setDoc(orig);
    setJsonString(JSON.stringify(orig, null, 2));
    setJsonError(null);
  };

  // Normal mode: Update system overview
  const updateOverviewField = (field: string, val: string) => {
    setDoc((prev) => {
      const next = {
        ...prev,
        system_overview: {
          ...prev.system_overview,
          [field]: val,
        },
      };
      setJsonString(JSON.stringify(next, null, 2));
      return next;
    });
  };

  // Normal mode: Update metadata system name
  const updateSystemName = (name: string) => {
    setDoc((prev) => {
      const next = {
        ...prev,
        metadata: {
          ...prev.metadata,
          system_name: name,
        },
      };
      setJsonString(JSON.stringify(next, null, 2));
      return next;
    });
  };

  // Normal mode: Actor Tag Management
  const handleAddActor = () => {
    const trimmed = newActor.trim();
    if (!trimmed) return;
    setDoc((prev) => {
      const currentActors = prev.system_overview?.primary_actors || [];
      if (currentActors.includes(trimmed)) return prev;
      const next = {
        ...prev,
        system_overview: {
          ...prev.system_overview,
          primary_actors: [...currentActors, trimmed],
        },
      };
      setJsonString(JSON.stringify(next, null, 2));
      return next;
    });
    setNewActor("");
  };

  const handleRemoveActor = (index: number) => {
    setDoc((prev) => {
      const currentActors = [...(prev.system_overview?.primary_actors || [])];
      currentActors.splice(index, 1);
      const next = {
        ...prev,
        system_overview: {
          ...prev.system_overview,
          primary_actors: currentActors,
        },
      };
      setJsonString(JSON.stringify(next, null, 2));
      return next;
    });
  };

  // Normal mode: Functional Requirements Management
  const handleAddFunctionalReq = () => {
    setDoc((prev) => {
      const currentFns = prev.functional_requirements || [];
      const newId = `FR-${String(currentFns.length + 1).padStart(2, "0")}`;
      const newReq: FunctionalRequirement = {
        id: newId,
        title: "New Functional Requirement",
        description: "Describe the architectural workflow, inputs, and outputs...",
        priority: "P1",
      };
      const next = {
        ...prev,
        functional_requirements: [...currentFns, newReq],
      };
      setJsonString(JSON.stringify(next, null, 2));
      return next;
    });
  };

  const handleUpdateFunctionalReq = (
    index: number,
    field: keyof FunctionalRequirement,
    val: string
  ) => {
    setDoc((prev) => {
      const currentFns = [...(prev.functional_requirements || [])];
      if (!currentFns[index]) return prev;
      currentFns[index] = {
        ...currentFns[index],
        [field]: val,
      };
      const next = {
        ...prev,
        functional_requirements: currentFns,
      };
      setJsonString(JSON.stringify(next, null, 2));
      return next;
    });
  };

  const handleDeleteFunctionalReq = (index: number) => {
    setDoc((prev) => {
      const currentFns = [...(prev.functional_requirements || [])];
      currentFns.splice(index, 1);
      const next = {
        ...prev,
        functional_requirements: currentFns,
      };
      setJsonString(JSON.stringify(next, null, 2));
      return next;
    });
  };

  // Normal mode: Non-Functional Requirements Management
  const updateNfrField = (field: string, val: string) => {
    setDoc((prev) => {
      const next = {
        ...prev,
        non_functional_requirements: {
          ...prev.non_functional_requirements,
          [field]: val,
        },
      };
      setJsonString(JSON.stringify(next, null, 2));
      return next;
    });
  };

  // Normal mode: Clarified Specs (from interview)
  const updateClarifiedSpec = (key: string, val: string) => {
    setDoc((prev) => {
      const next = {
        ...prev,
        system_overview: {
          ...prev.system_overview,
          clarified_specifications: {
            ...prev.system_overview?.clarified_specifications,
            [key]: val,
          },
        },
      };
      setJsonString(JSON.stringify(next, null, 2));
      return next;
    });
  };

  // Proceed button submission
  const handleProceedClick = () => {
    if (viewMode === "json") {
      try {
        const parsed = JSON.parse(jsonString);
        onProceed(parsed);
      } catch (err) {
        setJsonError(
          err instanceof Error
            ? `Fix JSON error first: ${err.message}`
            : "Invalid JSON format"
        );
      }
    } else {
      onProceed(doc);
    }
  };

  const fns = doc.functional_requirements || [];
  const actors = doc.system_overview?.primary_actors || [];
  const nfrs = doc.non_functional_requirements || {};
  const clarified = doc.system_overview?.clarified_specifications || {};

  return (
    <div className="relative my-3.5 overflow-hidden rounded-2xl border border-neutral-200 bg-white/95 p-4 sm:p-6 shadow-[0_15px_50px_rgba(0,0,0,0.08)] backdrop-blur-2xl text-neutral-900 transition-all dark:border-blue-500/30 dark:bg-neutral-950/95 dark:text-white dark:shadow-[0_15px_50px_rgba(0,0,0,0.8)]">
      {/* Top subtle ambient glow */}
      <div className="pointer-events-none absolute -top-24 left-1/2 -translate-x-1/2 w-96 h-40 bg-gradient-to-r from-blue-500/10 via-sky-500/10 to-purple-500/10 dark:from-blue-500/20 dark:via-sky-500/15 dark:to-purple-500/20 blur-3xl rounded-full" />

      {/* ── Header: Title, Mode Switcher (Normal <-> JSON), Copy & Reset ── */}
      <div className="relative z-10 flex flex-wrap items-center justify-between gap-3 border-b border-neutral-200 dark:border-white/10 pb-4 mb-5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow-md">
            <FileText className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base sm:text-lg font-bold tracking-tight text-neutral-900 dark:text-white">
                Architecture Specification (ARSRS)
              </h3>
              <span className="rounded-full bg-blue-500/10 border border-blue-400/30 px-2 py-0.5 text-[10px] font-mono text-blue-600 dark:bg-blue-500/20 dark:text-sky-300">
                v2.0.0
              </span>
            </div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">
              Review and edit requirements before synthesizing High-Level Design (HLD)
            </p>
          </div>
        </div>

        {/* View Switcher: Normal vs Text JSON */}
        <div className="flex items-center gap-2">
          {/* Segmented Control */}
          <div className="flex items-center rounded-xl border border-neutral-200 bg-neutral-100 p-1 dark:border-white/10 dark:bg-white/5">
            <button
              type="button"
              onClick={() => handleSwitchTab("normal")}
              className={cn(
                "flex items-center gap-1.5 rounded-lg px-3 py-1 text-xs font-semibold transition-all cursor-pointer",
                viewMode === "normal"
                  ? "bg-blue-600 text-white shadow-xs font-bold"
                  : "text-neutral-600 hover:text-black dark:text-neutral-400 dark:hover:text-white"
              )}
            >
              <FileText className="h-3.5 w-3.5" />
              <span>Normal View</span>
            </button>

            <button
              type="button"
              onClick={() => handleSwitchTab("json")}
              className={cn(
                "flex items-center gap-1.5 rounded-lg px-3 py-1 text-xs font-semibold transition-all cursor-pointer",
                viewMode === "json"
                  ? "bg-blue-600 text-white shadow-xs font-bold"
                  : "text-neutral-600 hover:text-black dark:text-neutral-400 dark:hover:text-white"
              )}
            >
              <Code2 className="h-3.5 w-3.5" />
              <span>Text JSON</span>
            </button>
          </div>

          {/* Action buttons */}
          <button
            type="button"
            onClick={handleCopyJson}
            title="Copy ARSRS JSON"
            className="flex items-center gap-1 rounded-xl border border-neutral-200 bg-neutral-100 px-2.5 py-1.5 text-xs text-neutral-700 hover:bg-neutral-200 hover:text-black transition-colors cursor-pointer dark:border-white/10 dark:bg-white/5 dark:text-neutral-300 dark:hover:bg-white/10 dark:hover:text-white"
          >
            {copied ? (
              <Check className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
            ) : (
              <Copy className="h-3.5 w-3.5" />
            )}
            <span className="hidden sm:inline">{copied ? "Copied" : "Copy"}</span>
          </button>

          <button
            type="button"
            onClick={handleReset}
            title="Reset to AI synthesized draft"
            className="flex items-center gap-1 rounded-xl border border-neutral-200 bg-neutral-100 px-2.5 py-1.5 text-xs text-neutral-700 hover:bg-neutral-200 hover:text-black transition-colors cursor-pointer dark:border-white/10 dark:bg-white/5 dark:text-neutral-300 dark:hover:bg-white/10 dark:hover:text-white"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Reset</span>
          </button>
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════
          MODE A: NORMAL / STRUCTURED FORMATTED REQUIREMENTS EDITOR
          ══════════════════════════════════════════════════════════ */}
      {viewMode === "normal" && (
        <div className="space-y-5 max-h-[560px] overflow-y-auto pr-1">
          {/* Section 1: System Overview */}
          <div className="space-y-3 rounded-2xl border border-neutral-200 bg-neutral-50/70 p-4 dark:border-white/10 dark:bg-white/[0.03]">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-sky-600 dark:text-sky-400 flex items-center gap-1.5">
                <Sliders className="h-3.5 w-3.5" />
                <span>1. System Overview & Problem Statement</span>
              </span>
              <span className="text-[10px] text-neutral-500 dark:text-neutral-400">Editable</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] font-semibold text-neutral-600 dark:text-neutral-400 block mb-1">
                  System Title:
                </label>
                <input
                  type="text"
                  value={doc.metadata?.system_name || ""}
                  onChange={(e) => updateSystemName(e.target.value)}
                  placeholder="e.g. College Library Management System"
                  className="w-full rounded-xl border border-neutral-300 bg-white px-3 py-2 text-xs sm:text-sm text-neutral-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 dark:border-white/10 dark:bg-black/60 dark:text-white"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-neutral-600 dark:text-neutral-400 block mb-1">
                  Architecture Pattern:
                </label>
                <input
                  type="text"
                  value={doc.system_overview?.architecture_pattern || ""}
                  onChange={(e) => updateOverviewField("architecture_pattern", e.target.value)}
                  placeholder="e.g. Modular Cloud Microservices with Reactive Event Streams"
                  className="w-full rounded-xl border border-neutral-300 bg-white px-3 py-2 text-xs sm:text-sm text-neutral-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 dark:border-white/10 dark:bg-black/60 dark:text-white"
                />
              </div>
            </div>

            <div>
              <label className="text-[11px] font-semibold text-neutral-600 dark:text-neutral-400 block mb-1">
                Problem Statement / Requirements Scope:
              </label>
              <textarea
                rows={2}
                value={doc.system_overview?.problem_statement || ""}
                onChange={(e) => updateOverviewField("problem_statement", e.target.value)}
                placeholder="Describe primary problem statement and scope..."
                className="w-full rounded-xl border border-neutral-300 bg-white p-3 text-xs sm:text-sm text-neutral-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 resize-y leading-relaxed dark:border-white/10 dark:bg-black/60 dark:text-white"
              />
            </div>
          </div>

          {/* Section 2: Primary Stakeholder Actors */}
          <div className="space-y-3 rounded-2xl border border-neutral-200 bg-neutral-50/70 p-4 dark:border-white/10 dark:bg-white/[0.03]">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-purple-600 dark:text-purple-400 flex items-center gap-1.5">
                <Users className="h-3.5 w-3.5" />
                <span>2. Primary Stakeholder Actors ({actors.length})</span>
              </span>
              <span className="text-[10px] text-neutral-500 dark:text-neutral-400">Click &apos;×&apos; to remove</span>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {actors.map((actor, idx) => (
                <span
                  key={idx}
                  className="group inline-flex items-center gap-1.5 rounded-full border border-purple-300 bg-purple-50 px-3 py-1 text-xs font-semibold text-purple-700 dark:border-purple-500/30 dark:bg-purple-500/10 dark:text-purple-200"
                >
                  <span>{actor}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveActor(idx)}
                    title={`Remove ${actor}`}
                    className="h-4 w-4 rounded-full text-purple-600 hover:bg-purple-200 hover:text-purple-900 dark:text-purple-400 dark:hover:bg-purple-500/30 dark:hover:text-white flex items-center justify-center transition-colors cursor-pointer"
                  >
                    ×
                  </button>
                </span>
              ))}

              {/* Add Actor Input */}
              <div className="flex items-center gap-1.5">
                <input
                  type="text"
                  value={newActor}
                  onChange={(e) => setNewActor(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleAddActor();
                    }
                  }}
                  placeholder="+ Add Actor..."
                  className="rounded-full border border-neutral-300 bg-white px-3 py-1 text-xs text-neutral-900 placeholder:text-neutral-400 outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/30 w-32 dark:border-white/10 dark:bg-black/60 dark:text-white dark:placeholder:text-neutral-500"
                />
                {newActor.trim() && (
                  <button
                    type="button"
                    onClick={handleAddActor}
                    className="rounded-full bg-purple-600 px-2 py-1 text-[11px] font-bold text-white hover:bg-purple-500 cursor-pointer"
                  >
                    Add
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Section 3: Functional Requirements (Editable List) */}
          <div className="space-y-3 rounded-2xl border border-neutral-200 bg-neutral-50/70 p-4 dark:border-white/10 dark:bg-white/[0.03]">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>3. Functional Requirements ({fns.length})</span>
              </span>

              <button
                type="button"
                onClick={handleAddFunctionalReq}
                className="flex items-center gap-1 rounded-xl bg-emerald-600 hover:bg-emerald-500 px-2.5 py-1 text-xs font-bold text-white transition-colors cursor-pointer shadow-xs"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Add Requirement</span>
              </button>
            </div>

            <div className="space-y-3">
              {fns.map((req, idx) => (
                <div
                  key={req.id || idx}
                  className="relative space-y-2 rounded-xl border border-neutral-200 bg-white p-3.5 transition-all hover:border-neutral-300 dark:border-white/10 dark:bg-black/50 dark:hover:border-white/20 shadow-2xs"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 flex-1">
                      <span className="rounded bg-neutral-100 px-2 py-0.5 text-[11px] font-mono font-bold text-neutral-700 dark:bg-white/10 dark:text-neutral-300">
                        {req.id}
                      </span>

                      {/* Priority selector */}
                      <select
                        value={req.priority || "P1"}
                        onChange={(e) =>
                          handleUpdateFunctionalReq(idx, "priority", e.target.value)
                        }
                        className={cn(
                          "rounded-lg px-2 py-0.5 text-[11px] font-bold outline-none cursor-pointer border",
                          req.priority === "P0"
                            ? "bg-red-50 text-red-700 border-red-200 dark:bg-red-500/20 dark:text-red-300 dark:border-red-500/30"
                            : req.priority === "P1"
                            ? "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-500/20 dark:text-amber-300 dark:border-amber-500/30"
                            : "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-500/20 dark:text-blue-300 dark:border-blue-500/30"
                        )}
                      >
                        <option value="P0" className="bg-white text-red-700 dark:bg-neutral-900 dark:text-red-300">
                          P0 - Critical
                        </option>
                        <option value="P1" className="bg-white text-amber-700 dark:bg-neutral-900 dark:text-amber-300">
                          P1 - High
                        </option>
                        <option value="P2" className="bg-white text-blue-700 dark:bg-neutral-900 dark:text-blue-300">
                          P2 - Standard
                        </option>
                      </select>

                      {/* Editable Requirement Title */}
                      <input
                        type="text"
                        value={req.title}
                        onChange={(e) =>
                          handleUpdateFunctionalReq(idx, "title", e.target.value)
                        }
                        placeholder="Requirement title..."
                        className="flex-1 rounded-lg border border-transparent hover:border-neutral-200 focus:border-blue-500 bg-transparent px-2 py-0.5 text-xs sm:text-sm font-bold text-neutral-900 dark:text-white dark:hover:border-white/10 outline-none"
                      />
                    </div>

                    <button
                      type="button"
                      onClick={() => handleDeleteFunctionalReq(idx)}
                      title="Delete requirement"
                      className="text-neutral-400 hover:text-red-600 dark:text-neutral-500 dark:hover:text-red-400 p-1 transition-colors cursor-pointer"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>

                  {/* Editable Description */}
                  <textarea
                    rows={2}
                    value={req.description}
                    onChange={(e) =>
                      handleUpdateFunctionalReq(idx, "description", e.target.value)
                    }
                    placeholder="Describe functional requirement behavior..."
                    className="w-full rounded-lg border border-neutral-200 hover:border-neutral-300 focus:border-blue-500 bg-neutral-50/60 p-2 text-xs text-neutral-700 outline-none leading-relaxed resize-y dark:border-white/5 dark:bg-black/40 dark:text-neutral-300 dark:hover:border-white/10"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Section 4: Non-Functional Requirements & SLAs */}
          <div className="space-y-3 rounded-2xl border border-neutral-200 bg-neutral-50/70 p-4 dark:border-white/10 dark:bg-white/[0.03]">
            <span className="text-xs font-bold uppercase tracking-wider text-sky-600 dark:text-sky-400 flex items-center gap-1.5">
              <ShieldAlert className="h-3.5 w-3.5" />
              <span>4. Non-Functional Requirements (NFR) & SLAs</span>
            </span>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] font-semibold text-neutral-600 dark:text-neutral-400 block mb-1">
                  Availability SLA:
                </label>
                <input
                  type="text"
                  value={String(nfrs.availability || "")}
                  onChange={(e) => updateNfrField("availability", e.target.value)}
                  placeholder="e.g. 99.95% multi-zone high-availability SLA"
                  className="w-full rounded-xl border border-neutral-300 bg-white px-3 py-2 text-xs text-neutral-900 outline-none focus:border-blue-500 dark:border-white/10 dark:bg-black/60 dark:text-white"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-neutral-600 dark:text-neutral-400 block mb-1">
                  Latency Target:
                </label>
                <input
                  type="text"
                  value={String(nfrs.latency || "")}
                  onChange={(e) => updateNfrField("latency", e.target.value)}
                  placeholder="e.g. < 120ms p95 API response time"
                  className="w-full rounded-xl border border-neutral-300 bg-white px-3 py-2 text-xs text-neutral-900 outline-none focus:border-blue-500 dark:border-white/10 dark:bg-black/60 dark:text-white"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-neutral-600 dark:text-neutral-400 block mb-1">
                  Horizontal Scalability:
                </label>
                <input
                  type="text"
                  value={String(nfrs.scalability || "")}
                  onChange={(e) => updateNfrField("scalability", e.target.value)}
                  placeholder="e.g. Auto-scaling 2 to 50 replica pods"
                  className="w-full rounded-xl border border-neutral-300 bg-white px-3 py-2 text-xs text-neutral-900 outline-none focus:border-blue-500 dark:border-white/10 dark:bg-black/60 dark:text-white"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-neutral-600 dark:text-neutral-400 block mb-1">
                  Security & Compliance:
                </label>
                <input
                  type="text"
                  value={String(nfrs.security || nfrs.compliance || "")}
                  onChange={(e) => updateNfrField("security", e.target.value)}
                  placeholder="e.g. TLS 1.3 in-transit, AES-256 at-rest, OAuth2 PKCE"
                  className="w-full rounded-xl border border-neutral-300 bg-white px-3 py-2 text-xs text-neutral-900 outline-none focus:border-blue-500 dark:border-white/10 dark:bg-black/60 dark:text-white"
                />
              </div>
            </div>
          </div>

          {/* Section 5: Clarified Architectural Specifications from Interview */}
          {Object.keys(clarified).length > 0 && (
            <div className="space-y-3 rounded-2xl border border-neutral-200 bg-neutral-50/70 p-4 dark:border-white/10 dark:bg-white/[0.03]">
              <span className="text-xs font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400 flex items-center gap-1.5">
                <Cpu className="h-3.5 w-3.5" />
                <span>5. Interview Clarifications & Constraints</span>
              </span>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {Object.entries(clarified).map(([key, val]) => (
                  <div key={key} className="rounded-xl border border-neutral-200 bg-white p-2.5 dark:border-white/10 dark:bg-black/40 shadow-2xs">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-neutral-500 dark:text-neutral-400 block mb-1">
                      {key.replace(/_/g, " ")}:
                    </span>
                    <input
                      type="text"
                      value={String(val)}
                      onChange={(e) => updateClarifiedSpec(key, e.target.value)}
                      className="w-full rounded-lg border border-neutral-300 bg-neutral-50 px-2 py-1 text-xs text-neutral-800 outline-none focus:border-amber-500 dark:border-white/5 dark:bg-black/60 dark:text-neutral-200"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════
          MODE B: TEXT JSON RAW SPECIFICATION EDITOR
          ══════════════════════════════════════════════════════════ */}
      {viewMode === "json" && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-neutral-600 dark:text-neutral-400">
                ARSRS JSON Raw Document:
              </span>
              {jsonError ? (
                <span className="inline-flex items-center gap-1 rounded-md bg-red-500/10 px-2 py-0.5 text-[11px] font-semibold text-red-600 dark:bg-red-500/20 dark:text-red-400">
                  <AlertCircle className="h-3 w-3" />
                  <span>Invalid JSON</span>
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 rounded-md bg-emerald-500/10 px-2 py-0.5 text-[11px] font-semibold text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400">
                  <Check className="h-3 w-3" />
                  <span>Valid JSON</span>
                </span>
              )}
            </div>

            <button
              type="button"
              onClick={handlePrettifyJson}
              className="rounded-lg border border-neutral-300 bg-neutral-100 px-2.5 py-1 text-xs text-neutral-700 hover:bg-neutral-200 hover:text-black transition-colors cursor-pointer dark:border-white/10 dark:bg-white/5 dark:text-neutral-300 dark:hover:bg-white/10 dark:hover:text-white"
            >
              Prettify JSON
            </button>
          </div>

          <textarea
            value={jsonString}
            onChange={handleJsonTextChange}
            rows={18}
            className="w-full rounded-2xl border border-neutral-300 bg-neutral-900 p-4 font-mono text-xs text-emerald-400 leading-relaxed outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 selection:bg-blue-500/30 dark:border-white/10 dark:bg-[#0d1117] dark:text-emerald-300"
          />

          {jsonError && (
            <p className="rounded-xl border border-red-500/30 bg-red-500/10 p-2.5 text-xs text-red-600 dark:text-red-400 font-mono">
              {jsonError}
            </p>
          )}
        </div>
      )}

      {/* ── Action Footer: Summary & "Proceed to Generate Design" ── */}
      <div className="relative z-10 flex flex-wrap items-center justify-between gap-4 pt-5 mt-5 border-t border-neutral-200 dark:border-white/10">
        <div className="flex items-center gap-2 text-xs text-neutral-600 dark:text-neutral-400 font-medium">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>
            {fns.length} Functional Requirements • {actors.length} Stakeholder Actors
          </span>
        </div>

        <Button
          onClick={handleProceedClick}
          disabled={isGenerating || Boolean(jsonError && viewMode === "json")}
          variant="glow"
          size="lg"
          neon={true}
          className="px-8 py-3.5 text-xs sm:text-sm font-bold tracking-wide cursor-pointer shadow-lg active:scale-98"
        >
          {isGenerating ? (
            <span className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin text-blue-400" />
              <span>Synthesizing HLD Architecture...</span>
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-sky-400" />
              <span>Proceed to Generate Design</span>
              <ArrowRight className="h-4 w-4 stroke-[2.5]" />
            </span>
          )}
        </Button>
      </div>
    </div>
  );
}
