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
  const [showDetails, setShowDetails] = useState(false);

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

      {/* Main Finding Text */}
      <div className="mb-4">
        <p className="text-sm text-soc-text-primary leading-relaxed font-sans font-normal">
          {finding.finding}
        </p>
      </div>

      {/* Indicator Badges */}
      {indicatorList.length > 0 && (
        <div className="mb-4">
          <div className="text-[11px] font-mono text-soc-text-muted uppercase tracking-wider mb-2">
            Extracted Indicators ({indicatorList.length})
          </div>
          <div className="flex flex-wrap gap-1.5">
            {indicatorList.map((indicator, idx) => (
              <Badge key={idx} variant="outline" className="text-[11px] font-mono py-0.5 px-2">
                {indicator}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Expandable Reasoning & Raw Evidence Toggle */}
      {(finding.reasoning || (finding.evidence && Object.keys(finding.evidence).length > 0)) && (
        <div className="border-t border-soc-border/50 pt-3">
          <button
            type="button"
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center gap-1.5 text-xs font-mono text-soc-text-secondary hover:text-soc-text-primary transition-colors cursor-pointer"
          >
            {showDetails ? (
              <>
                <ChevronUp className="h-3.5 w-3.5" />
                Hide Analysis Reasoning
              </>
            ) : (
              <>
                <ChevronDown className="h-3.5 w-3.5" />
                View Reasoning &amp; Evidence Details
              </>
            )}
          </button>

          {showDetails && (
            <div className="mt-3 space-y-3 pt-2 text-xs font-mono bg-soc-base/60 p-3.5 rounded border border-soc-border/60">
              {finding.reasoning && (
                <div>
                  <span className="text-soc-text-muted font-semibold uppercase tracking-wider block mb-1 text-[10px]">
                    Agent Reasoning Steps:
                  </span>
                  <p className="text-soc-text-secondary leading-relaxed whitespace-pre-line font-sans text-xs">
                    {finding.reasoning}
                  </p>
                </div>
              )}

              {finding.evidence && Object.keys(finding.evidence).length > 0 && (
                <div>
                  <span className="text-soc-text-muted font-semibold uppercase tracking-wider block mb-1 text-[10px]">
                    Supporting Payload Metadata:
                  </span>
                  <pre className="p-2.5 rounded bg-soc-base border border-soc-border overflow-x-auto text-[11px] text-soc-text-secondary leading-normal">
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
