"use client";

import React from "react";
import { Cpu, CheckCircle2, Clock, Zap } from "lucide-react";
import { AgentPerformanceData } from "./types";

interface Props {
  agents: AgentPerformanceData[];
  className?: string;
}

export function AgentPerformanceMetrics({ agents, className = "" }: Props) {
  return (
    <div className={`flex flex-col bg-soc-surface border border-soc-border rounded-lg p-5 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-soc-border mb-4">
        <div className="flex items-center gap-2">
          <Cpu className="h-4 w-4 text-accent-primary" />
          <h3 className="font-display font-semibold text-sm text-soc-text-primary tracking-wide uppercase">
            Specialist Agent Execution Performance
          </h3>
        </div>
        <span className="text-xs font-mono text-status-done flex items-center gap-1">
          <CheckCircle2 className="h-3.5 w-3.5" />
          5 Active Swarm Specialists
        </span>
      </div>

      {/* Grid of Agent Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
        {agents.map((agent) => {
          return (
            <div
              key={agent.agentName}
              className="p-3.5 bg-soc-base/50 border border-soc-border rounded flex flex-col justify-between hover:border-soc-border/90 transition-colors"
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-display font-bold text-xs text-soc-text-primary">
                    {agent.label}
                  </span>
                  <span className="w-2 h-2 rounded-full bg-status-done" />
                </div>
                <span className="text-[10px] font-mono text-soc-text-muted block truncate mb-3">
                  {agent.agentName}
                </span>
              </div>

              <div className="space-y-2 pt-2 border-t border-soc-border/60 text-xs font-mono">
                <div className="flex justify-between items-center text-[11px]">
                  <span className="text-soc-text-muted">Total Scans:</span>
                  <span className="text-soc-text-primary font-bold">{agent.runsCount}</span>
                </div>
                <div className="flex justify-between items-center text-[11px]">
                  <span className="text-soc-text-muted">Detection:</span>
                  <span className="text-accent-primary font-bold">{agent.detectionRate}%</span>
                </div>
                {agent.avgLatencyMs !== undefined && (
                  <div
                    className="flex justify-between items-center text-[10px] text-soc-text-muted"
                    title="Estimated benchmark reference — not live execution timing"
                  >
                    <span className="flex items-center gap-1">
                      <Clock className="h-2.5 w-2.5" />
                      <span>Benchmark Ref:</span>
                    </span>
                    <span className="font-mono text-soc-text-secondary">
                      {agent.avgLatencyMs.toFixed(0)} ms{" "}
                      <span className="text-[9px] text-soc-text-muted">(est.)</span>
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer Info */}
      <div className="mt-4 pt-3 border-t border-soc-border/60 flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-[11px] font-mono text-soc-text-muted">
        <span className="flex items-center gap-1">
          <Zap className="h-3 w-3 text-accent-primary" />
          Autonomous conditional bypass: Inactive modalities recorded as skipped in &lt; 5 ms
        </span>
        <span className="text-[10px] text-soc-text-muted/80">
          * Estimated latency based on benchmark reference (not live execution timing)
        </span>
      </div>
    </div>
  );
}
