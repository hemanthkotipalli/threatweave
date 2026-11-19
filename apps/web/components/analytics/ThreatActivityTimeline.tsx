"use client";

import React, { useState } from "react";
import { Activity, Calendar } from "lucide-react";
import { TimelineBucket } from "./types";

interface Props {
  data: TimelineBucket[];
  className?: string;
}

export function ThreatActivityTimeline({ data, className = "" }: Props) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const maxTotal = Math.max(...data.map((d) => d.total), 4);

  return (
    <div className={`flex flex-col bg-soc-surface border border-soc-border rounded-lg p-5 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-soc-border mb-4">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-accent-primary" />
          <h3 className="font-display font-semibold text-sm text-soc-text-primary tracking-wide uppercase">
            Threat Activity Timeline
          </h3>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-soc-text-muted">
          <Calendar className="h-3.5 w-3.5" />
          <span>Chronological Incident Frequency</span>
        </div>
      </div>

      {data.length === 0 ? (
        <div className="h-44 flex flex-col items-center justify-center text-xs font-mono text-soc-text-muted border border-dashed border-soc-border/60 rounded">
          <span>No historical activity recorded yet</span>
          <span className="text-[10px] mt-1 text-soc-text-secondary">Run threat investigations or launch demo scenarios</span>
        </div>
      ) : (
        <div className="flex flex-col">
          {/* Timeline Bars Grid */}
          <div className="relative flex items-end gap-2 sm:gap-4 h-44 pt-6 px-2 border-b border-soc-border">
            {data.map((bucket, idx) => {
              const isHovered = hoveredIndex === idx;
              const totalHeightPercent = (bucket.total / maxTotal) * 100;
              const critHighCount = bucket.critical + bucket.high;
              const critHighHeight = bucket.total > 0 ? (critHighCount / bucket.total) * 100 : 0;
              const medLowCount = bucket.medium + bucket.low + bucket.info;
              const medLowHeight = bucket.total > 0 ? (medLowCount / bucket.total) * 100 : 0;

              return (
                <div
                  key={bucket.dateKey}
                  className="flex-1 flex flex-col items-center h-full justify-end relative group cursor-pointer"
                  onMouseEnter={() => setHoveredIndex(idx)}
                  onMouseLeave={() => setHoveredIndex(null)}
                >
                  {/* Tooltip on Hover */}
                  {isHovered && (
                    <div className="absolute bottom-full mb-2 z-20 bg-soc-elevated border border-soc-border rounded shadow-xl p-2.5 text-xs font-mono whitespace-nowrap min-w-[140px] pointer-events-none">
                      <div className="font-bold text-soc-text-primary border-b border-soc-border pb-1 mb-1.5 flex justify-between">
                        <span>{bucket.displayDate}</span>
                        <span className="text-accent-primary">{bucket.total} Total</span>
                      </div>
                      <div className="space-y-1 text-[11px]">
                        <div className="flex justify-between text-severity-critical">
                          <span>Critical / High:</span>
                          <span className="font-bold">{critHighCount}</span>
                        </div>
                        <div className="flex justify-between text-severity-low">
                          <span>Medium / Low / Info:</span>
                          <span className="font-bold">{medLowCount}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Incident Count Indicator on top of bar */}
                  <span
                    className={`text-[10px] font-mono mb-1 transition-opacity ${
                      isHovered ? "opacity-100 text-accent-primary font-bold" : "opacity-60 text-soc-text-muted"
                    }`}
                  >
                    {bucket.total > 0 ? bucket.total : ""}
                  </span>

                  {/* Stacked Vertical Bar */}
                  <div
                    className={`w-full max-w-[36px] rounded-t-sm flex flex-col overflow-hidden transition-all duration-200 ${
                      isHovered ? "ring-2 ring-accent-primary" : ""
                    }`}
                    style={{ height: `${Math.max(totalHeightPercent, 6)}%` }}
                  >
                    {/* Critical/High Segment (Red) */}
                    <div
                      className="w-full bg-severity-critical transition-all"
                      style={{ height: `${critHighHeight}%` }}
                    />
                    {/* Medium/Low Segment (Green) */}
                    <div
                      className="w-full bg-severity-low transition-all"
                      style={{ height: `${medLowHeight}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Date Axis Labels */}
          <div className="flex items-center gap-2 sm:gap-4 px-2 pt-2 text-[10px] font-mono text-soc-text-muted">
            {data.map((bucket) => (
              <div key={bucket.dateKey} className="flex-1 text-center truncate">
                {bucket.displayDate}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Legend & Summary */}
      <div className="mt-4 pt-3 border-t border-soc-border/60 flex items-center justify-between text-xs font-mono text-soc-text-muted">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-severity-critical" />
            <span>High/Critical Alerts</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-severity-low" />
            <span>Medium/Low/Info</span>
          </span>
        </div>
        <span className="text-[11px] text-soc-text-secondary">
          Peak Active Window: {data.reduce((max, b) => (b.total > max.total ? b : max), { displayDate: "N/A", total: 0 }).displayDate}
        </span>
      </div>
    </div>
  );
}
