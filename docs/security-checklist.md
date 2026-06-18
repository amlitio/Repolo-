# Security checklist

This checklist tracks the security posture of FIRIP. Items are marked
`[x]` only once actually true in the codebase — not aspirationally.

## Secrets

- [x] No secrets are committed. `.gitignore` excludes `.env`, `.env.local`,
  and all `.env.*` variants except `.env.example` files.
- [x] `apps/api/.env.example` and `apps/web/.env.example` enumerate every
  required environment variable with a comment, but no real value.
- [ ] Secrets in deployed environments (Railway/Fly/Vercel) are provisioned
  through each platform's secret manager — to be done at deploy time, not
  in this repo.

## Authentication & authorization

- [x] Clerk-issued JWTs are verified against Clerk's published JWKS
  endpoint (`CLERK_JWKS_URL`), not a hardcoded shared secret.
- [x] `AUTH_DEV_BYPASS` exists only for local development/tests and is
  `0`/`false` by default. It must never be set in a deployed environment —
  treat any deployment with this flag enabled as a critical misconfiguration.
- [ ] Role-based access control is enforced at the router/dependency layer
  for every endpoint that returns org-scoped or role-restricted data —
  verify per-endpoint as routers are completed (see `apps/api/app/routers`).
- [x] Audit logging (`audit_logs` table) records mutating actions with
  actor, action, target, and timestamp.

## Data handling

- [x] Connectors never fabricate data when an upstream source is
  unavailable or rate-limited; failures are recorded in `source_runs` /
  `data_quality_events` with a `degraded`/`failed` status.
- [x] All currently registered data sources (`packages/shared/data/sources.json`)
  are U.S. Government Work or state open-data licensed; no source requiring
  a paid license or NDA is connected without `license` being populated.
- [ ] PII handling: this MVP's scope (property/county risk, public flood &
  water data) does not ingest personal data beyond user accounts (managed by
  Clerk) and org membership. If a future feature ingests personal data
  (e.g. claimant-level NFIP records), it must be reviewed against this
  checklist before shipping.

## Application security

- [ ] Input validation: Pydantic schemas validate all request bodies;
  spot-check that path/query parameters used in raw SQL (if any) are
  parameterized, never string-interpolated.
- [ ] CORS is restricted to `CORS_ORIGINS` (no wildcard `*` in production).
- [ ] Rate limiting on public-facing endpoints — not yet implemented; track
  as a pre-launch gap if FIRIP is exposed without a CDN/WAF in front.
- [ ] Dependency scanning (`npm audit`, `pip-audit` or equivalent) run in CI
  before each deploy — to be wired into CI, not yet present in this repo.

## Network egress (sandbox-specific note)

This repository was scaffolded in a sandboxed environment with an
egress allowlist that blocked direct access to most government API hosts
(`api.weather.gov`, `api.waterdata.usgs.gov`, `www.fema.gov`, etc.) and
several CDNs (`api.mapbox.com`, `unpkg.com`, `cdn.jsdelivr.net`). As a
result:

- Connector code was written and unit-tested against recorded fixtures,
  **not** validated against live upstream responses in this environment.
  Run `RUN_LIVE_SMOKE_TESTS=1 pytest -m integration` against a real network
  before trusting a connector in production.
- The frontend build was verified to have zero network dependency at
  `next build` time (no shadcn CLI, no `next/font/google`, Mapbox/Clerk
  both degrade gracefully when their tokens are absent) specifically
  because this sandbox could not reach those services either.
- Docker images were never built or run in this sandbox (no Docker daemon
  available) — `docker compose up --build` must be verified in a real
  environment before relying on it.
