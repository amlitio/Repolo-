-- Runs once, automatically, on first container start (docker-entrypoint-initdb.d
-- scripts only execute against an empty data directory). Manually-provisioned
-- managed Postgres (Railway/Fly) must run these same two statements once.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
