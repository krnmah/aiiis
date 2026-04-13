import {
  DbHealthResponse,
  HealthResponse,
  IncidentAnalyzeResponse,
  LogCreateRequest,
  LogCreateResponse,
  LogDetailResponse,
  SimilarLogsResponse,
} from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const hasBody = init?.body !== undefined;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(hasBody ? { "Content-Type": "application/json" } : {}),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export function getDbHealth(): Promise<DbHealthResponse> {
  return request<DbHealthResponse>("/health/db");
}

export function getSimilarLogs(
  query: string,
  topK: number,
): Promise<SimilarLogsResponse> {
  const params = new URLSearchParams({
    query,
    top_k: String(topK),
  });

  return request<SimilarLogsResponse>(`/logs/similar?${params.toString()}`);
}

export function analyzeIncident(
  query: string,
  topK: number,
): Promise<IncidentAnalyzeResponse> {
  return request<IncidentAnalyzeResponse>("/incidents", {
    method: "POST",
    body: JSON.stringify({ query, top_k: topK }),
  });
}

export function createLog(payload: LogCreateRequest): Promise<LogCreateResponse> {
  return request<LogCreateResponse>("/logs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getLogDetail(logId: number): Promise<LogDetailResponse> {
  return request<LogDetailResponse>(`/logs/${logId}`);
}
