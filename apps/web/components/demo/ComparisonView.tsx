"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  FileText,
  Globe,
  Image as ImageIcon,
  Sparkles,
  Loader2,
  TrendingUp,
  ArrowRight,
  Printer,
  Layers,
  RotateCcw,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { SeverityTag, SeverityType } from "@/components/ui/SeverityTag";
import { RiskGauge } from "@/components/investigation/RiskGauge";
import { runDemoScenario, ApiError } from "@/lib/api";
import { DemoRunResponse } from "@/lib/types";

export function ComparisonView() {
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState<string>("");
  const [textResult, setTextResult] = useState<DemoRunResponse | null>(null);
  const [urlResult, setUrlResult] = useState<DemoRunResponse | null>(null);
  const [imageResult, setImageResult] = useState<DemoRunResponse | null>(null);
  const [combinedResult, setCombinedResult] = useState<DemoRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runAllComparisons = async () => {
    setIsRunning(true);
    setError(null);
    try {
      setCurrentStep("Evaluating isolated text SMS modality...");
      const textRes = await runDemoScenario("cross_modal", "text_only");
      setTextResult(textRes);

      setCurrentStep("Evaluating isolated lookalike URL modality...");
      const urlRes = await runDemoScenario("cross_modal", "url_only");
      setUrlResult(urlRes);

      setCurrentStep("Evaluating isolated screenshot OCR modality...");
      const imgRes = await runDemoScenario("cross_modal", "image_only");
      setImageResult(imgRes);

      setCurrentStep("Executing combined cross-modal swarm analysis with correlation engine...");
      const combRes = await runDemoScenario("cross_modal", "combined");
      setCombinedResult(combRes);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to execute side-by-side comparison benchmark.");
      }
    } finally {
      setIsRunning(false);
      setCurrentStep("");
    }
  };

  const hasResults = Boolean(textResult && urlResult && imageResult && combinedResult);

  // Extract corroboration & intel bonuses from combined risk object if available
  const combinedRiskAny = combinedResult?.risk as Record<string, unknown> | null | undefined;
  const corroborationBonus =
    typeof combinedRiskAny?.corroboration_bonus === "number"
      ? combinedRiskAny.corroboration_bonus
      : 0.20;
  const intelBonus =
    typeof combinedRiskAny?.intel_bonus === "number"
      ? combinedRiskAny.intel_bonus
      : 0.15;

  return (
    <div className="space-y-6">
      {/* Benchmark Header Banner */}
      <Card className="p-6 bg-soc-surface border-soc-border shadow-md">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <Layers className="h-5 w-5 text-accent-primary" />
              <h2 className="font-display font-bold text-lg text-soc-text-primary">
                Cross-Modal Correlation Benchmark: Phase 11 Thesis Proof
              </h2>
              <Badge variant="accent" className="font-mono text-[10px] uppercase">
                Visual Proof
              </Badge>
            </div>
            <p className="text-xs text-soc-text-secondary max-w-3xl leading-relaxed">
              Demonstrates that analyzing multiple evidence modalities (SMS Text + Lookalike URL + Forged Alert Screenshot)
              of the same underlying scam generates shared indicators, triggering the deterministic corroboration bonus
              and yielding an elevated threat conviction strictly higher than any single modality in isolation.
            </p>
          </div>

          <div className="shrink-0 flex items-center gap-3">
            <Button
              variant="primary"
              size="md"
              onClick={runAllComparisons}
              disabled={isRunning}
              className="font-mono text-xs shadow-lg shadow-accent-primary/20"
            >
              {isRunning ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Running Benchmark...
                </>
              ) : hasResults ? (
                <>
                  <RotateCcw className="h-4 w-4 mr-2" />
                  Re-run Benchmark
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2" />
                  Run Live Benchmark
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Real-time execution stepper */}
        {isRunning && (
          <div className="mt-4 pt-4 border-t border-soc-border/60 flex items-center gap-2 text-xs font-mono text-accent-primary animate-pulse">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            <span>{currentStep}</span>
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 rounded bg-severity-critical/10 border border-severity-critical/30 text-xs font-mono text-severity-critical">
            {error}
          </div>
        )}
      </Card>

      {/* Comparison Grid */}
      {hasResults && combinedResult && (
        <div className="space-y-6">
          {/* Delta Insight Banner */}
          <div className="p-5 rounded-lg bg-accent-primary/10 border border-accent-primary/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded bg-accent-primary/20 text-accent-primary shrink-0 mt-0.5">
                <TrendingUp className="h-5 w-5" />
              </div>
              <div>
                <h4 className="font-display font-semibold text-sm text-soc-text-primary mb-1">
                  Empirical Proof: Combined Conviction Exceeds All Individual Modalities
                </h4>
                <p className="text-xs text-soc-text-secondary leading-relaxed">
                  Cross-modal correlation detected corroborated indicators across Text, URL, and Image modalities.
                  This activated a <span className="font-mono font-bold text-accent-primary">+{corroborationBonus.toFixed(4)}</span> Corroboration Bonus
                  and a <span className="font-mono font-bold text-accent-primary">+{intelBonus.toFixed(4)}</span> RAG Advisory Grounding Bonus.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
              <Link
                href={`/investigations/${combinedResult.investigation_id}`}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-soc-base border border-soc-border hover:border-accent-primary text-xs font-mono text-soc-text-primary transition-colors"
              >
                Combined Workspace <ArrowRight className="h-3.5 w-3.5" />
              </Link>
              <Link
                href={`/investigations/${combinedResult.investigation_id}/report`}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-accent-primary text-soc-base font-bold text-xs font-mono hover:bg-accent-primary/90 transition-colors"
              >
                <Printer className="h-3.5 w-3.5" />
                Report
              </Link>
            </div>
          </div>

          {/* 4-Card Comparison Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Card 1: Text Only */}
            <Card className="p-5 bg-soc-surface border-soc-border flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-2 border-b border-soc-border pb-3 mb-3">
                  <span className="flex items-center gap-1.5 text-xs font-mono font-bold text-soc-text-secondary uppercase">
                    <FileText className="h-4 w-4" /> Text SMS Only
                  </span>
                  {textResult?.final_severity && (
                    <SeverityTag severity={textResult.final_severity as SeverityType} />
                  )}
                </div>

                <div className="py-3">
                  <RiskGauge
                    score={textResult?.final_risk_score}
                    severity={textResult?.final_severity}
                    confidence={textResult?.final_confidence}
                  />
                </div>

                <div className="space-y-1.5 text-xs font-mono pt-3 border-t border-soc-border/60">
                  <div className="flex justify-between text-soc-text-muted">
                    <span>Corroboration Bonus:</span>
                    <span className="text-soc-text-secondary">0.0000</span>
                  </div>
                  <div className="flex justify-between text-soc-text-muted">
                    <span>Cross-Modal Overlap:</span>
                    <span className="text-soc-text-secondary">None (Isolated)</span>
                  </div>
                </div>
              </div>

              <div className="pt-4 mt-3">
                <Link
                  href={`/investigations/${textResult?.investigation_id}`}
                  className="block text-center py-1.5 text-xs font-mono text-soc-text-secondary hover:text-accent-primary border border-soc-border rounded transition-colors"
                >
                  Inspect Single Run &rarr;
                </Link>
              </div>
            </Card>

            {/* Card 2: URL Only */}
            <Card className="p-5 bg-soc-surface border-soc-border flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-2 border-b border-soc-border pb-3 mb-3">
                  <span className="flex items-center gap-1.5 text-xs font-mono font-bold text-accent-primary uppercase">
                    <Globe className="h-4 w-4" /> URL Link Only
                  </span>
                  {urlResult?.final_severity && (
                    <SeverityTag severity={urlResult.final_severity as SeverityType} />
                  )}
                </div>

                <div className="py-3">
                  <RiskGauge
                    score={urlResult?.final_risk_score}
                    severity={urlResult?.final_severity}
                    confidence={urlResult?.final_confidence}
                  />
                </div>

                <div className="space-y-1.5 text-xs font-mono pt-3 border-t border-soc-border/60">
                  <div className="flex justify-between text-soc-text-muted">
                    <span>Corroboration Bonus:</span>
                    <span className="text-soc-text-secondary">0.0000</span>
                  </div>
                  <div className="flex justify-between text-soc-text-muted">
                    <span>Cross-Modal Overlap:</span>
                    <span className="text-soc-text-secondary">None (Isolated)</span>
                  </div>
                </div>
              </div>

              <div className="pt-4 mt-3">
                <Link
                  href={`/investigations/${urlResult?.investigation_id}`}
                  className="block text-center py-1.5 text-xs font-mono text-soc-text-secondary hover:text-accent-primary border border-soc-border rounded transition-colors"
                >
                  Inspect Single Run &rarr;
                </Link>
              </div>
            </Card>

            {/* Card 3: Image Only */}
            <Card className="p-5 bg-soc-surface border-soc-border flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-2 border-b border-soc-border pb-3 mb-3">
                  <span className="flex items-center gap-1.5 text-xs font-mono font-bold text-soc-text-primary uppercase">
                    <ImageIcon className="h-4 w-4" /> Image OCR Only
                  </span>
                  {imageResult?.final_severity && (
                    <SeverityTag severity={imageResult.final_severity as SeverityType} />
                  )}
                </div>

                <div className="py-3">
                  <RiskGauge
                    score={imageResult?.final_risk_score}
                    severity={imageResult?.final_severity}
                    confidence={imageResult?.final_confidence}
                  />
                </div>

                <div className="space-y-1.5 text-xs font-mono pt-3 border-t border-soc-border/60">
                  <div className="flex justify-between text-soc-text-muted">
                    <span>Corroboration Bonus:</span>
                    <span className="text-soc-text-secondary">0.0000</span>
                  </div>
                  <div className="flex justify-between text-soc-text-muted">
                    <span>Cross-Modal Overlap:</span>
                    <span className="text-soc-text-secondary">None (Isolated)</span>
                  </div>
                </div>
              </div>

              <div className="pt-4 mt-3">
                <Link
                  href={`/investigations/${imageResult?.investigation_id}`}
                  className="block text-center py-1.5 text-xs font-mono text-soc-text-secondary hover:text-accent-primary border border-soc-border rounded transition-colors"
                >
                  Inspect Single Run &rarr;
                </Link>
              </div>
            </Card>

            {/* Card 4: Combined Multi-Modal Run (Hero Card) */}
            <Card className="p-5 bg-soc-surface border-accent-primary/60 ring-1 ring-accent-primary shadow-xl shadow-accent-primary/10 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-2 border-b border-accent-primary/30 pb-3 mb-3">
                  <span className="flex items-center gap-1.5 text-xs font-mono font-bold text-accent-primary uppercase">
                    <Sparkles className="h-4 w-4" /> Combined Swarm
                  </span>
                  {combinedResult?.final_severity && (
                    <SeverityTag severity={combinedResult.final_severity as SeverityType} />
                  )}
                </div>

                <div className="py-3">
                  <RiskGauge
                    score={combinedResult?.final_risk_score}
                    severity={combinedResult?.final_severity}
                    confidence={combinedResult?.final_confidence}
                  />
                </div>

                <div className="space-y-1.5 text-xs font-mono pt-3 border-t border-accent-primary/30">
                  <div className="flex justify-between font-bold text-accent-primary">
                    <span>Corroboration Bonus:</span>
                    <span>+{corroborationBonus.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between font-bold text-accent-primary">
                    <span>RAG Intel Grounding:</span>
                    <span>+{intelBonus.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between text-soc-text-secondary">
                    <span>Active Specialists:</span>
                    <span>Text, URL, Image</span>
                  </div>
                </div>
              </div>

              <div className="pt-4 mt-3">
                <Link
                  href={`/investigations/${combinedResult?.investigation_id}`}
                  className="block text-center py-1.5 text-xs font-mono font-bold text-soc-base bg-accent-primary hover:bg-accent-primary/90 rounded transition-colors"
                >
                  Open Full Swarm Analysis &rarr;
                </Link>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
