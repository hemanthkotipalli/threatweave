"use client";

import React, { useState } from "react";
import { GitMerge, Sparkles } from "lucide-react";
import { CorrelationCell } from "./types";

interface Props {
  cells: CorrelationCell[];
  modalities: { key: string; label: string }[];
  className?: string;
}

export function CorrelationMatrixHeatmap({ cells, modalities, className = "" }: Props) {
  const [hoveredCell, setHoveredCell] = useState<CorrelationCell | null>(null);

  // Find cell by pair
  const getCell = (mA: string, mB: string): CorrelationCell => {
    const match = cells.find(
      (c) =>
        (c.modalityA === mA && c.modalityB === mB) ||
        (c.modalityA === mB && c.modalityB === mA)
    );
    return (
      match || {
        modalityA: mA,
        modalityB: mB,
        coOccurrenceCount: 0,
        avgCombinedRisk: 0,
      }
    );
  };

  const maxCount = Math.max(...cells.map((c) => c.coOccurrenceCount), 1);

  return (
    <div className={`flex flex-col bg-soc-surface border border-soc-border rounded-lg p-5 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-soc-border mb-4">
        <div className="flex items-center gap-2">
          <GitMerge className="h-4 w-4 text-accent-primary" />
          <h3 className="font-display font-semibold text-sm text-soc-text-primary tracking-wide uppercase">
            Cross-Modal Threat Correlation Matrix
          </h3>
        </div>
        <div className="flex items-center gap-1.5 text-xs font-mono text-soc-text-muted">
          <Sparkles className="h-3.5 w-3.5 text-accent-primary" />
          <span>Multi-Agent Corroboration Synergy</span>
        </div>
      </div>

      {/* Heatmap Grid */}
      <div className="overflow-x-auto pb-2">
        <div className="min-w-[480px]">
          {/* Column Header */}
          <div className="grid grid-cols-6 gap-1 mb-1 font-mono text-[11px] text-soc-text-muted">
            <div className="p-2 text-right font-bold text-soc-text-secondary">Modality</div>
            {modalities.map((m) => (
              <div key={m.key} className="p-2 text-center font-bold text-soc-text-primary truncate">
                {m.label}
              </div>
            ))}
          </div>

          {/* Matrix Rows */}
          {modalities.map((rowM) => (
            <div key={rowM.key} className="grid grid-cols-6 gap-1 mb-1 font-mono text-xs">
              {/* Row Header */}
              <div className="p-2 flex items-center justify-end font-bold text-soc-text-primary text-[11px] truncate">
                {rowM.label}
              </div>

              {/* Cells */}
              {modalities.map((colM) => {
                const isDiagonal = rowM.key === colM.key;
                const cell = getCell(rowM.key, colM.key);
                const isHovered =
                  hoveredCell &&
                  ((hoveredCell.modalityA === rowM.key && hoveredCell.modalityB === colM.key) ||
                    (hoveredCell.modalityA === colM.key && hoveredCell.modalityB === rowM.key));

                const intensity = !isDiagonal && maxCount > 0 ? cell.coOccurrenceCount / maxCount : 0;

                // Color calculation based on intensity
                let bgColor = "bg-soc-base/40";
                if (isDiagonal) {
                  bgColor = "bg-soc-elevated/40 text-soc-text-muted";
                } else if (cell.coOccurrenceCount > 0) {
                  if (intensity > 0.6) bgColor = "bg-accent-primary/50 text-white font-bold";
                  else if (intensity > 0.3) bgColor = "bg-accent-primary/30 text-accent-primary font-bold";
                  else bgColor = "bg-accent-primary/15 text-soc-text-primary";
                }

                return (
                  <div
                    key={colM.key}
                    onMouseEnter={() => !isDiagonal && setHoveredCell(cell)}
                    onMouseLeave={() => setHoveredCell(null)}
                    className={`h-12 rounded flex flex-col items-center justify-center p-1 border transition-all cursor-pointer ${
                      isHovered ? "border-accent-primary scale-105 z-10 shadow-lg" : "border-soc-border/60"
                    } ${bgColor}`}
                  >
                    {isDiagonal ? (
                      <span className="text-[10px] text-soc-text-muted">—</span>
                    ) : (
                      <>
                        <span className="text-xs font-bold">
                          {cell.coOccurrenceCount > 0 ? cell.coOccurrenceCount : "0"}
                        </span>
                        {cell.coOccurrenceCount > 0 && (
                          <span className="text-[9px] text-soc-text-muted">
                            {(cell.avgCombinedRisk * 100).toFixed(0)}% risk
                          </span>
                        )}
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Selected Cell Detail or Callout */}
      <div className="mt-3 p-3 bg-soc-base/40 border border-soc-border rounded text-xs font-mono flex items-center justify-between">
        {hoveredCell && hoveredCell.coOccurrenceCount > 0 ? (
          <div className="flex items-center gap-4">
            <span className="text-soc-text-secondary">
              Correlated Pair:{" "}
              <strong className="text-accent-primary">
                {modalities.find((m) => m.key === hoveredCell.modalityA)?.label} +{" "}
                {modalities.find((m) => m.key === hoveredCell.modalityB)?.label}
              </strong>
            </span>
            <span className="text-soc-text-muted">
              Frequency: <strong className="text-soc-text-primary">{hoveredCell.coOccurrenceCount} incidents</strong>
            </span>
            <span className="text-severity-critical">
              Average Composite Risk:{" "}
              <strong className="font-bold">{(hoveredCell.avgCombinedRisk * 100).toFixed(1)}%</strong>
            </span>
          </div>
        ) : (
          <div className="text-soc-text-muted">
            Hover over any cross-modal cell to inspect multi-agent correlation frequency and combined risk rating.
          </div>
        )}
        <span className="text-[10px] text-soc-text-muted font-normal">
          Corroboration Bonus: +0.10 exact / +0.05 semantic
        </span>
      </div>
    </div>
  );
}
