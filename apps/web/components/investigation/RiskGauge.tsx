"use client";

import React from "react";
import { ShieldAlert, AlertTriangle } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { SeverityTag, SeverityType } from "@/components/ui/SeverityTag";
import { COLORS } from "@/lib/tokens";

interface RiskGaugeProps {
  score?: number | null;
  severity?: SeverityType | string | null;
  confidence?: number | null;
  lowConfidence?: boolean;
}

export function RiskGauge({
  score = 0,
  severity = "info",
  confidence,
  lowConfidence = false,
}: RiskGaugeProps) {
  const numericScore = typeof score === "number" ? Math.max(0, Math.min(1, score)) : 0;
  const percentage = Math.round(numericScore * 100);

  const validSeverity: SeverityType =
    severity === "critical" ||
    severity === "high" ||
    severity === "medium" ||
    severity === "low"
      ? severity
      : "info";

  const colorMap: Record<SeverityType, string> = {
    info: COLORS.severity.info,
    low: COLORS.severity.low,
    medium: COLORS.severity.medium,
    high: COLORS.severity.high,
    critical: COLORS.severity.critical,
  };

  const activeColor = colorMap[validSeverity];

  // SVG circular gauge geometry
  const size = 180;
  const strokeWidth = 14;
  const center = size / 2;
  const radius = center - strokeWidth;
  // Semi-circle arc circumference
  const arcLength = Math.PI * radius;
  const strokeDashoffset = arcLength * (1 - numericScore);

  return (
    <Card className="flex flex-col items-center justify-between p-6 border-soc-border bg-soc-surface h-full">
      <div className="w-full flex items-center justify-between border-b border-soc-border pb-3 mb-2">
        <div className="flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 text-accent-primary" />
          <h2 className="font-display font-semibold text-xs uppercase tracking-wider text-soc-text-secondary">
            Deterministic Threat Score
          </h2>
        </div>
        <SeverityTag severity={validSeverity} />
      </div>

      {/* SVG Arc Gauge */}
      <div className="relative flex flex-col items-center justify-center my-auto pt-2">
        <svg width={size} height={size * 0.65} viewBox={`0 0 ${size} ${size * 0.7}`} className="overflow-visible">
          {/* Background Track Arc */}
          <path
            d={`M ${strokeWidth},${center} A ${radius},${radius} 0 0,1 ${size - strokeWidth},${center}`}
            fill="none"
            stroke={COLORS.bg.elevated}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />
          {/* Active Value Arc */}
          <path
            d={`M ${strokeWidth},${center} A ${radius},${radius} 0 0,1 ${size - strokeWidth},${center}`}
            fill="none"
            stroke={activeColor}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={arcLength}
            strokeDashoffset={strokeDashoffset}
            className="transition-all duration-700 ease-out"
            style={{ filter: `drop-shadow(0 0 6px ${activeColor}40)` }}
          />
        </svg>

        {/* Center Display: Numeric Score and Severity Label */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pt-8 pointer-events-none">
          <span className="font-mono text-3xl sm:text-4xl font-bold tracking-tight text-soc-text-primary">
            {numericScore.toFixed(3)}
          </span>
          <span className="text-xs font-mono font-medium text-soc-text-secondary uppercase tracking-wider mt-0.5">
            {percentage}% RISK INDEX
          </span>
        </div>
      </div>

      {/* Footer Metrics / Low Confidence Notice */}
      <div className="w-full pt-4 border-t border-soc-border/60 mt-4 space-y-2">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-soc-text-muted">Aggregate Confidence:</span>
          <span className="text-soc-text-primary font-semibold">
            {typeof confidence === "number" ? `${Math.round(confidence * 100)}%` : "N/A"}
          </span>
        </div>

        {lowConfidence && (
          <div
            role="status"
            className="flex items-center gap-2 p-2 rounded bg-severity-medium/10 border border-severity-medium/30 text-[11px] text-severity-medium font-mono"
          >
            <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
            <span>Low Confidence Evaluation (&lt; 2 findings or conf &lt; 0.40)</span>
          </div>
        )}
      </div>
    </Card>
  );
}
