"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Play,
  Loader2,
  RefreshCw,
  AlertCircle,
  Clock,
  Calendar,
  CheckCircle2,
  Search,
  Sparkles,
  Printer,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { SeverityTag, SeverityType } from "@/components/ui/SeverityTag";
import { AgentActivityStrip } from "@/components/investigation/AgentActivityStrip";
import { RiskGauge } from "@/components/investigation/RiskGauge";
import { RiskBreakdownPanel } from "@/components/investigation/RiskBreakdownPanel";
import { EvidenceCard } from "@/components/investigation/EvidenceCard";
import { ConflictBanner } from "@/components/investigation/ConflictBanner";
import { RagCitationPanel } from "@/components/investigation/RagCitationPanel";
import { getInvestigation, analyzeInvestigation, ApiError } from "@/lib/api";
import { InvestigationDetail, AgentFindingDetail } from "@/lib/types";

export default function InvestigationWorkspacePage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [investigation, setInvestigation] = useState<InvestigationDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [pollTimeoutReached, setPollTimeoutReached] = useState<boolean>(false);
  const [pollCount, setPollCount] = useState<number>(0);

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const pollCountRef = useRef<number>(0);

  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  }, []);

  const fetchInvestigation = useCallback(async (showLoading = false) => {
    if (!id) return;
    if (showLoading) setIsLoading(true);
    setError(null);

    try {
      const data = await getInvestigation(id);
      setInvestigation(data);

      // If already completed or failed, ensure polling stops
      if (data.status === "completed" || data.status === "failed") {
        setIsAnalyzing(false);
        stopPolling();
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load investigation details.");
      }
      stopPolling();
    } finally {
      if (showLoading) setIsLoading(false);
    }
  }, [id, stopPolling]);

  const startPolling = useCallback(() => {
    stopPolling();
    pollCountRef.current = 0;
    setPollCount(0);
    setPollTimeoutReached(false);
    setIsAnalyzing(true);

    pollIntervalRef.current = setInterval(async () => {
      pollCountRef.current += 1;
      setPollCount(pollCountRef.current);

      try {
        const data = await getInvestigation(id);
        setInvestigation(data);

        if (data.status === "completed" || data.status === "failed") {
          setIsAnalyzing(false);
          stopPolling();
        } else if (pollCountRef.current >= 30) {
          // Hard cap at 30 attempts * 2s = 60s
          stopPolling();
          setIsAnalyzing(false);
          setPollTimeoutReached(true);
        }
      } catch {
        // Continue polling unless hard error
        if (pollCountRef.current >= 30) {
          stopPolling();
          setIsAnalyzing(false);
          setPollTimeoutReached(true);
        }
      }
    }, 2000);
  }, [id, stopPolling]);

  useEffect(() => {
    let isMounted = true;

    async function initialLoad() {
      try {
        const data = await getInvestigation(id);
        if (!isMounted) return;
        setInvestigation(data);
        if (data.status === "completed" || data.status === "failed") {
          setIsAnalyzing(false);
          stopPolling();
        } else if (data.status === "running") {
          startPolling();
        }
      } catch (err) {
        if (!isMounted) return;
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Failed to load investigation details.");
        }
        stopPolling();
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    initialLoad();

    return () => {
      isMounted = false;
      stopPolling();
    };
  }, [id, stopPolling, startPolling]);

  const handleRunAnalysis = async () => {
    if (!id || isAnalyzing) return;
    setError(null);
    setIsAnalyzing(true);
    setPollTimeoutReached(false);

    try {
      await analyzeInvestigation(id);
      startPolling();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to trigger swarm analysis.");
      }
      setIsAnalyzing(false);
      stopPolling();
    }
  };

  // Flatten all findings across runs
  const allFindings: { finding: AgentFindingDetail; agentName: string }[] = [];
  if (investigation?.agent_runs) {
    for (const run of investigation.agent_runs) {
      if (run.findings) {
        for (const f of run.findings) {
          allFindings.push({ finding: f, agentName: run.agent_name });
        }
      }
    }
  }

  // Check if findings are benign / all info
  const isAllBenign =
    investigation?.status === "completed" &&
    (allFindings.length === 0 ||
      allFindings.every(
        (item) => item.finding.severity === "info" || item.finding.severity === "low"
      )) &&
    (investigation.final_risk_score === null ||
      investigation.final_risk_score === undefined ||
      investigation.final_risk_score < 0.25);

  return (
    <div className="flex flex-col min-h-screen bg-soc-base text-soc-text-primary px-4 md:px-8 py-6 max-w-7xl mx-auto w-full">
      {/* Top Navigation */}
      <div className="flex items-center justify-between gap-4 mb-6">
        <Link
          href="/investigations"
          className="inline-flex items-center gap-1.5 text-xs font-mono text-soc-text-secondary hover:text-soc-text-primary transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Investigations Queue
        </Link>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => fetchInvestigation(false)}
            disabled={isAnalyzing}
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${isAnalyzing ? "animate-spin" : ""}`} />
            Refresh
          </Button>

          {investigation?.status === "completed" && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => router.push(`/investigations/${id}/report`)}
            >
              <Printer className="h-3.5 w-3.5 mr-1.5" />
              View Report
            </Button>
          )}

          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push("/investigations/new")}
          >
            New Task
          </Button>
        </div>
      </div>

      {/* Loading State */}
      {isLoading ? (
        <div className="space-y-6">
          <Card className="p-6">
            <Skeleton className="h-7 w-1/2 mb-3" />
            <Skeleton className="h-4 w-1/4" />
          </Card>
          <Card className="p-6">
            <Skeleton className="h-24 w-full" />
          </Card>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Skeleton className="h-64" />
            <Skeleton className="h-64 md:col-span-2" />
          </div>
        </div>
      ) : error && !investigation ? (
        /* Error State */
        <Card className="p-8 border-severity-critical/30 bg-soc-surface text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded bg-severity-critical/10 text-severity-critical mx-auto mb-4 border border-severity-critical/20">
            <AlertCircle className="h-6 w-6" />
          </div>
          <h2 className="font-display font-semibold text-lg text-soc-text-primary mb-2">
            Investigation Failed to Load
          </h2>
          <p className="text-sm text-soc-text-secondary max-w-md mx-auto mb-6">
            {error}
          </p>
          <Button variant="primary" size="md" onClick={() => fetchInvestigation(true)}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry Fetch
          </Button>
        </Card>
      ) : investigation ? (
        /* Content State */
        <div className="space-y-6">
          {/* Header Banner */}
          <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-soc-border pb-6">
            <div>
              <div className="flex items-center gap-3 mb-1.5 flex-wrap">
                <h1 className="font-display font-bold text-xl sm:text-2xl text-soc-text-primary">
                  {investigation.title || "Untitled Threat Investigation"}
                </h1>
                {investigation.final_severity && (
                  <SeverityTag
                    severity={
                      (investigation.final_severity as SeverityType) || "info"
                    }
                  />
                )}
                <Badge
                  variant={
                    investigation.status === "completed"
                      ? "accent"
                      : investigation.status === "failed"
                      ? "outline"
                      : "default"
                  }
                  className="font-mono text-xs uppercase"
                >
                  {investigation.status}
                </Badge>
                {(investigation.final_severity === "high" ||
                  investigation.final_severity === "critical") &&
                  investigation.status === "completed" && (
                    <Badge
                      variant="outline"
                      className="font-mono text-[11px] text-amber-400 border-amber-500/30 bg-amber-500/10 flex items-center gap-1.5"
                    >
                      <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
                      Automation Triggered
                    </Badge>
                  )}
              </div>

              <div className="flex items-center gap-4 text-xs font-mono text-soc-text-secondary flex-wrap">
                <span className="flex items-center gap-1.5">
                  <Calendar className="h-3.5 w-3.5 text-soc-text-muted" />
                  {new Date(investigation.created_at).toLocaleString()}
                </span>
                <span>ID: {investigation.id}</span>
                <span>
                  Artifacts: {investigation.evidence_inputs?.length || 0} inputs
                </span>
              </div>
            </div>

            {/* Run Analysis CTA button if status is pending */}
            {investigation.status === "pending" && (
              <div className="flex items-center gap-3">
                <Button
                  variant="primary"
                  size="lg"
                  onClick={handleRunAnalysis}
                  disabled={isAnalyzing}
                  className="w-full sm:w-auto shadow-lg shadow-accent-primary/20"
                >
                  {isAnalyzing ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Swarm Analyzing...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2 fill-current" />
                      Run Swarm Analysis
                    </>
                  )}
                </Button>
              </div>
            )}
          </header>

          {/* Analysis Error Alert */}
          {error && (
            <div
              role="alert"
              className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-md border border-severity-critical/40 bg-severity-critical/10 text-xs font-mono text-severity-critical"
            >
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 text-severity-critical" />
                <span>{error}</span>
              </div>
              <Button
                variant="secondary"
                size="sm"
                onClick={handleRunAnalysis}
                className="shrink-0 text-xs border-severity-critical/40 text-severity-critical hover:bg-severity-critical/20"
              >
                <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
                Retry Analysis
              </Button>
            </div>
          )}

          {/* Polling Notice / Timeout Notice */}
          {isAnalyzing && (
            <div
              role="status"
              className="flex items-center justify-between p-4 rounded-md border border-accent-primary/40 bg-accent-primary/10 text-xs font-mono text-accent-primary"
            >
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin shrink-0" />
                <span>
                  Executing specialist agent swarm across modalities (polling status every 2s)...
                </span>
              </div>
              <span className="text-soc-text-secondary">
                Attempt {pollCount}/30
              </span>
            </div>
          )}

          {pollTimeoutReached && (
            <div
              role="alert"
              className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-md border border-severity-medium/40 bg-severity-medium/10 text-xs font-mono text-severity-medium"
            >
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 shrink-0" />
                <span>
                  Analysis is taking longer than expected. Specialist agents may still be executing OCR or audio models.
                </span>
              </div>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => fetchInvestigation(false)}
                className="w-full sm:w-auto"
              >
                <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
                Manual Refresh
              </Button>
            </div>
          )}

          {/* Pending Evidence Inputs Summary */}
          {investigation.status === "pending" && (
            <Card className="p-6 border-soc-border bg-soc-surface">
              <h2 className="font-display font-semibold text-xs uppercase tracking-wider text-soc-text-secondary mb-3">
                Ingested Evidence Artifacts Ready for Analysis
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                {investigation.evidence_inputs?.map((input) => (
                  <div
                    key={input.id}
                    className="p-3.5 rounded bg-soc-base border border-soc-border font-mono text-xs"
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <Badge variant="accent" className="uppercase text-[10px]">
                        {input.modality}
                      </Badge>
                      <span className="text-soc-text-muted text-[10px]">
                        {new Date(input.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                    {input.raw_content_ref && (
                      <p className="text-soc-text-primary truncate text-xs">
                        {input.raw_content_ref}
                      </p>
                    )}
                    {input.file_path && (
                      <p className="text-soc-text-muted text-[10px] truncate mt-1">
                        {input.file_path}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* 1. Agent Activity Strip (Only after run or completed) */}
          <section aria-label="Agent Activity Strip">
            <AgentActivityStrip
              agentRuns={investigation.agent_runs}
              isAnalyzing={isAnalyzing}
            />
          </section>

          {/* Once completed: Main Intelligence Grid */}
          {investigation.status === "completed" && (
            <>
              {/* 2. Deterministic Risk Gauge + Breakdown Grid */}
              <section
                aria-label="Risk Scoring Assessment"
                className="grid grid-cols-1 lg:grid-cols-12 gap-6"
              >
                <div className="lg:col-span-4">
                  <RiskGauge
                    score={investigation.final_risk_score}
                    severity={investigation.final_severity}
                    confidence={investigation.final_confidence}
                    lowConfidence={investigation.risk?.low_confidence}
                  />
                </div>
                <div className="lg:col-span-8">
                  <RiskBreakdownPanel
                    breakdown={investigation.risk?.breakdown}
                    finalRiskScore={investigation.final_risk_score}
                  />
                </div>
              </section>

              {/* 3. Conflict Banner (if any conflicts logged) */}
              {investigation.risk?.conflicts && investigation.risk.conflicts.length > 0 && (
                <section aria-label="Agent Conflict Arbitration">
                  <ConflictBanner conflicts={investigation.risk.conflicts} />
                </section>
              )}

              {/* Benign Positive Notification if clean */}
              {isAllBenign && (
                <Card className="p-6 border-severity-low/30 bg-severity-low/5 flex items-start gap-4">
                  <div className="p-2 rounded bg-severity-low/10 border border-severity-low/20 text-severity-low shrink-0 mt-0.5">
                    <CheckCircle2 className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-display font-semibold text-sm text-severity-low mb-1">
                      Clean / Benign Sample — No Threats Detected
                    </h3>
                    <p className="text-xs text-soc-text-secondary leading-relaxed max-w-3xl">
                      The multimodal agent swarm completed heuristic scans, OCR extraction, and neural reasoning
                      without surfacing actionable indicators of compromise. No phishing lures, malicious URLs,
                      or social engineering patterns were validated.
                    </p>
                  </div>
                </Card>
              )}

              {/* 4. Specialist Findings Section */}
              <section aria-label="Agent Findings">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Search className="h-4 w-4 text-accent-primary" />
                    <h2 className="font-display font-semibold text-sm uppercase tracking-wider text-soc-text-primary">
                      Specialist Swarm Findings ({allFindings.length})
                    </h2>
                  </div>
                  <span className="text-xs font-mono text-soc-text-muted">
                    EVIDENCE AUDIT TRAILS
                  </span>
                </div>

                {allFindings.length === 0 ? (
                  <Card className="p-8 text-center text-xs text-soc-text-muted font-mono bg-soc-surface">
                    No specialist findings generated.
                  </Card>
                ) : (
                  <div className="space-y-4">
                    {allFindings.map((item, idx) => (
                      <EvidenceCard
                        key={item.finding.id || idx}
                        finding={item.finding}
                        agentName={item.agentName}
                      />
                    ))}
                  </div>
                )}
              </section>

              {/* 5. RAG Threat Intelligence Panel */}
              <section aria-label="External Advisory Citations">
                <RagCitationPanel citations={investigation.rag_citations} />
              </section>
            </>
          )}
        </div>
      ) : null}

      {/* Footer */}
      <footer className="mt-12 border-t border-soc-border pt-4 text-center">
        <p className="text-xs font-mono text-soc-text-muted flex items-center justify-center gap-1.5">
          <Sparkles className="h-3 w-3 text-accent-primary" />
          ThreatWeave Phase 13 — Multimodal SOC Investigation Workspace
        </p>
      </footer>
    </div>
  );
}
