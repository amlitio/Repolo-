"""Water schemas, mirroring packages/shared/src/types/api.ts (WaterStation,
WaterObservation)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class WaterStation(BaseModel):
    id: str
    source_id: str
    external_id: str
    name: str
    agency: str
    county_fips: str | None
    latitude: float
    longitude: float
    parameter_types: list[str]


class WaterObservation(BaseModel):
    station_id: str
    parameter: str
    value: float
    unit: str
    observed_at: datetime
    qualifier: str | None


class WaterSummaryLevel(BaseModel):
    station_id: str
    station_name: str
    parameter: str
    value: float
    unit: str
    observed_at: datetime


class WaterSummary(BaseModel):
    station_count: int
    latest_levels: list[WaterSummaryLevel]
    trend: str
