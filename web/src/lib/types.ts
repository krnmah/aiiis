export type HealthResponse = {
  status: string;
};

export type DbHealthResponse = {
  status: string;
  database: string;
};

export type SimilarLogItem = {
  id: number;
  service_name: string;
  level: "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL" | string;
  message: string;
  trace_id: string | null;
  timestamp: string;
  similarity_score: number;
};

export type SimilarLogsResponse = {
  query: string;
  total: number;
  results: SimilarLogItem[];
};

export type LogCreateRequest = {
  service_name: string;
  level: "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL";
  message: string;
  trace_id?: string | null;
  timestamp?: string | null;
};

export type LogCreateResponse = {
  id: number;
  service_name: string;
  level: string;
  message: string;
  trace_id: string | null;
  timestamp: string;
};

export type LogDetailResponse = {
  id: number;
  service_name: string;
  level: string;
  message: string;
  trace_id: string | null;
  timestamp: string;
};

export type IncidentAnalyzeResponse = {
  query: string;
  root_cause: string;
  analyzed_log_ids: number[];
  analyzed_log_count: number;
};

