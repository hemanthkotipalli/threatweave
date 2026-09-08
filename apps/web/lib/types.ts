/**
 * apps/web/lib/types.ts
 * ---------------------
 * TypeScript interfaces mirroring the ACTUAL CURRENT backend Pydantic schemas:
 * - app/schemas/investigation.py
 * - app/schemas/evidence.py
 * - app/schemas/rag.py
 * - app/schemas/common.py
 */

export type SeverityType = "info" | "low" | "medium" | "high" | "critical";

export type AgentStatusType = "idle" | "running" | "done" | "failed" | "skipped";

export interface UserProfile {
  id: string;
  email: string;
  role: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface AuthRegisterPayload {
  email: string;
  password: string;
}

export interface AuthLoginPayload {
  email: string;
  password: string;
}


export interface EvidenceInputCompact {
  id: string;
  modality: string;
  created_at: string;
}

export interface EvidenceInputDetail {
  id: string;
  modality: string;
  raw_content_ref?: string | null;
  file_path?: string | null;
  created_at: string;
}

export interface EvidenceItem {
  agent: string;
  modality: string;
  finding: string;
  confidence: number;
  severity: SeverityType;
  indicators: string[];
  evidence: Record<string, unknown>;
  reasoning: string;
  external_refs: string[];
  timestamp: string;
  status: "ok" | "degraded_fallback" | "failed" | "skipped";
}

export interface AgentFindingDetail {
  id: string;
  agent_run_id: string;
  finding: string;
  confidence: number;
  severity: SeverityType;
  indicators: string[] | Record<string, unknown>;
  evidence: Record<string, unknown>;
  reasoning: string;
  external_refs: unknown[] | Record<string, unknown>;
  status: string;
  timestamp: string;
}

export interface AgentRunDetail {
  id: string;
  agent_name: string;
  status: string;
  started_at?: string | null;
  finished_at?: string | null;
  latency_ms?: number | null;
  findings: AgentFindingDetail[];
}

export interface RiskBreakdownItem {
  component: "base_score" | "corroboration_bonus" | "intel_bonus" | "contradiction_penalty" | string;
  value: number;
  weight: number;
  contribution: number;
}

export interface ConflictLog {
  id: string;
  agent_a: string;
  agent_b: string;
  conflict_type: string;
  resolution_rule: string;
  resolution_outcome: string;
}

export interface RiskDetail {
  score?: number | null;
  severity?: SeverityType | string | null;
  confidence?: number | null;
  low_confidence: boolean;
  breakdown: RiskBreakdownItem[];
  conflicts: ConflictLog[];
}

export interface RagCitation {
  id?: string | null;
  source_title: string;
  source_type: "CERT-In" | "RBI" | "Scam-Intel" | string;
  chunk_text: string;
  similarity_score: number;
  url?: string | null;
  category?: string | null;
}

export interface InvestigationInfo {
  id: string;
  title: string;
  status: "pending" | "running" | "completed" | "failed" | string;
  created_at: string;
}

export interface InvestigationCreateResponse {
  investigation: InvestigationInfo;
  evidence_inputs: EvidenceInputCompact[];
}

export interface InvestigationDetail {
  id: string;
  title: string;
  status: "pending" | "running" | "completed" | "failed" | string;
  created_at: string;
  final_risk_score?: number | null;
  final_severity?: SeverityType | string | null;
  final_confidence?: number | null;
  evidence_inputs: EvidenceInputDetail[];
  agent_runs: AgentRunDetail[];
  rag_citations: RagCitation[];
  risk?: RiskDetail | null;
}

export interface InvestigationListItem {
  id: string;
  title: string;
  status: string;
  created_at: string;
  final_risk_score?: number | null;
  final_severity?: SeverityType | string | null;
  modalities?: string[];
}

export interface InvestigationFilterParams {
  status?: string;
  severity?: string;
  date_from?: string;
  date_to?: string;
}

export interface ReportFinding {
  id: string;
  agent_name: string;
  finding: string;
  confidence: number;
  severity: SeverityType | string;
  indicators: string[] | Record<string, unknown>;
  evidence: Record<string, unknown>;
  reasoning: string;
  external_refs: unknown[];
  status: string;
  timestamp?: string | null;
}

export interface InvestigationReportData {
  report_id: string;
  generated_at: string;
  format: string;
  investigation: {
    id: string;
    title: string;
    status: string;
    created_at?: string | null;
    completed_at?: string | null;
    final_risk_score?: number | null;
    final_severity?: SeverityType | string | null;
    final_confidence?: number | null;
  };
  evidence_inputs: EvidenceInputDetail[];
  agent_runs: AgentRunDetail[];
  findings: ReportFinding[];
  risk?: RiskDetail | null;
  rag_citations: RagCitation[];
  conflict_logs: ConflictLog[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface RagSearchResponse {
  query: string;
  threshold: number;
  total_results: number;
  results: RagCitation[];
}

export interface DemoScenario {
  key: string;
  title: string;
  description: string;
  modalities: string[];
}

export interface DemoRunResponse {
  investigation_id: string;
  scenario_key: string;
  mode: string;
  status: string;
  final_risk_score?: number | null;
  final_severity?: SeverityType | string | null;
  final_confidence?: number | null;
  risk?: RiskDetail | Record<string, unknown> | null;
}


