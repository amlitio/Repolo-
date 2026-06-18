# Fly.io deployment (alternative to Railway)

`infra/fly/api.fly.toml` and `infra/fly/workers.fly.toml` are alternatives
to the Railway configs in `infra/railway/` for teams that prefer Fly. Pick
one platform for the backend — they are not meant to run simultaneously
against the same database.

## Setup

```bash
flyctl postgres create --name firip-db --region mia
flyctl postgres connect -a firip-db
# inside psql:
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

# from the repo root (build context must include packages/shared/data):
flyctl launch --config infra/fly/api.fly.toml --dockerfile apps/api/Dockerfile --no-deploy
flyctl secrets set DATABASE_URL=... CLERK_JWKS_URL=... CLERK_ISSUER=... -a firip-api
flyctl deploy --config infra/fly/api.fly.toml

flyctl launch --config infra/fly/workers.fly.toml --dockerfile apps/workers/Dockerfile --no-deploy
flyctl secrets set DATABASE_URL=... -a firip-workers
flyctl deploy --config infra/fly/workers.fly.toml
```

## Notes

- `primary_region = "mia"` (Miami) is chosen for proximity to Florida data
  sources and the product's target users; change if Fly capacity or
  pricing in that region doesn't work for you.
- These configs were authored against Fly's documented `fly.toml` schema
  but never run against a real Fly account from the sandbox this repo was
  built in (no network access to fly.io). Validate `internal_port`,
  the Dockerfile `EXPOSE` port, and the `/health` endpoint path against the
  actual `apps/api` implementation before the first deploy.
