"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Printer,
  Shield,
  AlertTriangle,
  FileText,
  Globe,
  Image as ImageIcon,
  Mic,
  BookOpen,
  Scale,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { SeverityTag, SeverityType } from "@/components/ui/SeverityTag";
import { getInvestigationReport, ApiError } from "@/lib/api";
import { InvestigationReportData } from "@/lib/types";

export default function InvestigationReportPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [report, setReport] = useState<InvestigationReportData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadReport() {
      if (!id) return;
      setIsLoading(true);
      setError(null);
      try {
        const data = await getInvestigationReport(id);
        if (isMounted) {
          setReport(data);
        }
      } catch (err) {
        if (isMounted) {
          if (err instanceof ApiError) {
            setError(err.message);
          } else {
            setError("Failed to load investigation report.");
          }
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadReport();

    return () => {
      isMounted = false;
    };
  }, [id]);

  const handlePrint = () => {
    window.print();
  };

  const getModalityIcon = (mod: string) => {
    switch (mod.toLowerCase()) {
      case "text":
        return <FileText className="h-4 w-4" />;
      case "url":
        return <Globe className="h-4 w-4" />;
      case "image":
      case "qr":
        return <ImageIcon className="h-4 w-4" />;
      case "voice":
      case "audio":
        return <Mic className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  return (
    <div className="report-container min-h-screen bg-soc-base text-soc-text-primary px-4 sm:px-8 py-8 max-w-5xl mx-auto w-full">
      {/* Print-specific style overrides */}
      <style jsx global>{`
        @media print {
          @page {
            margin: 1.2cm;
            size: portrait;
          }
          body {
            background-color: #ffffff !important;
            color: #111827 !important;
            font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
          }
          .report-container {
            background-color: #ffffff !important;
            color: #111827 !important;
            padding: 0 !important;
            max-width: 100% !important;
          }
          .no-print {
            display: none !important;
          }
          .print-card {
            background-color: #ffffff !important;
            border: 1px solid #d1d5db !important;
            color: #111827 !important;
            box-shadow: none !important;
            break-inside: avoid !important;
            page-break-inside: avoid !important;
            margin-bottom: 1.5rem !important;
          }
          .print-table th {
            background-color: #f3f4f6 !important;
            color: #111827 !important;
            border-bottom: 2px solid #d1d5db !important;
          }
          .print-table td {
            border-bottom: 1px solid #e5e7eb !important;
            color: #1f2937 !important;
          }
          .print-badge {
            border: 1px solid #9ca3af !important;
            background-color: #f3f4f6 !important;
            color: #111827 !important;
          }
          .print-subtle {
            color: #4b5563 !important;
          }
          .print-accent {
            color: #0f172a !important;
            font-weight: 700 !important;
          }
        }
      `}</style>

      {/* Top Navigation & Action Controls (Hidden when printing) */}
      <div className="no-print flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-soc-border pb-6 mb-8">
        <div className="flex items-center gap-3">
          <Link
            href={`/investigations/${id}`}
            className="inline-flex items-center gap-1.5 text-xs font-mono text-soc-text-secondary hover:text-accent-primary transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Workspace
          </Link>
          <span className="text-soc-text-muted">/</span>
          <Link
            href="/investigations"
            className="text-xs font-mono text-soc-text-secondary hover:text-accent-primary transition-colors"
          >
            History
          </Link>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => router.push(`/investigations/${id}`)}
          >
            Open Interactive Workspace
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handlePrint}
            className="shadow-md"
          >
            <Printer className="h-4 w-4 mr-2" />
            Print / Export PDF
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-6">
          <Card className="p-6 space-y-3">
            <Skeleton className="h-8 w-2/3" />
            <Skeleton className="h-4 w-1/3" />
          </Card>
          <Card className="p-6 space-y-4">
            <Skeleton className="h-32 w-full" />
          </Card>
          <Card className="p-6 space-y-4">
            <Skeleton className="h-48 w-full" />
          </Card>
        </div>
      ) : error || !report ? (
        <Card className="p-8 text-center border-severity-critical/30 bg-soc-surface">
          <div className="flex h-12 w-12 items-center justify-center rounded bg-severity-critical/10 text-severity-critical mx-auto mb-4 border border-severity-critical/20">
            <AlertCircle className="h-6 w-6" />
          </div>
          <h2 className="font-display font-semibold text-lg text-soc-text-primary mb-2">
            Unable to Generate Report
          </h2>
          <p className="text-sm text-soc-text-secondary max-w-md mx-auto mb-6 font-mono">
            {error || "Report data could not be retrieved."}
          </p>
          <div className="flex justify-center gap-3">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => router.push("/investigations")}
            >
              Return to Queue
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => window.location.reload()}
            >
              Retry
            </Button>
          </div>
        </Card>
      ) : (
        <div className="space-y-8">
          {/* Executive Document Header */}
          <header className="print-card bg-soc-surface border border-soc-border rounded-lg p-6 sm:p-8">
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-soc-border pb-6 mb-6">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="h-6 w-6 text-accent-primary" />
                  <span className="text-xs font-mono font-bold tracking-widest text-accent-primary uppercase">
                    ThreatWeave Multimodal Intelligence
                  </span>
                </div>
                <h1 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-soc-text-primary mb-2">
                  Executive Threat Investigation Report
                </h1>
                <p className="text-sm font-display font-medium text-soc-text-secondary">
                  Target: {report.investigation.title || "Untitled Multimodal Incident"}
                </p>
              </div>

              <div className="text-left sm:text-right space-y-1 font-mono text-xs text-soc-text-muted">
                <div>
                  <span className="font-semibold text-soc-text-secondary">Report ID:</span>{" "}
                  <span className="select-all">{report.report_id.slice(0, 13)}...</span>
                </div>
                <div>
                  <span className="font-semibold text-soc-text-secondary">Audit Status:</span>{" "}
                  <span className="text-accent-primary font-bold uppercase">{report.format}</span>
                </div>
                <div>
                  <span className="font-semibold text-soc-text-secondary">Generated:</span>{" "}
                  {new Date(report.generated_at).toLocaleString()}
                </div>
              </div>
            </div>

            {/* Incident Metadata Strip */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
              <div className="p-3 bg-soc-base rounded border border-soc-border print-card">
                <span className="text-soc-text-muted block mb-1">Investigation ID</span>
                <span className="text-soc-text-primary truncate block" title={report.investigation.id}>
                  {report.investigation.id.slice(0, 8)}...
                </span>
              </div>

              <div className="p-3 bg-soc-base rounded border border-soc-border print-card">
                <span className="text-soc-text-muted block mb-1">Incident Status</span>
                <span className="text-accent-primary font-bold uppercase block">
                  {report.investigation.status}
                </span>
              </div>

              <div className="p-3 bg-soc-base rounded border border-soc-border print-card">
                <span className="text-soc-text-muted block mb-1">Submitted At</span>
                <span className="text-soc-text-primary block">
                  {report.investigation.created_at
                    ? new Date(report.investigation.created_at).toLocaleDateString()
                    : "N/A"}
                </span>
              </div>

              <div className="p-3 bg-soc-base rounded border border-soc-border print-card">
                <span className="text-soc-text-muted block mb-1">Completed At</span>
                <span className="text-soc-text-primary block">
                  {report.investigation.completed_at
                    ? new Date(report.investigation.completed_at).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    : "In Progress"}
                </span>
              </div>
            </div>
          </header>

          {/* Section 1: Executive Risk Assessment */}
          <section className="print-card bg-soc-surface border border-soc-border rounded-lg p-6 sm:p-8">
            <div className="flex items-center justify-between gap-4 border-b border-soc-border pb-4 mb-6">
              <div className="flex items-center gap-2">
                <Scale className="h-5 w-5 text-accent-primary" />
                <h2 className="font-display text-lg font-bold tracking-tight text-soc-text-primary">
                  1. Executive Risk Assessment
                </h2>
              </div>
              {report.investigation.final_severity && (
                <SeverityTag
                  severity={report.investigation.final_severity as SeverityType}
                />
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              {/* Score Highlight Card */}
              <div className="p-5 rounded-lg bg-soc-base border border-soc-border print-card flex flex-col justify-center items-center text-center">
                <span className="text-xs font-mono text-soc-text-muted uppercase tracking-wider mb-1">
                  Final Deterministic Risk Score
                </span>
                <div className="font-mono text-4xl font-bold text-soc-text-primary mb-2">
                  {report.investigation.final_risk_score !== undefined &&
                  report.investigation.final_risk_score !== null
                    ? (report.investigation.final_risk_score * 100).toFixed(1) + "%"
                    : "Pending"}
                </div>
                <span className="text-xs font-mono text-soc-text-secondary">
                  Raw Metric: {report.investigation.final_risk_score?.toFixed(4) ?? "N/A"} / 1.0000
                </span>
              </div>

              {/* Severity & Confidence Summary */}
              <div className="md:col-span-2 p-5 rounded-lg bg-soc-base border border-soc-border print-card flex flex-col justify-between">
                <div>
                  <h3 className="text-xs font-mono text-soc-text-muted uppercase tracking-wider mb-2">
                    Consensus Severity Classification
                  </h3>
                  <p className="text-sm text-soc-text-primary mb-3">
                    Calculated via multi-agent corroboration across text, URL heuristics, QR decoding, and audio transcript features.
                  </p>
                </div>

                <div className="flex items-center gap-6 pt-3 border-t border-soc-border/60 text-xs font-mono">
                  <div>
                    <span className="text-soc-text-muted block">Confidence Rating:</span>
                    <span className="text-soc-text-primary font-bold">
                      {report.investigation.final_confidence
                        ? `${(report.investigation.final_confidence * 100).toFixed(0)}%`
                        : "N/A"}
                    </span>
                  </div>
                  <div>
                    <span className="text-soc-text-muted block">Consensus Status:</span>
                    <span className="text-accent-primary font-bold">
                      {report.risk?.conflicts && report.risk.conflicts.length > 0
                        ? `${report.risk.conflicts.length} Resolved Conflict(s)`
                        : "Unanimous / Corroborated"}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Formula Breakdown Table */}
            {report.risk?.breakdown && report.risk.breakdown.length > 0 && (
              <div className="mt-6">
                <h3 className="text-xs font-mono font-semibold text-soc-text-secondary uppercase tracking-wider mb-3">
                  Deterministic Formula Contributions
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono print-table border-collapse">
                    <thead>
                      <tr className="border-b border-soc-border text-soc-text-muted uppercase">
                        <th className="py-2.5 px-3">Formula Component</th>
                        <th className="py-2.5 px-3 text-right">Raw Value</th>
                        <th className="py-2.5 px-3 text-right">Weight</th>
                        <th className="py-2.5 px-3 text-right">Contribution</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-soc-border/60 text-soc-text-primary">
                      {report.risk.breakdown.map((item, idx) => (
                        <tr key={idx} className="hover:bg-soc-base/30 transition-colors">
                          <td className="py-2.5 px-3 font-medium capitalize">
                            {item.component.replace(/_/g, " ")}
                          </td>
                          <td className="py-2.5 px-3 text-right">{item.value.toFixed(4)}</td>
                          <td className="py-2.5 px-3 text-right">{item.weight.toFixed(2)}</td>
                          <td className="py-2.5 px-3 text-right font-bold text-accent-primary">
                            {item.contribution >= 0 ? `+${item.contribution.toFixed(4)}` : item.contribution.toFixed(4)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </section>

          {/* Section 2: Multimodal Evidence Inputs */}
          <section className="print-card bg-soc-surface border border-soc-border rounded-lg p-6 sm:p-8">
            <div className="flex items-center gap-2 border-b border-soc-border pb-4 mb-6">
              <FileText className="h-5 w-5 text-accent-primary" />
              <h2 className="font-display text-lg font-bold tracking-tight text-soc-text-primary">
                2. Multimodal Evidence Ingestion
              </h2>
            </div>

            {report.evidence_inputs.length === 0 ? (
              <p className="text-xs font-mono text-soc-text-muted">No raw inputs recorded for this investigation.</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {report.evidence_inputs.map((input) => (
                  <div
                    key={input.id}
                    className="p-4 bg-soc-base rounded border border-soc-border print-card text-xs font-mono space-y-2"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="flex items-center gap-1.5 font-bold uppercase text-accent-primary">
                        {getModalityIcon(input.modality)}
                        {input.modality}
                      </span>
                      <span className="text-soc-text-muted text-[11px]">
                        {input.created_at ? new Date(input.created_at).toLocaleTimeString() : ""}
                      </span>
                    </div>

                    {input.raw_content_ref && (
                      <div className="p-2 bg-soc-surface rounded border border-soc-border/60 break-all text-soc-text-secondary font-mono text-[11px]">
                        {input.raw_content_ref}
                      </div>
                    )}
                    {input.file_path && (
                      <div className="text-soc-text-muted text-[11px] truncate">
                        File: {input.file_path}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Section 3: Agent Swarm Findings */}
          <section className="print-card bg-soc-surface border border-soc-border rounded-lg p-6 sm:p-8">
            <div className="flex items-center justify-between border-b border-soc-border pb-4 mb-6">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-accent-primary" />
                <h2 className="font-display text-lg font-bold tracking-tight text-soc-text-primary">
                  3. Agent Swarm Findings
                </h2>
              </div>
              <Badge variant="outline" className="font-mono text-xs">
                {report.findings.length} Finding(s)
              </Badge>
            </div>

            {report.findings.length === 0 ? (
              <p className="text-xs font-mono text-soc-text-muted">
                No active findings recorded.
              </p>
            ) : (
              <div className="space-y-4">
                {report.findings.map((f) => (
                  <div
                    key={f.id}
                    className="p-4 bg-soc-base rounded border border-soc-border print-card space-y-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-xs uppercase text-accent-primary">
                          {f.agent_name}
                        </span>
                        <SeverityTag severity={(f.severity as SeverityType) || "info"} />
                      </div>
                      <span className="text-xs font-mono text-soc-text-muted">
                        Confidence: {(f.confidence * 100).toFixed(0)}%
                      </span>
                    </div>

                    <p className="text-sm font-medium text-soc-text-primary">
                      {f.finding}
                    </p>

                    {f.reasoning && (
                      <div className="text-xs text-soc-text-secondary bg-soc-surface p-3 rounded border border-soc-border/60">
                        <span className="font-mono font-semibold text-soc-text-muted block mb-1">
                          Analytical Reasoning:
                        </span>
                        {f.reasoning}
                      </div>
                    )}

                    {Array.isArray(f.indicators) && f.indicators.length > 0 && (
                      <div className="flex items-center gap-1.5 flex-wrap pt-1">
                        <span className="text-[11px] font-mono text-soc-text-muted mr-1">
                          Indicators:
                        </span>
                        {f.indicators.map((ind, i) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 rounded bg-soc-surface border border-soc-border text-[11px] font-mono text-soc-text-secondary"
                          >
                            {String(ind)}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Section 4: RAG Threat Intelligence Advisory Grounding */}
          <section className="print-card bg-soc-surface border border-soc-border rounded-lg p-6 sm:p-8">
            <div className="flex items-center justify-between border-b border-soc-border pb-4 mb-6">
              <div className="flex items-center gap-2">
                <BookOpen className="h-5 w-5 text-accent-primary" />
                <h2 className="font-display text-lg font-bold tracking-tight text-soc-text-primary">
                  4. External Threat Intelligence Grounding (RAG)
                </h2>
              </div>
              <Badge variant="outline" className="font-mono text-xs">
                {report.rag_citations.length} Advisory Match(es)
              </Badge>
            </div>

            {report.rag_citations.length === 0 ? (
              <div className="p-4 rounded bg-soc-base border border-soc-border print-card text-xs font-mono text-soc-text-muted space-y-1">
                <p className="font-semibold text-soc-text-secondary">
                  No External Intelligence Matches Exceeded Threshold
                </p>
                <p>
                  In accordance with ThreatWeave&apos;s strict honesty principle, no advisories were forced or fabricated.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {report.rag_citations.map((cit, idx) => (
                  <div
                    key={cit.id || idx}
                    className="p-4 bg-soc-base rounded border border-soc-border print-card space-y-2 text-xs"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 font-mono">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded bg-accent-primary/10 border border-accent-primary/20 text-accent-primary font-bold">
                          {cit.source_type}
                        </span>
                        <span className="font-semibold text-soc-text-primary">
                          {cit.source_title}
                        </span>
                      </div>
                      <span className="text-soc-text-muted">
                        Similarity Score: {(cit.similarity_score * 100).toFixed(1)}%
                      </span>
                    </div>

                    <p className="text-soc-text-secondary leading-relaxed bg-soc-surface p-3 rounded border border-soc-border/60 font-mono text-[11px]">
                      &ldquo;{cit.chunk_text}&rdquo;
                    </p>

                    {cit.url && (
                      <div className="pt-1">
                        <a
                          href={cit.url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-[11px] font-mono text-accent-primary hover:underline"
                        >
                          Reference Advisory <ExternalLink className="h-3 w-3" />
                        </a>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Section 5: Swarm Conflict Resolutions (if any) */}
          {report.conflict_logs && report.conflict_logs.length > 0 && (
            <section className="print-card bg-soc-surface border border-severity-medium/30 rounded-lg p-6 sm:p-8">
              <div className="flex items-center gap-2 border-b border-severity-medium/20 pb-4 mb-6">
                <AlertTriangle className="h-5 w-5 text-severity-medium" />
                <h2 className="font-display text-lg font-bold tracking-tight text-soc-text-primary">
                  5. Swarm Disagreements & Consensus Arbitration
                </h2>
              </div>

              <div className="space-y-3">
                {report.conflict_logs.map((c) => (
                  <div
                    key={c.id}
                    className="p-4 bg-soc-base rounded border border-soc-border print-card text-xs font-mono space-y-1.5"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-bold text-severity-medium">
                        Discrepancy: {c.agent_a} vs {c.agent_b} ({c.conflict_type})
                      </span>
                      <span className="text-soc-text-muted">
                        Rule: {c.resolution_rule}
                      </span>
                    </div>
                    <p className="text-soc-text-secondary">
                      Outcome: {c.resolution_outcome}
                    </p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Report Footer / Signature Area */}
          <footer className="print-card pt-6 border-t border-soc-border text-center text-xs font-mono text-soc-text-muted space-y-1">
            <p>Generated by ThreatWeave Multi-Agent Intelligence System — Phase 14</p>
            <p>Audit Verification Hash ID: {report.report_id}</p>
          </footer>
        </div>
      )}
    </div>
  );
}
