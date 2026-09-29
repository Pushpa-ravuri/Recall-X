# RECALL-X Backend Service FastAPI-powered operational memory backend for RECALL-X. ## Architecture - **`memory.py`**: Integrates with Hindsight memory service via `hindsight-client`. Implements `retain`, `recall`, and `reflect` operations. Features resilient fallback mode (`DEMO_MODE=true`) with transparent UI status labeling.
- **`comparison.py`**: The "What Changed?" Engine. Detects cutting parameter, tooling, and environmental deviations between current and historical conditions.
- **`agent.py`**: Reasoning engine powered by Groq LLM (with deterministic expert fallback), strictly constrained to evidence-based deductions.
- **`models.py`**: Pydantic models for Incidents, Outcomes, Comparisons, and Analytics.
- **`seed_data.py`**: Loads 15 realistic historical manufacturing scenarios.
- **`main.py`**: Exposes REST endpoints with CORS support for the Next.js frontend. ## Environment Variables Copy `.env.example` to `.env`: ```bash
HINDSIGHT_URL=http://localhost:8888
HINDSIGHT_API_KEY=your_hindsight_api_key
HINDSIGHT_BANK_ID=recall-x
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
DEMO_MODE=true
FRONTEND_URL=http://localhost:3000
PORT=8000
``` ## Running the Backend 1. Install dependencies: ```bash pip install -r requirements.txt ``` 2. Seed historical incidents: ```bash python seed_data.py ``` 3. Test Hindsight connectivity: ```bash python test_hindsight.py ``` 4. Run tests: ```bash pytest tests/test_flow.py -v ``` 5. Launch server: ```bash uvicorn main:app --reload --port 8000 ```
