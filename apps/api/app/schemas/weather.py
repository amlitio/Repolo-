"""Weather/hurricane schemas, mirroring packages/shared/src/types/api.ts
(WeatherAlert, HurricaneTrack)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

SeverityLevel = str  # "Extreme" | "Severe" | "Moderate" | "Minor" | "Unknown"


class WeatherAlert(BaseModel):
    id: str
    event: str
    severity: SeverityLevel
    certainty: str
    urgency: str
    headline: str
    description: str
    area_desc: str
    county_fips: list[str]
    effective_at: datetime
    expires_at: datetime
    source_id: str


class HurricaneTrack(BaseModel):
    storm_id: str
    name: str
    season: int
    advisory_num: str
    classification: str
    issued_at: datetime
    geometry: dict[str, Any]
