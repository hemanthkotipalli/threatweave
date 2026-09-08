"use client";

import React, { useEffect, useState, useRef } from "react";
import Link from "next/link";
import {
  Sparkles,
  Layers,
  ArrowLeft,
  RefreshCw,
  AlertCircle,
  PlayCircle,
  BarChart3,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { ScenarioCard } from "@/components/demo/ScenarioCard";
import { ComparisonView } from "@/components/demo/ComparisonView";
import { getDemoScenarios, ApiError } from "@/lib/api";
import { DemoScenario } from "@/lib/types";

export default function DemoPage() {
  const [scenarios, setScenarios] = useState<DemoScenario[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"scenarios" | "comparison">("scenarios");

  const comparisonSectionRef = useRef<HTMLDivElement>(null);

  const fetchScenarios = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getDemoScenarios();
      setScenarios(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load demo scenarios.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    async function load() {
      try {
        const data = await getDemoScenarios();
        if (isMounted) {
          setScenarios(data);
          setIsLoading(false);
        }
      } catch (err) {
        if (isMounted) {
          if (err instanceof ApiError) {
            setError(err.message);
          } else {
            setError("Failed to load demo scenarios.");
          }
          setIsLoading(false);
        }
      }
    }
    void load();
    return () => {
      isMounted = false;
    };
  }, []);


  const handleSelectComparison = () => {
    setActiveTab("comparison");
    setTimeout(() => {
      comparisonSectionRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 50);
  };

  return (
    <div className="flex flex-col min-h-screen bg-soc-base text-soc-text-primary px-4 md:px-8 py-8 max-w-7xl mx-auto w-full">
      {/* Top Header */}
      <header className="border-b border-soc-border pb-6 mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div className="flex items-center gap-2">
            <Link
              href="/"
              className="inline-flex items-center gap-1.5 text-xs font-mono text-soc-text-secondary hover:text-soc-text-primary transition-colors"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Dashboard
            </Link>
            <span className="text-soc-text-muted">/</span>
            <span className="text-xs font-mono text-accent-primary">Demo Mode</span>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="secondary"
              size="sm"
              onClick={fetchScenarios}
              disabled={isLoading}
            >
              <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${isLoading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Link href="/investigations">
              <Button variant="ghost" size="sm">
                Investigation History
              </Button>
            </Link>
          </div>
        </div>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5 mb-2">
              <Sparkles className="h-6 w-6 text-accent-primary" />
              <h1 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-soc-text-primary">
                ThreatWeave Live Demonstration Lab
              </h1>
              <Badge variant="accent" className="font-mono text-xs uppercase">
                Zero Mocking
              </Badge>
            </div>
            <p className="text-sm text-soc-text-secondary max-w-3xl leading-relaxed">
              Curated, production-grade attack scenarios executed live through the genuine
              multimodal ingestion service, LangGraph agent swarm, and deterministic risk engine.
            </p>
          </div>

          {/* Tab Switcher */}
          <div className="flex items-center p-1 bg-soc-surface border border-soc-border rounded-lg shrink-0">
            <button
              onClick={() => setActiveTab("scenarios")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-mono transition-colors ${
                activeTab === "scenarios"
                  ? "bg-accent-primary text-soc-base font-bold shadow-sm"
                  : "text-soc-text-secondary hover:text-soc-text-primary"
              }`}
            >
              <PlayCircle className="h-3.5 w-3.5" />
              6 Curated Scenarios
            </button>
            <button
              onClick={() => setActiveTab("comparison")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-mono transition-colors ${
                activeTab === "comparison"
                  ? "bg-accent-primary text-soc-base font-bold shadow-sm"
                  : "text-soc-text-secondary hover:text-soc-text-primary"
              }`}
            >
              <BarChart3 className="h-3.5 w-3.5" />
              Cross-Modal Benchmark
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-grow flex flex-col space-y-8">
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Skeleton className="h-64 rounded-lg" />
            <Skeleton className="h-64 rounded-lg" />
            <Skeleton className="h-64 rounded-lg" />
            <Skeleton className="h-64 rounded-lg" />
            <Skeleton className="h-64 rounded-lg" />
            <Skeleton className="h-64 rounded-lg" />
          </div>
        ) : error ? (
          <Card className="p-8 text-center border-severity-critical/30 bg-soc-surface">
            <div className="flex h-12 w-12 items-center justify-center rounded bg-severity-critical/10 text-severity-critical mx-auto mb-4 border border-severity-critical/20">
              <AlertCircle className="h-6 w-6" />
            </div>
            <h2 className="font-display font-semibold text-lg text-soc-text-primary mb-2">
              Unable to Load Demo Scenarios
            </h2>
            <p className="text-sm text-soc-text-secondary max-w-md mx-auto mb-6 font-mono">
              {error}
            </p>
            <Button variant="primary" size="sm" onClick={fetchScenarios}>
              Retry Connection
            </Button>
          </Card>
        ) : activeTab === "scenarios" ? (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Layers className="h-4 w-4 text-soc-text-secondary" />
                <h2 className="font-display font-semibold text-sm text-soc-text-secondary uppercase tracking-wider">
                  Select a threat vector to execute live
                </h2>
              </div>
              <span className="text-xs font-mono text-soc-text-muted">
                {scenarios.length} Scenarios Available
              </span>
            </div>

            {/* Scenario Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {scenarios.map((scenario) => (
                <ScenarioCard
                  key={scenario.key}
                  scenario={scenario}
                  onSelectComparison={handleSelectComparison}
                />
              ))}
            </div>
          </div>
        ) : (
          <div ref={comparisonSectionRef}>
            <ComparisonView />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-16 border-t border-soc-border pt-4 text-center">
        <p className="text-xs font-mono text-soc-text-muted">
          ThreatWeave Phase 15 — Live Multimodal Demonstration & Benchmarking Suite
        </p>
      </footer>
    </div>
  );
}
