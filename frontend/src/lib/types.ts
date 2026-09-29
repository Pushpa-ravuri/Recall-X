export type ResultType = "SUCCESS" | "FAILED" | "PARTIAL" | "UNKNOWN";
export type SeverityType = "important" | "moderate" | "minor" | "neutral";
export type ConfidenceType = "HIGH" | "MEDIUM" | "LOW"; export interface Outcome { incident_id: string; action: string; result: ResultType; root_cause?: string; notes?: string; timestamp?: string;
} export interface Incident { incident_id?: string; machine: string; problem: string; material?: string; tool?: string; rpm?: number; feed_rate?: number; temperature?: number; pressure?: number; vibration?: number; coolant_condition?: string; tool_condition?: string; operator_observation?: string; timestamp?: string; outcome?: Outcome;
} export interface WhatChangedItem { parameter: string; previous: string | number; current: string | number; unit?: string; change_pct?: number; severity: SeverityType; note?: string;
} export interface IncidentAnalysisResponse { incident_id: string; incident: Incident; memory_count: number; historical_incidents: Incident[]; what_changed: WhatChangedItem[]; successful_interventions: string[]; failed_interventions: string[]; recommendation: string; reasoning: string; evidence: string[]; confidence: ConfidenceType; warning?: string; human_review_required: boolean; data_source: string;
} export interface OutcomeSubmissionRequest { incident_id: string; action: string; result: ResultType; root_cause?: string; notes?: string;
} export interface OutcomeSubmissionResponse { status: string; message: string; incident_id: string; stored_in_hindsight: boolean; data_source: string; timestamp: string;
} export interface MachineStat { machine: string; count: number;
} export interface ProblemStat { problem: string; count: number;
} export interface StatsResponse { total_incidents: number; historical_memories: number; successful_interventions: number; failed_interventions: number; recurring_problems: number; success_rate: number; data_source: string; machines: MachineStat[]; common_problems: ProblemStat[]; recent_experiences: Incident[];
} export interface HistoryResponse { total: number; data_source: string; incidents: Incident[];
} export interface ReflectResponse { query: string; reflection: string; data_source: string; timestamp: string;
} export interface HealthStatus { status: string; hindsight_connected: boolean; groq_connected: boolean; data_source: string; demo_mode: boolean;
} export interface DemoPreset { id: string; title: string; subtitle: string; tag: string; incident: Partial<Incident>; contextNote: string;
}
