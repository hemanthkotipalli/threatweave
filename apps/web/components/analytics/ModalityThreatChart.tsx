"use client";

import React, { useState } from "react";
import { Layers, HelpCircle } from "lucide-react";
import { ModalityThreatData } from "./types";

interface Props {
  data: ModalityThreatData[];
  className?: string;
}

export function ModalityThreatChart({ data, className = "" }: Props) {
  const [hoveredModality, setHoveredModality] = useState<string | null>(null);

  const maxTotal = Math.max(...data.map((d) => d.total), 1);

  return (
    <div className={`flex flex-col bg-soc-surface border border-soc-border rounded-lg p-5 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-soc-border mb-4">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-accent-primary" />
          <h3 className="font-display font-semibold text-sm text-soc-text-primary tracking-wide uppercase">
            Modality-Wise Threat Breakdown
          </h3>
        </div>
        <div className="flex items-center gap-3 text-[11px] font-mono">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-severity-critical" />
            <span className="text-soc-text-secondary">Malicious (High/Crit)</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-severity-low" />
            <span className="text-soc-text-secondary">Benign (Med/Low)</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-soc-text-muted" />
            <span className="text-soc-text-secondary">Pending</span>
          </span>
        </div>
      </div>

      {/* Bar List */}
      <div className="space-y-4 py-1">
        {data.map((item) => {
          const isHovered = hoveredModality === item.modality;
          const barWidthPercent = Math.max((item.total / maxTotal) * 100, item.total > 0 ? 8 : 2);
          const malRatio = item.total > 0 ? (item.malicious / item.total) * 100 : 0;
          const benRatio = item.total > 0 ? (item.benign / item.total) * 100 : 0;
          const penRatio = item.total > 0 ? (item.pending / item.total) * 100 : 0;

          return (
            <div
              key={item.modality}
              onMouseEnter={() => setHoveredModality(item.modality)}
              onMouseLeave={() => setHoveredModality(null)}
              className={`p-2.5 rounded transition-colors ${
                isHovered ? "bg-soc-elevated/70" : "hover:bg-soc-base/40"
              }`}
            >
              {/* Row Label and Stats */}
              <div className="flex items-center justify-between text-xs font-mono mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-soc-text-primary">{item.label}</span>
                  <span className="text-[10px] text-soc-text-muted">
                    ({item.total} {item.total === 1 ? "scan" : "scans"})
                  </span>
                </div>
                <div className="flex items-center gap-3 text-[11px]">
                  <span className="text-severity-critical font-bold">{item.malicious} Malicious</span>
                  <span className="text-soc-border">|</span>
                  <span className="text-soc-text-secondary">Avg Risk: {(item.avgRiskScore * 100).toFixed(0)}%</span>
                </div>
              </div>

              {/* Stacked Progress Bar */}
              <div className="w-full bg-soc-base h-3 rounded-sm overflow-hidden flex border border-soc-border/60">
                {item.total > 0 ? (
                  <div
                    className="h-full flex transition-all duration-300"
                    style={{ width: `${barWidthPercent}%` }}
                  >
                    {item.malicious > 0 && (
                      <div
                        style={{ width: `${malRatio}%` }}
                        className="bg-severity-critical h-full transition-all"
                        title={`${item.malicious} Malicious`}
                      />
                    )}
                    {item.benign > 0 && (
                      <div
                        style={{ width: `${benRatio}%` }}
                        className="bg-severity-low h-full transition-all"
                        title={`${item.benign} Benign`}
                      />
                    )}
                    {item.pending > 0 && (
                      <div
                        style={{ width: `${penRatio}%` }}
                        className="bg-soc-text-muted h-full transition-all"
                        title={`${item.pending} Pending`}
                      />
                    )}
                  </div>
                ) : (
                  <div className="w-full h-full bg-soc-border/20 text-[9px] font-mono text-soc-text-muted flex items-center px-2">
                    No incident records
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer Info */}
      <div className="mt-4 pt-3 border-t border-soc-border/60 flex items-center justify-between text-[11px] text-soc-text-muted font-mono">
        <span className="flex items-center gap-1">
          <HelpCircle className="h-3 w-3 text-soc-text-secondary" />
          Cross-Modal incidents aggregate evidence across 2+ simultaneous channels
        </span>
        <span>Swarm Dynamic Fan-Out</span>
      </div>
    </div>
  );
}
