# RECALL-X
## AI Agent for Recovering Lost Operational Knowledge > *"Factories don't just lose data. They lose experience."* RECALL-X is an enterprise AI operational experience memory system designed for modern manufacturing shop floors. Modern machining centers generate millions of sensor readings, but when a machine begins to chatter, overheat, or drift out of tolerance, the critical information is not raw data—it is **experience**: *What did the previous shift try? What worked? What catastrophically failed? And what conditions changed since then?* RECALL-X captures, retains, compares, and reasons over operational experience using **Hindsight memory** and **Groq LLM reasoning**, keeping the human operator firmly in the decision loop. --- ## 1. System Architecture ``` ┌──────────────────────────────────────────┐ │ Next.js Enterprise UI │ │ (/dashboard, /analyze, /memory, /history)│ └────────────────────┬─────────────────────┘ │ HTTP REST / JSON ▼ ┌──────────────────────────────────────────┐ │ FastAPI Backend │ └─────────────┬──────────────┬─────────────┘ │ │ ┌─────────────▼────┐ ┌─────▼─────────────┐ │ Hindsight Memory │ │ Groq LLM │ │ (retain, recall, │ │ (RECALL-X │ │ reflect) │ │ Reasoning Agent) │ └─────────────┬────┘ └─────┬─────────────┘ │ │ ▼ ▼ ┌──────────────────────────────────────────┐ │ "What Changed?" Engine │ │ (Telemetry Diffs, Tool & Env Analysis) │ └────────────────────┬─────────────────────┘ │ ▼ ┌──────────────────────────────────────────┐ │ Explainable Recommendation │ │ (Evidence, Differences, Failed History) │ └────────────────────┬─────────────────────┘ │ ▼ ┌──────────────────────────────────────────┐ │ Human Operator Decision │ │ (Accept / Reject / Execute) │ └────────────────────┬─────────────────────┘ │ ▼ ┌──────────────────────────────────────────┐ │ Outcome Learning Loop │ │ (POST /outcome -> Retained in Memory) │ │ "RECALL-X LEARNED" │ └──────────────────────────────────────────┘
``` ### The Continuous Learning Loop:
```
CURRENT INCIDENT ↓
HINDSIGHT MEMORY ↓
SIMILAR HISTORICAL INCIDENTS ↓
WHAT CHANGED? ↓
EXPERIENCE ANALYSIS ↓
AI RECOMMENDATION ↓
HUMAN DECISION ↓
OUTCOME ↓
HINDSIGHT MEMORY ↓
FUTURE INCIDENTS
``` --- ## 2. Core Distinctions & Safety Boundaries RECALL-X is **NOT**:
- A generic chatbot or prompt-wrapper
- A static document search (generic RAG)
- A simple CRUD application
- An autonomous machine controller RECALL-X **IS**:
- A **DECISION-SUPPORT** system that remembers operational cause-and-effect across shifts.
- It **NEVER** directly controls or modifies real machine CNC parameters.
- All advice is explicitly presented as: **"Recommendation for operator review."** --- ## 3. Technology Stack - **Frontend**: Next.js 15 (App Router), TypeScript, Tailwind CSS, Lucide React, Recharts, Interactive SVG Experience Graph & Dynamic Memory Timeline.
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, `hindsight-client`, `groq`, `python-dotenv`, `uvicorn`.
- **Memory Layer**: Hindsight (`retain`, `recall`, `reflect`) with multi-factor operational similarity ranking and resilient offline demo fallback.
- **LLM Reasoning**: Groq API (preferring `gpt-oss-20b` or `llama-3.3-70b-versatile` with deterministic expert reasoning fallback). --- ## 4. Project Monorepo Structure ```
recall-x/
├── backend/
│ ├── main.py # FastAPI server & REST endpoints
│ ├── agent.py # Groq LLM operational reasoning agent
│ ├── memory.py # Hindsight experience memory management
│ ├── comparison.py # "What Changed?" engineering delta engine
│ ├── models.py # Pydantic models for Incidents & Outcomes
│ ├── seed_data.py # Seed loader for 15 manufacturing scenarios
│ ├── test_hindsight.py # Connectivity & retain/recall sanity test
│ ├── tests/
│ │ └── test_flow.py # Automated pytest test suite
│ ├── requirements.txt # Python backend dependencies
│ ├── .env.example # Example backend environment variables
│ └── README.md
│
├── frontend/
│ ├── src/
│ │ ├── app/
│ │ │ ├── layout.tsx # Root dark-mode enterprise layout
│ │ │ ├── page.tsx # Redirect to /dashboard
│ │ │ ├── dashboard/ # High-level operational command center
│ │ │ ├── analyze/ # 2-column live demo analysis studio
│ │ │ ├── history/ # Searchable, filterable incident archive
│ │ │ ├── memory/ # Dedicated memory center & reflect console
│ │ │ └── insights/ # Real empirical metrics & distributions
│ │ ├── components/
│ │ │ ├── Navbar.tsx # Enterprise navigation & live status
│ │ │ ├── IncidentForm.tsx # Telemetry cutting condition form
│ │ │ ├── RecommendationCard.tsx # Explainable AI recommendation card
│ │ │ ├── WhatChangedTable.tsx # Parameter delta comparison table
│ │ │ ├── MemoryTimeline.tsx # Dynamic chronological timeline
│ │ │ ├── ExperienceGraph.tsx # Interactive SVG memory graph
│ │ │ ├── OutcomeModal.tsx # Closed-loop outcome recording modal
│ │ │ └── DemoPresetSelector.tsx # 1-click demo scenario loader
│ │ └── lib/
│ │ ├── api.ts # Centralized API service layer
│ │ └── types.ts # TypeScript interfaces
│ ├── package.json
│ ├── tailwind.config.ts
│ ├── tsconfig.json
│ └── README.md
│
├── data/
│ ├── seed_incidents.json # 15 baseline manufacturing incidents
│ ├── incidents.json # Synchronized local memory cache
│ └── README.md
│
├── docs/
│ ├── architecture.md # Detailed system design
│ └── demo-script.md # 3-minute presentation script
│
├── .gitignore
├── README.md
└── LICENSE
``` --- ## 5. Environment Setup & Configuration ### Backend Environment Variables (`backend/.env`) Copy `backend/.env.example` to `backend/.env`: ```bash
# Hindsight Experience Memory
HINDSIGHT_URL=http://localhost:8888
HINDSIGHT_API_KEY=your_hindsight_api_key
HINDSIGHT_BANK_ID=recall-x
# Groq LLM Reasoning
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile
# Operational Mode
# When DEMO_MODE=true, if Hindsight or Groq is unreachable, fallback to high-fidelity seed experience data
# with explicit UI labeling: "[DEMO DATA - Hindsight unavailable]"
DEMO_MODE=true
# Server Configuration
PORT=8000
FRONTEND_URL=http://localhost:3000
``` --- ## 6. Exact Commands to Install & Run ### Step 1: Install Backend Dependencies
```bash
pip install -r backend/requirements.txt
``` ### Step 2: Seed the Operational Memory Bank
```bash
python backend/seed_data.py
``` ### Step 3: Run Backend Sanity & Integration Tests
```bash
# Verify Hindsight connectivity
python backend/test_hindsight.py
# Run the complete pytest test suite
python -m pytest backend/tests/test_flow.py -v
``` ### Step 4: Start the FastAPI Backend
```bash
# From workspace root:
python -m uvicorn backend.main:app --reload --port 8000
```
Backend will be live at: `http://localhost:8000` (Docs: `http://localhost:8000/docs`). ### Step 5: Install & Start the Next.js Frontend
```bash
# In frontend directory:
npm --prefix frontend install
npm --prefix frontend run dev
```
Frontend will be live at: `http://localhost:3000`. --- ## 7. Fast-Track 3-Minute Demo 1. Open `http://localhost:3000/analyze`.
2. Select **"Demo 1: CNC Rough Surface (Main Demo)"**: - Machine: `CNC-07` - Problem: `Rough surface finish` - Material: `AL-6061` - Tool: `T-19` *(Historical baseline used T-17)* - Temp: `34°C` *(Historical baseline was 27°C)*
3. Click **[ANALYZE INCIDENT WITH RECALL-X]**: - Live progress indicator displays reasoning progression. - **What Changed?** flags: - `Tool: T-17 → T-19` (Severity: CRITICAL DELTA). - `Temperature: 27°C → 34°C (+25.9%)` (Severity: CRITICAL DELTA). - **AI Recommendation** appears: - Advises against blindly repeating the old feed-rate intervention without inspecting the changed tool and coolant condition. - Cites 2 previous successes and explicitly warns that increasing RPM previously excited harmonic chatter.
4. Click **[RECORD INTERVENTION OUTCOME]**: - Select **[ SUCCESS ]**. - Action: `Inspected T-19 insert—found chipped corner. Replaced insert and adjusted feed to 410 mm/min.` - Click **[Submit Outcome]**. - Notice banner: **"RECALL-X LEARNED — Intervention experience retained into Hindsight for future incidents."**
5. Navigate to **`/memory`**: - Verify the newly learned incident and outcome appears in the **Experience Graph** and **Timeline**. --- ## 8. API Endpoints Summary | Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | API status, operational mode, and memory backend |
| `GET` | `/health` | Connectivity status for Hindsight, Groq, and demo fallback |
| `POST` | `/incident` | Submit incident, recall experiences, run What Changed?, and generate recommendation |
| `POST` | `/outcome` | Record operator intervention outcome and retain in Hindsight |
| `POST` | `/seed` | Reset and reload 15 realistic historical manufacturing incidents |
| `GET` | `/incident/{id}` | Retrieve specific incident details |
| `GET` | `/history` | Query historical incidents with search, machine, problem, and outcome filters |
| `POST` | `/reflect` | Trigger Hindsight `reflect()` agentic synthesis over memory |
| `GET` | `/stats` | Real empirical KPIs, machine distributions, and success rates | --- ## 9. Safety & Boundaries - All recommendations are strictly framed as **recommendations for operator review**.
- RECALL-X never executes machine commands or adjusts CNC G-code directly.
- The AI agent is prohibited from inventing historical interventions or claiming certainty without evidence.
