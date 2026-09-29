from typing import Any, Dict, List

from models import Incident, WhatChangedItem


class WhatChangedEngine:
    """Compare current cutting conditions with a historical baseline incident."""

    @staticmethod
    def compare_incident(
        current: Incident, historical: List[Dict[str, Any]]
    ) -> List[WhatChangedItem]:
        if not historical:
            return []

        baseline = None
        for item in historical:
            outcome = item.get("outcome") or {}
            result = outcome.get("result", "") if isinstance(outcome, dict) else ""
            if result == "SUCCESS" or item.get("result") == "SUCCESS":
                baseline = item
                break
        if baseline is None:
            baseline = historical[0]

        changes: List[WhatChangedItem] = []

        previous_tool, current_tool = baseline.get("tool"), current.tool
        if previous_tool and current_tool and previous_tool.strip().lower() != current_tool.strip().lower():
            changes.append(
                WhatChangedItem(
                    parameter="Tool",
                    previous=previous_tool,
                    current=current_tool,
                    severity="important",
                    note="Tool geometry, coating, or substrate differs from the previous successful baseline. Cutting dynamics and wear characteristics may vary.",
                )
            )
        elif previous_tool and not current_tool:
            changes.append(
                WhatChangedItem(
                    parameter="Tool",
                    previous=previous_tool,
                    current="Unspecified",
                    severity="moderate",
                    note="Tool specification missing for current incident.",
                )
            )

        numeric_comparisons = [
            ("Temperature", "temperature", "°C", 1.0, 5.0, 18.0),
            ("Spindle Speed (RPM)", "rpm", "RPM", 10.0, 0.0, 15.0),
            ("Feed Rate", "feed_rate", "mm/min", 5.0, 0.0, 15.0),
            ("Vibration", "vibration", "mm/s RMS", 0.08, 0.8, 30.0),
            ("Pressure", "pressure", "bar", 0.2, 0.0, 20.0),
        ]
        for label, key, unit, threshold, important_delta, important_pct in numeric_comparisons:
            previous = baseline.get(key)
            value = getattr(current, key)
            if previous is None or value is None:
                continue
            delta = value - previous
            pct = round(delta / previous * 100, 1) if previous else 0.0
            if abs(delta) < threshold:
                continue

            if key == "temperature":
                severity = "important" if abs(delta) >= important_delta or abs(pct) >= important_pct else "moderate"
                direction = "higher" if delta > 0 else "cooler"
                note = (
                    f"Current temperature is {abs(delta):.1f}°C ({pct:+0.1f}%) {direction} than historical baseline "
                    f"({previous}°C). Thermal expansion and coolant effectiveness may be affected."
                )
            elif key == "rpm":
                severity = "important" if abs(pct) >= important_pct else "moderate"
                note = f"Spindle speed is {pct:+0.1f}% relative to historical baseline ({previous} RPM)."
            elif key == "feed_rate":
                severity = "important" if abs(pct) >= important_pct else "moderate"
                note = f"Feed rate differs by {pct:+0.1f}% from historical baseline ({previous} mm/min)."
            elif key == "vibration":
                severity = "important" if value > important_delta or abs(pct) >= important_pct else "moderate"
                note = f"Vibration is {pct:+0.1f}% relative to historical baseline."
            else:
                severity = "important" if abs(pct) >= important_pct else "minor"
                note = f"Coolant/Hydraulic pressure variance of {pct:+0.1f}% detected."

            changes.append(
                WhatChangedItem(
                    parameter=label,
                    previous=int(previous) if key == "rpm" else previous,
                    current=int(value) if key == "rpm" else value,
                    unit=unit,
                    change_pct=pct,
                    severity=severity,
                    note=note,
                )
            )

        for label, key, note in [
            (
                "Coolant Condition",
                "coolant_condition",
                "Coolant state has changed; potential degradation in lubricity, dilution, or delivery flow.",
            ),
            (
                "Tool Condition",
                "tool_condition",
                "Tool physical wear/state has changed relative to historical run.",
            ),
        ]:
            previous = baseline.get(key)
            value = getattr(current, key)
            if previous and value and previous.strip().lower() != value.strip().lower():
                changes.append(
                    WhatChangedItem(
                        parameter=label,
                        previous=previous,
                        current=value,
                        severity="important",
                        note=note,
                    )
                )

        previous_material, current_material = baseline.get("material"), current.material
        if previous_material and current_material:
            clean_previous = previous_material.strip().lower().replace("-t6", "").replace("-t4", "").replace(" ", "")
            clean_current = current_material.strip().lower().replace("-t6", "").replace("-t4", "").replace(" ", "")
            if (
                clean_previous != clean_current
                and clean_previous not in clean_current
                and clean_current not in clean_previous
            ):
                changes.append(
                    WhatChangedItem(
                        parameter="Workpiece Material",
                        previous=previous_material,
                        current=current_material,
                        severity="important",
                        note="Material grade changed. Cutting speeds and feed mechanics differ significantly across alloys.",
                    )
                )

        return changes
