# RECALL-X Architecture & System Design RECALL-X is an AI-powered operational experience memory system designed for modern manufacturing shop floors. It transforms fragmented tribal knowledge and shift logs into an evolving operational memory bank. ```
+-------------------------------------------------------------------------+
| Next.js 15 Enterprise UI |
| (/dashboard, /analyze, /memory, /history, /insights, Demo Presets) |
+------------------------------------+------------------------------------+ | HTTP REST / JSON v
+-------------------------------------------------------------------------+
| FastAPI Backend |
| (/incident, /outcome, /history, /seed, /reflect, /stats, /health) |
+-------------------+---------------------------------+-------------------+ | | v v
+------------------------------------+ +--------------------------------+
| Hindsight Memory Engine | | Groq AI Reasoning |
| - retain: Persist experiences | | - Operational experience |
| - recall: Multi-vector retrieval | | reasoning agent |
| - reflect: Synthesize insights | | - Strict evidence constraint |
| - Bank ID: recall-x | | - Pydantic schema validation |
+-------------------+----------------+ +----------------+---------------+ | | +------------------+------------------+ | v
+-------------------------------------------------------------------------+
| "What Changed?" Engine |
| - Multi-parameter delta calculation (Numerical % & Categorical Diffs) |
| - Severity classification (Important, Moderate, Minor, Neutral) |
| - Tool, Metallurgy, Cutting Parameters, Thermal, & Coolant Diffs |
+--------------------------------------+----------------------------------+ | v
+-------------------------------------------------------------------------+
| Explainable Recommendation |
| - Clear WHY: Historical supporting evidence |
| - Clear WHAT CHANGED: Tool/Temperature divergence warnings |
| - Clear FAILED WARNING: Lessons learned from previous bad attempts |
| - Confidence metric & Explicit "Recommendation for Operator Review" |
+--------------------------------------+----------------------------------+ | v
+-------------------------------------------------------------------------+
| Human Operator Decision |
| (Accept Recommendation / Reject / Modify Planned Action) |
+--------------------------------------+----------------------------------+ | v
+-------------------------------------------------------------------------+
| Outcome Learning Loop |
| (POST /outcome -> Retain in Hindsight Bank) |
| "RECALL-X LEARNED" -> Enriches future recalls |
+-------------------------------------------------------------------------+
``` ## Core Modules ### 1. Backend Layer (`backend/`)
- `main.py`: FastAPI server with CORS, lifespan startup, endpoints for incident analysis, outcome retention, memory reflection, and operational telemetry metrics.
- `models.py`: Strongly typed Pydantic models for Incidents, Outcomes, What-Changed diffs, Matches, and Recommendations.
- `memory.py`: Encapsulates `hindsight-client`. Formats rich contextual memory records with metadata, executes multi-factor recall queries, and supports seamless demo fallback with clear labeling (`DEMO DATA — Hindsight unavailable`).
- `comparison.py`: The "What Changed?" Engine. Compares the current incident parameters against retrieved historical cases and scores deviations by severity.
- `agent.py`: Groq LLM integration. Enforces evidence-only reasoning, prohibits hallucinated interventions, evaluates condition deltas, and validates structured outputs.
- `seed_data.py`: Loads the 15 seed scenarios into Hindsight and local persistence.
- `test_hindsight.py`: Automated sanity test for Hindsight retain/recall/reflect. ### 2. Frontend Layer (`frontend/`)
- Modern App Router Next.js architecture styled with Tailwind CSS.
- **Pages**: - `/dashboard`: High-level operational command center with real-time KPIs, quick incident submission, experience timeline preview, and active graph. - `/analyze`: Live demo studio with 1-click test scenarios, animated multi-step reasoning indicator, and traceable evidence cards. - `/memory`: Interactive visual timeline and dynamic SVG Experience Memory Graph mapping Machine -> Problem -> Tool -> Intervention -> Outcome. - `/history`: Operational shift archive with instant search and multi-attribute filtering. - `/insights`: Empirical failure-mode analysis and intervention success metrics.
