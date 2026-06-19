"""Flood zone schema, mirroring packages/shared/src/types/api.ts::FloodZone."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel


class FloodZone(BaseModel):
    id: str
    fips: str
    zone_label: str
    is_special_flood_hazard_area: bool
    base_flood_elevation: float | None
    geometry: dict[str, Any]
    effective_date: date | None


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: dict[str, Any]
    properties: dict[str, Any]


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[GeoJSONFeature]
