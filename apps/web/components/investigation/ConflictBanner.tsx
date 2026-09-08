"use client";

import React from "react";
import { AlertTriangle, GitPullRequest, ArrowRight } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ConflictLog } from "@/lib/types";

interface ConflictBannerProps {
  conflicts?: ConflictLog[];
}

export function ConflictBanner({ conflicts = [] }: ConflictBannerProps) {
  if (!conflicts || conflicts.length === 0) {
    return null;
  }

  return (
    <Card className="p-5 border-severity-medium/40 bg-severity-medium/5">
      <div className="flex items-center gap-2.5 mb-3">
        <AlertTriangle className="h-4 w-4 text-severity-medium shrink-0" />
        <h3 className="font-display font-semibold text-xs text-severity-medium uppercase tracking-wider">
          Multi-Agent Conflict Detected ({conflicts.length}) — Deterministic Resolution Applied
        </h3>
      </div>
      <p className="text-xs text-soc-text-secondary mb-4 leading-relaxed">
        Specialist agents produced contradictory conclusions regarding this evidence. In accordance with
        ThreatWeave&apos;s defensibility principle, conflicts are logged transparently and resolved via
        pre-established deterministic arbitration rules. A deduction (-0.20) was factored into the score.
      </p>

      <div className="space-y-3">
        {conflicts.map((c, idx) => (
          <div
            key={c.id || idx}
            className="p-3.5 rounded-md bg-soc-base border border-soc-border flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs font-mono"
          >
            <div className="flex items-center gap-2.5">
              <GitPullRequest className="h-3.5 w-3.5 text-severity-medium shrink-0" />
              <div className="flex items-center gap-1.5 flex-wrap">
                <Badge variant="outline" className="text-soc-text-primary">
                  {c.agent_a}
                </Badge>
                <span className="text-soc-text-muted">vs</span>
                <Badge variant="outline" className="text-soc-text-primary">
                  {c.agent_b}
                </Badge>
                <span className="text-soc-text-secondary ml-1">
                  Type: <span className="text-severity-medium">{c.conflict_type}</span>
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2 text-soc-text-secondary pl-6 md:pl-0">
              <ArrowRight className="h-3 w-3 text-soc-text-muted shrink-0" />
              <span>
                Rule: <strong className="text-soc-text-primary">{c.resolution_rule}</strong>
              </span>
              {c.resolution_outcome && (
                <span className="text-soc-text-muted">({c.resolution_outcome})</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
