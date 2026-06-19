# FIRIP — Florida Risk + Water Intelligence Platform

FIRIP is a map-first intelligence platform for Florida flood and water
risk: live FEMA flood zones, NOAA/NWS weather alerts and NHC hurricane
tracks, USGS and Florida water management district station telemetry,
explainable property/county risk scoring, hybrid search, and role-based
dashboards for government, engineering, investment, and emergency
management users.

See [`docs/architecture.md`](docs/architecture.md) for the full system
diagram and [`docs/roadmap.md`](docs/roadmap.md) for what's built versus
what's ahead. This MVP is scoped to **Risk + Water**; procurement and
construction modules are scaffolded but not yet activated (see
[`docs/roadmap.md`](docs/roadmap.md)).

## Monorepo layout

```
apps/
  api/       FastAPI backend - REST API, Postgres+PostGIS+pgvector, scoring engine
  workers/   Ingestion scheduler, connectors, agents (Data Discovery, Water
             Intelligence, Risk Modeling, Research)
  web/       Next.js 16 frontend - map UI, role-based dashboards
packages/
  shared/    Cross-language data: counties.json, sources.json, scoring.json,
             plus the TypeScript types/constants generated from them
docs/        Architecture, data sources, security, deployment, roadmap, etc.
infra/       docker-compose, Railway, Fly, Vercel, Terraform configs
```

## Prerequisites

- Node.js >= 22 (see `.nvmrc`)
- Python >= 3.11
- Postgres with the `postgis` and `vector` extensions, for anything beyond
  unit tests (unit tests run against SQLite and need neither)

## Getting started

```bash
# Frontend + shared package
npm install
npm run build            # builds packages/shared, then apps/web
npm run dev:web           # http://localhost:3000

# Backend
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env      # defaults to an in-memory SQLite DB
uvicorn app.main:app --reload   # http://localhost:8000

# Workers
cd apps/workers
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python -m worker.scheduler
```

Copy `apps/web/.env.example` to `apps/web/.env.local` and fill in
`NEXT_PUBLIC_MAPBOX_TOKEN` / Clerk keys for a fully working local map and
auth flow — the app degrades gracefully (placeholders, no crash) when
those are absent, which is what this repo's own CI/sandbox build relies on.

## Verification commands

| Command | What it checks |
| --- | --- |
| `npm run lint` | ESLint on `apps/web` |
| `npm run typecheck` | TypeScript on `packages/shared` and `apps/web` |
| `npm run test` | Vitest unit tests (`packages/shared`, `apps/web`) |
| `npm run test:e2e` | Playwright e2e (`apps/web`, requires a running app) |
| `npm run build` | Production build of `packages/shared` + `apps/web` |
| `cd apps/api && pytest` | Backend unit tests (SQLite, no live network) |
| `cd apps/api && pytest -m integration` | Backend tests requiring real Postgres+PostGIS |
| `cd apps/workers && pytest` | Worker/agent unit tests |

## Data sources & licensing

All ingested data sources are cataloged in
[`packages/shared/data/sources.json`](packages/shared/data/sources.json)
with their license and verification status. See
[`docs/data-sources/README.md`](docs/data-sources/README.md) for the
verification methodology, including which sources and counties are fully
verified versus still flagged `needs_verification` — that file is the
honest record of what's actually been checked.

## Security

See [`docs/security-checklist.md`](docs/security-checklist.md).

## Deployment

See [`docs/deployment-guide.md`](docs/deployment-guide.md) and the
platform-specific configs in `infra/`.

## License

GPL-3.0 — see [`LICENSE`](LICENSE).
