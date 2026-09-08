"use client";

import React from "react";
import { FileText, Globe, QrCode, Image as ImageIcon, Mic, Cpu } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { StatusDot, StatusType } from "@/components/ui/StatusDot";
import { AgentRunDetail } from "@/lib/types";

interface AgentActivityStripProps {
  agentRuns?: AgentRunDetail[];
  isAnalyzing?: boolean;
}

interface SpecialistDef {
  key: string;
  name: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const SPECIALISTS: SpecialistDef[] = [
  { key: "text_agent", name: "Text Specialist", label: "SMS & Text", icon: FileText },
  { key: "url_agent", name: "URL Specialist", label: "Domain & Host", icon: Globe },
  { key: "qr_agent", name: "QR Specialist", label: "Payload & Deeplink", icon: QrCode },
  { key: "image_agent", name: "Image Specialist", label: "OCR & Vision", icon: ImageIcon },
  { key: "voice_agent", name: "Voice Specialist", label: "Audio & Speech", icon: Mic },
];

export function AgentActivityStrip({ agentRuns = [], isAnalyzing = false }: AgentActivityStripProps) {
  // Map agent name -> AgentRunDetail
  const runsMap = new Map<string, AgentRunDetail>();
  for (const run of agentRuns) {
    runsMap.set(run.agent_name, run);
  }

  const getAgentState = (key: string): { status: StatusType; label: string; latency?: number | null; findingsCount: number } => {
    const run = runsMap.get(key);

    if (!run) {
      if (isAnalyzing) {
        return { status: "running", label: "Evaluating...", findingsCount: 0 };
      }
      return { status: "idle", label: "Standby", findingsCount: 0 };
    }

    const rawStatus = (run.status || "").toLowerCase();
    const findingsCount = run.findings ? run.findings.length : 0;
    const latency = run.latency_ms;

    if (rawStatus === "running") {
      return { status: "running", label: "Analyzing", latency, findingsCount };
    }
    if (rawStatus === "done" || rawStatus === "ok" || rawStatus === "completed" || rawStatus === "degraded_fallback") {
      return { status: "done", label: "Completed", latency, findingsCount };
    }
    if (rawStatus === "failed") {
      return { status: "failed", label: "Failed", latency, findingsCount };
    }
    if (rawStatus === "skipped") {
      return { status: "idle", label: "Skipped", latency, findingsCount };
    }

    return { status: "idle", label: "Standby", latency, findingsCount };
  };

  return (
    <Card className="p-4 sm:p-5 border-soc-border bg-soc-surface">
      <div className="flex items-center justify-between border-b border-soc-border pb-3 mb-4">
        <div className="flex items-center gap-2">
          <Cpu className="h-4 w-4 text-accent-primary" />
          <h2 className="font-display font-semibold text-xs uppercase tracking-wider text-soc-text-secondary">
            Swarm Specialist Execution State
          </h2>
        </div>
        <span className="text-[11px] font-mono text-soc-text-muted">
          5 ACTIVE MULTIMODAL AGENTS
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 sm:gap-4">
        {SPECIALISTS.map((spec) => {
          const Icon = spec.icon;
          const { status, label, latency, findingsCount } = getAgentState(spec.key);

          return (
            <div
              key={spec.key}
              className="flex flex-col justify-between p-3 rounded-md bg-soc-base border border-soc-border transition-all"
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded bg-soc-elevated text-soc-text-primary border border-soc-border">
                    <Icon className="h-3.5 w-3.5" />
                  </div>
                  <div>
                    <h3 className="font-display font-medium text-xs text-soc-text-primary leading-tight">
                      {spec.name}
                    </h3>
                    <p className="text-[10px] font-mono text-soc-text-muted">{spec.label}</p>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-soc-border/60 flex items-center justify-between text-[11px] font-mono">
                <StatusDot status={status} showLabel={false} />
                <span className="text-soc-text-secondary text-[11px]">{label}</span>
                {latency !== undefined && latency !== null ? (
                  <span className="text-[10px] text-soc-text-muted">{latency}ms</span>
                ) : findingsCount > 0 ? (
                  <span className="text-[10px] text-accent-primary font-medium">{findingsCount} findings</span>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
