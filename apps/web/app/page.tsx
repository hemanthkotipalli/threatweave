"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Plus,
  Terminal,
  RefreshCw,
  Layers,
  ArrowRight,
  ArrowUpRight,
  Shield,
  Activity,
  Cpu,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { SeverityTag, SeverityType } from "@/components/ui/SeverityTag";
import { StatusDot } from "@/components/ui/StatusDot";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { listInvestigations } from "@/lib/api";
import { getStoredUser, isAuthenticated, logoutUser } from "@/lib/auth";
import { InvestigationListItem, UserProfile } from "@/lib/types";

export default function Dashboard() {
  const router = useRouter();

  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [isAuth, setIsAuth] = useState<boolean>(false);
  const [recentItems, setRecentItems] = useState<InvestigationListItem[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchRecent = async () => {
    setIsLoading(true);
    try {
      const res = await listInvestigations(1, 5);
      setRecentItems(res.items);
      setTotalCount(res.total);
    } catch {
      // Fallback gracefully to empty state
      setRecentItems([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsAuth(isAuthenticated());
      setCurrentUser(getStoredUser());
    }, 0);

    let isMounted = true;
    void (async () => {
      try {
        const res = await listInvestigations(1, 5);
        if (!isMounted) return;
        setRecentItems(res.items);
        setTotalCount(res.total);
      } catch {
        if (!isMounted) return;
        setRecentItems([]);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    })();

    return () => {
      clearTimeout(timer);
      isMounted = false;
    };
  }, []);


  return (
    <div className="flex flex-col min-h-screen bg-soc-base text-soc-text-primary px-4 md:px-8 py-6 max-w-7xl mx-auto w-full">
      {/* 1. Page Header */}
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-soc-border pb-6 mb-8">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Layers className="h-5 w-5 text-accent-primary" />
            <h1 className="font-display font-bold text-xxl tracking-tight text-soc-text-primary">
              ThreatWeave
            </h1>
            <Badge variant="accent">PHASE 17</Badge>
          </div>
          <p className="text-soc-text-secondary text-sm">
            Agentic Multimodal Cyber Threat Intelligence &amp; Response Swarm
          </p>
        </div>
        <div className="flex items-center flex-wrap gap-2.5">
          <Button variant="secondary" size="sm" onClick={fetchRecent} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-1.5 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button variant="secondary" size="sm" onClick={() => router.push("/demo")}>
            <Sparkles className="h-4 w-4 mr-1.5 text-accent-primary" />
            Demo Mode
          </Button>
          <Button variant="primary" size="sm" onClick={() => router.push("/investigations/new")}>
            <Plus className="h-4 w-4 mr-1.5" />
            New Investigation
          </Button>

          {/* Auth State (Phase 17) */}
          <div className="h-6 w-px bg-soc-border mx-1 hidden sm:block" />
          {isAuth && currentUser ? (
            <div className="flex items-center gap-2">
              <div className="hidden md:flex flex-col items-end">
                <span className="text-xs font-mono text-soc-text-primary truncate max-w-[180px]">
                  {currentUser.email}
                </span>
                <span className="text-[10px] font-mono text-accent-primary uppercase">
                  {currentUser.role}
                </span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  logoutUser();
                  setIsAuth(false);
                  setCurrentUser(null);
                }}
                className="text-xs text-soc-text-secondary hover:text-severity-critical"
              >
                Sign Out
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-1.5">
              <Button variant="ghost" size="sm" onClick={() => router.push("/login")}>
                Sign In
              </Button>
              <Button variant="secondary" size="sm" onClick={() => router.push("/register")}>
                Register
              </Button>
            </div>
          )}
        </div>
      </header>


      {/* Demo Mode Feature Banner */}
      <section className="mb-8" aria-label="Demo Mode Quick Launch">
        <Card className="p-6 bg-gradient-to-r from-soc-surface via-soc-surface to-accent-primary/10 border-accent-primary/40 shadow-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-lg bg-accent-primary/20 text-accent-primary shrink-0">
              <Sparkles className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h2 className="font-display font-bold text-base text-soc-text-primary">
                  ThreatWeave Demonstration Lab &amp; Cross-Modal Benchmark
                </h2>
                <Badge variant="accent" className="text-[10px] font-mono uppercase">
                  1-Click Live Swarm
                </Badge>
              </div>
              <p className="text-xs text-soc-text-secondary max-w-2xl leading-relaxed">
                Execute 6 curated threat scenarios (phishing, malicious URLs, fake UPI QR codes, fraudulent payment screenshots, vishing audio, and multi-modal correlation) against the live swarm with zero mocking.
              </p>
            </div>
          </div>
          <Button
            variant="primary"
            size="md"
            onClick={() => router.push("/demo")}
            className="shrink-0 font-mono text-xs shadow-md shadow-accent-primary/20"
          >
            <Sparkles className="h-3.5 w-3.5 mr-1.5" />
            Launch Demo Scenarios
            <ArrowRight className="h-3.5 w-3.5 ml-1.5" />
          </Button>
        </Card>
      </section>

      {/* 2. System Status & Swarm Metrics Row */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8" aria-label="System Architecture Status">
        {/* Severity Classification Showcase */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display font-semibold text-xs text-soc-text-secondary tracking-wider uppercase">
              Severity Hierarchy
            </h2>
            <Shield className="h-3.5 w-3.5 text-soc-text-muted" />
          </div>
          <div className="flex flex-wrap gap-2">
            <SeverityTag severity="info" />
            <SeverityTag severity="low" />
            <SeverityTag severity="medium" />
            <SeverityTag severity="high" />
            <SeverityTag severity="critical" />
          </div>
        </Card>

        {/* Multi-Agent Swarm Pipeline */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display font-semibold text-xs text-soc-text-secondary tracking-wider uppercase">
              Swarm Execution Engines
            </h2>
            <Cpu className="h-3.5 w-3.5 text-accent-primary" />
          </div>
          <div className="grid grid-cols-2 gap-y-2.5 text-xs font-mono">
            <div className="flex items-center gap-2">
              <StatusDot status="done" showLabel={false} />
              <span>Text &amp; SMS</span>
            </div>
            <div className="flex items-center gap-2">
              <StatusDot status="done" showLabel={false} />
              <span>URL Sandbox</span>
            </div>
            <div className="flex items-center gap-2">
              <StatusDot status="done" showLabel={false} />
              <span>OCR &amp; Vision</span>
            </div>
            <div className="flex items-center gap-2">
              <StatusDot status="done" showLabel={false} />
              <span>Audio Speech</span>
            </div>
          </div>
        </Card>

        {/* Intelligence Grounding */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display font-semibold text-xs text-soc-text-secondary tracking-wider uppercase">
              RAG Intelligence Grounding
            </h2>
            <Activity className="h-3.5 w-3.5 text-severity-low" />
          </div>
          <p className="text-xs text-soc-text-secondary leading-relaxed mb-3">
            Grounded against 24 curated CERT-In advisories, RBI directives, and threat syndicates.
          </p>
          <div className="flex items-center gap-2 text-xs font-mono text-soc-text-muted">
            <Badge variant="accent">CHROMA DB</Badge>
            <Badge variant="outline">STRICT 0.40 THRESHOLD</Badge>
          </div>
        </Card>
      </section>

      {/* 3. Recent Investigations Queue Table */}
      <main className="flex-grow flex flex-col">
        <Card className="flex-grow flex flex-col p-6 border-soc-border bg-soc-surface">
          <div className="flex items-center justify-between border-b border-soc-border pb-4 mb-6">
            <div className="flex items-center gap-2 text-soc-text-primary">
              <Terminal className="h-4 w-4 text-accent-primary" />
              <h2 className="font-display font-semibold text-base">
                Recent Threat Investigations
              </h2>
              {totalCount > 0 && (
                <Badge variant="outline" className="font-mono text-xs ml-1">
                  {totalCount} Total
                </Badge>
              )}
            </div>

            <Link
              href="/investigations"
              className="inline-flex items-center gap-1.5 text-xs font-mono text-accent-primary hover:underline"
            >
              View All Queue
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          <div className="border border-soc-border rounded-lg overflow-hidden flex-grow flex flex-col bg-soc-base/30">
            {isLoading ? (
              <div className="p-6 space-y-3">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            ) : recentItems.length === 0 ? (
              <div className="flex-grow flex items-center justify-center p-6 bg-soc-base/10">
                <EmptyState
                  className="w-full max-w-2xl border-none bg-transparent"
                  title="No active investigations found"
                  description="Your security queue is currently clean. Initiate a threat analysis workflow by uploading security messages, malicious URLs, screenshot artifacts, or audio briefings."
                  action={
                    <Button variant="primary" size="sm" onClick={() => router.push("/investigations/new")}>
                      <Plus className="h-4 w-4 mr-1.5" />
                      Launch Swarm Workspace
                    </Button>
                  }
                />
              </div>
            ) : (
              <div className="divide-y divide-soc-border/60">
                {/* Table Header */}
                <div className="grid grid-cols-12 bg-soc-surface border-b border-soc-border px-5 py-3 text-xs font-mono text-soc-text-secondary uppercase tracking-wider font-semibold">
                  <div className="col-span-6">Investigation Title / ID</div>
                  <div className="col-span-2">Severity</div>
                  <div className="col-span-2">Status</div>
                  <div className="col-span-2 text-right">Created</div>
                </div>

                {/* Table Rows */}
                {recentItems.map((item) => (
                  <Link
                    key={item.id}
                    href={`/investigations/${item.id}`}
                    className="grid grid-cols-12 items-center px-5 py-3.5 hover:bg-soc-elevated/50 transition-colors group text-sm"
                  >
                    <div className="col-span-6 pr-2">
                      <div className="flex items-center gap-1.5 mb-0.5">
                        <span className="font-display font-medium text-soc-text-primary group-hover:text-accent-primary transition-colors truncate">
                          {item.title || "Untitled Investigation"}
                        </span>
                        <ArrowUpRight className="h-3.5 w-3.5 text-soc-text-muted opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                      </div>
                      <span className="text-[11px] font-mono text-soc-text-muted block truncate">
                        ID: {item.id}
                      </span>
                    </div>

                    <div className="col-span-2">
                      {item.final_severity ? (
                        <SeverityTag severity={(item.final_severity as SeverityType) || "info"} />
                      ) : (
                        <span className="text-xs font-mono text-soc-text-muted">Pending</span>
                      )}
                    </div>

                    <div className="col-span-2">
                      <Badge
                        variant={
                          item.status === "completed"
                            ? "accent"
                            : item.status === "failed"
                            ? "outline"
                            : "default"
                        }
                        className="text-[10px] font-mono uppercase"
                      >
                        {item.status}
                      </Badge>
                    </div>

                    <div className="col-span-2 text-right text-xs font-mono text-soc-text-muted">
                      {new Date(item.created_at).toLocaleDateString()}
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </Card>
      </main>

      {/* 4. Footer */}
      <footer className="mt-8 border-t border-soc-border pt-4 text-center">
        <p className="text-xs font-mono text-soc-text-muted">
          ThreatWeave Phase 13 — Multimodal SOC Investigation Workspace
        </p>
      </footer>
    </div>
  );
}
