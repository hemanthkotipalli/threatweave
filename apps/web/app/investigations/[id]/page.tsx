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
  Printer,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { InvestigationOverviewBanner } from "@/components/investigation/InvestigationOverviewBanner";
import { AnalystWorkflowBar } from "@/components/investigation/AnalystWorkflowBar";
import { AgentExecutionInspector } from "@/components/investigation/AgentExecutionInspector";
import { AlertExplanationPanel } from "@/components/investigation/AlertExplanationPanel";
import { EvidenceExplorer } from "@/components/investigation/EvidenceExplorer";
import { CrossModalRelationshipExplorer } from "@/components/investigation/CrossModalRelationshipExplorer";
import { InvestigationTimeline } from "@/components/investigation/InvestigationTimeline";
import { RiskGauge } from "@/components/investigation/RiskGauge";
import { RiskBreakdownPanel } from "@/components/investigation/RiskBreakdownPanel";
import { ConflictBanner } from "@/components/investigation/ConflictBanner";
import { AgentActivityStrip } from "@/components/investigation/AgentActivityStrip";
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

  // Analyst workflow bookmarks
  const [bookmarkedIds, setBookmarkedIds] = useState<string[]>([]);
  const [isFilterBookmarksActive, setIsFilterBookmarksActive] = useState<boolean>(false);

  // Active workspace tab
  const [activeWorkspaceTab, setActiveWorkspaceTab] = useState<
    "evidence" | "explain" | "agents" | "correlation" | "timeline"
  >("evidence");

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const pollCountRef = useRef<number>(0);

  // Load bookmarks from localStorage
  useEffect(() => {
    let isMounted = true;
    const loadBookmarks = () => {
      if (!id) return;
      try {
        const saved = localStorage.getItem(`threatweave:bookmarks:${id}`);
        if (saved && isMounted) {
          const parsed = JSON.parse(saved);
          if (Array.isArray(parsed)) {
            setBookmarkedIds(parsed);
          }
        }
      } catch {
        // Ignored
      }
    };
    void Promise.resolve().then(loadBookmarks);
    return () => {
      isMounted = false;
    };
  }, [id]);

  const toggleBookmark = (findingId: string) => {
    setBookmarkedIds((prev) => {
      const updated = prev.includes(findingId)
        ? prev.filter((item) => item !== findingId)
        : [...prev, findingId];
      try {
        localStorage.setItem(`threatweave:bookmarks:${id}`, JSON.stringify(updated));
      } catch {
        // Ignored
      }
      return updated;
    });
  };

  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  }, []);

  const fetchInvestigation = useCallback(
    async (showLoading = false) => {
      if (!id) return;
      if (showLoading) setIsLoading(true);
      setError(null);

      try {
        const data = await getInvestigation(id);
        setInvestigation(data);

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
    },
    [id, stopPolling]
  );

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
          stopPolling();
          setIsAnalyzing(false);
          setPollTimeoutReached(true);
        }
      } catch (err) {
        if (
          err instanceof ApiError &&
          (err.status === 404 || err.status === 403 || err.status >= 500)
        ) {
          stopPolling();
          setIsAnalyzing(false);
          setError(
            err.message ||
              `Investigation polling stopped due to server error (${err.status}).`
          );
          return;
        }

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

  // Flatten all findings across runs and sort severity-first
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

  const SEVERITY_RANK: Record<string, number> = {
    critical: 0,
    high: 1,
    medium: 2,
    low: 3,
    info: 4,
  };

  allFindings.sort((a, b) => {
    const sevA = SEVERITY_RANK[a.finding.severity?.toLowerCase() || "info"] ?? 5;
    const sevB = SEVERITY_RANK[b.finding.severity?.toLowerCase() || "info"] ?? 5;
    if (sevA !== sevB) return sevA - sevB;
    return (b.finding.confidence || 0) - (a.finding.confidence || 0);
  });

  const displayedFindings = isFilterBookmarksActive
    ? allFindings.filter((f) => bookmarkedIds.includes(String(f.finding.id)))
    : allFindings;

  // Deriving stage-appropriate copy
  const getAnalysisStageMessage = () => {
    if (!investigation) return "Initializing specialist swarm...";
    const runs = investigation.agent_runs || [];
    const completedRuns = runs.filter(
      (r) => r.status === "done" || r.status === "completed"
    );
    const activeRuns = runs.filter((r) => r.status === "running");

    if (runs.length === 0) {
      return "Routing ingested evidence modalities & initializing specialist swarm...";
    }
    if (activeRuns.length > 0 || completedRuns.length < runs.length) {
      const activeNames = activeRuns
        .map((r) => r.agent_name.replace("_agent", ""))
        .join(", ");
      return activeNames
        ? `Running specialist neural analysis (${activeNames})...`
        : `Executing specialist swarm (${completedRuns.length}/${runs.length} modalities analyzed)...`;
    }
    if (!investigation.risk) {
      return "Correlating cross-modal indicators, resolving conflicts & calculating risk...";
    }
    if (!investigation.rag_citations || investigation.rag_citations.length === 0) {
      return "Retrieving grounded threat advisories & synthesizing incident dossier...";
    }
    return "Finalizing investigation record & telemetry...";
  };

  return (
    <div className="flex flex-col min-h-screen bg-soc-base text-soc-text-primary px-4 md:px-8 py-6 max-w-7xl mx-auto w-full">
      {/* 1. Top Navigation Bar */}
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
            <RefreshCw
              className={`h-3.5 w-3.5 mr-1.5 ${isAnalyzing ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>

          {investigation?.status === "completed" && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => router.push(`/investigations/${id}/report`)}
            >
              <Printer className="h-3.5 w-3.5 mr-1.5" />
              Incident Report
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

      {/* Loading Skeleton State */}
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
          <Button
            variant="primary"
            size="md"
            onClick={() => fetchInvestigation(true)}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry Fetch
          </Button>
        </Card>
      ) : investigation ? (
        <div className="space-y-6">
          {/* 3.1 Investigation Overview Banner */}
          <InvestigationOverviewBanner
            investigation={investigation}
            allFindings={allFindings}
          />

          {/* Pending Swarm CTA Banner */}
          {investigation.status === "pending" && (
            <Card className="p-6 border-accent-primary/40 bg-accent-primary/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h3 className="font-display font-bold text-base text-soc-text-primary mb-1">
                  Multimodal Evidence Ingested &bull; Ready for Swarm Analysis
                </h3>
                <p className="text-xs text-soc-text-secondary">
                  Trigger autonomous LangGraph specialist routing across text, URL sandbox, OCR, and speech audio models.
                </p>
              </div>
              <Button
                variant="primary"
                size="lg"
                onClick={handleRunAnalysis}
                disabled={isAnalyzing}
                className="shrink-0 shadow-lg shadow-accent-primary/20"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Analyzing Swarm...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2 fill-current" />
                    Run Swarm Analysis
                  </>
                )}
              </Button>
            </Card>
          )}

          {/* Polling Notice */}
          {isAnalyzing && (
            <div
              role="status"
              className="flex items-center justify-between p-4 rounded-md border border-accent-primary/40 bg-accent-primary/10 text-xs font-mono text-accent-primary"
            >
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin shrink-0" />
                <span>
                  {getAnalysisStageMessage()} (polling status every 2s)
                </span>
              </div>
              <span className="text-soc-text-secondary shrink-0 ml-2">
                Attempt {pollCount}/30
              </span>
            </div>
          )}

          {/* Timeout Alert */}
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

          {/* Swarm Specialist Execution State Strip */}
          <section aria-label="Agent Activity Strip">
            <AgentActivityStrip
              agentRuns={investigation.agent_runs}
              isAnalyzing={isAnalyzing}
            />
          </section>

          {/* PHASE 4: Analyst Workflow Bar (Status, Tags, Notes, JSON Case Export) */}
          <AnalystWorkflowBar
            investigation={investigation}
            bookmarkedIds={bookmarkedIds}
            onToggleFilterBookmarks={() =>
              setIsFilterBookmarksActive(!isFilterBookmarksActive)
            }
            isFilterBookmarksActive={isFilterBookmarksActive}
          />

          {/* Completed State: Primary Investigation Workspace Views */}
          {investigation.status === "completed" && (
            <>
              {/* Workspace Navigation Tabs */}
              <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-soc-border scrollbar-thin">
                {[
                  {
                    key: "evidence",
                    label: `Evidence Explorer (${allFindings.length})`,
                  },
                  { key: "explain", label: "Explain This Alert" },
                  { key: "agents", label: "Agent Inspector (All 6)" },
                  { key: "correlation", label: "Cross-Modal Relationships" },
                  { key: "timeline", label: "Investigation Timeline" },
                ].map((tab) => (
                  <button
                    key={tab.key}
                    type="button"
                    onClick={() =>
                      setActiveWorkspaceTab(
                        tab.key as
                          | "evidence"
                          | "explain"
                          | "agents"
                          | "correlation"
                          | "timeline"
                      )
                    }
                    className={`px-3.5 py-2 rounded text-xs font-mono font-bold tracking-tight whitespace-nowrap transition-colors ${
                      activeWorkspaceTab === tab.key
                        ? "bg-accent-primary text-white"
                        : "bg-soc-surface border border-soc-border text-soc-text-secondary hover:text-soc-text-primary"
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Tab 1: Evidence Explorer (Phase 3.3) */}
              {activeWorkspaceTab === "evidence" && (
                <div className="space-y-6">
                  {/* Conflict Notice if any */}
                  {investigation.risk?.conflicts &&
                    investigation.risk.conflicts.length > 0 && (
                      <ConflictBanner
                        conflicts={investigation.risk.conflicts}
                      />
                    )}

                  <EvidenceExplorer
                    investigation={investigation}
                    allFindings={displayedFindings}
                    bookmarkedIds={bookmarkedIds}
                    onToggleBookmark={toggleBookmark}
                  />

                  {/* Supporting Deterministic Risk Assessment */}
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

                  {/* RAG Threat Intelligence Grounding Panel */}
                  <section aria-label="External Advisory Citations">
                    <RagCitationPanel citations={investigation.rag_citations} />
                  </section>
                </div>
              )}

              {/* Tab 2: Explain This Alert (Phase 3.4) */}
              {activeWorkspaceTab === "explain" && (
                <AlertExplanationPanel
                  investigation={investigation}
                  allFindings={allFindings}
                />
              )}

              {/* Tab 3: Agent Execution Inspector (Phase 3.5 - All 6 Agents) */}
              {activeWorkspaceTab === "agents" && (
                <AgentExecutionInspector investigation={investigation} />
              )}

              {/* Tab 4: Cross-Modal Relationship Explorer (Phase 3.6) */}
              {activeWorkspaceTab === "correlation" && (
                <CrossModalRelationshipExplorer
                  investigation={investigation}
                  allFindings={allFindings}
                />
              )}

              {/* Tab 5: Chronological Investigation Timeline (Phase 3.2) */}
              {activeWorkspaceTab === "timeline" && (
                <InvestigationTimeline investigation={investigation} />
              )}
            </>
          )}
        </div>
      ) : null}

      {/* Footer */}
      <footer className="mt-12 border-t border-soc-border pt-4 text-center">
        <p className="text-xs font-mono text-soc-text-muted flex items-center justify-center gap-1.5">
          <Sparkles className="h-3 w-3 text-accent-primary" />
          ThreatWeave — Multimodal Cyber Threat Intelligence &amp; Incident Response Swarm
        </p>
      </footer>
    </div>
  );
}
