"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  FileText,
  Globe,
  Image as ImageIcon,
  Mic,
  QrCode,
  Play,
  Loader2,
  Sparkles,
  ArrowRight,
  Layers,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { DemoScenario } from "@/lib/types";
import { runDemoScenario, ApiError } from "@/lib/api";

interface ScenarioCardProps {
  scenario: DemoScenario;
  onSelectComparison?: () => void;
}

export function ScenarioCard({ scenario, onSelectComparison }: ScenarioCardProps) {
  const router = useRouter();
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isCrossModal = scenario.key === "cross_modal";

  const renderModalityIcon = (mod: string) => {
    switch (mod.toLowerCase()) {
      case "text":
        return (
          <span
            key={mod}
            title="Text Lure"
            className="inline-flex items-center gap-1 px-2 py-1 rounded bg-soc-base border border-soc-border text-xs font-mono text-soc-text-secondary"
          >
            <FileText className="h-3.5 w-3.5" />
            <span>Text</span>
          </span>
        );
      case "url":
        return (
          <span
            key={mod}
            title="Malicious URL"
            className="inline-flex items-center gap-1 px-2 py-1 rounded bg-soc-base border border-soc-border text-xs font-mono text-accent-primary"
          >
            <Globe className="h-3.5 w-3.5" />
            <span>URL</span>
          </span>
        );
      case "qr":
        return (
          <span
            key={mod}
            title="QR Code"
            className="inline-flex items-center gap-1 px-2 py-1 rounded bg-soc-base border border-soc-border text-xs font-mono text-accent-primary"
          >
            <QrCode className="h-3.5 w-3.5" />
            <span>QR</span>
          </span>
        );
      case "image":
        return (
          <span
            key={mod}
            title="Image Screenshot"
            className="inline-flex items-center gap-1 px-2 py-1 rounded bg-soc-base border border-soc-border text-xs font-mono text-soc-text-primary"
          >
            <ImageIcon className="h-3.5 w-3.5" />
            <span>Image</span>
          </span>
        );
      case "voice":
        return (
          <span
            key={mod}
            title="Vishing Audio"
            className="inline-flex items-center gap-1 px-2 py-1 rounded bg-soc-base border border-soc-border text-xs font-mono text-severity-medium"
          >
            <Mic className="h-3.5 w-3.5" />
            <span>Voice</span>
          </span>
        );
      default:
        return (
          <span
            key={mod}
            className="px-2 py-1 rounded bg-soc-base border border-soc-border text-xs font-mono text-soc-text-muted"
          >
            {mod}
          </span>
        );
    }
  };

  const handleRun = async () => {
    setIsRunning(true);
    setError(null);
    try {
      const res = await runDemoScenario(scenario.key, "combined");
      if (res.investigation_id) {
        router.push(`/investigations/${res.investigation_id}`);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to execute demo scenario.");
      }
      setIsRunning(false);
    }
  };

  return (
    <Card
      className={`p-6 flex flex-col justify-between transition-all duration-200 border-soc-border hover:border-accent-primary/60 bg-soc-surface ${
        isCrossModal ? "ring-1 ring-accent-primary/30 shadow-lg shadow-accent-primary/5" : ""
      }`}
    >
      <div>
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <h3 className="font-display font-semibold text-base text-soc-text-primary">
              {scenario.title}
            </h3>
          </div>
          {isCrossModal ? (
            <Badge variant="accent" className="font-mono text-[10px] tracking-wider uppercase shrink-0">
              <Sparkles className="h-3 w-3 mr-1" />
              Thesis Proof
            </Badge>
          ) : (
            <Badge variant="outline" className="font-mono text-[10px] text-soc-text-muted shrink-0">
              Curated
            </Badge>
          )}
        </div>

        <p className="text-xs text-soc-text-secondary leading-relaxed mb-4">
          {scenario.description}
        </p>

        {/* Modality Chips */}
        <div className="flex items-center gap-2 flex-wrap mb-6">
          {scenario.modalities.map((m) => renderModalityIcon(m))}
        </div>
      </div>

      {error && (
        <p className="text-xs font-mono text-severity-critical mb-3">
          {error}
        </p>
      )}

      {/* Action Footer */}
      <div className="pt-4 border-t border-soc-border/60 flex flex-col sm:flex-row items-stretch sm:items-center gap-2 mt-auto">
        <Button
          variant={isCrossModal ? "primary" : "secondary"}
          size="sm"
          onClick={handleRun}
          disabled={isRunning}
          className="w-full sm:flex-1 font-mono text-xs"
        >
          {isRunning ? (
            <>
              <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />
              Running Pipeline...
            </>
          ) : (
            <>
              <Play className="h-3.5 w-3.5 mr-1.5 fill-current" />
              Run Scenario
            </>
          )}
        </Button>

        {isCrossModal && onSelectComparison && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onSelectComparison}
            disabled={isRunning}
            className="w-full sm:w-auto font-mono text-xs text-accent-primary hover:text-accent-primary hover:bg-accent-primary/10"
          >
            <Layers className="h-3.5 w-3.5 mr-1.5" />
            Comparison View
            <ArrowRight className="h-3 w-3 ml-1" />
          </Button>
        )}
      </div>
    </Card>
  );
}
