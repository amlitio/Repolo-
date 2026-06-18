# Investor pitch (internal notes)

## Problem

Florida sits at the intersection of the country's highest flood exposure
and the most fragmented public data landscape for assessing it: FEMA flood
maps, NOAA weather/hurricane products, USGS and five separate water
management districts' telemetry, and county-level GIS/procurement portals
are each maintained independently, in different formats, with no shared
identifier scheme and wildly inconsistent API maturity (one of Florida's
five water management districts, SRWMD, has no public API at all today).
Anyone trying to assess flood/water risk for a property, a portfolio, or a
county has to manually reconcile a dozen-plus sources.

## What FIRIP does

FIRIP normalizes that landscape into one registry (`packages/shared/data/`)
and one map-first product: live flood/weather/water layers, transparent
property and county risk scoring (0-100 + A-F, with a factor-level
explanation rather than a black-box number), and role-specific dashboards
for government, engineering, investment, and emergency-management users.

## Why now

- FEMA's NFHL, NOAA's Alerts API and NHC GIS feeds, and USGS's OGC water
  data API are all modern, queryable, public-domain REST/GIS services —
  the raw data has gotten more accessible even though no one has unified
  it for Florida specifically.
- Climate-driven flood risk is increasingly priced into insurance,
  lending, and resilience-grant decisions, raising willingness to pay for
  a credible, explainable risk score over a black-box one.

## What's built vs. what's ahead (honest status)

This repository is an MVP scaffold, not a finished commercial product:

- **Built**: the full data model (~35 tables), the REST contract, real
  (not mocked) connector logic for FEMA/NOAA/NHC/USGS/the four WMDs with
  public APIs, the scoring engine, the map-first UI shell, RBAC/audit
  logging scaffolding, and a 67-county registry (8 counties fully
  verified, 59 flagged for follow-up rather than guessed).
- **Ahead**: live-network validation of every connector outside a
  sandboxed dev environment, completing county-level URL verification,
  activating procurement/construction modules, and any billing
  integration. See `docs/roadmap.md` for the sequencing.

This honesty is deliberate: a risk-scoring product's core asset is
credibility, and overclaiming verification status in an investor deck
would undermine the exact thing the product sells.
