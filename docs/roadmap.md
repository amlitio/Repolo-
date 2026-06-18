# Roadmap

## MVP scope (this build): Risk + Water

The first acceptance gate is a map-first Risk + Water intelligence product
for Florida:

- FEMA flood zones, NOAA/NWS alerts, NHC hurricane tracks, USGS + Florida
  water management district station telemetry, all rendered as toggleable
  map layers.
- Property and county risk scoring (0-100 + A-F grade) with a transparent,
  versioned, factor-level explanation.
- Hybrid search and a research agent (RAG) over ingested documents, gated
  honestly on LLM API key presence.
- Alerts/subscriptions and role-based dashboards (executive, government,
  engineering, contractor, investor, emergency management).
- Clerk auth + RBAC, audit logging.

Procurement and construction modules are **production-scaffolded** (real
database tables, real model classes, agent stubs) but intentionally not
wired into the ingestion scheduler or the acceptance criteria for this MVP.

## Near-term (post-MVP)

- Complete the county registry: drive `needs_verification` ->
  `verified`/`partially_verified` for the 59 counties not yet manually
  checked, via the Data Discovery Agent plus spot manual review.
- Turn on live connector smoke tests in a real (non-sandboxed) CI
  environment; confirm FEMA/NOAA/USGS/WMD responses match the fixtures the
  unit tests were built against, and update fixtures if upstream schemas
  have shifted.
- Stand up the real Postgres + PostGIS + pgvector environment (Railway or
  Fly) and run `alembic upgrade head` against it for the first time outside
  a sandbox.
- Wire notifications (email/SMS/webhook) for the `subscriptions` /
  `alerts` tables — currently scaffolded with a "simulate" mode when no
  provider is configured.

## Mid-term

- Activate the Procurement Agent: ingest SAM.gov Opportunities v2,
  Grants.gov, and MyFloridaMarketPlace (once its API access/license is
  confirmed) into `procurement_opportunities`, and implement
  `GET /opportunities/rank` against `opportunity_scores`.
- Activate the Construction Agent against `projects` /
  `funding_sources` for tracked mitigation/infrastructure projects.
- Expand risk scoring with additional factors as new verified sources come
  online (e.g. drought indices, NFIP claims data at finer geography),
  bumping `scoring.json`'s `model_version` for each material change.

## Longer-term

- Multi-state expansion of the same architecture (the registry pattern in
  `packages/shared/data/` was designed to generalize beyond Florida: swap
  in a new `counties.json`/`sources.json` rather than rewriting code).
- Public API tier for third-party integrators, with API-key-based auth
  alongside Clerk session auth.
