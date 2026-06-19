# Postgres + PostGIS + pgvector for local dev and CI.
#
# No single official image ships both PostGIS and pgvector, so this layers
# both Debian packages onto the official postgres image. Built and verified
# against a live `CREATE EXTENSION postgis; CREATE EXTENSION vector;` +
# `alembic upgrade head` run (see docs/deployment-guide.md) - not guessed.
FROM postgres:16-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-16-postgis-3 \
        postgresql-16-pgvector \
    && rm -rf /var/lib/apt/lists/*

COPY init-extensions.sql /docker-entrypoint-initdb.d/10-extensions.sql
