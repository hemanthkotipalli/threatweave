"use client";

import React, { useState } from "react";
import {
  FileText,
  Globe,
  QrCode,
  Image as ImageIcon,
  Mic,
  Sparkles,
  BookOpen,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Search,
  Bookmark,
  BookmarkCheck,
  ExternalLink,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { SeverityTag, SeverityType } from "@/components/ui/SeverityTag";
import { InvestigationDetail, AgentFindingDetail } from "@/lib/types";

interface Props {
  investigation: InvestigationDetail;
  allFindings: { finding: AgentFindingDetail; agentName: string }[];
  bookmarkedIds?: string[];
  onToggleBookmark?: (id: string) => void;
  className?: string;
}

export function EvidenceExplorer({
  investigation,
  allFindings,
  bookmarkedIds = [],
  onToggleBookmark,
  className = "",
}: Props) {
  const [activeTab, setActiveTab] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [expandedPayloads, setExpandedPayloads] = useState<Record<string, boolean>>({});
  const [copiedIndicator, setCopiedIndicator] = useState<string | null>(null);

  const togglePayload = (id: string) => {
    setExpandedPayloads((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedIndicator(text);
    setTimeout(() => setCopiedIndicator(null), 2000);
  };

  // Helper to determine evidence provenance
  const getProvenance = (f: AgentFindingDetail) => {
    const rawRefs = f.external_refs;
    const hasExternal =
      (Array.isArray(rawRefs) && rawRefs.length > 0) ||
      (rawRefs && typeof rawRefs === "object" && Object.keys(rawRefs).length > 0);

    if (hasExternal) {
      return {
        label: "EXTERNAL REPUTATION",
        color: "text-amber-400 border-amber-500/30 bg-amber-500/10",
        description: "Corroborated against external threat intelligence registries",
      };
    }

    if (f.evidence && (f.evidence as Record<string, unknown>).heuristic_rule) {
      return {
        label: "HEURISTIC DETECTION",
        color: "text-cyan-400 border-cyan-500/30 bg-cyan-500/10",
        description: "Deterministic pattern, regex match, or domain entropy rule",
      };
    }

    if (f.reasoning && f.reasoning.length > 80) {
      return {
        label: "AI-GENERATED EXPLANATION",
        color: "text-indigo-400 border-indigo-500/30 bg-indigo-500/10",
        description: "Neural LLM multimodal reasoning and intent analysis",
      };
    }

    return {
      label: "VERIFIED EVIDENCE",
      color: "text-status-done border-status-done/30 bg-status-done/10",
      description: "Direct observation extracted from ingested artifact",
    };
  };

  // Group / filter findings by tab
  const getModalityFromAgent = (agent: string) => {
    const a = agent.toLowerCase();
    if (a.includes("text")) return "text";
    if (a.includes("url")) return "url";
    if (a.includes("qr")) return "qr";
    if (a.includes("image")) return "image";
    if (a.includes("voice") || a.includes("audio")) return "voice";
    return "other";
  };

  // Precompute indicator frequencies for cross-modal
  const indicatorFreq = new Map<string, number>();
  for (const item of allFindings) {
    const rawInd = item.finding.indicators;
    const indList = Array.isArray(rawInd)
      ? rawInd.filter((x): x is string => typeof x === "string")
      : rawInd && typeof rawInd === "object"
      ? Object.keys(rawInd)
      : [];
    for (const ind of indList) {
      indicatorFreq.set(ind, (indicatorFreq.get(ind) || 0) + 1);
    }
  }

  const filteredFindings = allFindings.filter((item) => {
    const mod = getModalityFromAgent(item.agentName);

    // Tab filter
    if (activeTab === "text" && mod !== "text") return false;
    if (activeTab === "url" && mod !== "url") return false;
    if (activeTab === "qr" && mod !== "qr") return false;
    if (activeTab === "image" && mod !== "image") return false;
    if (activeTab === "voice" && mod !== "voice") return false;
    if (activeTab === "cross-modal") {
      const rawInd = item.finding.indicators;
      const indList = Array.isArray(rawInd)
        ? rawInd.filter((x): x is string => typeof x === "string")
        : rawInd && typeof rawInd === "object"
        ? Object.keys(rawInd)
        : [];
      const hasShared = indList.some((ind) => (indicatorFreq.get(ind) || 0) > 1);
      if (!hasShared) return false;
    }

    // Search query filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const inTitle = item.finding.finding.toLowerCase().includes(q);
      const inReasoning = (item.finding.reasoning || "").toLowerCase().includes(q);
      const rawInd = item.finding.indicators;
      const indList = Array.isArray(rawInd)
        ? rawInd.filter((x): x is string => typeof x === "string")
        : [];
      const inInd = indList.some((i) => i.toLowerCase().includes(q));
      return inTitle || inReasoning || inInd;
    }

    return true;
  });

  const citations = investigation.rag_citations || [];

  return (
    <Card className={`p-5 md:p-6 border-soc-border bg-soc-surface ${className}`}>
      {/* Header and Search */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-soc-border pb-4 mb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Search className="h-4 w-4 text-accent-primary" />
            <h2 className="font-display font-semibold text-sm uppercase tracking-wider text-soc-text-primary">
              Multimodal Evidence Explorer
            </h2>
          </div>
          <p className="text-xs text-soc-text-secondary">
            Inspect verified indicators, analytical reasoning, and provenance classifications
          </p>
        </div>

        {/* Search Input */}
        <div className="relative w-full md:w-64">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search indicators, tokens, findings..."
            className="w-full bg-soc-base border border-soc-border rounded px-3 py-1.5 text-xs font-mono text-soc-text-primary placeholder:text-soc-text-muted focus:outline-none focus:border-accent-primary"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery("")}
              className="absolute right-2.5 top-2 text-[10px] font-mono text-soc-text-muted hover:text-soc-text-primary"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Modality Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 border-b border-soc-border/70 mb-5 scrollbar-thin">
        {[
          { key: "all", label: `All Findings (${allFindings.length})` },
          { key: "text", label: "Text / SMS", icon: FileText },
          { key: "url", label: "URL Sandbox", icon: Globe },
          { key: "qr", label: "QR Code", icon: QrCode },
          { key: "image", label: "Image / OCR", icon: ImageIcon },
          { key: "voice", label: "Voice / Speech", icon: Mic },
          { key: "cross-modal", label: "Cross-Modal", icon: Sparkles },
          { key: "rag", label: `RAG Intel (${citations.length})`, icon: BookOpen },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveTab(tab.key)}
              className={`px-3 py-1.5 rounded text-xs font-mono flex items-center gap-1.5 whitespace-nowrap transition-colors ${
                activeTab === tab.key
                  ? "bg-accent-primary text-white font-bold"
                  : "bg-soc-base border border-soc-border text-soc-text-secondary hover:text-soc-text-primary"
              }`}
            >
              {Icon && <Icon className="h-3.5 w-3.5" />}
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab: RAG Intel Special View */}
      {activeTab === "rag" ? (
        <div className="space-y-4">
          {citations.length === 0 ? (
            <div className="p-8 text-center text-xs font-mono text-soc-text-muted bg-soc-base rounded border border-soc-border">
              No external threat advisories met the cosine similarity threshold for this incident.
            </div>
          ) : (
            citations.map((cit, idx) => (
              <div
                key={cit.id || idx}
                className="p-4 rounded bg-soc-base border border-soc-border space-y-2 text-xs font-mono"
              >
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-accent-primary/10 border border-accent-primary/30 text-accent-primary">
                      {cit.source_type}
                    </span>
                    <span className="font-semibold text-soc-text-primary">
                      {cit.source_title}
                    </span>
                  </div>
                  <span className="text-soc-text-muted text-[11px]">
                    Cosine Similarity: {(cit.similarity_score * 100).toFixed(1)}%
                  </span>
                </div>
                <p className="text-soc-text-secondary text-xs leading-relaxed bg-soc-surface p-3 rounded border border-soc-border/60">
                  &ldquo;{cit.chunk_text}&rdquo;
                </p>
                {cit.url && (
                  <a
                    href={cit.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-[11px] text-accent-primary hover:underline"
                  >
                    View Official Threat Intelligence Source <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>
            ))
          )}
        </div>
      ) : (
        /* Findings List */
        <div className="space-y-4">
          {filteredFindings.length === 0 ? (
            <div className="p-8 text-center text-xs font-mono text-soc-text-muted bg-soc-base rounded border border-soc-border">
              No findings matched the selected filter or search term.
            </div>
          ) : (
            filteredFindings.map((item, idx) => {
              const findingId = String(item.finding.id || idx);
              const prov = getProvenance(item.finding);
              const isPayloadOpen = Boolean(expandedPayloads[findingId]);
              const isBookmarked = bookmarkedIds.includes(findingId);

              const rawInd = item.finding.indicators;
              const indicators = Array.isArray(rawInd)
                ? rawInd.filter((x): x is string => typeof x === "string")
                : rawInd && typeof rawInd === "object"
                ? Object.keys(rawInd)
                : [];

              return (
                <div
                  key={findingId}
                  className="p-4 rounded-lg bg-soc-base border border-soc-border transition-colors hover:border-soc-border/90 space-y-3"
                >
                  {/* Top Bar */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-xs font-bold text-accent-primary uppercase">
                        {item.agentName.replace("_agent", "")} specialist
                      </span>

                      <SeverityTag
                        severity={(item.finding.severity as SeverityType) || "info"}
                      />

                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase font-bold border ${prov.color}`}
                        title={prov.description}
                      >
                        {prov.label}
                      </span>

                      <span className="text-[11px] font-mono text-soc-text-muted">
                        Confidence: {(item.finding.confidence * 100).toFixed(0)}%
                      </span>
                    </div>

                    {/* Bookmark Action */}
                    {onToggleBookmark && (
                      <button
                        type="button"
                        onClick={() => onToggleBookmark(findingId)}
                        className={`text-xs font-mono flex items-center gap-1 transition-colors ${
                          isBookmarked
                            ? "text-accent-primary font-bold"
                            : "text-soc-text-muted hover:text-soc-text-primary"
                        }`}
                      >
                        {isBookmarked ? (
                          <>
                            <BookmarkCheck className="h-3.5 w-3.5" /> Bookmarked
                          </>
                        ) : (
                          <>
                            <Bookmark className="h-3.5 w-3.5" /> Bookmark
                          </>
                        )}
                      </button>
                    )}
                  </div>

                  {/* Finding Title */}
                  <h3 className="font-display font-semibold text-sm sm:text-base text-soc-text-primary">
                    {item.finding.finding}
                  </h3>

                  {/* Analytical Reasoning */}
                  {item.finding.reasoning && (
                    <div className="p-3 rounded bg-soc-surface border border-soc-border/70 text-xs text-soc-text-secondary leading-relaxed">
                      <span className="font-mono font-bold text-soc-text-muted text-[10px] uppercase block mb-1">
                        Forensic Reasoning
                      </span>
                      {item.finding.reasoning}
                    </div>
                  )}

                  {/* Indicators Chip Bar */}
                  {indicators.length > 0 && (
                    <div className="flex items-center gap-1.5 flex-wrap pt-1">
                      <span className="text-[11px] font-mono text-soc-text-muted mr-1">
                        Extracted IOCs:
                      </span>
                      {indicators.map((ind) => {
                        const isCopied = copiedIndicator === ind;
                        return (
                          <button
                            key={ind}
                            type="button"
                            onClick={() => handleCopy(ind)}
                            title="Click to copy IOC indicator"
                            className="px-2 py-0.5 rounded bg-soc-surface border border-soc-border hover:border-accent-primary text-[11px] font-mono text-soc-text-primary flex items-center gap-1 transition-colors group"
                          >
                            <span>{ind}</span>
                            {isCopied ? (
                              <Check className="h-3 w-3 text-status-done" />
                            ) : (
                              <Copy className="h-2.5 w-2.5 text-soc-text-muted group-hover:text-accent-primary" />
                            )}
                          </button>
                        );
                      })}
                    </div>
                  )}

                  {/* Expand Raw Evidence Payload */}
                  <div className="pt-2 border-t border-soc-border/50 flex items-center justify-between text-[11px] font-mono">
                    <button
                      type="button"
                      onClick={() => togglePayload(findingId)}
                      className="text-accent-primary hover:underline flex items-center gap-1"
                    >
                      {isPayloadOpen ? (
                        <>
                          <ChevronUp className="h-3 w-3" /> Hide Raw Evidence
                        </>
                      ) : (
                        <>
                          <ChevronDown className="h-3 w-3" /> Inspect Raw Evidence JSON
                        </>
                      )}
                    </button>
                    <span className="text-soc-text-muted">
                      Status: {item.finding.status || "ok"}
                    </span>
                  </div>

                  {isPayloadOpen && (
                    <div className="p-3 rounded bg-soc-surface border border-soc-border text-xs font-mono">
                      <pre className="text-[11px] text-soc-text-secondary overflow-x-auto whitespace-pre-wrap">
                        {JSON.stringify(
                          {
                            finding: item.finding.finding,
                            evidence: item.finding.evidence,
                            indicators: item.finding.indicators,
                            external_refs: item.finding.external_refs,
                          },
                          null,
                          2
                        )}
                      </pre>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}
    </Card>
  );
}
