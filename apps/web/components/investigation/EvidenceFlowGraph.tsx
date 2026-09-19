"use client";

import React, { useState } from "react";
import {
  FileText,
  Globe,
  QrCode,
  Image as ImageIcon,
  Mic,
  Sparkles,
  ArrowRight,
  GitMerge,
  AlertTriangle,
  BookOpen,
  Info,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { SeverityTag, SeverityType } from "@/components/ui/SeverityTag";
import { InvestigationDetail, AgentFindingDetail } from "@/lib/types";

interface EvidenceFlowGraphProps {
  investigation: InvestigationDetail;
  onSelectAgent?: (agentName: string) => void;
}

const MODALITY_ICONS: Record<string, React.ElementType> = {
  text: FileText,
  url: Globe,
  qr: QrCode,
  image: ImageIcon,
  voice: Mic,
};

export function EvidenceFlowGraph({
  investigation,
  onSelectAgent,
}: EvidenceFlowGraphProps) {
  const [showFormulaDetails, setShowFormulaDetails] = useState(false);

  const runs = investigation.agent_runs || [];
  const inputs = investigation.evidence_inputs || [];
  const risk = investigation.risk;
  const citations = investigation.rag_citations || [];

  // Extract all findings with agent name
  const allFindings: { finding: AgentFindingDetail; agentName: string }[] = [];
  for (const run of runs) {
    if (run.findings) {
      for (const f of run.findings) {
        allFindings.push({ finding: f, agentName: run.agent_name });
      }
    }
  }

  // Precompute indicator frequencies and corroboration groups
  const indicatorAgents = new Map<string, Set<string>>();
  for (const item of allFindings) {
    const rawInd = item.finding.indicators;
    const indList = Array.isArray(rawInd)
      ? rawInd.filter((x): x is string => typeof x === "string")
      : rawInd && typeof rawInd === "object"
      ? Object.keys(rawInd)
      : [];
    for (const ind of indList) {
      if (!indicatorAgents.has(ind)) {
        indicatorAgents.set(ind, new Set());
      }
      indicatorAgents.get(ind)!.add(item.agentName);
    }
  }

  // Shared indicators across 2+ distinct agents
  const sharedIndicators: { indicator: string; agents: string[] }[] = [];
  indicatorAgents.forEach((agentsSet, indicator) => {
    if (agentsSet.size >= 2) {
      sharedIndicators.push({
        indicator,
        agents: Array.from(agentsSet),
      });
    }
  });

  const conflicts = risk?.conflicts || [];
  const hasCorroboration = sharedIndicators.length > 0;
  const hasIntelBonus = citations.some((c) => (c.similarity_score || 0) >= 0.4);

  // Breakdown metrics
  const baseScoreItem = risk?.breakdown?.find((b) => b.component === "base_score");
  const corrobBonusItem = risk?.breakdown?.find((b) => b.component === "corroboration_bonus");
  const intelBonusItem = risk?.breakdown?.find((b) => b.component === "intel_bonus");
  const penaltyItem = risk?.breakdown?.find((b) => b.component === "contradiction_penalty");

  return (
    <Card className="p-5 md:p-6 border-soc-border bg-soc-surface overflow-hidden">
      {/* Header with Title and Mode */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-soc-border pb-4 mb-5">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded bg-accent-primary/10 border border-accent-primary/20 text-accent-primary">
            <GitMerge className="h-4 w-4" />
          </div>
          <div>
            <h3 className="font-display font-bold text-sm tracking-wider uppercase text-soc-text-primary flex items-center gap-2">
              Cross-Modal Evidence Narrative Flow
              <span className="text-[10px] font-mono text-soc-text-muted font-normal normal-case">
                (Deterministic Relationship Graph)
              </span>
            </h3>
            <p className="text-xs text-soc-text-secondary">
              Trace how physical evidence artifacts converge through specialist agents into shared indicators and composite risk.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {hasCorroboration && (
            <Badge
              variant="accent"
              className="text-[10px] font-mono uppercase px-2 py-0.5 flex items-center gap-1"
            >
              <Sparkles className="h-3 w-3" />
              {sharedIndicators.length} Corroborated {sharedIndicators.length === 1 ? "IoC" : "IoCs"}
            </Badge>
          )}
          {conflicts.length > 0 && (
            <Badge
              variant="outline"
              className="text-[10px] font-mono uppercase text-severity-medium border-severity-medium/30 bg-severity-medium/10 flex items-center gap-1"
            >
              <AlertTriangle className="h-3 w-3" />
              {conflicts.length} Conflict {conflicts.length === 1 ? "Penalty" : "Penalties"}
            </Badge>
          )}
        </div>
      </div>

      {/* Main Narrative Flow Stages: 4-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 relative">
        {/* STAGE 1: INGESTED ARTIFACTS */}
        <div className="flex flex-col bg-soc-base/60 rounded border border-soc-border/60 p-3.5">
          <div className="flex items-center justify-between mb-3 pb-2 border-b border-soc-border/40">
            <span className="font-display font-semibold text-[11px] text-soc-text-secondary uppercase tracking-wider">
              1. Ingested Artifacts ({inputs.length})
            </span>
            <span className="text-[10px] font-mono text-soc-text-muted">SOURCE</span>
          </div>

          <div className="space-y-2 flex-grow">
            {inputs.length === 0 ? (
              <p className="text-xs font-mono text-soc-text-muted italic">No raw inputs logged</p>
            ) : (
              inputs.map((inp) => {
                const Icon = MODALITY_ICONS[inp.modality.toLowerCase()] || FileText;
                return (
                  <div
                    key={inp.id}
                    className="p-2.5 rounded bg-soc-surface border border-soc-border/80 text-xs font-mono"
                  >
                    <div className="flex items-center justify-between gap-1.5 mb-1">
                      <div className="flex items-center gap-1.5 text-accent-primary">
                        <Icon className="h-3.5 w-3.5" />
                        <span className="font-semibold uppercase text-[10px] tracking-wide">
                          {inp.modality}
                        </span>
                      </div>
                      <span className="text-[9px] text-soc-text-muted">
                        {new Date(inp.created_at).toLocaleTimeString([], {
                          minute: "2-digit",
                          second: "2-digit",
                        })}
                      </span>
                    </div>
                    <p className="text-soc-text-secondary text-[11px] truncate" title={inp.raw_content_ref || inp.file_path || ""}>
                      {inp.raw_content_ref || inp.file_path || "Binary Artifact"}
                    </p>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* STAGE 2: SPECIALIST SWARM FINDINGS */}
        <div className="flex flex-col bg-soc-base/60 rounded border border-soc-border/60 p-3.5">
          <div className="flex items-center justify-between mb-3 pb-2 border-b border-soc-border/40">
            <span className="font-display font-semibold text-[11px] text-soc-text-secondary uppercase tracking-wider">
              2. Specialist Claims ({runs.length})
            </span>
            <span className="text-[10px] font-mono text-soc-text-muted">ANALYSIS</span>
          </div>

          <div className="space-y-2 flex-grow">
            {runs.length === 0 ? (
              <p className="text-xs font-mono text-soc-text-muted italic">Swarm pending</p>
            ) : (
              runs.map((r) => {
                const findingsCount = r.findings?.length || 0;
                // Find highest severity finding for this agent
                const sevs = r.findings?.map((f) => f.severity) || [];
                const highestSev: SeverityType = sevs.includes("critical")
                  ? "critical"
                  : sevs.includes("high")
                  ? "high"
                  : sevs.includes("medium")
                  ? "medium"
                  : sevs.includes("low")
                  ? "low"
                  : "info";

                return (
                  <div
                    key={r.id}
                    onClick={() => onSelectAgent?.(r.agent_name)}
                    className="p-2.5 rounded bg-soc-surface border border-soc-border hover:border-accent-primary/50 transition-colors cursor-pointer text-xs font-mono"
                  >
                    <div className="flex items-center justify-between gap-1.5 mb-1">
                      <span className="font-display font-semibold uppercase text-[11px] text-soc-text-primary tracking-wider truncate">
                        {r.agent_name.replace(/_/g, " ")}
                      </span>
                      <SeverityTag severity={highestSev} />
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-soc-text-muted mt-1">
                      <span>{findingsCount} {findingsCount === 1 ? "claim" : "claims"}</span>
                      {r.latency_ms ? <span>{r.latency_ms} ms</span> : null}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* STAGE 3: CORROBORATION HUB & SHARED IoCs */}
        <div className="flex flex-col bg-soc-base/60 rounded border border-accent-primary/20 p-3.5">
          <div className="flex items-center justify-between mb-3 pb-2 border-b border-soc-border/40">
            <span className="font-display font-semibold text-[11px] text-accent-primary uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="h-3 w-3" />
              3. Corroboration Hub
            </span>
            <span className="text-[10px] font-mono text-accent-primary">SYNTHESIS</span>
          </div>

          <div className="space-y-2 flex-grow">
            {sharedIndicators.length === 0 ? (
              <div className="p-3 text-center border border-dashed border-soc-border rounded text-[11px] font-mono text-soc-text-muted">
                No overlapping IoCs across distinct modalities. Single-modality indicators only.
              </div>
            ) : (
              sharedIndicators.map((item, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded bg-accent-primary/5 border border-accent-primary/30 text-xs font-mono"
                >
                  <div className="flex items-center justify-between gap-1 mb-1">
                    <span className="text-accent-primary font-bold text-[11px] truncate" title={item.indicator}>
                      {item.indicator}
                    </span>
                    <Badge variant="accent" className="text-[9px] py-0 px-1 font-mono shrink-0">
                      +0.10 BONUS
                    </Badge>
                  </div>
                  <div className="text-[10px] text-soc-text-secondary flex items-center gap-1 flex-wrap">
                    <span className="text-soc-text-muted">Shared by:</span>
                    {item.agents.map((ag) => (
                      <span key={ag} className="px-1 py-0.2 bg-soc-base rounded border border-soc-border/80">
                        {ag.replace(/_agent/g, "")}
                      </span>
                    ))}
                  </div>
                </div>
              ))
            )}

            {/* Conflicts if detected */}
            {conflicts.map((conf, cIdx) => (
              <div
                key={cIdx}
                className="p-2.5 rounded bg-severity-medium/10 border border-severity-medium/30 text-xs font-mono"
              >
                <div className="flex items-center justify-between gap-1 mb-1">
                  <span className="text-severity-medium font-semibold text-[10px] uppercase flex items-center gap-1">
                    <AlertTriangle className="h-3 w-3" />
                    Severity Divergence
                  </span>
                  <span className="text-[9px] text-severity-medium font-bold">-0.10 PENALTY</span>
                </div>
                <p className="text-[10px] text-soc-text-secondary truncate" title={conf.resolution_rule || conf.conflict_type}>
                  {conf.agent_a.replace(/_agent/, "")} vs {conf.agent_b.replace(/_agent/, "")}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* STAGE 4: DETERMINISTIC VERDICT & INTEL */}
        <div className="flex flex-col bg-soc-base/60 rounded border border-soc-border/60 p-3.5">
          <div className="flex items-center justify-between mb-3 pb-2 border-b border-soc-border/40">
            <span className="font-display font-semibold text-[11px] text-soc-text-secondary uppercase tracking-wider">
              4. Composite Verdict
            </span>
            <span className="text-[10px] font-mono text-soc-text-muted">RESULT</span>
          </div>

          <div className="space-y-3 flex-grow flex flex-col justify-between">
            {/* Verdict Display Box */}
            <div className="p-3 rounded bg-soc-surface border border-soc-border text-center">
              <div className="text-[10px] font-mono text-soc-text-muted uppercase tracking-wider mb-1">
                Deterministic Risk Score
              </div>
              <div className="font-display font-bold text-2xl text-soc-text-primary tracking-tight">
                {investigation.final_risk_score !== null && investigation.final_risk_score !== undefined
                  ? investigation.final_risk_score.toFixed(3)
                  : "N/A"}
              </div>
              <div className="mt-1.5 flex justify-center">
                <SeverityTag severity={(investigation.final_severity as SeverityType) || "info"} />
              </div>
            </div>

            {/* RAG Intel Grounding Summary */}
            <div className="p-2.5 rounded bg-soc-surface border border-soc-border/80 text-[11px] font-mono">
              <div className="flex items-center justify-between gap-1 mb-1">
                <span className="text-soc-text-secondary font-semibold text-[10px] uppercase flex items-center gap-1">
                  <BookOpen className="h-3 w-3 text-severity-low" />
                  RAG Intelligence
                </span>
                {hasIntelBonus ? (
                  <Badge variant="outline" className="text-[9px] py-0 px-1 text-severity-low border-severity-low/30 bg-severity-low/10 font-mono">
                    +0.15 INTEL
                  </Badge>
                ) : (
                  <span className="text-[9px] text-soc-text-muted">0.00</span>
                )}
              </div>
              <p className="text-[10px] text-soc-text-muted truncate">
                {citations.length > 0
                  ? citations[0].source_title
                  : "No high-similarity CERT-In advisories"}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* SVG Connecting Flow Arrows Indicator Bar */}
      <div className="mt-4 pt-3 border-t border-soc-border/60 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs font-mono text-soc-text-muted">
        <div className="flex items-center gap-2 flex-wrap text-[11px]">
          <span className="text-soc-text-secondary font-semibold uppercase text-[10px]">Flow Logic:</span>
          <span>Inputs</span>
          <ArrowRight className="h-3 w-3 text-accent-primary" />
          <span>Specialists</span>
          <ArrowRight className="h-3 w-3 text-accent-primary" />
          <span className="text-accent-primary font-semibold">Corroboration (+0.10)</span>
          <ArrowRight className="h-3 w-3 text-accent-primary" />
          <span className="text-soc-text-primary font-semibold">Risk Verdict</span>
        </div>

        {/* Expandable Mathematical Proof Drawer Toggle */}
        <button
          type="button"
          onClick={() => setShowFormulaDetails(!showFormulaDetails)}
          className="inline-flex items-center gap-1.5 text-[11px] text-accent-primary hover:underline cursor-pointer"
        >
          <Info className="h-3.5 w-3.5" />
          {showFormulaDetails ? "Hide Formula Trace" : "Inspect Formula Trace"}
          {showFormulaDetails ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        </button>
      </div>

      {/* Expandable Mathematical Formula Arithmetic Trace */}
      {showFormulaDetails && (
        <div className="mt-3 p-3.5 rounded bg-soc-base border border-soc-border font-mono text-xs space-y-2">
          <div className="text-[10px] text-soc-text-muted uppercase tracking-wider font-semibold">
            Deterministic Formula Calculation Trace
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-2 text-[11px]">
            <div className="p-2 rounded bg-soc-surface border border-soc-border">
              <span className="text-soc-text-muted block text-[10px]">1. Base Evidence:</span>
              <span className="font-bold text-soc-text-primary">
                {baseScoreItem ? baseScoreItem.value.toFixed(4) : "0.0000"}
              </span>
            </div>
            <div className="p-2 rounded bg-soc-surface border border-soc-border">
              <span className="text-soc-text-muted block text-[10px]">2. Corroboration Bonus:</span>
              <span className="font-bold text-accent-primary">
                +{corrobBonusItem ? corrobBonusItem.value.toFixed(4) : "0.0000"}
              </span>
            </div>
            <div className="p-2 rounded bg-soc-surface border border-soc-border">
              <span className="text-soc-text-muted block text-[10px]">3. Threat Intel Bonus:</span>
              <span className="font-bold text-severity-low">
                +{intelBonusItem ? intelBonusItem.value.toFixed(4) : "0.0000"}
              </span>
            </div>
            <div className="p-2 rounded bg-soc-surface border border-soc-border">
              <span className="text-soc-text-muted block text-[10px]">4. Contradiction Penalty:</span>
              <span className="font-bold text-severity-medium">
                -{penaltyItem ? penaltyItem.value.toFixed(4) : "0.0000"}
              </span>
            </div>
          </div>
          <p className="text-[10px] text-soc-text-secondary leading-relaxed pt-1">
            <span className="font-semibold text-soc-text-primary">Composite Math:</span> clamp({baseScoreItem?.value.toFixed(4) || "0.0000"} + {corrobBonusItem?.value.toFixed(4) || "0.0000"} + {intelBonusItem?.value.toFixed(4) || "0.0000"} - {penaltyItem?.value.toFixed(4) || "0.0000"}, 0.0, 1.0) = <span className="font-bold text-accent-primary">{investigation.final_risk_score?.toFixed(4) || "0.0000"}</span>
          </p>
        </div>
      )}
    </Card>
  );
}
