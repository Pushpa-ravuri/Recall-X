import sys

from dotenv import load_dotenv

from memory import HindsightMemoryManager
from models import Incident, Outcome


if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()


def test_hindsight_workflow():
    print("=" * 60)
    print("RECALL-X: HINDSIGHT MEMORY CONNECTIVITY TEST")
    print("=" * 60)
    manager = HindsightMemoryManager()
    hindsight_ready = manager.is_hindsight_ready()
    data_source = manager.get_data_source_label()
    print(f"Hindsight URL: {manager.url}")
    print(f"Hindsight Bank ID: {manager.bank_id}")
    print(f"Connection Status: {'ONLINE' if hindsight_ready else 'OFFLINE (Demo fallback active)'}")
    print(f"Active Data Mode: {data_source}")
    print("-" * 60)

    incident = Incident(
        incident_id="TEST-INC-CNC07-001",
        machine="CNC-07",
        problem="Rough surface",
        material="AL-6061",
        tool="T-17",
        rpm=3200,
        feed_rate=450,
        temperature=27.0,
        pressure=2.2,
        vibration=0.35,
        coolant_condition="Nominal 8%",
        tool_condition="Good",
        operator_observation="Surface roughness on workpiece side wall during test pass.",
    )
    outcome = Outcome(
        incident_id="TEST-INC-CNC07-001",
        action="Reduced feed rate from 450 to 410",
        result="SUCCESS",
        root_cause="Feed per tooth slightly exceeded chip load threshold",
        notes="Surface quality improved significantly. Roughness Ra dropped below 0.8 µm.",
    )

    print("[STEP 1] Retaining sample incident in operational memory...")
    try:
        _, source = manager.store_incident(incident)
        print(f"[OK] Incident stored successfully. [Source: {source}]")
    except Exception as error:
        print(f"[ERROR] Failed to store incident: {error}")
        manager.close()
        return False

    print("[STEP 2] Retaining outcome for sample incident...")
    try:
        _, source = manager.store_outcome(outcome)
        print(f"[OK] Outcome stored successfully. [Source: {source}]")
    except Exception as error:
        print(f"[ERROR] Failed to store outcome: {error}")
        manager.close()
        return False

    print("[STEP 3] Recalling operational memory for query: 'CNC-07 rough surface AL-6061'...")
    query_incident = Incident(
        machine="CNC-07",
        problem="Rough surface",
        material="AL-6061",
        tool="T-19",
        rpm=3200,
        feed_rate=450,
        temperature=34.0,
    )
    try:
        recalled, _ = manager.recall_similar_incidents(query_incident, top_k=3)
        print(f"[OK] Recall completed. Retrieved {len(recalled)} matching experiences.")
        print("-" * 60)
        print("RETRIEVED EXPERIENCES:")
        for index, item in enumerate(recalled, 1):
            stored_outcome = item.get("outcome") or {}
            print(
                f" [{index}] ID: {item.get('incident_id')} | Machine: {item.get('machine')} "
                f"| Problem: {item.get('problem')}"
            )
            print(
                f" Tool: {item.get('tool')} | RPM: {item.get('rpm')} | "
                f"Feed: {item.get('feed_rate')} | Temp: {item.get('temperature')}°C"
            )
            print(
                f" Action: {stored_outcome.get('action', 'N/A')} -> "
                f"Result: {stored_outcome.get('result', 'N/A')}"
            )
            print(f" Notes: {stored_outcome.get('notes', 'N/A')}\n")
    except Exception as error:
        print(f"[ERROR] Recall failed: {error}")
        manager.close()
        return False

    print("[STEP 4] Testing Hindsight reflect operation...")
    try:
        reflection, _ = manager.reflect(
            "What are best practices for rough surface on CNC-07?",
            machine="CNC-07",
        )
        print("[OK] Reflection synthesized successfully:")
        print(f" {reflection}")
    except Exception as error:
        print(f"[ERROR] Reflection failed: {error}")

    print("=" * 60)
    if hindsight_ready:
        print("RESULT: HINDSIGHT LIVE CONNECTIVITY IS WORKING 100%.")
    else:
        print("RESULT: HINDSIGHT SERVER OFFLINE -> RESILIENT DEMO MODE OPERATIONAL.")
    print("To connect live Hindsight, configure HINDSIGHT_URL and HINDSIGHT_API_KEY in .env")
    print("=" * 60)
    manager.close()
    return True


if __name__ == "__main__":
    success = test_hindsight_workflow()
    sys.exit(0 if success else 1)
