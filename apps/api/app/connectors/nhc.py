"""National Hurricane Center (NHC) GIS connector.

LIMITATIONS (documented per project spec): NHC's GIS products
(https://www.nhc.noaa.gov/gis/) are distributed as Shapefile/KMZ/GRIB2
archives, not a JSON REST API. A full implementation would need to download
and unzip a shapefile bundle, then parse it with a library like `fiona`/`shapely`
which is out of scope for this MVP's dependency footprint.

This connector is therefore best-effort and metadata-level only:
- `fetch_raw()` retrieves the NHC GIS index page / known product JSON
  (NHC also publishes a lightweight "CurrentStorms.json" active-storm feed at
  https://www.nhc.noaa.gov/CurrentStorms.json, which IS plain JSON and is what
  this connector targets) rather than full shapefile geometry.
- `normalize()` produces HurricaneTrack-shaped records with geometry reduced
  to a Point at the storm's current center (when available) instead of the
  full forecast cone/track polyline, which would require shapefile parsing.
- Full cone-of-uncertainty / track-line polygons are NOT extracted by this
  connector. A future iteration should add shapefile parsing if hurricane
  track polygons become a hard product requirement.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx
from pydantic import BaseModel

from app.connectors.base import Connector

NHC_CURRENT_STORMS_URL = "https://www.nhc.noaa.gov/CurrentStorms.json"


class HurricaneTrackRecord(BaseModel):
    storm_id: str
    name: str
    season: int
    advisory_num: str
    classification: str
    issued_at: datetime
    geometry: dict[str, Any]


class NhcConnector(Connector[HurricaneTrackRecord]):
    def __init__(self) -> None:
        super().__init__(source_id="nhc-gis")

    async def fetch_raw(self, timeout: float = 30.0) -> dict:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(NHC_CURRENT_STORMS_URL)
            response.raise_for_status()
            return response.json()

    def normalize(self, raw: dict) -> list[HurricaneTrackRecord]:
        records: list[HurricaneTrackRecord] = []
        for storm in raw.get("activeStorms", []):
            lat = storm.get("latitudeNumeric")
            lon = storm.get("longitudeNumeric")
            geometry: dict[str, Any] = (
                {"type": "Point", "coordinates": [lon, lat]} if lat is not None and lon is not None else {}
            )
            issued_raw = storm.get("lastUpdate")
            try:
                issued_at = datetime.fromisoformat(issued_raw) if issued_raw else datetime.now(UTC)
            except ValueError:
                issued_at = datetime.now(UTC)
            records.append(
                HurricaneTrackRecord(
                    storm_id=str(storm.get("id", storm.get("binNumber", "unknown"))),
                    name=storm.get("name", "Unknown"),
                    season=issued_at.year,
                    advisory_num=str(storm.get("advisoryNumber", "")),
                    classification=storm.get("classification", "unknown"),
                    issued_at=issued_at,
                    geometry=geometry,
                )
            )
        return records
