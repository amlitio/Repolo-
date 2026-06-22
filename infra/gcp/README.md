# Google Cloud deployment (alternative to Fly/Railway)

Deploys `apps/api` to Cloud Run with a Cloud SQL for PostgreSQL backend.
Pick one platform for the backend (this, `infra/fly/`, or `infra/railway/`)
- they are not meant to run simultaneously against the same database.
`apps/workers` is a long-running scheduler (see `apps/workers/worker/scheduler.py`),
not a request-driven service, so it does not fit Cloud Run's model well;
deploy it as a Cloud Run **job** on a Cloud Scheduler trigger, or on a small
always-on Compute Engine VM / GKE CronJob instead.

## One-time setup

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com sqladmin.googleapis.com \
  artifactregistry.googleapis.com cloudbuild.googleapis.com

gcloud artifacts repositories create firip --repository-format=docker \
  --location=us-east1

# Cloud SQL: Postgres 15+ so the pgvector extension is available.
gcloud sql instances create firip-db --database-version=POSTGRES_15 \
  --region=us-east1 --tier=db-custom-1-3840
gcloud sql databases create firip --instance=firip-db
gcloud sql users set-password postgres --instance=firip-db --password=CHANGE_ME

# Enable PostGIS + pgvector (via Cloud SQL Auth Proxy or the Cloud Console
# query editor) - both extensions are allowlisted on Cloud SQL Postgres:
#   CREATE EXTENSION IF NOT EXISTS postgis;
#   CREATE EXTENSION IF NOT EXISTS vector;
```

## Build and deploy

```bash
# From the repo root (build context must include packages/shared/data -
# see apps/api/Dockerfile):
gcloud builds submit --config infra/gcp/cloudbuild.yaml .

# First-time env/secret wiring (values from apps/api/.env.example):
gcloud run services update firip-api --region=us-east1 \
  --add-cloudsql-instances=YOUR_PROJECT_ID:us-east1:firip-db \
  --set-env-vars="ENVIRONMENT=production,CORS_ORIGINS=https://YOUR-VERCEL-DOMAIN" \
  --set-secrets="DATABASE_URL=firip-database-url:latest,CLERK_JWKS_URL=firip-clerk-jwks-url:latest,CLERK_ISSUER=firip-clerk-issuer:latest"

# Run the migration once against the new database (via Cloud SQL Auth Proxy
# from your machine, or as a one-off `gcloud run jobs execute` using the
# same image with `alembic upgrade head` as the command):
DATABASE_URL=postgresql+asyncpg://postgres:...@127.0.0.1:5432/firip \
  alembic -c apps/api/alembic.ini upgrade head
```

Then point the frontend at the deployed API: get the service URL with
`gcloud run services describe firip-api --region=us-east1 --format='value(status.url)'`
and set it as `NEXT_PUBLIC_API_URL` in the Vercel project's environment
variables (Project Settings -> Environment Variables), then redeploy the
frontend so the new value is baked into the build (`NEXT_PUBLIC_*` vars are
inlined at build time, not read at runtime).

## Notes

- `apps/api/Dockerfile` already listens on `$PORT` (default 8080), which
  matches Cloud Run's contract - no Dockerfile changes needed.
- This config was authored against Cloud Run/Cloud SQL's documented
  behavior but never run against a real GCP project from the sandbox this
  repo was built in (no GCP credentials or `gcloud` CLI available there).
  Validate the Cloud SQL Auth Proxy connection string format, the
  `--add-cloudsql-instances` flag, and secret names against your actual
  project before the first real deploy.
- `GET /health` (see `apps/api/app/routers/system.py`) never touches the DB
  and requires no auth, so it's safe to use as the Cloud Run startup/liveness
  probe if you configure one explicitly.
