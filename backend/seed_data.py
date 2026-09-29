import json
import logging
from pathlib import Path
from typing import Any, Dict

from memory import HindsightMemoryManager
from models import Incident, Outcome


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("recall_x.seed")

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "incidents.json"
SEED_FILE = Path(__file__).resolve().parent.parent / "data" / "seed_incidents.json"


def seed_memory(memory_manager: HindsightMemoryManager) -> Dict[str, Any]:
    """Seed Hindsight and the local store with historical manufacturing incidents."""
    source_file = SEED_FILE if SEED_FILE.exists() else DATA_FILE
    if not source_file.exists():
        raise FileNotFoundError(f"Seed file not found: {source_file}")

    with source_file.open("r", encoding="utf-8") as file:
        incidents_data = json.load(file)

    logger.info(
        "Found %d incidents to seed into RECALL-X operational memory.",
        len(incidents_data),
    )
    memory_manager._local_incidents = []
    total_seeded = 0

    for item in incidents_data:
        outcome_data = item.get("outcome")
        outcome = Outcome(**outcome_data) if outcome_data else None
        incident = Incident(
            incident_id=item.get("incident_id"),
            timestamp=item.get("timestamp"),
            machine=item.get("machine"),
            problem=item.get("problem"),
            material=item.get("material"),
            tool=item.get("tool"),
            rpm=item.get("rpm"),
            feed_rate=item.get("feed_rate"),
            temperature=item.get("temperature"),
            pressure=item.get("pressure"),
            vibration=item.get("vibration"),
            coolant_condition=item.get("coolant_condition"),
            tool_condition=item.get("tool_condition"),
            operator_observation=item.get("operator_observation"),
            outcome=outcome,
        )
        memory_manager.store_incident(incident)
        if outcome:
            memory_manager.store_outcome(outcome)
        total_seeded += 1

    source_label = memory_manager.get_data_source_label()
    logger.info(
        "Seeding complete! %d incidents processed. Memory Source: %s",
        total_seeded,
        source_label,
    )
    return {
        "status": "success",
        "total_seeded": total_seeded,
        "data_source": source_label,
        "message": f"Successfully loaded {total_seeded} operational incidents into {source_label}.",
    }


if __name__ == "__main__":
    manager = HindsightMemoryManager()
    result = seed_memory(manager)
    manager.close()
    print(json.dumps(result, indent=2))
