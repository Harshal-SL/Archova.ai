"use client";

import React, { useState } from "react";
import {
  X,
  Scale,
  KeyRound,
  Check,
  Cpu,
  ShieldAlert,
  Zap,
  Info,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import {
  DEFAULT_BENCHMARK_PRESETS,
  type BenchmarkModelConfig,
} from "@/lib/ai-engine-client";

interface BenchmarkConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function BenchmarkConfigModal({
  isOpen,
  onClose,
}: BenchmarkConfigModalProps) {
  const {
    benchmarkModelsConfig,
    setBenchmarkModelsConfig,
    benchmarkApiKey,
    setBenchmarkApiKey,
  } = useAppStore();

  const [selectedIds, setSelectedIds] = useState<string[]>(
    benchmarkModelsConfig.map((m) => m.id)
  );
  const [apiKeyInput, setApiKeyInput] = useState<string>(benchmarkApiKey || "");
  const [customModelId, setCustomModelId] = useState<string>("");
  const [customModelName, setCustomModelName] = useState<string>("");

  if (!isOpen) return null;

  const toggleModel = (preset: BenchmarkModelConfig) => {
    if (selectedIds.includes(preset.id)) {
      setSelectedIds(selectedIds.filter((id) => id !== preset.id));
    } else {
      setSelectedIds([...selectedIds, preset.id]);
    }
  };

  const handleAddCustomModel = () => {
    if (!customModelId.trim()) return;
    const cleanId = customModelId.toLowerCase().replace(/[^a-z0-9-_]/g, "-");
    const newModel: BenchmarkModelConfig = {
      id: cleanId,
      name: customModelName.trim() || customModelId.trim(),
      model_id: customModelId.trim(),
      provider: "openrouter",
    };
    setSelectedIds([...selectedIds, newModel.id]);
    setBenchmarkModelsConfig([...benchmarkModelsConfig, newModel]);
    setCustomModelId("");
    setCustomModelName("");
  };

  const handleSave = () => {
    // Combine presets and any custom models that match selectedIds
    const allCandidates = [
      ...DEFAULT_BENCHMARK_PRESETS,
      ...benchmarkModelsConfig.filter(
        (m) => !DEFAULT_BENCHMARK_PRESETS.some((p) => p.id === m.id)
      ),
    ];
    const filtered = allCandidates.filter((m) => selectedIds.includes(m.id));

    setBenchmarkModelsConfig(filtered);
    setBenchmarkApiKey(apiKeyInput.trim());
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-xl rounded-2xl border border-neutral-200 bg-white p-6 shadow-2xl dark:border-neutral-800 dark:bg-neutral-950 text-neutral-900 dark:text-white">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-neutral-100 dark:border-neutral-800">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 text-white shadow-md">
              <Scale className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold">Benchmark LLM Models</h3>
              <p className="text-xs text-neutral-500 dark:text-neutral-400">
                Direct 1-shot architecture generation evaluated by the Validator Engine
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-neutral-400 hover:bg-neutral-100 hover:text-black dark:hover:bg-[#161619] dark:hover:text-white transition-colors cursor-pointer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Info banner about 1-call architecture */}
        <div className="mt-4 flex items-start gap-2.5 rounded-xl bg-indigo-50/70 p-3 text-xs text-indigo-900 border border-indigo-200/60 dark:bg-indigo-950/40 dark:text-indigo-200 dark:border-indigo-900/60">
          <Zap className="h-4 w-4 shrink-0 text-indigo-600 dark:text-indigo-400 mt-0.5" />
          <div>
            <span className="font-bold">Strict 1-Call Direct Benchmark:</span> Each
            selected model receives 1 single-shot prompt to generate the entire architecture package (no recursive calls). Output is directly audited by the Validator Engine to measure raw LLM quality against Archova.
          </div>
        </div>

        {/* Model Selection */}
        <div className="mt-4 space-y-2">
          <label className="text-xs font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
            Select Baseline Models ({selectedIds.length} active)
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {DEFAULT_BENCHMARK_PRESETS.map((preset) => {
              const isSelected = selectedIds.includes(preset.id);
              const keySnippet = preset.api_key
                ? `${preset.api_key.slice(0, 8)}...${preset.api_key.slice(-4)}`
                : "System Key";
              const providerLabel =
                preset.provider === "gemini"
                  ? "Google AI Studio"
                  : preset.provider === "groq"
                  ? "Groq Cloud"
                  : "OpenRouter";

              return (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => toggleModel(preset)}
                  className={`flex items-center justify-between p-3 rounded-xl border text-left transition-all cursor-pointer ${
                    isSelected
                      ? "border-indigo-500/80 bg-indigo-50/50 dark:border-indigo-500 dark:bg-indigo-950/30 text-indigo-950 dark:text-indigo-100 shadow-xs"
                      : "border-neutral-200/80 dark:border-[#262626] hover:border-neutral-300 dark:hover:border-white/20 bg-neutral-50/50 dark:bg-[#0D0D0F] text-neutral-700 dark:text-neutral-300"
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <Cpu className={`h-4 w-4 shrink-0 ${isSelected ? "text-indigo-600 dark:text-indigo-400" : "text-neutral-400"}`} />
                    <div className="truncate">
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-bold truncate">{preset.name}</span>
                        <span className="text-[9px] px-1.5 py-0.5 rounded-md bg-neutral-200/70 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 font-semibold uppercase">
                          {providerLabel}
                        </span>
                      </div>
                      <div className="text-[10px] text-neutral-400 truncate font-mono">{preset.model_id}</div>
                      <div className="text-[10px] text-emerald-600 dark:text-emerald-400 font-mono mt-0.5">
                        Key: {keySnippet}
                      </div>
                    </div>
                  </div>
                  <div
                    className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-md border ${
                      isSelected
                        ? "bg-indigo-600 border-indigo-600 text-white"
                        : "border-neutral-300 dark:border-neutral-700"
                    }`}
                  >
                    {isSelected && <Check className="h-3 w-3 stroke-[3]" />}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* API Key Configuration */}
        <div className="mt-4 space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold text-neutral-700 dark:text-neutral-300 flex items-center gap-1.5">
              <KeyRound className="h-3.5 w-3.5 text-neutral-400" />
              <span>Custom OpenRouter / LLM API Key (Optional)</span>
            </label>
            <span className="text-[11px] text-neutral-400">Leave blank to use system key</span>
          </div>
          <input
            type="password"
            value={apiKeyInput}
            onChange={(e) => setApiKeyInput(e.target.value)}
            placeholder="sk-or-v1-..."
            className="w-full rounded-xl border border-neutral-200 bg-neutral-50 px-3 py-2 text-xs font-mono text-neutral-900 placeholder:text-neutral-400 focus:border-indigo-500 focus:outline-hidden dark:border-neutral-800 dark:bg-neutral-900 dark:text-white"
          />
        </div>

        {/* Add Custom Model */}
        <div className="mt-4 pt-3 border-t border-neutral-100 dark:border-neutral-800">
          <label className="text-[11px] font-bold text-neutral-500 dark:text-neutral-400 block mb-1.5">
            Add Any Other Model from OpenRouter:
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={customModelId}
              onChange={(e) => setCustomModelId(e.target.value)}
              placeholder="e.g. mistralai/mistral-large-2407"
              className="flex-1 rounded-xl border border-neutral-200 bg-neutral-50 px-3 py-1.5 text-xs font-mono text-neutral-900 placeholder:text-neutral-400 dark:border-neutral-800 dark:bg-neutral-900 dark:text-white"
            />
            <button
              type="button"
              onClick={handleAddCustomModel}
              disabled={!customModelId.trim()}
              className="px-3 py-1.5 text-xs font-bold rounded-xl bg-neutral-900 text-white dark:bg-white dark:text-black disabled:opacity-40 cursor-pointer"
            >
              Add
            </button>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="mt-6 flex items-center justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold rounded-xl border border-neutral-200/80 bg-white/70 backdrop-blur-md text-neutral-600 hover:text-black hover:border-black dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-300 dark:hover:bg-[#161619] dark:hover:border-white/20 dark:hover:text-white transition-all cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            className="px-5 py-2 text-xs font-bold rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-md hover:shadow-lg transition-all cursor-pointer"
          >
            Save Benchmark Configuration
          </button>
        </div>
      </div>
    </div>
  );
}
