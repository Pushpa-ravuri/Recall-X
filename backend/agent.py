import json
import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from models import AgentReasoningOutput, Incident, WhatChangedItem


load_dotenv()
logger = logging.getLogger("recall_x.agent")
MODEL_CANDIDATES = [
    os.getenv("GROQ_MODEL", "gpt-oss-20b"),
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]

SYSTEM_PROMPT = """You are RECALL-X, an operational experience reasoning agent for manufacturing decision support. You do not invent historical incidents, interventions, outcomes, or facts.
You must distinguish evidence from inference.
You must never claim certainty when historical evidence is insufficient.
You provide recommendations for human operator review.
You do not directly control machines.

CRITICAL OPERATIONAL RULES:
1. Operational experience shows that similarity does NOT mean the same historical action should be blindly repeated.
2. If machine parameters or environment changed (e.g. different tool, higher temperature, coolant degradation), highlight these differences and advise inspecting those factors BEFORE repeating past interventions.
3. Clearly cite which historical actions SUCCEEDED and which FAILED as direct warnings.
4. Always conclude with an actionable, safe "Recommendation for operator review".

Reply with ONLY a single valid JSON object matching this schema:
{
  "summary": "Concise summary of current problem and historical context",
  "similar_incidents": ["Relevant historical incident IDs and problem descriptions"],
  "successful_interventions": ["Historical actions that SUCCEEDED"],
  "failed_interventions": ["Historical actions that FAILED and their harmful consequences"],
  "important_differences": ["Critical parameters that differ from historical cases"],
  "likely_factors": ["Probable contributing physical factors"],
  "recommendation": "Actionable, precise recommendation for human operator review",
  "reasoning": "Engineering rationale based on historical evidence and condition differences",
  "evidence": ["Traceable points citing previous incidents and outcomes"],
  "confidence": "HIGH | MEDIUM | LOW",
  "warning": "Safety or caution note",
  "human_review_required": true
}
Do not include markdown formatting or backticks around the JSON."""


