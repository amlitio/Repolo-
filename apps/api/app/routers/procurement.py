"""Procurement/project scaffolding endpoints.

Ingestion for procurement_opportunities/projects/opportunity_scores is not
yet implemented in this MVP (see apps/workers/worker/agents/procurement_agent.py,
which is a scaffold-only class per the product plan). These endpoints return
real, correctly-shaped (but currently empty) paginated responses rather than
fake rows, and document that fact in their OpenAPI description.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.procurement import ProcurementOpportunity as ProcurementOpportunityModel
from app.models.procurement import Project as ProjectModel
from app.schemas.common import Paginated
from app.schemas.procurement import ProcurementOpportunity, Project, RankedOpportunity

router = APIRouter(tags=["procurement"])


@router.get(
    "/procurement/opportunities",
    response_model=Paginated[ProcurementOpportunity],
    summary="List procurement opportunities",
    description="INGESTION PENDING: the procurement_opportunities table is scaffolded but not yet "
    "populated by an ingestion pipeline (SAM.gov/Grants.gov/MyFloridaMarketPlace connectors are not "
    "built in this MVP). This endpoint returns a real, correctly-shaped paginated response that will "
    "currently be empty - not fabricated rows.",
)
async def list_procurement_opportunities(
    db: AsyncSession = Depends(get_db),
    county_fips: str | None = Query(None),
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> Paginated[ProcurementOpportunity]:
    stmt = select(ProcurementOpportunityModel)
    if county_fips:
        stmt = stmt.where(ProcurementOpportunityModel.county_fips == county_fips)
    if q:
        stmt = stmt.where(ProcurementOpportunityModel.title.ilike(f"%{q}%"))
    result = await db.execute(stmt)
    rows = result.scalars().all()
    total = len(rows)
    start = (page - 1) * page_size
    page_items = rows[start : start + page_size]
    return Paginated[ProcurementOpportunity](
        items=[ProcurementOpportunity.model_validate(r) for r in page_items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/projects",
    response_model=Paginated[Project],
    summary="List tracked projects",
    description="SCAFFOLD: projects table exists but is not yet populated by an ingestion pipeline in "
    "this MVP.",
)
async def list_projects(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> Paginated[Project]:
    result = await db.execute(select(ProjectModel))
    rows = result.scalars().all()
    total = len(rows)
    start = (page - 1) * page_size
    page_items = rows[start : start + page_size]
    return Paginated[Project](
        items=[Project.model_validate(r) for r in page_items], total=total, page=page, page_size=page_size
    )


@router.get(
    "/opportunities/rank",
    response_model=list[RankedOpportunity],
    summary="Ranked procurement/project opportunities",
    description="NOT YET SCORED: opportunity ranking depends on the procurement ingestion pipeline and "
    "opportunity_scores being populated, neither of which ship in this MVP. Always returns an empty list "
    "today rather than a fabricated ranking.",
)
async def rank_opportunities() -> list[RankedOpportunity]:
    return []
