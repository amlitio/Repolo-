"""Water station/observation/summary endpoints. Public, read-only."""

from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.water import WaterObservation as WaterObservationModel
from app.models.water import WaterStation as WaterStationModel
from app.schemas.common import Paginated
from app.schemas.water import WaterObservation, WaterStation, WaterSummary, WaterSummaryLevel

router = APIRouter(tags=["water"])


def _to_station_schema(model: WaterStationModel) -> WaterStation:
    return WaterStation(
        id=model.id,
        source_id=model.source_id,
        external_id=model.external_id,
        name=model.name,
        agency=model.agency,
        county_fips=model.county_fips,
        latitude=model.latitude,
        longitude=model.longitude,
        parameter_types=json.loads(model.parameter_types_json),
    )


@router.get(
    "/water/stations",
    response_model=Paginated[WaterStation],
    summary="List water monitoring stations",
)
async def list_water_stations(
    db: AsyncSession = Depends(get_db),
    county_fips: str | None = Query(None),
    source_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> Paginated[WaterStation]:
    stmt = select(WaterStationModel)
    if county_fips:
        stmt = stmt.where(WaterStationModel.county_fips == county_fips)
    if source_id:
        stmt = stmt.where(WaterStationModel.source_id == source_id)
    result = await db.execute(stmt)
    stations = result.scalars().all()
    total = len(stations)
    start = (page - 1) * page_size
    page_items = stations[start : start + page_size]
    return Paginated[WaterStation](
        items=[_to_station_schema(s) for s in page_items], total=total, page=page, page_size=page_size
    )


@router.get(
    "/water/observations",
    response_model=Paginated[WaterObservation],
    summary="List water observations for a station",
)
async def list_water_observations(
    db: AsyncSession = Depends(get_db),
    station_id: str | None = Query(None),
    parameter: str | None = Query(None),
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> Paginated[WaterObservation]:
    stmt = select(WaterObservationModel)
    if station_id:
        stmt = stmt.where(WaterObservationModel.station_id == station_id)
    if parameter:
        stmt = stmt.where(WaterObservationModel.parameter == parameter)
    if start:
        stmt = stmt.where(WaterObservationModel.observed_at >= start)
    if end:
        stmt = stmt.where(WaterObservationModel.observed_at <= end)
    stmt = stmt.order_by(WaterObservationModel.observed_at.desc())
    result = await db.execute(stmt)
    observations = result.scalars().all()
    total = len(observations)
    page_start = (page - 1) * page_size
    page_items = observations[page_start : page_start + page_size]
    return Paginated[WaterObservation](
        items=[
            WaterObservation(
                station_id=o.station_id,
                parameter=o.parameter,
                value=o.value,
                unit=o.unit,
                observed_at=o.observed_at,
                qualifier=o.qualifier,
            )
            for o in page_items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/water/summary",
    response_model=WaterSummary,
    summary="County-level water station summary",
    description="Returns station count, latest observed levels, and a simple rising/falling/stable trend "
    "for a county.",
)
async def water_summary(
    db: AsyncSession = Depends(get_db),
    county_fips: str = Query(...),
) -> WaterSummary:
    stations_result = await db.execute(
        select(WaterStationModel).where(WaterStationModel.county_fips == county_fips)
    )
    stations = stations_result.scalars().all()
    station_ids = [s.id for s in stations]

    latest_levels: list[WaterSummaryLevel] = []
    trend = "stable"
    if station_ids:
        obs_result = await db.execute(
            select(WaterObservationModel)
            .where(WaterObservationModel.station_id.in_(station_ids))
            .order_by(WaterObservationModel.observed_at.desc())
        )
        observations = obs_result.scalars().all()
        seen_stations: set[str] = set()
        station_by_id = {s.id: s for s in stations}
        recent_values: list[float] = []
        for obs in observations:
            if obs.station_id in seen_stations:
                continue
            seen_stations.add(obs.station_id)
            station = station_by_id.get(obs.station_id)
            latest_levels.append(
                WaterSummaryLevel(
                    station_id=obs.station_id,
                    station_name=station.name if station else "Unknown",
                    parameter=obs.parameter,
                    value=obs.value,
                    unit=obs.unit,
                    observed_at=obs.observed_at,
                )
            )
            recent_values.append(obs.value)

        if len(recent_values) >= 2:
            delta = recent_values[0] - recent_values[-1]
            if delta > 0.05 * abs(recent_values[-1] or 1):
                trend = "rising"
            elif delta < -0.05 * abs(recent_values[-1] or 1):
                trend = "falling"

    return WaterSummary(station_count=len(stations), latest_levels=latest_levels, trend=trend)
