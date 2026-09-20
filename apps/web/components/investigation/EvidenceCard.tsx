"use client";

import React, { useState } from "react";
import {
  FileText,
  Globe,
  QrCode,
  Image as ImageIcon,
  Mic,
  ChevronDown,
  ChevronUp,
  Target,
  Bot,
  LucideIcon,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { SeverityTag, SeverityType } from "@/components/ui/SeverityTag";
import { Badge } from "@/components/ui/Badge";
import { AgentFindingDetail } from "@/lib/types";

interface EvidenceCardProps {
  finding: AgentFindingDetail;
  agentName?: string;
}

const AGENT_ICONS: Record<string, LucideIcon> = {
  text_agent: FileText,
  url_agent: Globe,
  qr_agent: QrCode,
  image_agent: ImageIcon,
  voice_agent: Mic,
};

export function EvidenceCard({ finding, agentName }: EvidenceCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const displayAgent = agentName || "specialist_agent";
  const IconComponent = AGENT_ICONS[displayAgent.toLowerCase()] || Bot;

  // Normalize indicators
  let indicatorList: string[] = [];
  if (Array.isArray(finding.indicators)) {
    indicatorList = finding.indicators.filter((item): item is string => typeof item === "string");
  } else if (finding.indicators && typeof finding.indicators === "object") {
    indicatorList = Object.keys(finding.indicators);
  }

  const confidencePct = Math.round(finding.confidence * 100);

  const validSeverity: SeverityType =
    finding.severity === "critical" ||
    finding.severity === "high" ||
    finding.severity === "medium" ||
    finding.severity === "low"
      ? finding.severity
      : "info";

  const hasExtraIndicators = indicatorList.length > 3;
  const visibleIndicators = isExpanded ? indicatorList : indicatorList.slice(0, 3);
  const hasDetails = Boolean(
    finding.reasoning ||
    (finding.evidence && Object.keys(finding.evidence).length > 0) ||
    hasExtraIndicators
  );

  return (
    <Card hoverable className="p-5 border-soc-border bg-soc-surface transition-all">
      {/* Top Bar: Agent metadata, Severity tag, Confidence score */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-soc-border/70 pb-3.5 mb-3.5">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded bg-soc-elevated border border-soc-border text-soc-text-primary">
            <IconComponent className="h-4 w-4" />
          </div>
          <div>
            <span className="font-display font-semibold text-xs text-soc-text-primary uppercase tracking-wider">
              {displayAgent.replace(/_/g, " ")}
            </span>
            {finding.status && finding.status !== "ok" && (
              <span className="ml-2 text-[10px] font-mono text-soc-text-muted">
                ({finding.status})
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs font-mono text-soc-text-secondary bg-soc-base px-2.5 py-1 rounded border border-soc-border">
            <Target className="h-3 w-3 text-soc-text-muted" />
            <span>{confidencePct}% Confidence</span>
          </div>
          <SeverityTag severity={validSeverity} />
        </div>
      </div>

      {/* Main Finding Text: 1-line summary when collapsed for 2-second scan, full text when expanded */}
      <div className="mb-3">
        <p
          className={`text-sm text-soc-text-primary font-sans leading-relaxed ${
            !isExpanded ? "line-clamp-1" : ""
          }`}
          title={!isExpanded ? finding.finding : undefined}
        >
          {finding.finding}
        </p>
      </div>

      {/* Scannable Indicator Badges (Top 3 scannable when collapsed, all when expanded) */}
      {indicatorList.length > 0 && (
        <div className="mb-3">
          <div className="flex flex-wrap items-center gap-1.5">
            {visibleIndicators.map((indicator, idx) => (
              <Badge key={idx} variant="outline" className="text-[11px] font-mono py-0.5 px-2">
                {indicator}
              </Badge>
            ))}
            {!isExpanded && hasExtraIndicators && (
              <button
                type="button"
                onClick={() => setIsExpanded(true)}
                className="text-[11px] font-mono text-soc-text-muted hover:text-accent-primary bg-soc-base/80 px-2 py-0.5 rounded border border-soc-border/70 transition-colors cursor-pointer"
              >
                +{indicatorList.length - 3} more
              </button>
            )}
          </div>
        </div>
      )}

      {/* Progressive Disclosure Expand / Collapse Affordance */}
      {hasDetails && (
        <div className="border-t border-soc-border/50 pt-3 mt-1">
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1.5 text-xs font-mono text-soc-text-secondary hover:text-soc-text-primary transition-colors cursor-pointer group"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="h-3.5 w-3.5 text-soc-text-muted group-hover:text-soc-text-primary" />
                <span>Hide Analysis Reasoning &amp; Evidence</span>
              </>
            ) : (
              <>
                <ChevronDown className="h-3.5 w-3.5 text-soc-text-muted group-hover:text-soc-text-primary" />
                <span>View Full Evidence &amp; Reasoning</span>
              </>
            )}
          </button>

          {isExpanded && (
            <div className="mt-3 space-y-3 pt-2 text-xs font-mono bg-soc-base/60 p-3.5 rounded border border-soc-border/60">
              {finding.reasoning && (
                <div>
                  <span className="text-soc-text-muted font-semibold uppercase tracking-wider block mb-1 text-[10px]">
                    Analysis &amp; Reasoning Steps:
                  </span>
                  <p className="text-soc-text-secondary leading-relaxed whitespace-pre-line font-sans text-xs">
                    {finding.reasoning}
                  </p>
                </div>
              )}

              {finding.evidence && Object.keys(finding.evidence).length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-1.5 flex-wrap gap-1">
                    <span className="text-soc-text-muted font-semibold uppercase tracking-wider block text-[10px]">
                      Raw Evidence &amp; Telemetry Payload:
                    </span>
                    {(finding.evidence.source === "seed_curated_data" || finding.evidence.verified === true) && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-mono text-accent-primary bg-accent-primary/10 px-2 py-0.5 rounded border border-accent-primary/30 uppercase tracking-wider font-semibold">
                        <span className="w-1.5 h-1.5 rounded-full bg-accent-primary" />
                        Curated Benchmark Incident
                      </span>
                    )}
                  </div>
                  <pre className="p-2.5 rounded bg-soc-base border border-soc-border overflow-x-auto text-[11px] text-soc-text-secondary leading-normal max-h-64 overflow-y-auto">
                    {JSON.stringify(finding.evidence, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
