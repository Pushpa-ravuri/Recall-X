# RECALL-X Seed Operational Knowledge Dataset This directory contains `incidents.json`, the seed corpus of 15 realistic historical manufacturing incidents used by RECALL-X for experience retrieval, memory bank initialization, and live demonstrations. ## Dataset Structure Each incident entry contains: - `incident_id`: Unique identifier (e.g. `INC-2026-0101`).
- `timestamp`: ISO 8601 creation timestamp.
- `machine`: Machine identifier (e.g., `CNC-07`, `CNC-12`, `CNC-03`, `LATHE-04`, `VMC-01`).
- `problem`: Operational issue or symptom (e.g., `Rough surface finish`, `Excessive spindle vibration`, `Spindle bearing overheating`).
- `material`: Workpiece metallurgy (e.g., `AL-6061-T6`, `AISI 4140 Steel`, `Inconel 718`, `SS-316L`, `Ti-6Al-4V`).
- `tool`: Cutting tool assembly / insert specification (e.g., `T-17`, `T-22`, `T-08`, `T-31`).
- `rpm`, `feed_rate`, `temperature`, `pressure`, `vibration`: Telemetry cutting parameters.
- `coolant_condition`, `tool_condition`: Environmental and physical component state.
- `operator_observation`: Shop-floor human qualitative assessment.
- `outcome`: - `action`: Exact operational intervention attempted by the machinist. - `result`: `SUCCESS` | `FAILED` | `PARTIAL` | `UNKNOWN`. - `root_cause`: Engineering root cause discovered post-mortem. - `notes`: Quantitative metrics (e.g., Ra surface roughness, vibration mm/s RMS, thermal drop). ## Key Scenarios Covered 1. **CNC Rough Surface on CNC-07 (Scenarios A & B)**: - Feed rate reduction from 450 to 410 mm/min: **SUCCESS** (Ra drops to 0.8 µm). - RPM increase to 3800: **FAILED** (structural resonance excited, Ra degrades to 4.8 µm).
2. **Excessive Spindle Vibration on CNC-12 (Scenarios C & D)**: - RPM reduction to 1900: **SUCCESS** (breaks harmonic lock). - RPM increase: **FAILED** (secondary harmonic triggers emergency spindle overload trip). - ER-32 Collet Runout: **SUCCESS** (uncovers hardware root cause).
3. **Spindle Bearing Overheating on CNC-03 (Scenario E)**: - Coolant filter backflush: **SUCCESS**. - Feed reduction in work-hardening Inconel: **FAILED** (increased rubbing friction).
4. **Premature Tool Wear on LATHE-04 (Scenario F)**: - Coolant emulsion brix restoration vs PVD insert grade switch for interrupted cuts.
5. **Recurring Learning Loop on CNC-07 (Scenario G)**: - Persistent documentation of feed rate optimization, validating that repeat interventions succeed only when machine conditions match historical baseline.