class RecallXAgent:
    """Use Groq when configured, with a deterministic local reasoning fallback."""

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.client = None
        self._init_groq_client()

    def _init_groq_client(self):
        if not self.api_key:
            logger.info("GROQ_API_KEY not configured. Using local deterministic reasoning.")
            return
        try:
            from groq import Groq

            self.client = Groq(api_key=self.api_key)
            logger.info("Groq client initialized successfully.")
        except Exception as error:
            logger.error("Failed to initialize Groq client: %s", error)
            self.client = None

    def analyze(
        self,
        incident: Incident,
        historical: List[Dict[str, Any]],
        what_changed: List[WhatChangedItem],
    ) -> AgentReasoningOutput:
        if self.client:
            prompt_context = self._build_prompt_context(incident, historical, what_changed)
            for model_name in MODEL_CANDIDATES:
                try:
                    logger.info("Attempting reasoning with model: %s", model_name)
                    response = self.client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt_context},
                        ],
                        temperature=0.1,
                        max_tokens=1500,
                        response_format={"type": "json_object"},
                    )
                    raw_content = response.choices[0].message.content
                    parsed = self._parse_and_validate(raw_content)
                    if parsed:
                        return parsed
                except Exception as error:
                    logger.warning("Groq call failed with model %s: %s", model_name, error)

        logger.info("Synthesizing recommendation via local operational reasoning engine.")
        return self._generate_deterministic_analysis(incident, historical, what_changed)

    def _build_prompt_context(
        self,
        incident: Incident,
        historical: List[Dict[str, Any]],
        what_changed: List[WhatChangedItem],
    ) -> str:
        changes = json.dumps([item.model_dump() for item in what_changed], indent=2)
        memories = json.dumps(historical, indent=2)
        current = json.dumps(incident.model_dump(), indent=2)
        return (
            f"=== CURRENT INCIDENT ===\n{current}\n\n"
            f"=== RETRIEVED HISTORICAL MEMORIES ===\n{memories}\n\n"
            f"=== 'WHAT CHANGED?' PARAMETER DIFFS ===\n{changes}\n\n"
            "Reason strictly over the provided evidence. Highlight differences and generate an explainable recommendation for operator review."
        )

    def _parse_and_validate(self, text: str) -> Optional[AgentReasoningOutput]:
        try:
            cleaned = text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            data = json.loads(cleaned.strip())
            data["human_review_required"] = True
            return AgentReasoningOutput(**data)
        except Exception as error:
            logger.error("Failed to parse and validate LLM output: %s. Raw: %s", error, text)
            return None

    def _generate_deterministic_analysis(
        self,
        incident: Incident,
        historical: List[Dict[str, Any]],
        what_changed: List[WhatChangedItem],
    ) -> AgentReasoningOutput:
        similar_ids: List[str] = []
        successful_actions: List[str] = []
        failed_actions: List[str] = []
        evidence: List[str] = []

        for item in historical:
            incident_id = item.get("incident_id", "HIST")
            machine = item.get("machine", "")
            problem = item.get("problem", "")
            outcome = item.get("outcome") or {}
            result = outcome.get("result") or item.get("result", "")
            action = outcome.get("action") or item.get("action", "")
            notes = outcome.get("notes") or ""
            similar_ids.append(f"{incident_id} ({machine} - {problem})")
            if result == "SUCCESS":
                successful_actions.append(f"{incident_id}: {action}")
                evidence.append(f"✓ {incident_id}: Successfully resolved '{problem}' via {action}. ({notes})")
            elif result == "FAILED":
                failed_actions.append(f"{incident_id}: {action}")
                evidence.append(f"✗ {incident_id}: FAILED intervention: {action}. ({notes})")

        differences: List[str] = []
        tool_diff = None
        temperature_diff = None
        for change in what_changed:
            if change.severity in ("important", "moderate"):
                description = f"{change.parameter}: {change.previous} → {change.current}"
                if change.change_pct:
                    description += f" ({change.change_pct:+0.1f}%)"
                if change.note:
                    description += f" — {change.note}"
                differences.append(description)
            if change.parameter == "Tool":
                tool_diff = change
            elif change.parameter == "Temperature":
                temperature_diff = change

        problem = incident.problem.lower()
        if "rough" in problem or "surface" in problem:
            if tool_diff or temperature_diff:
                recommendation = (
                    f"Recommendation for operator review: Inspect cutting tool {incident.tool or 'current tool'} for premature micro-chipping or nose wear, "
                    "and verify coolant concentration before applying historical feed-rate reduction to 410 mm/min. "
                    "Do NOT increase RPM (previous attempt worsened harmonic chatter)."
                )
                reasoning = (
                    f"Historical memory on {incident.machine} demonstrates that reducing feed rate from 450 to 410 mm/min previously succeeded twice "
                    f"(INC-2026-0101, INC-2026-0189) in restoring Ra under 0.8 µm. However, the current tool is {incident.tool} "
                    f"(historical baseline was {tool_diff.previous if tool_diff else 'T-17'}) and temperature is running at {incident.temperature}°C "
                    f"(historical baseline was 27°C, a {temperature_diff.change_pct if temperature_diff else '+25'}% rise). "
                    "Blindly repeating the feed reduction without inspecting tool wear and thermal cooling could cause tool deflection or part gouging."
                )
                warning = "CRITICAL CAUTION: Do NOT increase RPM. Incident INC-2026-0142 confirmed that increasing RPM to 3800 excited fixture harmonics and destroyed surface finish."
            else:
                recommendation = "Recommendation for operator review: Apply calibrated feed-rate reduction from 450 mm/min to 410 mm/min while maintaining 3200 RPM."
                reasoning = "Conditions match historical successful operations on CNC-07 (AL-6061, T-17 carbide). Feed reduction reliably mitigates chip-load sensitivity."
                warning = "Do not increase spindle speed."
            confidence = "HIGH"
        elif "vibration" in problem:
            recommendation = "Recommendation for operator review: Reduce spindle speed to 1900 RPM and inspect toolholder collet runout with a dial test indicator. Do NOT increase RPM."
            reasoning = (
                "Historical experience on CNC-12 shows that reducing RPM from 2100 to 1900 successfully dampens harmonic bending resonance (INC-2026-0210). "
                "INC-2026-0490 revealed that persistent vibration despite RPM adjustment was caused by collet fretting corrosion (>20 µm runout)."
            )
            warning = "CRITICAL: Never attempt to 'power through' resonance by increasing RPM. Incident INC-2026-0235 caused an emergency spindle overload shutdown at 2.1 mm/s RMS."
            confidence = "HIGH"
        elif "overheating" in problem:
            recommendation = "Recommendation for operator review: Backflush the high-pressure through-spindle coolant filter and verify delivery pressure. Inspect tool cutting edge for flank blunting."
            reasoning = (
                "Past memory on CNC-03 shows overheating in heat-resistant alloys stems from either coolant filter blinding (INC-2026-0280) "
                "or severe flank wear transferring friction heat to the spindle nose (INC-2026-0305). "
                "Incident INC-2026-0520 proved that simply reducing feed rate causes rubbing and catastrophic temperature rise."
            )
            warning = "Do NOT simply reduce feed rate without addressing cooling or tool wear; rubbing worsens thermal accumulation in Inconel."
            confidence = "HIGH"
        else:
            prior_action = successful_actions[0] if successful_actions else "Check tool alignment"
            recommendation = f"Recommendation for operator review: Verify machine setup, inspect tooling for wear, and review previous successful intervention: {prior_action}."
            reasoning = "Retrieved operational memories indicate high correlation between the current symptom and tooling/coolant state."
            warning = "Validate all tool offsets and clamping rigidity before restarting the cycle."
            confidence = "MEDIUM"

        summary = (
            f"RECALL-X retrieved {len(historical)} historical operational memories for {incident.machine} facing '{incident.problem}'. "
            f"Found {len(successful_actions)} successful resolution(s) and {len(failed_actions)} documented failure mode(s)."
        )
        return AgentReasoningOutput(
            summary=summary,
            similar_incidents=similar_ids,
            successful_interventions=successful_actions,
            failed_interventions=failed_actions,
            important_differences=differences,
            likely_factors=[
                "Tool wear / geometry variance",
                "Thermal expansion / coolant concentration degradation",
                "Spindle harmonic resonance threshold",
            ],
            recommendation=recommendation,
            reasoning=reasoning,
            evidence=evidence,
            confidence=confidence,
            warning=warning,
            human_review_required=True,
        )
