# Railway deployment

FIRIP's backend (`apps/api`) and ingestion worker (`apps/workers`) deploy to
Railway as two separate services from this monorepo. A managed Postgres
instance with the PostGIS and pgvector extensions enabled is required (add
both via `CREATE EXTENSION` once the database is provisioned — Railway's
Postgres template does not enable them by default).

## Setup

1. Create a new Railway project, add a Postgres database (enable the
   `postgis` and `vector` extensions via a one-off `psql` connection or a
   migration).
2. Add two services from this repo:
   - **api**: set the build context to the repo root, and the config file
     path to `infra/railway/api.railway.json` (Railway's config-as-code
     file does not follow the service's root directory setting — point it
     at the absolute path of the file). Dockerfile: `apps/api/Dockerfile`.
   - **workers**: same pattern, config file `infra/railway/workers.railway.json`,
     Dockerfile `apps/workers/Dockerfile`.
3. Set environment variables on both services from `apps/api/.env.example`
   (the worker reuses `DATABASE_URL` and the source-specific variables; it
   does not need `CLERK_*` or `CORS_ORIGINS`).
4. Run `alembic upgrade head` against the Railway Postgres instance once
   (e.g. via `railway run alembic upgrade head` from `apps/api`) before the
   api service's first deploy.

## Notes

- These config files were never deployed or tested against a live Railway
  project from the sandbox this repo was scaffolded in (no network access
  to railway.com). Validate the build/deploy commands against
  `apps/api/Dockerfile` and `apps/workers/Dockerfile` once those exist and
  before the first real deploy.
- `healthcheckPath: /health` assumes `apps/api` exposes a `GET /health`
  endpoint that does not require auth — confirm this matches the actual
  router.
