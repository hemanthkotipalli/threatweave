"use client";

import React from "react";
import {
  ShieldAlert,
  ShieldCheck,
  Clock,
  Fingerprint,
  Layers,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Sparkles,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { SeverityTag, SeverityType } from "@/components/ui/SeverityTag";
import { InvestigationDetail, AgentFindingDetail } from "@/lib/types";

interface Props {
  investigation: InvestigationDetail;
  allFindings: { finding: AgentFindingDetail; agentName: string }[];
  className?: string;
}

export function InvestigationOverviewBanner({
  investigation,
  allFindings,
  className = "",
}: Props) {
  const runs = investigation.agent_runs || [];
  const inputs = investigation.evidence_inputs || [];

  const completedAgents = runs.filter(
    (r) =>
      r.status?.toLowerCase() === "done" ||
      r.status?.toLowerCase() === "completed" ||
      r.status?.toLowerCase() === "ok"
  );
  const degradedAgents = runs.filter(
    (r) => r.status?.toLowerCase() === "degraded_fallback"
  );
  const failedAgents = runs.filter(
    (r) => r.status?.toLowerCase() === "failed"
  );
  const skippedAgents = runs.filter(
    (r) => r.status?.toLowerCase() === "skipped"
  );

  const modalities = Array.from(
    new Set(inputs.map((inp) => inp.modality.toLowerCase()))
  );

  // Synthesize concise summary based on real findings
  const generateSummary = () => {
    if (investigation.status !== "completed") {
      return "Investigation is currently in queue or awaiting specialist agent execution.";
    }

    if (
      allFindings.length === 0 ||
      (investigation.final_risk_score !== null &&
        investigation.final_risk_score !== undefined &&
        investigation.final_risk_score < 0.25 &&
        allFindings.every(
          (f) =>
            f.finding.severity === "info" || f.finding.severity === "low"
        ))
    ) {
      return "Multimodal swarm analysis completed across all evidence inputs with zero critical threats or high-risk indicators detected. All analyzed modalities conform to benign operational baselines.";
    }

    const topFinding = allFindings[0];
    const topSev = topFinding.finding.severity.toUpperCase();
    const agentLabel = topFinding.agentName.replace("_agent", "").toUpperCase();
    const countThreats = allFindings.filter(
      (f) =>
        f.finding.severity === "critical" || f.finding.severity === "high"
    ).length;

    return `${topSev} severity threat detected by ${agentLabel} specialist with ${(
      topFinding.finding.confidence * 100
    ).toFixed(0)}% confidence: "${topFinding.finding.finding}". Total of ${countThreats} high-confidence threat finding(s) surfaced across ${
      modalities.length
    } evidence channel(s).`;
  };

  const isCriticalOrHigh =
    investigation.final_severity === "critical" ||
    investigation.final_severity === "high";

  return (
    <Card
      className={`p-6 border-soc-border bg-soc-surface transition-all ${className}`}
    >
      {/* Top Header */}
      <header className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-soc-border pb-5 mb-5">
        <div>
          <div className="flex items-center gap-2.5 mb-1.5 flex-wrap">
            <span className="font-mono text-xs text-accent-primary font-bold uppercase tracking-wider flex items-center gap-1.5">
              <Fingerprint className="h-4 w-4" />
              INVESTIGATION INTELLIGENCE OVERVIEW
            </span>
            <span className="text-soc-text-muted">&bull;</span>
            <span className="font-mono text-xs text-soc-text-muted select-all">
              ID: {investigation.id}
            </span>
            <Badge
              variant={
                investigation.status === "completed"
                  ? "accent"
                  : investigation.status === "failed"
                  ? "outline"
                  : "default"
              }
              className="font-mono text-[10px] lowercase"
            >
              {investigation.status}
            </Badge>
            {investigation.status === "completed" && (
              <Badge
                variant={isCriticalOrHigh ? "accent" : "outline"}
                className="font-mono text-[10px] uppercase"
              >
                {isCriticalOrHigh ? "THREAT DETECTED" : "ANALYSIS COMPLETED"}
              </Badge>
            )}
          </div>
          <h1 className="font-display font-bold text-xl sm:text-2xl text-soc-text-primary tracking-tight">
            {investigation.title || "Untitled Multimodal Incident"}
          </h1>
        </div>

        {/* Severity & Score Badges */}
        <div className="flex items-center gap-3 shrink-0 flex-wrap">
          {investigation.final_severity && (
            <SeverityTag
              severity={
                (investigation.final_severity as SeverityType) || "info"
              }
            />
          )}

          <div className="px-3.5 py-1.5 rounded bg-soc-base border border-soc-border font-mono text-xs flex items-center gap-2">
            <span className="text-soc-text-muted uppercase text-[10px]">
              Risk Score:
            </span>
            <span
              className={`font-bold ${
                (investigation.final_risk_score ?? 0) >= 0.65
                  ? "text-severity-critical"
                  : (investigation.final_risk_score ?? 0) >= 0.4
                  ? "text-severity-medium"
                  : "text-severity-low"
              }`}
            >
              {investigation.final_risk_score !== null &&
              investigation.final_risk_score !== undefined
                ? `${(investigation.final_risk_score * 100).toFixed(1)}%`
                : "PENDING"}
            </span>
          </div>

          {investigation.final_confidence !== null &&
            investigation.final_confidence !== undefined && (
              <div className="px-3.5 py-1.5 rounded bg-soc-base border border-soc-border font-mono text-xs flex items-center gap-2">
                <span className="text-soc-text-muted uppercase text-[10px]">
                  Confidence:
                </span>
                <span className="text-soc-text-primary font-bold">
                  {(investigation.final_confidence * 100).toFixed(0)}%
                </span>
              </div>
            )}
        </div>
      </header>

      {/* Dynamic Grounded Summary */}
      <div className="mb-6 p-4 rounded bg-soc-base/80 border border-soc-border text-xs leading-relaxed text-soc-text-secondary flex items-start gap-3">
        {isCriticalOrHigh ? (
          <ShieldAlert className="h-5 w-5 text-severity-critical shrink-0 mt-0.5" />
        ) : (
          <ShieldCheck className="h-5 w-5 text-severity-low shrink-0 mt-0.5" />
        )}
        <div>
          <span className="font-mono font-bold text-soc-text-primary text-[11px] block uppercase tracking-wide mb-0.5">
            Executive Incident Briefing
          </span>
          <p className="text-soc-text-primary">{generateSummary()}</p>
        </div>
      </div>

      {/* Operational Metadata Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5 text-xs font-mono">
        {/* Submission Timestamp */}
        <div className="p-3 bg-soc-base rounded border border-soc-border flex flex-col justify-between">
          <span className="text-[10px] text-soc-text-muted uppercase flex items-center gap-1 mb-1">
            <Clock className="h-3 w-3" />
            Submitted
          </span>
          <span className="text-soc-text-primary font-bold">
            {new Date(investigation.created_at).toLocaleDateString()}
          </span>
          <span className="text-[11px] text-soc-text-secondary">
            {new Date(investigation.created_at).toLocaleTimeString()}
          </span>
        </div>

        {/* Analyzed Modalities */}
        <div className="p-3 bg-soc-base rounded border border-soc-border flex flex-col justify-between">
          <span className="text-[10px] text-soc-text-muted uppercase flex items-center gap-1 mb-1">
            <Layers className="h-3 w-3" />
            Modalities ({modalities.length})
          </span>
          <div className="flex flex-wrap gap-1 mt-0.5">
            {modalities.length > 0 ? (
              modalities.map((mod) => (
                <Badge
                  key={mod}
                  variant="outline"
                  className="text-[10px] uppercase font-mono px-1.5 py-0"
                >
                  {mod}
                </Badge>
              ))
            ) : (
              <span className="text-soc-text-muted text-[11px]">None</span>
            )}
          </div>
          <span className="text-[10px] text-soc-text-muted mt-1">
            {inputs.length} artifact input(s)
          </span>
        </div>

        {/* Agent Execution Health */}
        <div className="p-3 bg-soc-base rounded border border-soc-border flex flex-col justify-between">
          <span className="text-[10px] text-soc-text-muted uppercase flex items-center gap-1 mb-1">
            <Cpu className="h-3 w-3" />
            Agent Health
          </span>
          <div className="flex items-center gap-1.5 text-status-done font-bold text-xs">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>{completedAgents.length} Completed</span>
          </div>
          <div className="text-[10px] text-soc-text-muted flex items-center gap-2 mt-0.5">
            {degradedAgents.length > 0 && (
              <span className="text-severity-medium flex items-center gap-0.5">
                <AlertTriangle className="h-2.5 w-2.5" />
                {degradedAgents.length} fallback
              </span>
            )}
            {failedAgents.length > 0 && (
              <span className="text-severity-critical flex items-center gap-0.5">
                <XCircle className="h-2.5 w-2.5" />
                {failedAgents.length} failed
              </span>
            )}
            {skippedAgents.length > 0 && (
              <span>{skippedAgents.length} skipped</span>
            )}
          </div>
        </div>

        {/* Investigation Lifecycle Status */}
        <div className="p-3 bg-soc-base rounded border border-soc-border flex flex-col justify-between">
          <span className="text-[10px] text-soc-text-muted uppercase flex items-center gap-1 mb-1">
            <Sparkles className="h-3 w-3" />
            Lifecycle Status
          </span>
          <span className="text-accent-primary font-bold uppercase tracking-wider text-xs">
            {investigation.status}
          </span>
          <span className="text-[10px] text-soc-text-muted truncate">
            {investigation.completed_at
              ? `Done: ${new Date(
                  investigation.completed_at
                ).toLocaleTimeString()}`
              : "Awaiting final state"}
          </span>
        </div>
      </div>
    </Card>
  );
}
