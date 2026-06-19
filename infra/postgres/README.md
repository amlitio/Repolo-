# Local Postgres + PostGIS + pgvector image

No single official Docker image ships both PostGIS and pgvector, so
`Dockerfile` layers the `postgresql-16-postgis-3` and `postgresql-16-pgvector`
Debian packages onto the official `postgres:16-bookworm` image, and
`init-extensions.sql` runs `CREATE EXTENSION postgis;` / `CREATE EXTENSION
vector;` once on first container start (via Postgres's
`docker-entrypoint-initdb.d` convention).

## What's been verified, and how

- The two extensions (PostGIS 3.4.2, pgvector 0.6.0) and the
  `postgresql-16-postgis-3` / `postgresql-16-pgvector` apt package names were
  installed and exercised directly against a real **Postgres 16** instance
  (Ubuntu host packages, not this Dockerfile) in the environment this image
  was authored in: `CREATE EXTENSION postgis; CREATE EXTENSION vector;`
  succeeded, and `alembic upgrade head` (from `apps/api/alembic`) ran
  end-to-end against it - every geometry column came out as a real
  PostGIS `geometry(...)` type with a GiST spatial index auto-created, and
  the `embeddings.vector` column came out as a real pgvector `vector(1536)`.
  See `apps/api/app/models/types.py` for the column types this proves out.
- **This Dockerfile's `docker build` itself was never run** - the sandbox
  this repo was built in has the `docker` CLI but no privilege to start a
  Docker daemon (`dockerd` fails with `ulimit: Operation not permitted`,
  consistent with running inside an unprivileged container). The package
  names are the same well-known PGDG-published packages either way, but
  verify a real `docker compose -f infra/docker-compose.yml up --build` once
  in an environment with a working Docker daemon before relying on it.

## Managed Postgres (Railway/Fly/RDS/etc.)

This image is for local dev / CI only. A managed provider's Postgres almost
certainly isn't running this custom image, so run the two `CREATE EXTENSION`
statements in `init-extensions.sql` manually (one-off `psql` session) before
the first `alembic upgrade head` against it - see
[`../railway/README.md`](../railway/README.md).
