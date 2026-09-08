"use client";

import React from "react";
import { Calculator, Plus, Minus, Info } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { RiskBreakdownItem } from "@/lib/types";

interface RiskBreakdownPanelProps {
  breakdown?: RiskBreakdownItem[];
  finalRiskScore?: number | null;
}

interface ComponentMeta {
  label: string;
  description: string;
  isPositive: boolean;
}

const META_MAP: Record<string, ComponentMeta> = {
  base_score: {
    label: "Base Finding Risk",
    description: "Evaluated from individual agent severity weights and confidence scores.",
    isPositive: true,
  },
  corroboration_bonus: {
    label: "Cross-Modal Corroboration",
    description: "Bonus awarded when independent multimodal agents detect shared indicators.",
    isPositive: true,
  },
  intel_bonus: {
    label: "RAG Intel Grounding",
    description: "Bonus awarded when evidence matches verified CERT-In or RBI advisories.",
    isPositive: true,
  },
  contradiction_penalty: {
    label: "Contradiction Penalty",
    description: "Deduction applied when specialist agents produce conflicting verdicts.",
    isPositive: false,
  },
};

export function RiskBreakdownPanel({ breakdown = [], finalRiskScore }: RiskBreakdownPanelProps) {
  return (
    <Card className="p-6 border-soc-border bg-soc-surface h-full flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between border-b border-soc-border pb-3 mb-4">
          <div className="flex items-center gap-2">
            <Calculator className="h-4 w-4 text-accent-primary" />
            <h2 className="font-display font-semibold text-xs uppercase tracking-wider text-soc-text-secondary">
              Deterministic Arithmetic Breakdown
            </h2>
          </div>
          <span className="text-[11px] font-mono text-soc-text-muted">
            MATHEMATICALLY DEFENSIBLE
          </span>
        </div>

        {/* Breakdown Items List */}
        <div className="space-y-3">
          {breakdown.length === 0 ? (
            <div className="text-center py-6 text-xs text-soc-text-muted font-mono">
              No breakdown elements recorded for this evaluation.
            </div>
          ) : (
            breakdown.map((item, idx) => {
              const meta = META_MAP[item.component] || {
                label: item.component.replace(/_/g, " "),
                description: "Deterministic component.",
                isPositive: item.weight >= 0,
              };

              const contribution = item.contribution;
              const formattedContrib =
                contribution > 0
                  ? `+${contribution.toFixed(3)}`
                  : contribution < 0
                  ? contribution.toFixed(3)
                  : "0.000";

              const contribColor =
                contribution > 0
                  ? "text-severity-low"
                  : contribution < 0
                  ? "text-severity-critical"
                  : "text-soc-text-muted";

              return (
                <div
                  key={idx}
                  className="p-3 rounded-md bg-soc-base border border-soc-border flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 transition-colors"
                >
                  <div className="flex items-start gap-2.5">
                    <div
                      className={`p-1 rounded mt-0.5 border ${
                        meta.isPositive
                          ? "bg-severity-low/10 border-severity-low/30 text-severity-low"
                          : "bg-severity-critical/10 border-severity-critical/30 text-severity-critical"
                      }`}
                    >
                      {meta.isPositive ? (
                        <Plus className="h-3 w-3" />
                      ) : (
                        <Minus className="h-3 w-3" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-display font-semibold text-xs text-soc-text-primary">
                          {meta.label}
                        </span>
                        <span className="text-[10px] font-mono text-soc-text-muted">
                          (weight: {item.weight > 0 ? `+${item.weight}` : item.weight})
                        </span>
                      </div>
                      <p className="text-[11px] text-soc-text-secondary mt-0.5">
                        {meta.description}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between sm:justify-end gap-3 font-mono text-xs pl-7 sm:pl-0">
                    <div className="text-right">
                      <div className="text-[10px] text-soc-text-muted uppercase">Raw Value</div>
                      <div className="text-soc-text-primary">{item.value.toFixed(3)}</div>
                    </div>
                    <div className="text-right min-w-[75px]">
                      <div className="text-[10px] text-soc-text-muted uppercase">Contribution</div>
                      <div className={`font-bold ${contribColor}`}>{formattedContrib}</div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Footer: Formula and Final Sum */}
      <div className="mt-4 pt-4 border-t border-soc-border/60 bg-soc-elevated/40 -mx-6 -mb-6 p-4 rounded-b-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-[11px] font-mono text-soc-text-muted">
          <Info className="h-3.5 w-3.5 text-accent-primary shrink-0" />
          <span>Final Risk = clamp(Base + Corroboration + Intel − Penalty, 0.0, 1.0)</span>
        </div>

        {typeof finalRiskScore === "number" && (
          <div className="flex items-center gap-2 font-mono text-xs">
            <span className="text-soc-text-secondary uppercase">Resulting Score:</span>
            <span className="font-bold text-accent-primary text-sm">
              {finalRiskScore.toFixed(3)}
            </span>
          </div>
        )}
      </div>
    </Card>
  );
}
