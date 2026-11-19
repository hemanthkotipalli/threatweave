"use client";

import React from "react";
import {
  Cpu,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  FileText,
  Globe,
  QrCode,
  Image as ImageIcon,
  Mic,
  GitFork,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { InvestigationDetail, AgentRunDetail } from "@/lib/types";

interface Props {
  investigation: InvestigationDetail;
  className?: string;
}

interface AgentDef {
  key: string;
  name: string;
  role: string;
  icon: React.ComponentType<{ className?: string }>;
  isOrchestrator?: boolean;
}

const ALL_SIX_AGENTS: AgentDef[] = [
  {
    key: "orchestrator",
    name: "Orchestrator Agent",
    role: "LangGraph DAG Supervisor & Consensus Coordinator",
    icon: GitFork,
    isOrchestrator: true,
  },
  {
    key: "text_agent",
    name: "Text Specialist",
    role: "SMS, Natural Language Lures & Credential Harvester Detector",
    icon: FileText,
  },
  {
    key: "url_agent",
    name: "URL Specialist",
    role: "Automated Domain Detonation & External Reputation Lookup",
    icon: Globe,
  },
  {
    key: "qr_agent",
    name: "QR Code Specialist",
    role: "Computer Vision Deeplink Extraction & Quishing Payload Analyzer",
    icon: QrCode,
  },
  {
    key: "image_agent",
    name: "Image & OCR Specialist",
    role: "EasyOCR Visual Text Mining & Fraudulent Graphic Layout Analysis",
    icon: ImageIcon,
  },
  {
    key: "voice_agent",
    name: "Voice & Speech Specialist",
    role: "Faster-Whisper Acoustic Transcription & Social Engineering Vishing Detector",
    icon: Mic,
  },
];

export function AgentExecutionInspector({ investigation, className = "" }: Props) {
  const runs = investigation.agent_runs || [];
  const runsMap = new Map<string, AgentRunDetail>();
  for (const r of runs) {
    runsMap.set(r.agent_name.toLowerCase(), r);
  }

  const getAgentDetails = (agentDef: AgentDef) => {
    if (agentDef.isOrchestrator) {
      // Orchestrator status derived from overall investigation status
      const isDone = investigation.status === "completed";
      const isFailed = investigation.status === "failed";
      return {
        status: isDone ? "completed" : isFailed ? "failed" : "pending",
        startedAt: investigation.created_at,
        finishedAt: investigation.completed_at,
        latencyMs: null, // Orchestrator lifecycle duration
        findingsCount: 0,
        confidence: investigation.final_confidence,
        errorSummary: null,
      };
    }

    const run = runsMap.get(agentDef.key.toLowerCase());
    if (!run) {
      // If run record doesn't exist, it was skipped by conditional router
      return {
        status: "skipped",
        startedAt: null,
        finishedAt: null,
        latencyMs: null,
        findingsCount: 0,
        confidence: null,
        errorSummary: null,
      };
    }

    const rawStatus = (run.status || "").toLowerCase();
    let statusLabel = "pending";
    if (rawStatus === "done" || rawStatus === "ok" || rawStatus === "completed") {
      statusLabel = "completed";
    } else if (rawStatus === "degraded_fallback") {
      statusLabel = "degraded fallback";
    } else if (rawStatus === "failed") {
      statusLabel = "failed";
    } else if (rawStatus === "skipped") {
      statusLabel = "skipped";
    } else if (rawStatus === "running") {
      statusLabel = "running";
    }

    const findings = run.findings || [];
    const avgConfidence =
      findings.length > 0
        ? findings.reduce((sum, f) => sum + (f.confidence || 0), 0) / findings.length
        : null;

    return {
      status: statusLabel,
      startedAt: run.started_at,
      finishedAt: run.finished_at,
      latencyMs: run.latency_ms,
      findingsCount: findings.length,
      confidence: avgConfidence,
      errorSummary:
        statusLabel === "degraded fallback"
          ? "LLM quota or network unavailable; deterministic offline heuristic fallback executed."
          : statusLabel === "failed"
          ? "Specialist agent execution aborted due to unrecoverable ingestion error."
          : null,
    };
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase font-bold text-status-done bg-status-done/10 border border-status-done/30 flex items-center gap-1">
            <CheckCircle2 className="h-3 w-3" /> Completed
          </span>
        );
      case "degraded fallback":
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase font-bold text-severity-medium bg-severity-medium/10 border border-severity-medium/30 flex items-center gap-1">
            <AlertTriangle className="h-3 w-3" /> Degraded Fallback
          </span>
        );
      case "failed":
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase font-bold text-severity-critical bg-severity-critical/10 border border-severity-critical/30 flex items-center gap-1">
            <XCircle className="h-3 w-3" /> Failed
          </span>
        );
      case "skipped":
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase font-bold text-soc-text-muted bg-soc-base border border-soc-border">
            Skipped (Unneeded)
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase font-bold text-accent-primary bg-accent-primary/10 border border-accent-primary/30">
            Pending
          </span>
        );
    }
  };

  return (
    <Card className={`p-5 md:p-6 border-soc-border bg-soc-surface ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-soc-border pb-4 mb-5">
        <div className="flex items-center gap-2">
          <Cpu className="h-4 w-4 text-accent-primary" />
          <div>
            <h2 className="font-display font-semibold text-sm uppercase tracking-wider text-soc-text-primary">
              All 6 Swarm Agents &bull; Execution Inspector
            </h2>
            <p className="text-xs text-soc-text-secondary">
              Deep telemetry for Orchestrator DAG and all 5 specialist multimodal nodes
            </p>
          </div>
        </div>
        <span className="text-xs font-mono text-soc-text-muted">
          LANGGRAPH SUPERVISOR DAG
        </span>
      </div>

      {/* Grid of All 6 Agents */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {ALL_SIX_AGENTS.map((agent) => {
          const Icon = agent.icon;
          const details = getAgentDetails(agent);

          return (
            <div
              key={agent.key}
              className="p-4 rounded-lg bg-soc-base border border-soc-border flex flex-col justify-between hover:border-soc-border/90 transition-colors space-y-3"
            >
              {/* Agent Identity */}
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded bg-soc-surface border border-soc-border text-accent-primary">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div>
                      <h3 className="font-display font-bold text-sm text-soc-text-primary">
                        {agent.name}
                      </h3>
                      <span className="text-[10px] font-mono text-soc-text-muted block truncate">
                        {agent.key}
                      </span>
                    </div>
                  </div>
                  {getStatusBadge(details.status)}
                </div>

                <p className="text-[11px] font-mono text-soc-text-secondary leading-normal mb-3">
                  {agent.role}
                </p>
              </div>

              {/* Telemetry Metrics */}
              <div className="space-y-2 pt-2 border-t border-soc-border/60 text-xs font-mono">
                {/* Duration */}
                <div className="flex justify-between items-center text-[11px]">
                  <span className="text-soc-text-muted flex items-center gap-1">
                    <Clock className="h-3 w-3" /> Measured Latency:
                  </span>
                  <span className="text-soc-text-primary font-bold">
                    {details.latencyMs !== null && details.latencyMs !== undefined
                      ? `${details.latencyMs} ms`
                      : "Not recorded"}
                  </span>
                </div>

                {/* Findings Count */}
                <div className="flex justify-between items-center text-[11px]">
                  <span className="text-soc-text-muted">Findings Generated:</span>
                  <span className="text-soc-text-primary font-bold">
                    {details.findingsCount}
                  </span>
                </div>

                {/* Confidence */}
                <div className="flex justify-between items-center text-[11px]">
                  <span className="text-soc-text-muted">Model Confidence:</span>
                  <span className="text-accent-primary font-bold">
                    {details.confidence !== null && details.confidence !== undefined
                      ? `${(details.confidence * 100).toFixed(0)}%`
                      : "N/A"}
                  </span>
                </div>

                {/* Timestamps */}
                <div className="pt-1 text-[10px] text-soc-text-muted border-t border-soc-border/40 space-y-0.5">
                  <div className="flex justify-between">
                    <span>Started:</span>
                    <span>
                      {details.startedAt
                        ? new Date(details.startedAt).toLocaleTimeString()
                        : "Not recorded"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Finished:</span>
                    <span>
                      {details.finishedAt
                        ? new Date(details.finishedAt).toLocaleTimeString()
                        : "Not recorded"}
                    </span>
                  </div>
                </div>

                {/* Error Summary if degraded/failed */}
                {details.errorSummary && (
                  <div className="mt-2 p-2 rounded bg-severity-medium/10 border border-severity-medium/30 text-[10px] text-severity-medium leading-relaxed">
                    <strong>Notice:</strong> {details.errorSummary}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
