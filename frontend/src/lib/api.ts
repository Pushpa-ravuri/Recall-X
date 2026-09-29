import {
  HealthStatus,
  HistoryResponse,
  Incident,
  IncidentAnalysisResponse,
  OutcomeSubmissionRequest,
  OutcomeSubmissionResponse,
  ReflectResponse,
  StatsResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
    });

    if (!response.ok) {
      let errorMessage = `Server responded with status ${response.status}`;
      try {
        const errorJson = await response.json();
        if (errorJson.detail) {
          errorMessage =
            typeof errorJson.detail === "string"
              ? errorJson.detail
              : JSON.stringify(errorJson.detail);
        }
      } catch {
        // The server response wasn't JSON; keep the generic status message.
      }
      throw new Error(errorMessage);
    }

    return (await response.json()) as T;
  } catch (error: any) {
    if (error.message && error.message.includes("Failed to fetch")) {
      throw new Error(
        `Cannot connect to RECALL-X backend at ${API_BASE}. Ensure backend is running.`,
      );
    }
    throw error;
  }
}

export function getHealth(): Promise<HealthStatus> {
  return request<HealthStatus>("/health");
}

export function analyzeIncident(
  incident: Partial<Incident>,
): Promise<IncidentAnalysisResponse> {
  return request<IncidentAnalysisResponse>("/incident", {
    method: "POST",
    body: JSON.stringify(incident),
  });
}

export function recordOutcome(
  outcome: OutcomeSubmissionRequest,
): Promise<OutcomeSubmissionResponse> {
  return request<OutcomeSubmissionResponse>("/outcome", {
    method: "POST",
    body: JSON.stringify(outcome),
  });
}

export function getOperationalStats(): Promise<StatsResponse> {
  return request<StatsResponse>("/stats");
}

export function getHistory(params?: {
  search?: string;
  machine?: string;
  problem?: string;
  result?: string;
}): Promise<HistoryResponse> {
  const query = new URLSearchParams();
  if (params?.search) query.set("search", params.search);
  if (params?.machine) query.set("machine", params.machine);
  if (params?.problem) query.set("problem", params.problem);
  if (params?.result) query.set("result", params.result);

  const queryString = query.toString();
  return request<HistoryResponse>(
    `/history${queryString ? `?${queryString}` : ""}`,
  );
}

export function reflectOnProblem(
  query: string,
  machine?: string,
): Promise<ReflectResponse> {
  return request<ReflectResponse>("/reflect", {
    method: "POST",
    body: JSON.stringify({ query, machine }),
  });
}

export function seedMemoryData(): Promise<{
  status: string;
  total_seeded: number;
  data_source: string;
  message: string;
}> {
  return request("/seed", { method: "POST" });
}
