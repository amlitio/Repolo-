# Deployment guide

## Recommended topology

- **apps/web** -> Vercel (see [`infra/vercel/`](../infra/vercel/))
- **apps/api** + **apps/workers** -> Railway (see [`infra/railway/`](../infra/railway/)),
  Fly.io (see [`infra/fly/`](../infra/fly/)), or Cloud Run on Google Cloud
  (see [`infra/gcp/`](../infra/gcp/)) - pick one
- **Database** -> managed Postgres with the `postgis` and `vector`
  extensions enabled (Railway's, Fly's, or Cloud SQL's managed Postgres, or
  any Postgres 16+ host that allows installing those extensions)

## Local development (no containers required)

This is the fastest loop and what this repository's own automated checks
rely on, since the sandbox this repo was built in has no Docker daemon:

```bash
npm install && npm run build && npm run dev:web   # apps/web on :3000

cd apps/api && pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env   # DATABASE_URL defaults to sqlite+aiosqlite:///:memory:
uvicorn app.main:app --reload   # :8000

cd apps/workers && pip install -r requirements.txt -r requirements-dev.txt
python -m worker.scheduler
```

## Local development with Docker Compose

`infra/docker-compose.yml` runs Postgres+PostGIS+pgvector (built from
[`infra/postgres/`](../infra/postgres/)), a one-shot `migrate` service
(`alembic upgrade head`), the API, the worker, and the web app together:

```bash
docker compose -f infra/docker-compose.yml up --build
```

**The `docker build`/`up` step itself has not been run end-to-end in the
environment this repo was scaffolded in** — that sandbox has the `docker`
CLI but no privilege to start a daemon. The Alembic migration it runs *has*
been verified end-to-end against a real Postgres 16 + PostGIS 3.4.2 +
pgvector 0.6.0 instance (see [`infra/postgres/README.md`](../infra/postgres/README.md)
for exactly what was and wasn't exercised, and how). Before relying on the
compose file itself, verify all services start cleanly, the api can reach
the db, and the web app can reach the api, in an environment with a working
Docker daemon.

## First deploy checklist

1. Provision Postgres; run `CREATE EXTENSION IF NOT EXISTS postgis;` and
   `CREATE EXTENSION IF NOT EXISTS vector;`.
2. Run `alembic upgrade head` against that database from `apps/api`
   (e.g. `railway run alembic upgrade head` or `flyctl ssh console` then
   run it inside the deployed container, or `docker compose -f
   infra/docker-compose.yml run --rm migrate` locally). Verified end-to-end
   against real Postgres+PostGIS+pgvector — see
   [`infra/postgres/README.md`](../infra/postgres/README.md) — but still
   watch the first run against any new managed Postgres provider for
   provider-specific extension/permission quirks.
3. Set all required environment variables on `apps/api` and
   `apps/workers` from `apps/api/.env.example`, and on `apps/web` from
   `apps/web/.env.example`. At minimum for a non-degraded deploy:
   `DATABASE_URL`, `CORS_ORIGINS`, `CLERK_JWKS_URL`, `CLERK_ISSUER`,
   `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_MAPBOX_TOKEN`,
   `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`.
4. Confirm `AUTH_DEV_BYPASS` is unset/`0` on every deployed environment —
   see [`docs/security-checklist.md`](security-checklist.md).
5. Deploy `apps/api`, then `apps/workers`, then `apps/web` (the web app's
   build doesn't depend on the others being up, but its runtime API calls
   do).
6. Smoke-test: load the deployed web URL, confirm the map renders (or
   shows the "set Mapbox token" placeholder if not yet configured), and
   hit `GET /health` on the deployed api URL directly.

## Known gaps (be honest about these until closed)

- Live connector behavior against real FEMA/NOAA/USGS/WMD endpoints was
  never verified from the sandbox this repo was built in (network
  egress was restricted to a small allowlist that excluded those hosts).
  Run with `RUN_LIVE_SMOKE_TESTS=1` against a real network before trusting
  ingestion in production.
- `docker compose up --build` was never executed in this repo's build
  environment (no Docker daemon) — see above.
- 59 of 67 counties' GIS/procurement/permits/parcels URLs are still
  `needs_verification` (see [`docs/data-sources/README.md`](data-sources/README.md)).
