"use client";

import React, { useState } from "react";
import {
  HelpCircle,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { InvestigationDetail, AgentFindingDetail } from "@/lib/types";

interface Props {
  investigation: InvestigationDetail;
  allFindings: { finding: AgentFindingDetail; agentName: string }[];
  className?: string;
}

export function AlertExplanationPanel({
  investigation,
  allFindings,
  className = "",
}: Props) {
  const [showFormulaDetails, setShowFormulaDetails] = useState<boolean>(false);

  const risk = investigation.risk;
  const runs = investigation.agent_runs || [];

  // Extract all indicators
  const allIndicators: string[] = [];
  allFindings.forEach((f) => {
    const raw = f.finding.indicators;
    if (Array.isArray(raw)) {
      raw.forEach((item) => {
        if (typeof item === "string" && !allIndicators.includes(item)) {
          allIndicators.push(item);
        }
      });
    }
  });

  const isBenign =
    (investigation.final_risk_score ?? 0) < 0.25 &&
    (investigation.final_severity === "low" || investigation.final_severity === "info");

  // Prescriptive analyst playbooks based on real findings
  const getAnalystNextSteps = () => {
    if (isBenign) {
      return [
        {
          title: "Close Alert as Benign / True Negative",
          action: "No malicious indicators were surfaced across analyzed modalities. Archive ticket or flag benign baseline.",
          priority: "Low",
        },
        {
          title: "Periodic Baseline Re-scan",
          action: "If external sender reputation changes in future SIEM logs, re-ingest fresh payload artifact.",
          priority: "Low",
        },
      ];
    }

    const steps = [
      {
        title: "Block Malicious Destination Indicators",
        action: "Export extracted domains and URLs to egress perimeter firewalls, Secure Web Gateways (SWG), and DNS sinkholes.",
        priority: "High",
      },
      {
        title: "Search SIEM / EDR Telemetry for IOC Spread",
        action: `Correlate host process executions and network connection logs across the organization for observed IOCs (${allIndicators.slice(0, 3).join(", ") || "extracted targets"}).`,
        priority: "High",
      },
    ];

    const hasVoice = runs.some((r) => r.agent_name.includes("voice") && (r.findings?.length || 0) > 0);
    if (hasVoice) {
      steps.push({
        title: "Initiate Voice Phishing (Vishing) Alert",
        action: "Notify telephony gateways and customer service desks regarding active social engineering caller lures.",
        priority: "Medium",
      });
    }

    const hasQr = runs.some((r) => r.agent_name.includes("qr") && (r.findings?.length || 0) > 0);
    if (hasQr) {
      steps.push({
        title: "Remediate Physical / Digital Quishing Poster",
        action: "Purge deceptive QR code graphics from corporate email caches and physical workplace noticeboards.",
        priority: "Medium",
      });
    }

    steps.push({
      title: "Credential Invalidation & Session Revocation",
      action: "If target user engaged with suspicious link or SMS lure, force immediate password reset and invalidate active SSO tokens.",
      priority: "Critical",
    });

    return steps;
  };

  return (
    <Card className={`p-5 md:p-6 border-soc-border bg-soc-surface ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-soc-border pb-4 mb-6">
        <div className="flex items-center gap-2">
          <HelpCircle className="h-5 w-5 text-accent-primary" />
          <div>
            <h2 className="font-display font-semibold text-sm uppercase tracking-wider text-soc-text-primary">
              Explain This Alert (Security Intelligence Breakdown)
            </h2>
            <p className="text-xs text-soc-text-secondary">
              Deterministic mathematical rationale, evidence provenance, and SOC incident playbook
            </p>
          </div>
        </div>
        <Badge variant="accent" className="font-mono text-[10px] uppercase">
          AI EXPLAINABILITY &bull; DETERMINISTIC AUDIT
        </Badge>
      </div>

      <div className="space-y-6">
        {/* 1. What Happened? */}
        <div className="p-4 rounded-lg bg-soc-base border border-soc-border space-y-2">
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-soc-text-primary uppercase">
            <span className="flex h-5 w-5 items-center justify-center rounded bg-accent-primary/20 text-accent-primary text-[11px]">
              1
            </span>
            <span>What Happened?</span>
          </div>
          <p className="text-xs sm:text-sm text-soc-text-primary leading-relaxed pl-7">
            {isBenign
              ? "All submitted modalities (text, URL, QR, image, or audio) were evaluated through deterministic heuristics and neural model verification. No deceptive lures, malicious domains, credential harvesting forms, or fraudulent patterns were detected."
              : `A multi-vector security incident was surfaced. Specialist agents identified ${allFindings.length} distinct threat indicator(s) across ${
                  investigation.evidence_inputs?.length || 1
                } evidence channel(s), resulting in a consensus ${
                  investigation.final_severity?.toUpperCase() || "EVALUATED"
                } severity rating.`}
          </p>
        </div>

        {/* 2. What Evidence Supports the Finding? */}
        <div className="p-4 rounded-lg bg-soc-base border border-soc-border space-y-2">
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-soc-text-primary uppercase">
            <span className="flex h-5 w-5 items-center justify-center rounded bg-accent-primary/20 text-accent-primary text-[11px]">
              2
            </span>
            <span>What Evidence Supports This Assessment?</span>
          </div>
          <div className="pl-7 space-y-2 text-xs">
            {allFindings.length === 0 ? (
              <p className="text-soc-text-muted">Zero malicious evidence detected.</p>
            ) : (
              <ul className="space-y-1.5 list-disc list-inside text-soc-text-secondary">
                {allFindings.slice(0, 4).map((f, i) => (
                  <li key={i}>
                    <strong className="text-soc-text-primary">
                      {f.agentName.replace("_agent", "").toUpperCase()} Agent:
                    </strong>{" "}
                    {f.finding.finding} (Confidence: {(f.finding.confidence * 100).toFixed(0)}%)
                  </li>
                ))}
              </ul>
            )}

            {allIndicators.length > 0 && (
              <div className="pt-2 flex items-center gap-1.5 flex-wrap">
                <span className="text-[11px] font-mono text-soc-text-muted">
                  Corroborated Indicators:
                </span>
                {allIndicators.slice(0, 6).map((ind, i) => (
                  <Badge key={i} variant="outline" className="text-[10px] font-mono">
                    {ind}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 3. Which Agents Contributed? */}
        <div className="p-4 rounded-lg bg-soc-base border border-soc-border space-y-2">
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-soc-text-primary uppercase">
            <span className="flex h-5 w-5 items-center justify-center rounded bg-accent-primary/20 text-accent-primary text-[11px]">
              3
            </span>
            <span>Which Specialist Agents Contributed?</span>
          </div>
          <div className="pl-7 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 pt-1">
            {runs.map((run) => (
              <div
                key={run.agent_name}
                className="p-3 rounded bg-soc-surface border border-soc-border text-xs font-mono flex items-center justify-between"
              >
                <div>
                  <span className="font-bold text-soc-text-primary block">
                    {run.agent_name}
                  </span>
                  <span className="text-[10px] text-soc-text-muted">
                    {run.findings?.length || 0} finding(s)
                  </span>
                </div>
                <Badge
                  variant={
                    run.status === "done" || run.status === "completed"
                      ? "accent"
                      : "outline"
                  }
                  className="text-[10px] uppercase py-0"
                >
                  {run.status}
                </Badge>
              </div>
            ))}
          </div>
        </div>

        {/* 4. Why Was This Severity Assigned? (Deterministic Formula) */}
        <div className="p-4 rounded-lg bg-soc-base border border-soc-border space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-soc-text-primary uppercase">
              <span className="flex h-5 w-5 items-center justify-center rounded bg-accent-primary/20 text-accent-primary text-[11px]">
                4
              </span>
              <span>Why Was This Severity Assigned? (Deterministic Risk Formula)</span>
            </div>
            <button
              type="button"
              onClick={() => setShowFormulaDetails(!showFormulaDetails)}
              className="text-xs font-mono text-accent-primary hover:underline flex items-center gap-1"
            >
              {showFormulaDetails ? (
                <>
                  <ChevronUp className="h-3.5 w-3.5" /> Hide Breakdown
                </>
              ) : (
                <>
                  <ChevronDown className="h-3.5 w-3.5" /> View Math Rationale
                </>
              )}
            </button>
          </div>

          <div className="pl-7 text-xs font-mono text-soc-text-secondary leading-relaxed">
            <p>
              ThreatWeave rejects arbitrary LLM risk scoring. The final score (
              <span className="text-accent-primary font-bold">
                {investigation.final_risk_score !== null && investigation.final_risk_score !== undefined
                  ? `${(investigation.final_risk_score * 100).toFixed(1)}%`
                  : "N/A"}
              </span>
              ) was computed deterministically by the consensus engine using the audited formula:
            </p>
            <div className="my-2 p-2.5 rounded bg-soc-surface border border-soc-border text-[11px] text-soc-text-primary font-mono overflow-x-auto">
              <code>Final Risk = Base Score (0.50) + Corroboration Bonus (0.25) + Threat Intel Bonus (0.10) - Contradiction Penalty (0.15)</code>
            </div>

            {showFormulaDetails && risk?.breakdown && (
              <div className="mt-3 overflow-x-auto">
                <table className="w-full text-left text-xs font-mono border-collapse">
                  <thead>
                    <tr className="border-b border-soc-border text-soc-text-muted uppercase text-[10px]">
                      <th className="py-2">Factor</th>
                      <th className="py-2 text-right">Value</th>
                      <th className="py-2 text-right">Weight</th>
                      <th className="py-2 text-right">Contribution</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-soc-border/60">
                    {risk.breakdown.map((b, i) => (
                      <tr key={i}>
                        <td className="py-1.5 font-medium text-soc-text-primary capitalize">
                          {b.component.replace(/_/g, " ")}
                        </td>
                        <td className="py-1.5 text-right">{b.value.toFixed(2)}</td>
                        <td className="py-1.5 text-right">{b.weight.toFixed(2)}</td>
                        <td className="py-1.5 text-right font-bold text-accent-primary">
                          {b.contribution >= 0 ? `+${b.contribution.toFixed(4)}` : b.contribution.toFixed(4)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* 5. What Should an Analyst Investigate Next? */}
        <div className="p-4 rounded-lg bg-soc-base border border-soc-border space-y-3">
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-soc-text-primary uppercase">
            <span className="flex h-5 w-5 items-center justify-center rounded bg-accent-primary/20 text-accent-primary text-[11px]">
              5
            </span>
            <span>What Should a Security Analyst Investigate Next? (SOC Playbook)</span>
          </div>

          <div className="pl-7 space-y-2.5 pt-1">
            {getAnalystNextSteps().map((step, idx) => (
              <div
                key={idx}
                className="p-3 rounded bg-soc-surface border border-soc-border/80 flex items-start justify-between gap-3"
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-display font-semibold text-xs text-soc-text-primary">
                      {step.title}
                    </span>
                    <Badge
                      variant={
                        step.priority === "Critical"
                          ? "accent"
                          : step.priority === "High"
                          ? "outline"
                          : "default"
                      }
                      className="text-[9px] uppercase font-mono py-0"
                    >
                      {step.priority} Priority
                    </Badge>
                  </div>
                  <p className="text-xs text-soc-text-secondary leading-relaxed font-mono">
                    {step.action}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
}
