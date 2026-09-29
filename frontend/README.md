# RECALL-X Frontend

Next.js App Router interface for RECALL-X.

## Requirements

Use Node.js 20.19.x, 22.13.x, or 24+. The recommended exact version is in `.nvmrc`.

## Configuration

Copy `.env.example` to `.env.local` and set `NEXT_PUBLIC_API_URL` to the public origin of the deployed FastAPI service before building. This value is embedded in the browser bundle at build time.

## Install and run

```bash
npm ci
npm run dev
```

## Production checks and build

```bash
npm run typecheck
npm run lint
npm run build
npm start
```

`npm start` serves the production build on port 3000.

## Pages

- `/dashboard`: operational KPIs, experience graph, and recent history.
- `/analyze`: incident analysis and operator outcome recording.
- `/history`: searchable incident archive.
- `/memory`: timeline, graph, and reflection console.
- `/insights`: operational metrics and intervention outcomes.
