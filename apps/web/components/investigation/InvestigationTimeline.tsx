"use client";

import React, { useState } from "react";
import {
  Clock,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { SeverityTag, SeverityType } from "@/components/ui/SeverityTag";
import { InvestigationDetail, AgentFindingDetail } from "@/lib/types";

interface TimelineEvent {
  id: string;
  timestamp: string | null;
  recordedDate: Date | null;
  stageName: string;
  title: string;
  category: "submission" | "modality" | "agent" | "finding" | "correlation" | "rag" | "risk" | "report";
  agentName?: string;
  severity?: string;
  confidence?: number;
  description?: string;
  details?: Record<string, unknown> | string[];
  isRecorded: boolean;
}

interface Props {
  investigation: InvestigationDetail;
  className?: string;
}

export function InvestigationTimeline({ investigation, className = "" }: Props) {
  const [filterCategory, setFilterCategory] = useState<string>("all");
  const [expandedEvents, setExpandedEvents] = useState<Record<string, boolean>>({});

  const toggleExpand = (id: string) => {
    setExpandedEvents((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const runs = investigation.agent_runs || [];
  const inputs = investigation.evidence_inputs || [];
  const citations = investigation.rag_citations || [];
  const conflicts = investigation.risk?.conflicts || [];

  // Build real event stream
  const events: TimelineEvent[] = [];

  // 1. Investigation Submitted
  if (investigation.created_at) {
    events.push({
      id: "ev-sub",
      timestamp: investigation.created_at,
      recordedDate: new Date(investigation.created_at),
      stageName: "Investigation Ingestion",
      title: "Investigation Task Initialized & Submitted",
      category: "submission",
      agentName: "Orchestrator",
      description: `Target title: "${investigation.title || "Untitled Incident"}". Ingestion pipeline received evidence payload.`,
      isRecorded: true,
    });
  }

  // 2. Modality Evidence Inputs
  inputs.forEach((inp, idx) => {
    events.push({
      id: `ev-inp-${inp.id || idx}`,
      timestamp: inp.created_at || investigation.created_at,
      recordedDate: inp.created_at ? new Date(inp.created_at) : new Date(investigation.created_at),
      stageName: "Evidence Ingestion",
      title: `Evidence Channel Verified: ${inp.modality.toUpperCase()}`,
      category: "modality",
      agentName: "Orchestrator",
      description: inp.raw_content_ref || (inp.file_path ? `File artifact: ${inp.file_path}` : "Raw evidence stream"),
      details: {
        modality: inp.modality,
        artifactId: inp.id,
        contentRef: inp.raw_content_ref || inp.file_path,
      },
      isRecorded: Boolean(inp.created_at),
    });
  });

  // 3. Specialist Agent Runs (started & completed)
  runs.forEach((run, idx) => {
    if (run.started_at) {
      events.push({
        id: `ev-run-start-${run.id || idx}`,
        timestamp: run.started_at,
        recordedDate: new Date(run.started_at),
        stageName: "Agent Dispatch",
        title: `Swarm Specialist Dispatched: ${run.agent_name}`,
        category: "agent",
        agentName: run.agent_name,
        description: `Autonomous specialist node activated in LangGraph state machine.`,
        isRecorded: true,
      });
    }

    if (run.finished_at) {
      events.push({
        id: `ev-run-end-${run.id || idx}`,
        timestamp: run.finished_at,
        recordedDate: new Date(run.finished_at),
        stageName: "Agent Execution Complete",
        title: `Specialist ${run.agent_name} -> ${run.status?.toUpperCase()}`,
        category: "agent",
        agentName: run.agent_name,
        description: `Execution concluded with status: ${run.status}.${
          run.latency_ms !== null && run.latency_ms !== undefined
            ? ` Duration: ${run.latency_ms} ms.`
            : " Duration: Not recorded."
        } Findings produced: ${run.findings ? run.findings.length : 0}.`,
        details: {
          status: run.status,
          latencyMs: run.latency_ms ?? "Not recorded",
          findingsCount: run.findings?.length || 0,
        },
        isRecorded: true,
      });
    } else if (run.status === "skipped" || run.status === "failed") {
      events.push({
        id: `ev-run-status-${run.id || idx}`,
        timestamp: null,
        recordedDate: null,
        stageName: "Agent Lifecycle",
        title: `Specialist ${run.agent_name} marked as ${run.status?.toUpperCase()}`,
        category: "agent",
        agentName: run.agent_name,
        description: `Agent did not record explicit finished_at timestamp. Status recorded in database: ${run.status}.`,
        isRecorded: false,
      });
    }

    // 4. Individual Threat Findings
    if (run.findings) {
      run.findings.forEach((f: AgentFindingDetail, fIdx: number) => {
        const rawInd = f.indicators;
        const indicators = Array.isArray(rawInd)
          ? rawInd.filter((x): x is string => typeof x === "string")
          : rawInd && typeof rawInd === "object"
          ? Object.keys(rawInd)
          : [];

        events.push({
          id: `ev-finding-${f.id || `${idx}-${fIdx}`}`,
          timestamp: f.timestamp || run.finished_at || null,
          recordedDate: f.timestamp
            ? new Date(f.timestamp)
            : run.finished_at
            ? new Date(run.finished_at)
            : null,
          stageName: "Threat Finding Generation",
          title: `Finding: ${f.finding}`,
          category: "finding",
          agentName: run.agent_name,
          severity: f.severity,
          confidence: f.confidence,
          description: f.reasoning || "Analytical conclusion generated by specialist agent.",
          details: {
            indicators,
            confidence: `${(f.confidence * 100).toFixed(0)}%`,
            severity: f.severity,
          },
          isRecorded: Boolean(f.timestamp),
        });
      });
    }
  });

  // 5. Cross-Agent Conflicts / Arbitration
  conflicts.forEach((c, idx) => {
    events.push({
      id: `ev-conf-${c.id || idx}`,
      timestamp: null,
      recordedDate: null,
      stageName: "Cross-Agent Arbitration",
      title: `Consensus Conflict Resolved: ${c.agent_a} vs ${c.agent_b}`,
      category: "correlation",
      agentName: "Orchestrator",
      description: `Discrepancy (${c.conflict_type}): ${c.resolution_outcome}. Applied rule: ${c.resolution_rule}.`,
      details: {
        agentA: c.agent_a,
        agentB: c.agent_b,
        conflictType: c.conflict_type,
        rule: c.resolution_rule,
        outcome: c.resolution_outcome,
      },
      isRecorded: false,
    });
  });

  // 6. External RAG Threat Intelligence Grounding
  if (citations.length > 0) {
    events.push({
      id: "ev-rag",
      timestamp: null,
      recordedDate: null,
      stageName: "Threat Intelligence Grounding",
      title: `RAG Advisory Knowledge Ingestion (${citations.length} Citations)`,
      category: "rag",
      agentName: "Orchestrator",
      description: `Retrieved ${citations.length} advisory chunks from ChromaDB threat knowledge base exceeding strict similarity threshold.`,
      details: {
        sources: citations.map((c) => `${c.source_title} (${(c.similarity_score * 100).toFixed(0)}%)`),
      },
      isRecorded: false,
    });
  }

  // 7. Final Risk Calculation
  if (investigation.final_risk_score !== null && investigation.final_risk_score !== undefined) {
    events.push({
      id: "ev-risk",
      timestamp: investigation.completed_at || null,
      recordedDate: investigation.completed_at ? new Date(investigation.completed_at) : null,
      stageName: "Consensus Risk Calculation",
      title: `Deterministic Risk Score Finalized: ${(investigation.final_risk_score * 100).toFixed(1)}%`,
      category: "risk",
      agentName: "Orchestrator",
      severity: investigation.final_severity || "info",
      confidence: investigation.final_confidence || undefined,
      description: `Severity classified as ${(investigation.final_severity || "info").toUpperCase()} with ${(
        (investigation.final_confidence || 0) * 100
      ).toFixed(0)}% confidence across all corroborated features.`,
      isRecorded: Boolean(investigation.completed_at),
    });
  }

  // Sort: chronological first for events with recordedDate; unrecorded events positioned logically at the end
  const sortedEvents = [...events].sort((a, b) => {
    if (a.recordedDate && b.recordedDate) {
      return a.recordedDate.getTime() - b.recordedDate.getTime();
    }
    if (a.recordedDate && !b.recordedDate) return -1;
    if (!a.recordedDate && b.recordedDate) return 1;
    return 0;
  });

  const filteredEvents =
    filterCategory === "all"
      ? sortedEvents
      : sortedEvents.filter((e) => e.category === filterCategory);

  const getCategoryColor = (cat: TimelineEvent["category"]) => {
    switch (cat) {
      case "submission":
        return "text-accent-primary border-accent-primary/40 bg-accent-primary/10";
      case "modality":
        return "text-cyan-400 border-cyan-500/40 bg-cyan-500/10";
      case "agent":
        return "text-indigo-400 border-indigo-500/40 bg-indigo-500/10";
      case "finding":
        return "text-severity-critical border-severity-critical/40 bg-severity-critical/10";
      case "correlation":
        return "text-amber-400 border-amber-500/40 bg-amber-500/10";
      case "rag":
        return "text-emerald-400 border-emerald-500/40 bg-emerald-500/10";
      case "risk":
        return "text-rose-400 border-rose-500/40 bg-rose-500/10";
      default:
        return "text-soc-text-muted border-soc-border bg-soc-base";
    }
  };

  return (
    <Card className={`p-5 md:p-6 border-soc-border bg-soc-surface ${className}`}>
      {/* Header and Filter Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-soc-border pb-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Clock className="h-4 w-4 text-accent-primary" />
            <h2 className="font-display font-semibold text-sm uppercase tracking-wider text-soc-text-primary">
              Investigation Chronological Timeline
            </h2>
          </div>
          <p className="text-xs text-soc-text-secondary">
            Auditable progression from evidence ingestion to deterministic risk consensus
          </p>
        </div>

        {/* Category Filter Pills */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {[
            { key: "all", label: "All Events" },
            { key: "finding", label: "Findings" },
            { key: "agent", label: "Agents" },
            { key: "modality", label: "Evidence" },
            { key: "correlation", label: "Arbitration" },
          ].map((pill) => (
            <button
              key={pill.key}
              type="button"
              onClick={() => setFilterCategory(pill.key)}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                filterCategory === pill.key
                  ? "bg-accent-primary text-white font-bold"
                  : "bg-soc-base border border-soc-border text-soc-text-secondary hover:text-soc-text-primary"
              }`}
            >
              {pill.label}
            </button>
          ))}
        </div>
      </div>

      {/* Timeline Stream */}
      <div className="relative pl-6 sm:pl-8 border-l border-soc-border/70 space-y-6">
        {filteredEvents.map((evt) => {
          const isExpanded = Boolean(expandedEvents[evt.id]);

          return (
            <div key={evt.id} className="relative group">
              {/* Timeline Dot Marker */}
              <div
                className={`absolute -left-[31px] sm:-left-[39px] top-1.5 h-3.5 w-3.5 rounded-full border-2 bg-soc-surface transition-all group-hover:scale-110 ${
                  evt.isRecorded
                    ? "border-accent-primary bg-accent-primary"
                    : "border-soc-text-muted bg-soc-base"
                }`}
              />

              <div className="p-4 rounded-lg bg-soc-base border border-soc-border transition-colors hover:border-soc-border/90">
                {/* Event Top Bar */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase font-bold border ${getCategoryColor(
                        evt.category
                      )}`}
                    >
                      {evt.stageName}
                    </span>

                    {evt.agentName && (
                      <span className="text-[11px] font-mono text-soc-text-muted">
                        via {evt.agentName}
                      </span>
                    )}

                    {evt.severity && (
                      <SeverityTag severity={(evt.severity as SeverityType) || "info"} />
                    )}

                    {evt.confidence !== undefined && (
                      <span className="text-[10px] font-mono text-accent-primary">
                        {(evt.confidence * 100).toFixed(0)}% conf
                      </span>
                    )}
                  </div>

                  {/* Timestamp / Provenance Badge */}
                  <div className="flex items-center gap-2">
                    {evt.isRecorded ? (
                      <span className="text-[11px] font-mono text-soc-text-primary flex items-center gap-1 font-semibold">
                        <CheckCircle2 className="h-3 w-3 text-status-done shrink-0" />
                        {evt.recordedDate?.toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                        })}
                      </span>
                    ) : (
                      <Badge
                        variant="outline"
                        className="text-[9px] font-mono text-soc-text-muted py-0"
                      >
                        DERIVED STAGE (UNTIMED)
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Event Title & Summary */}
                <h3 className="font-display font-semibold text-xs sm:text-sm text-soc-text-primary mb-1">
                  {evt.title}
                </h3>
                {evt.description && (
                  <p className="text-xs text-soc-text-secondary leading-relaxed">
                    {evt.description}
                  </p>
                )}

                {/* Expandable Details Button */}
                {evt.details && (
                  <div className="mt-3 pt-2.5 border-t border-soc-border/60">
                    <button
                      type="button"
                      onClick={() => toggleExpand(evt.id)}
                      className="text-[11px] font-mono text-accent-primary hover:underline flex items-center gap-1"
                    >
                      {isExpanded ? (
                        <>
                          <ChevronUp className="h-3 w-3" /> Hide Forensic Detail
                        </>
                      ) : (
                        <>
                          <ChevronDown className="h-3 w-3" /> Inspect Forensic Detail
                        </>
                      )}
                    </button>

                    {isExpanded && (
                      <div className="mt-2 p-3 rounded bg-soc-surface border border-soc-border text-xs font-mono space-y-1.5 text-soc-text-secondary">
                        <pre className="text-[11px] overflow-x-auto whitespace-pre-wrap">
                          {JSON.stringify(evt.details, null, 2)}
                        </pre>
                      </div>
                    )}
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
