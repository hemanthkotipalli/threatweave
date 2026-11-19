"use client";

import React, { useState } from "react";
import { Award, Zap, ShieldCheck, ArrowUpRight } from "lucide-react";
import { ModalityBenchmarkComparison } from "./types";

interface Props {
  data: ModalityBenchmarkComparison[];
  className?: string;
}

export function EvaluationBenchmarkTable({ data, className = "" }: Props) {
  const [activeMode, setActiveMode] = useState<"llm" | "heuristic">("llm");

  return (
    <div className={`flex flex-col bg-soc-surface border border-soc-border rounded-lg p-5 ${className}`}>
      {/* Header with Mode Toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-soc-border mb-4">
        <div className="flex items-center gap-2">
          <Award className="h-4 w-4 text-accent-primary" />
          <div>
            <h3 className="font-display font-semibold text-sm text-soc-text-primary tracking-wide uppercase">
              94-Sample Empirical Benchmark &amp; Research Evaluation
            </h3>
            <span className="text-[11px] font-mono text-soc-text-muted">
              Grounded in verified multi-agent evaluation audit
            </span>
          </div>
        </div>

        {/* Mode Selector Tabs */}
        <div className="flex items-center rounded border border-soc-border p-0.5 bg-soc-base">
          <button
            type="button"
            onClick={() => setActiveMode("llm")}
            className={`px-3 py-1 rounded text-xs font-mono transition-colors ${
              activeMode === "llm"
                ? "bg-accent-primary text-white font-bold"
                : "text-soc-text-secondary hover:text-soc-text-primary"
            }`}
          >
            Production LLM Mode
          </button>
          <button
            type="button"
            onClick={() => setActiveMode("heuristic")}
            className={`px-3 py-1 rounded text-xs font-mono transition-colors ${
              activeMode === "heuristic"
                ? "bg-accent-primary text-white font-bold"
                : "text-soc-text-secondary hover:text-soc-text-primary"
            }`}
          >
            Offline Heuristic Fallback
          </button>
        </div>
      </div>

      {/* Mode Sub-banner */}
      <div className="mb-4 p-3 rounded bg-soc-base/60 border border-soc-border text-xs font-mono flex items-center justify-between">
        {activeMode === "llm" ? (
          <div className="flex items-center gap-2 text-soc-text-secondary">
            <ShieldCheck className="h-4 w-4 text-severity-low shrink-0" />
            <span>
              <strong>Primary Swarm:</strong> Deep semantic LLM synthesis (<code className="text-accent-primary">openai/gpt-oss-120b</code>) + OCR + Whisper.
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-soc-text-secondary">
            <Zap className="h-4 w-4 text-severity-medium shrink-0" />
            <span>
              <strong>Offline Resilience:</strong> 100% local deterministic heuristics, regex vectors &amp; PyAV audio parsing (0 cloud calls).
            </span>
          </div>
        )}
        <span className="text-[10px] text-soc-text-muted hidden sm:inline">
          Ground-Truth Decision Rule: Severity &ge; high (&ge; 0.60)
        </span>
      </div>

      {/* Metrics Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs font-mono">
          <thead>
            <tr className="border-b border-soc-border text-left text-soc-text-muted uppercase tracking-wider text-[10px]">
              <th className="pb-2.5 font-semibold">Specialist Modality</th>
              <th className="pb-2.5 font-semibold text-center">Dataset</th>
              <th className="pb-2.5 font-semibold text-center">Precision</th>
              <th className="pb-2.5 font-semibold text-center">Recall</th>
              <th className="pb-2.5 font-semibold text-center">F1 Score</th>
              <th className="pb-2.5 font-semibold text-center">Accuracy</th>
              <th className="pb-2.5 font-semibold text-center">Confusion (TP/FP/TN/FN)</th>
              <th className="pb-2.5 font-semibold text-right">Mean Latency</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-soc-border/50">
            {data.map((row) => {
              const metrics = activeMode === "llm" ? row.llmMode : row.heuristicMode;
              const hasRecallImprovement =
                activeMode === "llm" && row.baselineRecall !== undefined && metrics.recall > row.baselineRecall;

              return (
                <tr key={row.modality} className="hover:bg-soc-base/30 transition-colors">
                  <td className="py-3 font-semibold text-soc-text-primary">
                    <div className="flex items-center gap-1.5">
                      <span>{row.label}</span>
                      {hasRecallImprovement && (
                        <span className="text-[9px] px-1 py-0.2 rounded bg-severity-low/20 text-severity-low border border-severity-low/40 flex items-center">
                          <ArrowUpRight className="h-2.5 w-2.5 mr-0.5" />
                          +{(metrics.recall * 100 - row.baselineRecall * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-3 text-center text-soc-text-secondary">{metrics.total}</td>
                  <td className="py-3 text-center font-bold text-soc-text-primary">
                    {(metrics.precision * 100).toFixed(1)}%
                  </td>
                  <td className="py-3 text-center font-bold text-accent-primary">
                    {(metrics.recall * 100).toFixed(1)}%
                  </td>
                  <td className="py-3 text-center font-bold text-severity-low">
                    {metrics.f1.toFixed(3)}
                  </td>
                  <td className="py-3 text-center text-soc-text-primary">
                    {(metrics.accuracy * 100).toFixed(1)}%
                  </td>
                  <td className="py-3 text-center text-[11px] text-soc-text-muted">
                    <span className="text-severity-low font-bold">{metrics.tp}</span>/
                    <span className="text-severity-critical font-bold">{metrics.fp}</span>/
                    <span className="text-soc-text-secondary">{metrics.tn}</span>/
                    <span className="text-severity-medium">{metrics.fn}</span>
                  </td>
                  <td className="py-3 text-right text-soc-text-muted">
                    {metrics.avgLatencyMs.toFixed(0)} ms
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Summary Footer */}
      <div className="mt-4 pt-3 border-t border-soc-border/60 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[11px] font-mono text-soc-text-muted">
        <div>
          <span>Confusion Matrix Key: </span>
          <span className="text-severity-low font-bold">TP (True Pos)</span>,{" "}
          <span className="text-severity-critical font-bold">FP (False Pos)</span>,{" "}
          <span className="text-soc-text-secondary font-bold">TN (True Neg)</span>,{" "}
          <span className="text-severity-medium font-bold">FN (False Neg)</span>
        </div>
        <div className="text-soc-text-secondary">
          Academic Reference: IEEE Publication Manuscript Section IV
        </div>
      </div>
    </div>
  );
}
