# Deployment

RECALL-X runs as two services: the Next.js frontend and the FastAPI backend. The backend also needs a reachable Hindsight service for persistent memory. Groq is optional; without a Groq key, the backend uses its deterministic local reasoning fallback.

## Frontend

Use the Node.js version in `frontend/.nvmrc` (or a version allowed by `frontend/package.json`). Set `NEXT_PUBLIC_API_URL` to the public backend origin in the frontend build environment. Next.js embeds this public URL into the browser bundle, so changing it requires a new build.

From `frontend/`, install from the lockfile and build:

```bash
npm ci
npm run typecheck
npm run lint
npm run build
npm start
```

The start command honors the hosting platform's `PORT` value and defaults to port 3000.

## Backend

Install `backend/requirements.txt`, then start the app with the platform's port and a public bind address:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8000}"
```

Configure these backend environment variables in the hosting platform's secret/environment settings:

- `HINDSIGHT_URL`, `HINDSIGHT_API_KEY`, and `HINDSIGHT_BANK_ID` for the memory service.
- `GROQ_API_KEY` and `GROQ_MODEL` if hosted LLM reasoning is enabled.
- `DEMO_MODE=false` when the deployment must fail closed if Hindsight is unavailable; keep it `true` only when the labeled local fallback is intended.
- `FRONTEND_URL` set to the exact deployed frontend origin for CORS.
- `PORT` set by the platform, if it provides one.
- `RECALL_X_DATA_FILE` set to a writable persistent-volume path when local history and analytics must survive restarts. The default is `data/incidents.json` in the project directory.

For a new installation, seed the memory bank once after configuring Hindsight:

```bash
python backend/seed_data.py
```

Do not run the seed command on every restart: it replaces the local history cache with the sample corpus. Keep the local cache on persistent storage; history and analytics endpoints read from this cache. Run a single backend worker while this JSON cache is in use.

Use `/health` for service status and `/docs` for the FastAPI API reference. Keep provider API keys in secret settings; never put them in frontend variables or source control.
