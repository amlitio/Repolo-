"""USGS Water Data OGC API connector.

Targets the "monitoring-locations" and "daily" (daily values) collections
documented at https://api.waterdata.usgs.gov/docs/ogcapi/. This replaces the
legacy waterservices.usgs.gov endpoints (decommissioning early 2027) per
sources.json's notes for "usgs-water-data-ogcapi".
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx
from pydantic import BaseModel

from app.connectors.base import Connector
from app.core.registry import get_registry


class UsgsStationRecord(BaseModel):
    external_id: str
    name: str
    county_fips: str | None
    latitude: float
    longitude: float
    parameter_types: list[str]


class UsgsObservationRecord(BaseModel):
    station_external_id: str
    parameter: str
    value: float
    unit: str
    observed_at: datetime
    qualifier: str | None


class UsgsWaterStationsConnector(Connector[UsgsStationRecord]):
    """Fetches monitoring-locations within Florida."""

    def __init__(self) -> None:
        super().__init__(source_id="usgs-water-data-ogcapi")

    def _base_url(self) -> str:
        source = get_registry().get_source_by_id(self.source_id)
        if source is None:
            raise ValueError(f"Unknown source id: {self.source_id}")
        return source["base_url"].rstrip("/")

    async def fetch_raw(self, state_fips: str = "12", limit: int = 1000, timeout: float = 30.0) -> dict:
        url = f"{self._base_url()}/collections/monitoring-locations/items"
        params: dict[str, Any] = {"state_fips_code": state_fips, "f": "json", "limit": limit}
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    def normalize(self, raw: dict) -> list[UsgsStationRecord]:
        records: list[UsgsStationRecord] = []
        for feature in raw.get("features", []):
            props = feature.get("properties", {}) or {}
            geometry = feature.get("geometry") or {}
            coords = geometry.get("coordinates") or [None, None]
            lon, lat = coords[0], coords[1]
            if lat is None or lon is None:
                continue
            county_cd = props.get("county_code")
            county_fips = f"12{county_cd}" if county_cd else None
            records.append(
                UsgsStationRecord(
                    external_id=props.get("monitoring_location_id", feature.get("id", "")),
                    name=props.get("monitoring_location_name", "Unknown station"),
                    county_fips=county_fips,
                    latitude=float(lat),
                    longitude=float(lon),
                    parameter_types=props.get("parameter_codes", []) or [],
                )
            )
        return records


class UsgsDailyValuesConnector(Connector[UsgsObservationRecord]):
    """Fetches daily values for a given monitoring location."""

    def __init__(self) -> None:
        super().__init__(source_id="usgs-water-data-ogcapi")

    def _base_url(self) -> str:
        source = get_registry().get_source_by_id(self.source_id)
        if source is None:
            raise ValueError(f"Unknown source id: {self.source_id}")
        return source["base_url"].rstrip("/")

    async def fetch_raw(
        self, monitoring_location_id: str, limit: int = 100, timeout: float = 30.0
    ) -> dict:
        url = f"{self._base_url()}/collections/daily/items"
        params: dict[str, Any] = {
            "monitoring_location_id": monitoring_location_id,
            "f": "json",
            "limit": limit,
        }
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    def normalize(self, raw: dict) -> list[UsgsObservationRecord]:
        records: list[UsgsObservationRecord] = []
        for feature in raw.get("features", []):
            props = feature.get("properties", {}) or {}
            value = props.get("value")
            observed_raw = props.get("time")
            if value is None or not observed_raw:
                continue
            records.append(
                UsgsObservationRecord(
                    station_external_id=props.get("monitoring_location_id", ""),
                    parameter=props.get("parameter_code", "unknown"),
                    value=float(value),
                    unit=props.get("unit_of_measure", ""),
                    observed_at=datetime.fromisoformat(observed_raw),
                    qualifier=props.get("qualifier"),
                )
            )
        return records
