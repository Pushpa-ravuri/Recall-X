import concurrent.futures
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

from models import Incident, Outcome


load_dotenv()
logger = logging.getLogger("recall_x.memory")


def _run_in_isolated_thread(func, *args, **kwargs):
    """Run a blocking SDK call in a worker thread."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(func, *args, **kwargs).result()


HINDSIGHT_URL = os.getenv("HINDSIGHT_URL", "http://localhost:8888")
HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY", "")
HINDSIGHT_BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "recall-x")
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")
DEFAULT_DATA_FILE_PATH = Path(__file__).resolve().parent.parent / "data" / "incidents.json"
DATA_FILE_PATH = Path(
    os.getenv("RECALL_X_DATA_FILE", str(DEFAULT_DATA_FILE_PATH))
).expanduser()
if not DATA_FILE_PATH.is_absolute():
    DATA_FILE_PATH = Path(__file__).resolve().parent.parent / DATA_FILE_PATH


class HindsightMemoryManager:
    """Persist and recall operational experiences with a local demo fallback."""

    def __init__(self):
        self.bank_id = HINDSIGHT_BANK_ID
        self.url = HINDSIGHT_URL
        self.api_key = HINDSIGHT_API_KEY
        self.demo_mode = DEMO_MODE
        self.client = None
        self.hindsight_available = False
        self._local_incidents: List[Dict[str, Any]] = []
        self._load_local_data()
        self._init_hindsight_client()

    def _init_hindsight_client(self):
        """Initialize the Hindsight client and make a lightweight connectivity check."""
        try:
            from hindsight_client import Hindsight

            kwargs = {"base_url": self.url}
            if self.api_key:
                kwargs["api_key"] = self.api_key
            self.client = Hindsight(**kwargs)
            try:
                _run_in_isolated_thread(
                    self.client.recall,
                    bank_id=self.bank_id,
                    query="ping test",
                )
                self.hindsight_available = True
                logger.info(
                    "Connected successfully to Hindsight at %s (Bank: %s)",
                    self.url,
                    self.bank_id,
                )
            except Exception as error:
                self.hindsight_available = False
                logger.warning("Hindsight server at %s not responding: %s", self.url, error)
        except ImportError:
            logger.warning("hindsight-client library not installed.")
            self.hindsight_available = False
        except Exception as error:
            logger.warning("Error initializing Hindsight client: %s", error)
            self.hindsight_available = False

    def _load_local_data(self):
        """Load fallback records from the local incidents JSON file."""
        if not DATA_FILE_PATH.exists():
            self._local_incidents = []
            return
        try:
            with DATA_FILE_PATH.open("r", encoding="utf-8") as file:
                self._local_incidents = json.load(file)
        except Exception as error:
            logger.error("Failed to load local incidents file: %s", error)
            self._local_incidents = []

    def _save_local_data(self):
        """Save local incidents for persistent demo-mode state."""
        try:
            DATA_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with DATA_FILE_PATH.open("w", encoding="utf-8") as file:
                json.dump(self._local_incidents, file, indent=2)
        except Exception as error:
            logger.error("Failed to save local data file: %s", error)

    def is_hindsight_ready(self) -> bool:
        return self.hindsight_available

    def get_data_source_label(self) -> str:
        if self.hindsight_available:
            return f"Hindsight Memory Bank ({self.bank_id})"
        if self.demo_mode:
            return "DEMO DATA - Hindsight unavailable"
        return "ERROR - Hindsight unavailable"

    def store_incident(self, incident: Incident) -> Tuple[bool, str]:
        """Store an incident in Hindsight when available and in local storage."""
        if not incident.incident_id:
            incident.incident_id = f"INC-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

        memory_content = (
            f"Manufacturing Operational Incident ID: {incident.incident_id}\n"
            f"Timestamp: {incident.timestamp}\n"
            f"Machine: {incident.machine}\n"
            f"Problem Symptom: {incident.problem}\n"
            f"Workpiece Material: {incident.material or 'N/A'}\n"
            f"Tool Specification: {incident.tool or 'N/A'}\n"
            f"Cutting Parameters -> Spindle Speed: {incident.rpm} RPM | Feed Rate: {incident.feed_rate} mm/min | "
            f"Temperature: {incident.temperature}°C | Pressure: {incident.pressure} bar | Vibration: {incident.vibration} mm/s RMS\n"
            f"Coolant State: {incident.coolant_condition or 'Nominal'}\n"
            f"Tool Physical Condition: {incident.tool_condition or 'Nominal'}\n"
            f"Operator Direct Observation: {incident.operator_observation or 'None logged'}\n"
        )
        if self.client and self.hindsight_available:
            try:
                _run_in_isolated_thread(
                    self.client.retain,
                    bank_id=self.bank_id,
                    content=memory_content,
                )
                logger.info("Successfully retained incident %s in Hindsight", incident.incident_id)
            except Exception as error:
                logger.error("Failed to retain incident in Hindsight: %s", error)
                if not self.demo_mode:
                    raise RuntimeError(f"Hindsight memory service unavailable: {error}") from error

        incident_data = incident.model_dump()
        index = next(
            (
                i
                for i, item in enumerate(self._local_incidents)
                if item.get("incident_id") == incident.incident_id
            ),
            None,
        )
        if index is None:
            self._local_incidents.insert(0, incident_data)
        else:
            self._local_incidents[index] = incident_data
        self._save_local_data()
        return True, self.get_data_source_label()

    def store_outcome(self, outcome: Outcome) -> Tuple[bool, str]:
        """Store a human intervention outcome and attach it to its incident."""
        matching = next(
            (item for item in self._local_incidents if item.get("incident_id") == outcome.incident_id),
            None,
        )
        machine = matching.get("machine", "Unknown Machine") if matching else "Unknown Machine"
        problem = matching.get("problem", "Unknown Problem") if matching else "Unknown Problem"
        memory_content = (
            f"Operational Experience Outcome for Incident {outcome.incident_id}:\n"
            f"Machine: {machine}\n"
            f"Problem: {problem}\n"
            f"Intervention Action Attempted: {outcome.action}\n"
            f"Result: {outcome.result}\n"
            f"Root Cause Discovered: {outcome.root_cause or 'N/A'}\n"
            f"Operational Lessons & Engineering Notes: {outcome.notes or 'None'}\n"
            f"Timestamp: {outcome.timestamp}\n"
        )
        if self.client and self.hindsight_available:
            try:
                _run_in_isolated_thread(
                    self.client.retain,
                    bank_id=self.bank_id,
                    content=memory_content,
                )
                logger.info("Successfully retained outcome for %s in Hindsight", outcome.incident_id)
            except Exception as error:
                logger.error("Failed to retain outcome in Hindsight: %s", error)
                if not self.demo_mode:
                    raise RuntimeError(f"Hindsight memory service unavailable: {error}") from error

        for item in self._local_incidents:
            if item.get("incident_id") == outcome.incident_id:
                item["outcome"] = outcome.model_dump()
                break
        self._save_local_data()
        return True, self.get_data_source_label()

    def recall_similar_incidents(
        self, incident: Incident, top_k: int = 5
    ) -> Tuple[List[Dict[str, Any]], str]:
        """Recall and locally rank historical incidents relevant to the current incident."""
        if not self.hindsight_available and not self.demo_mode:
            raise RuntimeError("Hindsight server unavailable. Historical recall could not be completed.")

        query_parts = [f"Machine: {incident.machine}", f"Problem symptom: {incident.problem}"]
        for label, value in [
            ("Material", incident.material),
            ("Tool", incident.tool),
            ("RPM", incident.rpm),
            ("Feed rate", incident.feed_rate),
            ("Temperature", f"{incident.temperature}°C" if incident.temperature else None),
            ("Observation", incident.operator_observation),
        ]:
            if value:
                query_parts.append(f"{label}: {value}")
        semantic_query = " | ".join(query_parts)

        if self.client and self.hindsight_available:
            try:
                recalled = _run_in_isolated_thread(
                    self.client.recall,
                    bank_id=self.bank_id,
                    query=semantic_query,
                )
                logger.info("Hindsight recall returned results: %s", recalled)
            except Exception as error:
                logger.error("Hindsight recall call failed: %s", error)
                if not self.demo_mode:
                    raise RuntimeError(f"Hindsight recall error: {error}") from error

        ranked = self._rank_local_incidents(incident, top_k=top_k)
        return ranked, self.get_data_source_label()

    def _rank_local_incidents(
        self, incident: Incident, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Rank local records by machine, symptom, material, tool, and parameter similarity."""
        candidates = []
        for historical in self._local_incidents:
            if historical.get("incident_id") == incident.incident_id:
                continue
            outcome = historical.get("outcome") or {}
            if not outcome.get("result"):
                continue

            score = 0.0
            hist_machine = str(historical.get("machine", ""))
            current_machine = incident.machine
            if hist_machine.strip().lower() == current_machine.strip().lower():
                score += 30.0
            elif hist_machine[:3].lower() == current_machine[:3].lower():
                score += 15.0

            hist_problem = str(historical.get("problem", "")).strip().lower()
            current_problem = incident.problem.strip().lower()
            if hist_problem == current_problem:
                score += 35.0
            elif any(word in hist_problem for word in current_problem.split()):
                score += 20.0

            hist_material = str(historical.get("material") or "")
            if incident.material and hist_material:
                if hist_material.strip().lower() == incident.material.strip().lower():
                    score += 15.0
                elif incident.material.split("-")[0].lower() in hist_material.lower():
                    score += 8.0

            hist_tool = str(historical.get("tool") or "")
            if incident.tool and hist_tool:
                if incident.tool.split()[0].upper() == hist_tool.split()[0].upper():
                    score += 10.0

            parameter_score = 0.0
            for attribute, weight, tolerance in [
                ("rpm", 4.0, 0.1),
                ("feed_rate", 4.0, 0.1),
                ("temperature", 2.0, None),
            ]:
                current_value = getattr(incident, attribute)
                historical_value = historical.get(attribute)
                if current_value is None or historical_value is None:
                    continue
                if attribute == "temperature":
                    if abs(current_value - historical_value) < 4.0:
                        parameter_score += weight
                else:
                    difference = abs(current_value - historical_value) / max(historical_value, 1)
                    if difference < tolerance:
                        parameter_score += weight
            score += parameter_score
            candidates.append((score, historical))

        candidates.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in candidates[:top_k]]

    def reflect(self, query: str, machine: Optional[str] = None) -> Tuple[str, str]:
        """Synthesize a reflection using Hindsight or local historical counts."""
        if self.client and self.hindsight_available:
            try:
                full_query = f"{query} for machine {machine}" if machine else query
                reflection = _run_in_isolated_thread(
                    self.client.reflect,
                    bank_id=self.bank_id,
                    query=full_query,
                )
                return getattr(reflection, "text", str(reflection)), self.get_data_source_label()
            except Exception as error:
                logger.error("Hindsight reflect failed: %s", error)
                if not self.demo_mode:
                    raise RuntimeError(f"Hindsight reflect error: {error}") from error

        matching = [
            item
            for item in self._local_incidents
            if not machine or item.get("machine") == machine
        ]
        successes = [
            item for item in matching
            if (item.get("outcome") or {}).get("result") == "SUCCESS"
        ]
        failures = [
            item for item in matching
            if (item.get("outcome") or {}).get("result") == "FAILED"
        ]
        reflection = (
            f"Operational Reflection on: '{query}'\n"
            f"Total relevant historical incidents analyzed: {len(matching)}.\n"
            f"Verified Successful Interventions: {len(successes)}.\n"
            f"Documented Historical Failure Modes: {len(failures)}.\n"
            "Key Principle: Operational experience reveals that machining symptoms like chatter, vibration, and overheating "
            "strongly correlate with tool geometry and coolant thermal dissipation rather than isolated parameter overrides."
        )
        return reflection, self.get_data_source_label()

    def get_all_incidents(self) -> List[Dict[str, Any]]:
        return self._local_incidents

    def get_incident_by_id(self, incident_id: str) -> Optional[Dict[str, Any]]:
        return next(
            (item for item in self._local_incidents if item.get("incident_id") == incident_id),
            None,
        )

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._local_incidents)
        with_outcomes = [item for item in self._local_incidents if item.get("outcome")]
        successes = [
            item for item in with_outcomes
            if item.get("outcome", {}).get("result") == "SUCCESS"
        ]
        failures = [
            item for item in with_outcomes
            if item.get("outcome", {}).get("result") == "FAILED"
        ]

        machines: Dict[str, int] = {}
        problems: Dict[str, int] = {}
        for item in self._local_incidents:
            machine = item.get("machine", "Unknown")
            problem = item.get("problem", "Unknown")
            machines[machine] = machines.get(machine, 0) + 1
            problems[problem] = problems.get(problem, 0) + 1

        machine_list = [
            {"machine": key, "count": count}
            for key, count in sorted(machines.items(), key=lambda pair: pair[1], reverse=True)
        ]
        problem_list = [
            {"problem": key, "count": count}
            for key, count in sorted(problems.items(), key=lambda pair: pair[1], reverse=True)
        ]
        return {
            "total_incidents": total,
            "historical_memories": total + len(with_outcomes),
            "successful_interventions": len(successes),
            "failed_interventions": len(failures),
            "recurring_problems": sum(1 for count in problems.values() if count > 1),
            "success_rate": round(len(successes) / len(with_outcomes) * 100, 1) if with_outcomes else 0.0,
            "data_source": self.get_data_source_label(),
            "machines": machine_list,
            "common_problems": problem_list,
            "recent_experiences": self._local_incidents[:5],
        }

    def close(self):
        """Close the Hindsight client session, if it exposes close()."""
        if self.client and hasattr(self.client, "close"):
            try:
                _run_in_isolated_thread(self.client.close)
            except Exception:
                pass

    def __del__(self):
        self.close()
