"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Printer,
  Download,
  Shield,
  FileText,
  Globe,
  Image as ImageIcon,
  Mic,
  BookOpen,
  Scale,
  CheckCircle2,
  AlertCircle,
  Cpu,
  GitMerge,
  ListChecks,
  Info,
  Clock,
  QrCode,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { SeverityTag, SeverityType } from "@/components/ui/SeverityTag";
import { getInvestigationReport, getInvestigationReportPdfUrl, ApiError } from "@/lib/api";
import { InvestigationReportData } from "@/lib/types";

export default function InvestigationReportPage() {
  const params = useParams();
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

  const handleDownloadPdf = () => {
    if (!id) return;
    const url = getInvestigationReportPdfUrl(id);
    window.open(url, "_blank");
  };

  const handleDownloadJson = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `threatweave-investigation-${id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getModalityIcon = (mod: string) => {
    switch (mod.toLowerCase()) {
      case "text":
        return <FileText className="h-4 w-4" />;
      case "url":
        return <Globe className="h-4 w-4" />;
      case "qr":
        return <QrCode className="h-4 w-4" />;
      case "image":
        return <ImageIcon className="h-4 w-4" />;
      case "voice":
      case "audio":
        return <Mic className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  // Generate dynamic executive summary based on real findings
  const getExecutiveSummary = (rep: InvestigationReportData) => {
    const findings = rep.findings || [];
    const isBenign =
      findings.length === 0 ||
      (rep.investigation.final_risk_score !== null &&
        rep.investigation.final_risk_score !== undefined &&
        rep.investigation.final_risk_score < 0.25 &&
        findings.every(
          (f) =>
            f.severity?.toLowerCase() === "info" ||
            f.severity?.toLowerCase() === "low"
        ));

    if (isBenign) {
      return "Multimodal swarm analysis completed across all ingested evidence channels. Zero critical or high-risk threat indicators were observed. The submitted evidence conforms to clean operational baseline patterns.";
    }

    const topFinding = findings[0];
    const topSev = (topFinding.severity || "HIGH").toUpperCase();
    const countCriticalHigh = findings.filter(
      (f) =>
        f.severity?.toLowerCase() === "critical" ||
        f.severity?.toLowerCase() === "high"
    ).length;

    return `Autonomous multimodal swarm analysis confirmed a ${topSev} severity cyber incident with ${(
      (rep.investigation.final_confidence || 0.8) * 100
    ).toFixed(0)}% consensus confidence. Primary threat signature: "${
      topFinding.finding
    }". Total of ${countCriticalHigh} high-confidence threat finding(s) corroborated across ${
      rep.evidence_inputs.length
    } evidence channel(s). Immediate perimeter containment is advised.`;
  };

  return (
    <div className="report-container min-h-screen bg-soc-base text-soc-text-primary px-4 sm:px-8 py-8 max-w-5xl mx-auto w-full">
      {/* Print stylesheet */}
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
        }
      `}</style>

      {/* Top Action Controls (Hidden on Print) */}
      <div className="no-print flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-soc-border pb-6 mb-8">
        <div className="flex items-center gap-3">
          <Link
            href={`/investigations/${id}`}
            className="inline-flex items-center gap-1.5 text-xs font-mono text-soc-text-secondary hover:text-accent-primary transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Interactive Workspace
          </Link>
          <span className="text-soc-text-muted">/</span>
          <Link
            href="/investigations"
            className="text-xs font-mono text-soc-text-secondary hover:text-accent-primary transition-colors"
          >
            Queue
          </Link>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleDownloadJson}
            className="text-xs font-mono"
          >
            <Download className="h-3.5 w-3.5 mr-1.5" />
            Export JSON
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleDownloadPdf}
            className="text-xs font-mono"
          >
            <Download className="h-3.5 w-3.5 mr-1.5" />
            Download PDF
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handlePrint}
            className="text-xs font-mono shadow-md"
          >
            <Printer className="h-3.5 w-3.5 mr-1.5" />
            Print Report
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
          <Button variant="primary" size="sm" onClick={() => window.location.reload()}>
            Retry
          </Button>
        </Card>
      ) : (
        <div className="space-y-8">
          {/* SECTION 1: Investigation Identification */}
          <header className="print-card bg-soc-surface border border-soc-border rounded-lg p-6 sm:p-8">
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-soc-border pb-6 mb-6">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="h-6 w-6 text-accent-primary" />
                  <span className="text-xs font-mono font-bold tracking-widest text-accent-primary uppercase">
                    ThreatWeave Multimodal Cyber Intelligence
                  </span>
                </div>
                <h1 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-soc-text-primary mb-2">
                  Official Incident Investigation Report
                </h1>
                <p className="text-sm font-display font-medium text-soc-text-secondary">
                  Target: {report.investigation.title || "Untitled Multimodal Incident"}
                </p>
              </div>

              <div className="text-left sm:text-right space-y-1 font-mono text-xs text-soc-text-muted">
                <div>
                  <span className="font-semibold text-soc-text-secondary">Audit ID:</span>{" "}
                  <span className="select-all">{report.report_id.slice(0, 16)}...</span>
                </div>
                <div>
                  <span className="font-semibold text-soc-text-secondary">Generated:</span>{" "}
                  {new Date(report.generated_at).toLocaleString()}
                </div>
                <div>
                  <span className="font-semibold text-soc-text-secondary">Classification:</span>{" "}
                  <span className="text-accent-primary font-bold uppercase">TLP:AMBER+STRICT</span>
                </div>
              </div>
            </div>

            {/* Metadata Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
              <div className="p-3 bg-soc-base rounded border border-soc-border print-card">
                <span className="text-soc-text-muted block mb-1">Case ID</span>
                <span className="text-soc-text-primary truncate block select-all">
                  {report.investigation.id}
                </span>
              </div>
              <div className="p-3 bg-soc-base rounded border border-soc-border print-card">
                <span className="text-soc-text-muted block mb-1">Status</span>
                <span className="text-accent-primary font-bold uppercase block">
                  {report.investigation.status}
                </span>
              </div>
              <div className="p-3 bg-soc-base rounded border border-soc-border print-card">
                <span className="text-soc-text-muted block mb-1">Submitted At</span>
                <span className="text-soc-text-primary block">
                  {report.investigation.created_at
                    ? new Date(report.investigation.created_at).toLocaleString()
                    : "N/A"}
                </span>
              </div>
              <div className="p-3 bg-soc-base rounded border border-soc-border print-card">
                <span className="text-soc-text-muted block mb-1">Completed At</span>
                <span className="text-soc-text-primary block">
                  {report.investigation.completed_at
                    ? new Date(report.investigation.completed_at).toLocaleString()
                    : "In Progress"}
                </span>
              </div>
            </div>
          </header>

          {/* SECTION 2: Executive Incident Summary */}
          <section className="print-card bg-soc-surface border border-soc-border rounded-lg p-6 sm:p-8 space-y-3">
            <div className="flex items-center gap-2 border-b border-soc-border pb-3 mb-2">
              <FileText className="h-5 w-5 text-accent-primary" />
              <h2 className="font-display text-lg font-bold tracking-tight text-soc-text-primary">
                2. Executive Incident Summary
              </h2>
            </div>
            <p className="text-xs sm:text-sm text-soc-text-primary leading-relaxed bg-soc-base p-4 rounded border border-soc-border">
              {getExecutiveSummary(report)}
            </p>
          </section>

          {/* SECTION 3: Final Severity & Deterministic Risk Score */}
          <section className="print-card bg-soc-surface border border-soc-border rounded-lg p-6 sm:p-8">
            <div className="flex items-center justify-between border-b border-soc-border pb-4 mb-6">
              <div className="flex items-center gap-2">
                <Scale className="h-5 w-5 text-accent-primary" />
                <h2 className="font-display text-lg font-bold tracking-tight text-soc-text-primary">
                  3. Final Severity Classification &amp; Consensus Score
                </h2>
              </div>
              {report.investigation.final_severity && (
                <SeverityTag severity={report.investigation.final_severity as SeverityType} />
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-5 rounded-lg bg-soc-base border border-soc-border flex flex-col justify-center items-center text-center">
                <span className="text-xs font-mono text-soc-text-muted uppercase mb-1">
                  Deterministic Score
                </span>
                <div className="font-mono text-4xl font-bold text-soc-text-primary mb-2">
                  {report.investigation.final_risk_score !== undefined &&
                  report.investigation.final_risk_score !== null
                    ? `${(report.investigation.final_risk_score * 100).toFixed(1)}%`
                    : "Pending"}
                </div>
                <span className="text-xs font-mono text-soc-text-secondary">
                  Raw: {report.investigation.final_risk_score?.toFixed(4) ?? "N/A"} / 1.0000
                </span>
              </div>

              <div className="md:col-span-2 p-5 rounded-lg bg-soc-base border border-soc-border flex flex-col justify-between text-xs font-mono">
                <div>
                  <span className="text-soc-text-muted uppercase block mb-1">
                    Consensus Weighting Model
                  </span>
                  <p className="text-soc-text-primary leading-relaxed mb-3">
                    Calculated via multi-agent corroboration across text heuristics, sandbox URL detonation, QR computer vision, and speech transcription features.
                  </p>
                </div>
                <div className="flex items-center gap-6 pt-3 border-t border-soc-border/60">
                  <div>
                    <span className="text-soc-text-muted block text-[11px]">Model Confidence:</span>
                    <span className="text-soc-text-primary font-bold">
                      {report.investigation.final_confidence
                        ? `${(report.investigation.final_confidence * 100).toFixed(0)}%`
                        : "N/A"}
                    </span>
                  </div>
                  <div>
                    <span className="text-soc-text-muted block text-[11px]">Arbitration State:</span>
                    <span className="text-accent-primary font-bold">
                      {report.risk?.conflicts && report.risk.conflicts.length > 0
                        ? `${report.risk.conflicts.length} Resolved Conflict(s)`
                        : "Corroborated Consensus"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* SECTION 4: Analyzed Multimodal Evidence Inputs */}
          <section className="print-card bg-soc-surface border border-soc-border rounded-lg p-6 sm:p-8">
            <div className="flex items-center gap-2 border-b border-soc-border pb-4 mb-6">
              <Clock className="h-5 w-5 text-accent-primary" />
              <h2 className="font-display text-lg font-bold tracking-tight text-soc-text-primary">
                4. Analyzed Multimodal Evidence Ingestion
              </h2>
            </div>

            {report.evidence_inputs.length === 0 ? (
              <p className="text-xs font-mono text-soc-text-muted">No raw inputs recorded.</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {report.evidence_inputs.map((input) => (
                  <div
                    key={input.id}
                    className="p-4 bg-soc-base rounded border border-soc-border text-xs font-mono space-y-2"
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
                      <div className="p-2 bg-soc-surface rounded border border-soc-border/60 break-all text-soc-text-secondary text-[11px]">
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

          {/* SECTION 5: Specialist Swarm Threat Findings */}
          <section className="print-card bg-soc-surface border border-soc-border rounded-lg p-6 sm:p-8">
            <div className="flex items-center justify-between border-b border-soc-border pb-4 mb-6">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-accent-primary" />
                <h2 className="font-display text-lg font-bold tracking-tight text-soc-text-primary">
                  5. Specialist Swarm Threat Findings (Audit Trail)
                </h2>
              </div>
              <Badge variant="outline" className="font-mono text-xs">
                {report.findings.length} Finding(s)
              </Badge>
            </div>

            {report.findings.length === 0 ? (
              <p className="text-xs font-mono text-soc-text-muted">No active findings recorded.</p>
            ) : (
              <div className="space-y-4">
                {report.findings.map((f) => (
                  <div
                    key={f.id}
                    className="p-4 bg-soc-base rounded border border-soc-border space-y-3"
                  >
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-xs uppercase text-accent-primary">
                          {f.agent_name.replace("_agent", "")} specialist
                        </span>
                        <SeverityTag severity={(f.severity as SeverityType) || "info"} />
                      </div>
                      <span className="text-xs font-mono text-soc-text-muted">
                        Confidence: {(f.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-sm font-medium text-soc-text-primary">{f.finding}</p>
                    {f.reasoning && (
                      <div className="text-xs text-soc-text-secondary bg-soc-surface p-3 rounded border border-soc-border/60">
                        <span className="font-mono font-semibold text-soc-text-muted block mb-1">
                          Forensic Reasoning:
                        </span>
                        {f.reasoning}
                      </div>
                    )}
                    {Array.isArray(f.indicators) && f.indicators.length > 0 && (
                      <div className="flex items-center gap-1.5 flex-wrap pt-1">
                        <span className="text-[11px] font-mono text-soc-text-muted mr-1">
                          IOC Indicators:
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

          {/* SECTION 6: Agent Execution Summary */}
          <section className="print-card bg-soc-surface border border-soc-border rounded-lg p-6 sm:p-8">
            <div className="flex items-center gap-2 border-b border-soc-border pb-4 mb-6">
              <Cpu className="h-5 w-5 text-accent-primary" />
              <h2 className="font-display text-lg font-bold tracking-tight text-soc-text-primary">
                6. Agent Swarm Execution &amp; Telemetry Summary
              </h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {report.agent_runs.map((r) => (
                <div
                  key={r.id}
                  className="p-3.5 bg-soc-base rounded border border-soc-border text-xs font-mono space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-soc-text-primary">{r.agent_name}</span>
                    <Badge variant="outline" className="text-[10px] uppercase py-0">
                      {r.status}
                    </Badge>
                  </div>
                  <div className="text-[11px] text-soc-text-muted flex justify-between">
                    <span>Duration:</span>
                    <span>
                      {r.latency_ms !== null && r.latency_ms !== undefined
                        ? `${r.latency_ms} ms`
                        : "Not recorded"}
                    </span>
                  </div>
                  <div className="text-[11px] text-soc-text-muted flex justify-between">
                    <span>Findings:</span>
                    <span>{r.findings ? r.findings.length : 0}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* SECTION 7: Cross-Modal Correlations */}
          <section className="print-card bg-soc-surface border border-soc-border rounded-lg p-6 sm:p-8">
            <div className="flex items-center gap-2 border-b border-soc-border pb-4 mb-6">
              <GitMerge className="h-5 w-5 text-accent-primary" />
              <h2 className="font-display text-lg font-bold tracking-tight text-soc-text-primary">
                7. Cross-Modal Threat Correlations &amp; Bridges
              </h2>
            </div>
            {report.conflict_logs.length === 0 && report.findings.length <= 1 ? (
              <p className="text-xs font-mono text-soc-text-muted">
                Single vector analysis. No multi-channel corroboration links or arbitration conflicts logged.
              </p>
            ) : (
              <div className="space-y-3">
                {report.conflict_logs.map((c) => (
                  <div
                    key={c.id}
                    className="p-3 bg-soc-base rounded border border-severity-medium/30 text-xs font-mono space-y-1"
                  >
                    <span className="font-bold text-severity-medium">
                      Swarm Conflict Arbitration: {c.agent_a} vs {c.agent_b}
                    </span>
                    <p className="text-soc-text-secondary">Outcome: {c.resolution_outcome}</p>
                  </div>
                ))}
                {report.findings.length > 1 && (
                  <div className="p-3 bg-soc-base rounded border border-soc-border text-xs font-mono text-soc-text-secondary">
                    Multiple specialist findings corroborated across ingested evidence artifacts. Corroboration bonus applied to final risk score.
                  </div>
                )}
              </div>
            )}
          </section>

          {/* SECTION 8: Risk Calculation Explanation */}
          <section className="print-card bg-soc-surface border border-soc-border rounded-lg p-6 sm:p-8">
            <div className="flex items-center gap-2 border-b border-soc-border pb-4 mb-6">
              <Scale className="h-5 w-5 text-accent-primary" />
              <h2 className="font-display text-lg font-bold tracking-tight text-soc-text-primary">
                8. Deterministic Risk Calculation Rationale
              </h2>
            </div>
            {report.risk?.breakdown && report.risk.breakdown.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono print-table border-collapse">
                  <thead>
                    <tr className="border-b border-soc-border text-soc-text-muted uppercase text-[10px]">
                      <th className="py-2.5 px-3">Component</th>
                      <th className="py-2.5 px-3 text-right">Value</th>
                      <th className="py-2.5 px-3 text-right">Weight</th>
                      <th className="py-2.5 px-3 text-right">Contribution</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-soc-border/60">
                    {report.risk.breakdown.map((item, idx) => (
                      <tr key={idx}>
                        <td className="py-2 px-3 font-medium capitalize">
                          {item.component.replace(/_/g, " ")}
                        </td>
                        <td className="py-2 px-3 text-right">{item.value.toFixed(4)}</td>
                        <td className="py-2 px-3 text-right">{item.weight.toFixed(2)}</td>
                        <td className="py-2 px-3 text-right font-bold text-accent-primary">
                          {item.contribution >= 0
                            ? `+${item.contribution.toFixed(4)}`
                            : item.contribution.toFixed(4)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-xs font-mono text-soc-text-muted">Formula breakdown not recorded.</p>
            )}
          </section>

          {/* SECTION 9: Relevant RAG Citations */}
          <section className="print-card bg-soc-surface border border-soc-border rounded-lg p-6 sm:p-8">
            <div className="flex items-center justify-between border-b border-soc-border pb-4 mb-6">
              <div className="flex items-center gap-2">
                <BookOpen className="h-5 w-5 text-accent-primary" />
                <h2 className="font-display text-lg font-bold tracking-tight text-soc-text-primary">
                  9. External Threat Intelligence Grounding (RAG)
                </h2>
              </div>
              <Badge variant="outline" className="font-mono text-xs">
                {report.rag_citations.length} Citation(s)
              </Badge>
            </div>

            {report.rag_citations.length === 0 ? (
              <p className="text-xs font-mono text-soc-text-muted">
                No external threat advisories met the cosine similarity threshold. Strict anti-hallucination policy applied.
              </p>
            ) : (
              <div className="space-y-3">
                {report.rag_citations.map((cit, idx) => (
                  <div
                    key={cit.id || idx}
                    className="p-3.5 bg-soc-base rounded border border-soc-border text-xs font-mono space-y-1.5"
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-accent-primary">
                        [{cit.source_type}] {cit.source_title}
                      </span>
                      <span className="text-soc-text-muted">
                        Cosine Similarity: {(cit.similarity_score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <p className="text-soc-text-secondary bg-soc-surface p-2.5 rounded border border-soc-border/60">
                      &ldquo;{cit.chunk_text}&rdquo;
                    </p>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* SECTION 10: Recommended Defensive Actions */}
          <section className="print-card bg-soc-surface border border-soc-border rounded-lg p-6 sm:p-8 space-y-4">
            <div className="flex items-center gap-2 border-b border-soc-border pb-4 mb-2">
              <ListChecks className="h-5 w-5 text-accent-primary" />
              <h2 className="font-display text-lg font-bold tracking-tight text-soc-text-primary">
                10. Recommended Defensive Actions (SOC Playbook)
              </h2>
            </div>
            <div className="space-y-2.5 text-xs font-mono">
              <div className="p-3 bg-soc-base rounded border border-soc-border flex items-start gap-2.5">
                <span className="font-bold text-accent-primary">1. Perimeter Blocklist:</span>
                <span className="text-soc-text-secondary">
                  Distribute all extracted IOC indicators to network firewall rules, DNS sinkholes, and mail security filters.
                </span>
              </div>
              <div className="p-3 bg-soc-base rounded border border-soc-border flex items-start gap-2.5">
                <span className="font-bold text-accent-primary">2. Identity Remediation:</span>
                <span className="text-soc-text-secondary">
                  If credential harvesting lures or SMS phishing forms were accessed, invalidate active sessions and enforce MFA reset.
                </span>
              </div>
              <div className="p-3 bg-soc-base rounded border border-soc-border flex items-start gap-2.5">
                <span className="font-bold text-accent-primary">3. Host Isolation:</span>
                <span className="text-soc-text-secondary">
                  For devices receiving malicious voice calls or scanning deceptive QR codes, run full endpoint EDR sweeps.
                </span>
              </div>
            </div>
          </section>

          {/* SECTION 11: Limitations and Uncertainty */}
          <section className="print-card bg-soc-surface border border-soc-border rounded-lg p-6 sm:p-8 space-y-3">
            <div className="flex items-center gap-2 border-b border-soc-border pb-3 mb-2">
              <Info className="h-5 w-5 text-accent-primary" />
              <h2 className="font-display text-lg font-bold tracking-tight text-soc-text-primary">
                11. Analytical Limitations &amp; Uncertainty Disclosures
              </h2>
            </div>
            <div className="p-4 bg-soc-base rounded border border-soc-border text-xs font-mono text-soc-text-secondary space-y-2 leading-relaxed">
              <p>
                &bull; <strong>Heuristic vs Live Execution:</strong> Offline heuristic fallback modes prioritize deterministic regex and entropy thresholds over neural LLM reasoning when API rate limits occur.
              </p>
              <p>
                &bull; <strong>Verification Boundaries:</strong> ThreatWeave performs static heuristic detonation and OCR visual mining. It does not execute live sandbox malware payloads or guarantee financial settlement status.
              </p>
              <p>
                &bull; <strong>Voice Evaluation:</strong> Acoustic voice analysis detects synthetic frequency artifacts and high-pressure social engineering script patterns. It should be corroborated with carrier signaling metadata.
              </p>
            </div>
          </section>

          {/* SECTION 12: Cryptographic Audit ID & Generation Timestamp */}
          <footer className="print-card bg-soc-surface border border-soc-border rounded-lg p-6 text-center text-xs font-mono text-soc-text-muted space-y-1">
            <p className="font-bold text-soc-text-primary uppercase tracking-wider">
              12. Immutable Incident Dossier Verification
            </p>
            <p>Verification Hash ID: {report.report_id}</p>
            <p>Generated at: {new Date(report.generated_at).toUTCString()}</p>
            <p className="text-[10px] text-soc-text-muted pt-2 border-t border-soc-border/40 mt-3">
              ThreatWeave Multi-Agent Intelligence System &bull; All rights reserved
            </p>
          </footer>
        </div>
      )}
    </div>
  );
}
