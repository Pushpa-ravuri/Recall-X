import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

backend_dir = str(Path(__file__).resolve().parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from agent import RecallXAgent
from comparison import WhatChangedEngine
from memory import HindsightMemoryManager
from models import (
    Incident,
    IncidentAnalysisResponse,
    Outcome,
    OutcomeSubmissionRequest,
    OutcomeSubmissionResponse,
    ReflectRequest,
    ReflectResponse,
    SeedResponse,
    StatsResponse,
    current_utc_iso,
)
from seed_data import seed_memory


load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("recall_x.api")

_memory_manager: Optional[HindsightMemoryManager] = None
_agent: Optional[RecallXAgent] = None


def get_memory_manager() -> HindsightMemoryManager:
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = HindsightMemoryManager()
        if not _memory_manager.get_all_incidents():
            logger.info("Local memory empty. Auto-seeding initial operational scenarios...")
            seed_memory(_memory_manager)
    return _memory_manager


def get_agent() -> RecallXAgent:
    global _agent
    if _agent is None:
        _agent = RecallXAgent()
    return _agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing RECALL-X Backend services...")
    get_memory_manager()
    get_agent()
    yield
    logger.info("Shutting down RECALL-X Backend services.")
    if _memory_manager:
        _memory_manager.close()


app = FastAPI(
    title="RECALL-X API",
    description="Operational Experience Memory System for Manufacturing Decision Support",
    version="1.0.0",
    lifespan=lifespan,
)

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
allowed_origins = [
    frontend_url.rstrip("/"),
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["System"])
def root():
    manager = get_memory_manager()
    return {
        "system": "RECALL-X",
        "description": "AI Agent for Recovering Lost Operational Knowledge",
        "mode": "Decision-Support (Human Review Required)",
        "memory_backend": manager.get_data_source_label(),
        "version": "1.0.0",
    }


@app.get("/health", tags=["System"])
def health():
    manager = get_memory_manager()
    agent = get_agent()
    return {
        "status": "healthy",
        "hindsight_connected": manager.is_hindsight_ready(),
        "groq_connected": bool(agent.client),
        "data_source": manager.get_data_source_label(),
        "demo_mode": manager.demo_mode,
    }


@app.post("/incident", response_model=IncidentAnalysisResponse, tags=["Incidents"])
def analyze_incident(incident: Incident):
    """Retrieve similar experience, compare conditions, and return a recommendation."""
    manager = get_memory_manager()
    agent = get_agent()
    try:
        manager.store_incident(incident)
        historical, data_source = manager.recall_similar_incidents(incident, top_k=5)
        what_changed = WhatChangedEngine.compare_incident(incident, historical)
        reasoning = agent.analyze(incident, historical, what_changed)
        return IncidentAnalysisResponse(
            incident_id=incident.incident_id,
            incident=incident,
            memory_count=len(historical),
            historical_incidents=historical,
            what_changed=what_changed,
            successful_interventions=reasoning.successful_interventions,
            failed_interventions=reasoning.failed_interventions,
            recommendation=reasoning.recommendation,
            reasoning=reasoning.reasoning,
            evidence=reasoning.evidence,
            confidence=reasoning.confidence,
            warning=reasoning.warning,
            human_review_required=True,
            data_source=data_source,
        )
    except RuntimeError as error:
        logger.error("Runtime error during incident analysis: %s", error)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except Exception as error:
        logger.exception("Unexpected error analyzing incident")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze incident: {error}",
        ) from error


@app.post("/outcome", response_model=OutcomeSubmissionResponse, tags=["Outcome Learning"])
def record_outcome(submission: OutcomeSubmissionRequest):
    """Persist an operator's intervention outcome."""
    manager = get_memory_manager()
    outcome = Outcome(
        incident_id=submission.incident_id,
        action=submission.action,
        result=submission.result,
        root_cause=submission.root_cause,
        notes=submission.notes,
    )
    try:
        _, data_source = manager.store_outcome(outcome)
        return OutcomeSubmissionResponse(
            status="success",
            message=f"Intervention outcome for {submission.incident_id} successfully retained in {data_source}.",
            incident_id=submission.incident_id,
            stored_in_hindsight=manager.is_hindsight_ready(),
            data_source=data_source,
            timestamp=outcome.timestamp,
        )
    except Exception as error:
        logger.exception("Error storing outcome")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error


@app.post("/seed", response_model=SeedResponse, tags=["Admin"])
def seed_data():
    """Reload the historical incident dataset."""
    try:
        return SeedResponse(**seed_memory(get_memory_manager()))
    except Exception as error:
        logger.exception("Error during seeding")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error


@app.get("/incident/{incident_id}", tags=["Incidents"])
def get_incident(incident_id: str):
    """Retrieve a stored incident by ID."""
    incident = get_memory_manager().get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )
    return incident


@app.get("/history", tags=["History"])
def get_history(
    search: Optional[str] = Query(None, description="Search machine, problem, or notes"),
    machine: Optional[str] = Query(None, description="Filter by machine ID"),
    problem: Optional[str] = Query(None, description="Filter by problem"),
    result: Optional[str] = Query(None, description="Filter by outcome result"),
):
    """Return historical experiences with optional filters."""
    manager = get_memory_manager()
    filtered = []
    for item in manager.get_all_incidents():
        if machine and item.get("machine", "").lower() != machine.lower():
            continue
        if problem and problem.lower() not in item.get("problem", "").lower():
            continue
        outcome = item.get("outcome") or {}
        if result and outcome.get("result", "").upper() != result.upper():
            continue
        if search:
            corpus = (
                f"{item.get('incident_id', '')} {item.get('machine', '')} {item.get('problem', '')} "
                f"{item.get('material', '')} {item.get('tool', '')} {item.get('operator_observation', '')} "
                f"{outcome.get('action', '')} {outcome.get('root_cause', '')} {outcome.get('notes', '')}"
            ).lower()
            if search.lower() not in corpus:
                continue
        filtered.append(item)
    return {
        "total": len(filtered),
        "data_source": manager.get_data_source_label(),
        "incidents": filtered,
    }


@app.post("/reflect", response_model=ReflectResponse, tags=["Reflection"])
def reflect_on_experience(request: ReflectRequest):
    """Synthesize insights from accumulated operational memory."""
    reflection, data_source = get_memory_manager().reflect(request.query, request.machine)
    return ReflectResponse(
        query=request.query,
        reflection=reflection,
        data_source=data_source,
        timestamp=current_utc_iso(),
    )


@app.get("/stats", response_model=StatsResponse, tags=["Analytics"])
def get_operational_stats():
    """Return operational metrics from stored experience."""
    return StatsResponse(**get_memory_manager().get_stats())
