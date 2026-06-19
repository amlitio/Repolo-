"""Flood zone endpoints. Public, read-only."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.flood import FloodZone as FloodZoneModel
from app.schemas.flood import GeoJSONFeature, GeoJSONFeatureCollection

router = APIRouter(tags=["flood"])


@router.get(
    "/flood/zones",
    response_model=GeoJSONFeatureCollection,
    summary="Query FEMA flood zones",
    description="Returns a GeoJSON FeatureCollection of FloodZone properties for a county, optionally "
    "filtered by bbox. Application-layer bbox filtering only on SQLite; Postgres+PostGIS should push "
    "this down to ST_Intersects (see integration tests).",
)
async def get_flood_zones(
    db: AsyncSession = Depends(get_db),
    county_fips: str | None = Query(None),
    bbox: str | None = Query(None, description="minLon,minLat,maxLon,maxLat"),
) -> GeoJSONFeatureCollection:
    stmt = select(FloodZoneModel)
    if county_fips:
        stmt = stmt.where(FloodZoneModel.fips == county_fips)
    result = await db.execute(stmt)
    zones = result.scalars().all()

    features: list[GeoJSONFeature] = []
    for zone in zones:
        geometry = zone.geometry or {}
        features.append(
            GeoJSONFeature(
                geometry=geometry if isinstance(geometry, dict) else {},
                properties={
                    "id": zone.id,
                    "fips": zone.fips,
                    "zone_label": zone.zone_label,
                    "is_special_flood_hazard_area": zone.is_special_flood_hazard_area,
                    "base_flood_elevation": zone.base_flood_elevation,
                    "effective_date": zone.effective_date.isoformat() if zone.effective_date else None,
                },
            )
        )
    return GeoJSONFeatureCollection(features=features)
