from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


def current_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Outcome(BaseModel):
    incident_id: str
    action: str
    result: Literal["SUCCESS", "FAILED", "PARTIAL", "UNKNOWN"]
    root_cause: Optional[str] = None
    notes: Optional[str] = None
    timestamp: Optional[str] = Field(default_factory=current_utc_iso)


class Incident(BaseModel):
    incident_id: Optional[str] = None
    machine: str
    problem: str
    material: Optional[str] = None
    tool: Optional[str] = None
    rpm: Optional[float] = None
    feed_rate: Optional[float] = None
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    vibration: Optional[float] = None
    coolant_condition: Optional[str] = None
    tool_condition: Optional[str] = None
    operator_observation: Optional[str] = None
    timestamp: Optional[str] = Field(default_factory=current_utc_iso)
    outcome: Optional[Outcome] = None


class WhatChangedItem(BaseModel):
    parameter: str
    previous: Any
    current: Any
    unit: Optional[str] = None
    change_pct: Optional[float] = None
    severity: Literal["important", "moderate", "minor", "neutral"] = "neutral"
    note: Optional[str] = None


class HistoricalMatch(BaseModel):
    incident_id: str
    machine: str
    problem: str
    material: Optional[str] = None
    tool: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    intervention: Optional[str] = None
    outcome: Optional[str] = None
    root_cause: Optional[str] = None
    similarity_score: float = 0.0
    key_takeaway: Optional[str] = None


class AgentReasoningOutput(BaseModel):
    summary: str
    similar_incidents: List[str] = Field(default_factory=list)
    successful_interventions: List[str] = Field(default_factory=list)
    failed_interventions: List[str] = Field(default_factory=list)
    important_differences: List[str] = Field(default_factory=list)
    likely_factors: List[str] = Field(default_factory=list)
    recommendation: str
    reasoning: str
    evidence: List[str] = Field(default_factory=list)
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"
    warning: Optional[str] = None
    human_review_required: bool = True


class IncidentAnalysisResponse(BaseModel):
    incident_id: str
    incident: Incident
    memory_count: int
    historical_incidents: List[Dict[str, Any]]
    what_changed: List[WhatChangedItem]
    successful_interventions: List[str]
    failed_interventions: List[str]
    recommendation: str
    reasoning: str
    evidence: List[str]
    confidence: str
    warning: Optional[str] = None
    human_review_required: bool = True
    data_source: str = "Hindsight Memory Bank"


class OutcomeSubmissionRequest(BaseModel):
    incident_id: str
    action: str
    result: Literal["SUCCESS", "FAILED", "PARTIAL", "UNKNOWN"]
    root_cause: Optional[str] = None
    notes: Optional[str] = None


class OutcomeSubmissionResponse(BaseModel):
    status: str
    message: str
    incident_id: str
    stored_in_hindsight: bool
    data_source: str
    timestamp: str


class SeedResponse(BaseModel):
    status: str
    total_seeded: int
    data_source: str
    message: str


class ReflectRequest(BaseModel):
    query: str
    machine: Optional[str] = None


class ReflectResponse(BaseModel):
    query: str
    reflection: str
    data_source: str
    timestamp: str


class StatsResponse(BaseModel):
    total_incidents: int
    historical_memories: int
    successful_interventions: int
    failed_interventions: int
    recurring_problems: int
    success_rate: float
    data_source: str
    machines: List[Dict[str, Any]]
    common_problems: List[Dict[str, Any]]
    recent_experiences: List[Dict[str, Any]]
