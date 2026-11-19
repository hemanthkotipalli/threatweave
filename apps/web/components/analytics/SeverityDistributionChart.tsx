"use client";

import React, { useState } from "react";
import { ShieldAlert, Info } from "lucide-react";
import { SeverityDistributionData } from "./types";

interface Props {
  data: SeverityDistributionData;
  className?: string;
}

export function SeverityDistributionChart({ data, className = "" }: Props) {
  const [hoveredKey, setHoveredKey] = useState<string | null>(null);

  const tiers: { key: keyof Omit<SeverityDistributionData, "total">; label: string; color: string; borderClass: string }[] = [
    { key: "critical", label: "Critical", color: "#EF4444", borderClass: "border-[#EF4444]" },
    { key: "high", label: "High", color: "#F97316", borderClass: "border-[#F97316]" },
    { key: "medium", label: "Medium", color: "#FBBF24", borderClass: "border-[#FBBF24]" },
    { key: "low", label: "Low", color: "#4EAB87", borderClass: "border-[#4EAB87]" },
    { key: "info", label: "Info", color: "#5B9EB8", borderClass: "border-[#5B9EB8]" },
    { key: "pending", label: "Pending", color: "#64748B", borderClass: "border-[#64748B]" },
  ];

  const total = data.total || 0;
  const criticalHighCount = data.critical + data.high;
  const threatPercent = total > 0 ? Math.round((criticalHighCount / total) * 100) : 0;

  // Donut geometry constants
  const size = 220;
  const strokeWidth = 26;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  // Build arc segments
  let accumulatedPercent = 0;
  const segments = tiers.map((tier) => {
    const count = data[tier.key] || 0;
    const fraction = total > 0 ? count / total : 0;
    const strokeDasharray = `${fraction * circumference} ${circumference}`;
    const strokeDashoffset = -accumulatedPercent * circumference;
    accumulatedPercent += fraction;

    return {
      ...tier,
      count,
      fraction,
      percent: Math.round(fraction * 100),
      strokeDasharray,
      strokeDashoffset,
    };
  });

  return (
    <div className={`flex flex-col bg-soc-surface border border-soc-border rounded-lg p-5 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-soc-border mb-4">
        <div className="flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 text-accent-primary" />
          <h3 className="font-display font-semibold text-sm text-soc-text-primary tracking-wide uppercase">
            Threat Severity Distribution
          </h3>
        </div>
        <span className="text-xs font-mono text-soc-text-muted">
          {total} {total === 1 ? "Incident" : "Incidents"}
        </span>
      </div>

      {/* Main Chart Body */}
      <div className="flex flex-col sm:flex-row items-center justify-around gap-6 py-2">
        {/* SVG Donut */}
        <div className="relative flex items-center justify-center">
          <svg
            width={size}
            height={size}
            viewBox={`0 0 ${size} ${size}`}
            className="transform -rotate-90"
            role="img"
            aria-label="Severity breakdown donut chart"
          >
            {/* Background Track */}
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              stroke="#211D1A"
              strokeWidth={strokeWidth}
              fill="transparent"
            />
            {/* Segments */}
            {total > 0 ? (
              segments.map((seg) => {
                if (seg.count === 0) return null;
                const isHovered = hoveredKey === seg.key;
                return (
                  <circle
                    key={seg.key}
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    stroke={seg.color}
                    strokeWidth={isHovered ? strokeWidth + 4 : strokeWidth}
                    strokeDasharray={seg.strokeDasharray}
                    strokeDashoffset={seg.strokeDashoffset}
                    fill="transparent"
                    className="transition-all duration-200 cursor-pointer"
                    onMouseEnter={() => setHoveredKey(seg.key)}
                    onMouseLeave={() => setHoveredKey(null)}
                  />
                );
              })
            ) : (
              <circle
                cx={size / 2}
                cy={size / 2}
                r={radius}
                stroke="#2E2722"
                strokeWidth={strokeWidth}
                fill="transparent"
              />
            )}
          </svg>

          {/* Center Callout */}
          <div className="absolute flex flex-col items-center justify-center text-center pointer-events-none">
            {hoveredKey ? (
              (() => {
                const hovered = segments.find((s) => s.key === hoveredKey);
                return (
                  <>
                    <span className="text-xl font-display font-bold" style={{ color: hovered?.color }}>
                      {hovered?.count}
                    </span>
                    <span className="text-[11px] font-mono text-soc-text-secondary uppercase">
                      {hovered?.label} ({hovered?.percent}%)
                    </span>
                  </>
                );
              })()
            ) : (
              <>
                <span className="text-2xl font-display font-bold text-soc-text-primary">
                  {threatPercent}%
                </span>
                <span className="text-[10px] font-mono text-soc-text-muted uppercase tracking-wider">
                  Threat Ratio
                </span>
              </>
            )}
          </div>
        </div>

        {/* Legend Grid */}
        <div className="grid grid-cols-2 gap-2.5 w-full sm:w-auto font-mono text-xs">
          {segments.map((tier) => {
            const isHovered = hoveredKey === tier.key;
            return (
              <div
                key={tier.key}
                onMouseEnter={() => setHoveredKey(tier.key)}
                onMouseLeave={() => setHoveredKey(null)}
                className={`flex items-center justify-between gap-3 px-3 py-1.5 rounded bg-soc-base/40 border transition-colors cursor-pointer ${
                  isHovered ? "border-accent-primary bg-soc-elevated" : "border-soc-border hover:border-soc-text-muted"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span
                    className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{ backgroundColor: tier.color }}
                  />
                  <span className="text-soc-text-secondary">{tier.label}</span>
                </div>
                <div className="flex items-center gap-1.5 font-bold">
                  <span className="text-soc-text-primary">{tier.count}</span>
                  <span className="text-[10px] text-soc-text-muted font-normal">
                    ({tier.percent}%)
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer Info */}
      <div className="mt-3 pt-3 border-t border-soc-border/60 flex items-center gap-1.5 text-[11px] text-soc-text-muted">
        <Info className="h-3 w-3 shrink-0" />
        <span>Critical and High severity alerts trigger automatic external SOC webhooks.</span>
      </div>
    </div>
  );
}
