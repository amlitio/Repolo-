# Data source & county registry methodology

FIRIP's data-source and county registries live in
[`packages/shared/data/`](../../packages/shared/data/) as JSON, not in code,
so the same file is read by both the TypeScript frontend
(`packages/shared/src/registry/index.ts`) and the Python backend
(`apps/api/app/config.py` resolves the path relative to the repo root and
loads it at startup). There is exactly one copy of each registry.

## `sources.json` — verification status

Every entry has a `data_quality_status` of `verified`, `needs_verification`,
or `degraded`, and a `verified_at` date (or `null`). This is an honesty
mechanism, not decoration: connectors and docs must not claim a source works
until someone has actually confirmed its base URL, auth requirements, and
license.

As of the last verification pass (2026-06-18):

| Status | Count | Examples |
| --- | --- | --- |
| `verified` | 15 | FEMA NFHL, OpenFEMA disaster declarations, NWS Alerts API, NHC GIS, NOAA CO-OPS, USGS Water Data OGC API, SFWMD/SJRWMD/SWFWMD/NWFWMD GIS portals, FL statewide GIS portal, FDEP, FDOT, SAM.gov Opportunities v2, Census API |
| `needs_verification` | 5 | OpenFEMA Hazard Mitigation Assistance Projects (dataset name should be reconfirmed against FEMA's current catalog), MyFloridaMarketPlace, FloridaCommerce economic data, Grants.gov search |
| `degraded` | 1 | Suwannee River Water Management District (SRWMD) — no public REST/GIS API was found during research; SRWMD publishes through a document center rather than a queryable service. Connectors for this source must report `degraded` in `source_runs`, not fabricate observations. |

Before any source backing a production feature is enabled for real
ingestion, confirm:

1. The base URL still resolves and returns the expected schema.
2. Authentication requirements (most are `auth_required: false` — public
   federal/state open data — but always re-check before shipping).
2. The license. Everything currently in the registry is U.S. Government
   Work / public domain or a state open-data license; if a future source
   is added under a more restrictive license, record it in the `license`
   field before ingestion is turned on.

## `counties.json` — verification status

All 67 Florida counties are present with FIPS code, name, region, and water
management district membership (sourced from the authoritative FIPS
reference at `kjhealy/fips-codes` and the five Florida WMDs' published
county-coverage lists, including counties split across more than one
district).

GIS open-data / procurement / permits / parcels portal URLs are the part
that needed per-county manual research and is **not** fully done:

- **8 counties** (`Broward 12011`, `Duval 12031`, `Hillsborough 12057`,
  `Lee 12071`, `Miami-Dade 12086`, `Orange 12095`, `Palm Beach 12099`,
  `Pinellas 12103`) are `data_quality_status: "partially_verified"` with
  real, checked GIS portal URLs.
- The remaining **59 counties** are `data_quality_status:
  "needs_verification"` with `null` URL fields. This is the explicit,
  intentional state of an honest scaffold — those URLs were not invented.

### Closing the gap

The Data Discovery Agent (`apps/workers/worker/agents`) is the long-term
mechanism for completing the remaining 59 counties: it is designed to crawl
each county's open-data catalog, attempt to identify GIS/procurement/permits
/parcels endpoints, and flip `data_quality_status` to `partially_verified`
or `verified` once a human or an automated check confirms the URL resolves
and returns the expected data. Until an entry is updated by that process (or
by a manual research pass), `apps/web` and `apps/api` must treat a `null`
URL as "not yet available" — never as license to guess a URL pattern from
the 8 verified counties and extrapolate it to the other 59.

## `scoring.json` — risk model

`scoring.json` holds `model_version`, `property_risk_weights`,
`county_risk_weights`, and `grade_thresholds`. Both weight maps sum to 1.0.
Changing a weight or threshold is a model change: bump `model_version` so
that previously persisted `property_risk_scores` / `county_risk_scores`
rows (which are stamped with the `model_version` active when they were
computed) remain distinguishable from scores computed under a new model.
