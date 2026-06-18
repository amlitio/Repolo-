"""Procurement/project scaffolding schemas. Ingestion for these tables is
not yet implemented in this MVP - see app/models/procurement.py and
apps/workers/worker/agents/procurement_agent.py (scaffold only)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class ProcurementOpportunity(BaseModel):
    id: str
    source_id: str
    external_id: str
    title: str
    agency: str | None
    county_fips: str | None
    posted_date: date | None
    response_due_date: date | None
    url: str | None
    description: str | None


class Project(BaseModel):
    id: str
    title: str
    county_fips: str | None
    status: str
    description: str | None


class RankedOpportunity(BaseModel):
    opportunity_id: str | None
    project_id: str | None
    title: str
    score: float | None
    rationale: str | None
