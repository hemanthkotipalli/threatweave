/**
 * apps/web/components/analytics/types.ts
 * --------------------------------------
 * Types and interfaces for ThreatWeave interactive analytics and visualization.
 */

export interface SeverityDistributionData {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
  pending: number;
  total: number;
}

export interface ModalityThreatData {
  modality: "text" | "url" | "qr" | "image" | "voice" | "cross_modal";
  label: string;
  total: number;
  malicious: number; // high or critical
  benign: number; // medium, low, info
  pending: number;
  avgRiskScore: number;
}

export interface TimelineBucket {
  dateKey: string; // "YYYY-MM-DD" or formatted label
  displayDate: string;
  total: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
}

export interface CorrelationCell {
  modalityA: string;
  modalityB: string;
  coOccurrenceCount: number;
  avgCombinedRisk: number;
}

export interface AgentPerformanceData {
  agentName: string;
  label: string;
  runsCount: number;
  detectionRate: number; // % of runs that identified threats
  avgLatencyMs?: number;
  status: "operational" | "degraded" | "offline";
}

export interface BenchmarkMetrics {
  total: number;
  tp: number;
  fp: number;
  tn: number;
  fn: number;
  precision: number;
  recall: number;
  f1: number;
  accuracy: number;
  avgLatencyMs: number;
}

export interface ModalityBenchmarkComparison {
  modality: string;
  label: string;
  llmMode: BenchmarkMetrics;
  heuristicMode: BenchmarkMetrics;
  baselineRecall: number;
  baselineF1: number;
}
