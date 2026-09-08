/**
 * apps/web/lib/api.ts
 * -------------------
 * Typed HTTP client functions for ThreatWeave API communication.
 */
import { getAuthHeaders } from "./auth";
import {
  DemoRunResponse,
  DemoScenario,
  InvestigationCreateResponse,
  InvestigationDetail,
  InvestigationFilterParams,
  InvestigationListItem,
  InvestigationReportData,
  PaginatedResponse,
  RagSearchResponse,
} from "./types";



const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  code?: string;
  details?: unknown;

  constructor(message: string, status: number, code?: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
  let response: Response;

  try {
    response = await fetch(url, options);
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : "Network request failed";
    throw new ApiError(
      `Unable to reach ThreatWeave API service at ${API_BASE_URL}. ${errorMsg}`,
      0,
      "NETWORK_ERROR"
    );
  }

  if (!response.ok) {
    let errorData: { error?: { message?: string; code?: string; details?: unknown }; detail?: string } = {};
    try {
      errorData = await response.json();
    } catch {
      // Body was not JSON
    }

    const message =
      errorData.error?.message ||
      (typeof errorData.detail === "string" ? errorData.detail : null) ||
      `HTTP request error: ${response.status} ${response.statusText}`;

    const code = errorData.error?.code || `HTTP_${response.status}`;
    const details = errorData.error?.details || errorData.detail;

    throw new ApiError(message, response.status, code, details);
  }

  return response.json() as Promise<T>;
}

/**
 * Creates a new threat investigation with multimodal evidence inputs (multipart/form-data).
 * Requires user authentication via Bearer token.
 */
export async function createInvestigation(formData: FormData): Promise<InvestigationCreateResponse> {
  return request<InvestigationCreateResponse>("/api/v1/investigations", {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
    },
    body: formData,
  });
}

/**
 * Initiates swarm analysis on an existing investigation.
 * Requires user authentication via Bearer token.
 */
export async function analyzeInvestigation(id: string): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>(`/api/v1/investigations/${id}/analyze`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
    },
  });
}


/**
 * Retrieves full investigation details, evidence sources, runs, citations, and risk scores.
 */
export async function getInvestigation(id: string): Promise<InvestigationDetail> {
  return request<InvestigationDetail>(`/api/v1/investigations/${id}`, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
  });
}

/**
 * Lists investigations with pagination and optional filtering by status, severity, and date range.
 */
export async function listInvestigations(
  page: number = 1,
  pageSize: number = 10,
  filters?: InvestigationFilterParams
): Promise<PaginatedResponse<InvestigationListItem>> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });

  if (filters?.status && filters.status !== "all") {
    params.set("status", filters.status);
  }
  if (filters?.severity && filters.severity !== "all") {
    params.set("severity", filters.severity);
  }
  if (filters?.date_from) {
    params.set("date_from", filters.date_from);
  }
  if (filters?.date_to) {
    params.set("date_to", filters.date_to);
  }

  return request<PaginatedResponse<InvestigationListItem>>(`/api/v1/investigations?${params.toString()}`, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
  });
}

/**
 * Retrieves a full structured report payload for an investigation on demand.
 */
export async function getInvestigationReport(id: string): Promise<InvestigationReportData> {
  return request<InvestigationReportData>(`/api/v1/investigations/${id}/report`, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
  });
}


/**
 * Queries ChromaDB threat advisory knowledge base with strict threshold filtering.
 */
export async function searchRag(
  query: string,
  topK: number = 5,
  threshold?: number
): Promise<RagSearchResponse> {
  const params = new URLSearchParams({
    q: query,
    top_k: String(topK),
  });
  if (threshold !== undefined) {
    params.set("threshold", String(threshold));
  }
  return request<RagSearchResponse>(`/api/v1/rag/search?${params.toString()}`, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
  });
}

/**
 * Lists all curated Demo Mode scenarios.
 */
export async function getDemoScenarios(): Promise<DemoScenario[]> {
  return request<DemoScenario[]>("/api/v1/demo/scenarios", {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
  });
}

/**
 * Runs a curated demo scenario end-to-end through the genuine pipeline.
 */
export async function runDemoScenario(key: string, mode: string = "combined"): Promise<DemoRunResponse> {
  const params = new URLSearchParams();
  if (mode && mode !== "combined") {
    params.set("mode", mode);
  }
  const queryStr = params.toString() ? `?${params.toString()}` : "";
  return request<DemoRunResponse>(`/api/v1/demo/scenarios/${key}/run${queryStr}`, {
    method: "POST",
    headers: {
      Accept: "application/json",
    },
  });
}

