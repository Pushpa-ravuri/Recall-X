import sys
from pathlib import Path

from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from comparison import WhatChangedEngine
from main import app
from models import Incident


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "data_source" in data


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["system"] == "RECALL-X"


def test_what_changed_engine():
    current = Incident(
        machine="CNC-07",
        problem="Rough surface",
        material="AL-6061",
        tool="T-19",
        rpm=3200,
        feed_rate=450,
        temperature=34.0,
        vibration=0.5,
    )
    historical = [
        {
            "incident_id": "INC-HIST-01",
            "machine": "CNC-07",
            "problem": "Rough surface",
            "material": "AL-6061",
            "tool": "T-17",
            "rpm": 3200,
            "feed_rate": 450,
            "temperature": 27.0,
            "vibration": 0.35,
            "outcome": {"action": "Reduced feed rate to 410", "result": "SUCCESS"},
        }
    ]
    diffs = WhatChangedEngine.compare_incident(current, historical)
    assert len(diffs) >= 2

    tool_diff = next((item for item in diffs if item.parameter == "Tool"), None)
    assert tool_diff is not None
    assert tool_diff.previous == "T-17"
    assert tool_diff.current == "T-19"
    assert tool_diff.severity == "important"

    temperature_diff = next((item for item in diffs if item.parameter == "Temperature"), None)
    assert temperature_diff is not None
    assert temperature_diff.previous == 27.0
    assert temperature_diff.current == 34.0
    assert temperature_diff.change_pct is not None
    assert temperature_diff.change_pct > 20.0
    assert temperature_diff.severity == "important"


def test_complete_incident_and_outcome_flow():
    seed_response = client.post("/seed")
    assert seed_response.status_code == 200

    payload = {
        "machine": "CNC-07",
        "problem": "Rough surface finish",
        "material": "AL-6061",
        "tool": "T-19",
        "rpm": 3200,
        "feed_rate": 450,
        "temperature": 34.0,
        "pressure": 2.1,
        "vibration": 0.5,
        "operator_observation": "Surface quality is deteriorating again.",
    }
    response = client.post("/incident", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "incident_id" in data
    incident_id = data["incident_id"]
    assert data["historical_incidents"]
    assert data["what_changed"]
    assert data["successful_interventions"]
    assert data["failed_interventions"]
    assert "T-19" in str(data["what_changed"])
    assert data["confidence"] in ["HIGH", "MEDIUM", "LOW"]
    assert data["human_review_required"] is True

    outcome_payload = {
        "incident_id": incident_id,
        "action": "Inspected T-19 insert—replaced chipped edge and dialed feed to 410 mm/min",
        "result": "SUCCESS",
        "root_cause": "Tool T-19 had micro-edge fracture and temperature caused thermal expansion",
        "notes": "Surface roughness Ra restored to 0.72 µm.",
    }
    outcome_response = client.post("/outcome", json=outcome_payload)
    assert outcome_response.status_code == 200
    outcome_data = outcome_response.json()
    assert outcome_data["status"] == "success"
    assert outcome_data["incident_id"] == incident_id

    history_response = client.get("/history?machine=CNC-07")
    assert history_response.status_code == 200
    history_data = history_response.json()
    assert history_data["total"] > 0
    matching = next(
        (item for item in history_data["incidents"] if item["incident_id"] == incident_id),
        None,
    )
    assert matching is not None
    assert matching["outcome"]["result"] == "SUCCESS"


def test_stats_endpoint():
    response = client.get("/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_incidents"] > 0
    assert stats["historical_memories"] > 0
    assert stats["machines"]


def test_reflect_endpoint():
    response = client.post(
        "/reflect",
        json={"query": "How to resolve spindle vibration?", "machine": "CNC-12"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "reflection" in data
    assert len(data["reflection"]) > 10
