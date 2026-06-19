"""Weather alert listing endpoint. Public, read-only.

Serves `weather_alerts` (the normalized NWS feed mirror - see
app/models/weather.py) rather than the generic `alerts` table, because the
response_model here must match packages/shared/src/types/api.ts::WeatherAlert
exactly (event/certainty/urgency/area_desc/etc. are NWS-CAP-specific fields
that the generic, source-agnostic `Alert` record does not carry). The
generic `alerts` table backs the subscription/notification pipeline instead
(see app/routers/subscriptions.py).
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.weather import WeatherAlert as WeatherAlertModel
from app.schemas.common import Paginated
from app.schemas.weather import WeatherAlert

router = APIRouter(tags=["alerts"])


@router.get(
    "/alerts",
    response_model=Paginated[WeatherAlert],
    summary="List weather alerts",
    description="Lists persisted NWS weather alerts, optionally filtered by county FIPS and/or "
    "active status. Never fabricates an alert - returns an empty (but correctly paginated) page "
    "if none are persisted yet.",
)
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    county_fips: str | None = Query(None),
    active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> Paginated[WeatherAlert]:
    stmt = select(WeatherAlertModel)
    if active is not None:
        stmt = stmt.where(WeatherAlertModel.is_active == active)
    stmt = stmt.order_by(WeatherAlertModel.effective_at.desc())
    result = await db.execute(stmt)
    rows = result.scalars().all()

    if county_fips:
        rows = [r for r in rows if county_fips in json.loads(r.county_fips_json)]

    total = len(rows)
    start = (page - 1) * page_size
    page_items = rows[start : start + page_size]
    return Paginated[WeatherAlert](
        items=[
            WeatherAlert(
                id=r.id,
                event=r.event,
                severity=r.severity,
                certainty=r.certainty,
                urgency=r.urgency,
                headline=r.headline,
                description=r.description,
                area_desc=r.area_desc,
                county_fips=json.loads(r.county_fips_json),
                effective_at=r.effective_at,
                expires_at=r.expires_at,
                source_id=r.source_id,
            )
            for r in page_items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )
