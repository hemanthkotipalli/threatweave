"use client";

import React, { useState } from "react";
import { BookOpen, ShieldCheck, ChevronDown, ChevronUp, Database } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { RagCitation } from "@/lib/types";

interface RagCitationPanelProps {
  citations?: RagCitation[];
}

function getSourceBadgeVariant(sourceType: string): "default" | "outline" | "accent" {
  switch (sourceType) {
    case "CERT-In":
      return "accent";
    case "RBI":
      return "outline";
    case "Scam-Intel":
      return "default";
    default:
      return "default";
  }
}

export function RagCitationPanel({ citations = [] }: RagCitationPanelProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <Card className="p-6 border-soc-border bg-soc-surface">
      <div className="flex items-center justify-between border-b border-soc-border pb-4 mb-6">
        <div className="flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-accent-primary" />
          <h2 className="font-display font-semibold text-sm uppercase tracking-wider text-soc-text-primary">
            RAG-Grounded Threat Intelligence Citations
          </h2>
        </div>
        <span className="text-xs font-mono text-soc-text-muted flex items-center gap-1.5">
          <Database className="h-3.5 w-3.5 text-soc-text-secondary" />
          CHROMADB VECTOR REPOSITORY
        </span>
      </div>

      {citations.length === 0 ? (
        <EmptyState
          title="No matching threat advisory found for this evidence"
          description="None of the curated CERT-In, RBI, or Scam-Intel advisory documents cleared the similarity threshold (0.40). In accordance with ThreatWeave's strict honesty principle, external intelligence is never fabricated or forced for low-relevance queries."
          className="border border-soc-border/60 bg-soc-base/20"
        />
      ) : (
        <div className="space-y-4">
          <div className="text-xs font-mono text-soc-text-secondary flex items-center justify-between">
            <span>Verified Grounding Matches ({citations.length}):</span>
            <span className="text-[11px] text-severity-low flex items-center gap-1 font-semibold">
              <ShieldCheck className="h-3.5 w-3.5" />
              +0.15 Intel Bonus Granted
            </span>
          </div>

          <div className="grid grid-cols-1 gap-3.5">
            {citations.map((citation, idx) => {
              const citationId = citation.id || `citation-${idx}`;
              const isExpanded = expandedId === citationId;
              const matchPct = Math.round(citation.similarity_score * 100);

              return (
                <div
                  key={citationId}
                  className="p-4 rounded-md bg-soc-base border border-soc-border hover:border-soc-border/80 transition-all"
                >
                  <div className="flex flex-wrap items-start justify-between gap-2.5 mb-2">
                    <div className="space-y-1 max-w-xl">
                      <div className="flex items-center gap-2">
                        <Badge variant={getSourceBadgeVariant(citation.source_type)}>
                          {citation.source_type}
                        </Badge>
                        <span className="text-[11px] font-mono text-soc-text-muted">
                          Similarity: {citation.similarity_score.toFixed(4)} ({matchPct}% Match)
                        </span>
                      </div>
                      <h3 className="font-display font-semibold text-sm text-soc-text-primary">
                        {citation.source_title}
                      </h3>
                    </div>

                    <button
                      type="button"
                      onClick={() => toggleExpand(citationId)}
                      className="flex items-center gap-1 text-xs font-mono text-soc-text-secondary hover:text-soc-text-primary transition-colors cursor-pointer"
                    >
                      {isExpanded ? (
                        <>
                          <ChevronUp className="h-3.5 w-3.5" />
                          Hide Excerpt
                        </>
                      ) : (
                        <>
                          <ChevronDown className="h-3.5 w-3.5" />
                          View Excerpt
                        </>
                      )}
                    </button>
                  </div>

                  {/* Excerpt Body */}
                  <div className="mt-2 text-xs font-sans text-soc-text-secondary leading-relaxed bg-soc-surface/60 p-3 rounded border border-soc-border/40">
                    <p className={isExpanded ? "whitespace-pre-line" : "line-clamp-3"}>
                      {citation.chunk_text}
                    </p>
                  </div>

                  {citation.url && (
                    <div className="mt-2 text-[11px] font-mono text-soc-text-muted italic truncate">
                      Source ref: {citation.url}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </Card>
  );
}
