"""FEMA National Flood Hazard Layer (NFHL) connector.

Queries the NFHL ArcGIS MapServer (base_url from sources.json id
"fema-nfhl") for flood zone polygons by bbox or county FIPS. The NFHL
MapServer's "Flood Hazard Zones" layer is conventionally layer index 28
(https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer) - this
is documented in FEMA's NFHL technical reference; we expose it as a
constructor default but allow override since FEMA has changed layer
indices between MapServer revisions in the past.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import httpx
from pydantic import BaseModel

from app.connectors.base import Connector
from app.core.registry import get_registry

NFHL_FLOOD_HAZARD_ZONES_LAYER = 28


class NfhlFloodZoneRecord(BaseModel):
    external_id: str
    fips: str | None
    zone_label: str
    is_special_flood_hazard_area: bool
    base_flood_elevation: float | None
    geometry: dict[str, Any]
    effective_date: date | None


def _is_sfha(zone_label: str) -> bool:
    """SFHA zones start with A or V per FEMA's FIRM zone designation scheme
    (e.g. A, AE, AH, AO, A99, V, VE). Zones B/C/X/D are not SFHA."""
    return zone_label.strip().upper().startswith(("A", "V"))


class FemaNfhlConnector(Connector[NfhlFloodZoneRecord]):
    def __init__(self, layer_id: int = NFHL_FLOOD_HAZARD_ZONES_LAYER) -> None:
        super().__init__(source_id="fema-nfhl")
        self.layer_id = layer_id

    def _base_url(self) -> str:
        source = get_registry().get_source_by_id(self.source_id)
        if source is None:
            raise ValueError(f"Unknown source id: {self.source_id}")
        return source["base_url"]

    async def fetch_raw(
        self,
        bbox: tuple[float, float, float, float] | None = None,
        county_fips: str | None = None,
        timeout: float = 30.0,
    ) -> dict:
        """Query the ArcGIS REST `query` endpoint for the flood-hazard-zones
        layer, filtered by bbox (minLon,minLat,maxLon,maxLat) and/or county
        FIPS (DFIRM_ID/CO_FIPS field, schema varies by FEMA region)."""

        url = f"{self._base_url()}/{self.layer_id}/query"
        params: dict[str, Any] = {
            "f": "geojson",
            "outFields": "*",
            "where": "1=1",
        }
        if bbox is not None:
            min_lon, min_lat, max_lon, max_lat = bbox
            params["geometry"] = f"{min_lon},{min_lat},{max_lon},{max_lat}"
            params["geometryType"] = "esriGeometryEnvelope"
            params["inSR"] = "4326"
            params["spatialRel"] = "esriSpatialRelIntersects"
        if county_fips is not None:
            params["where"] = f"CO_FIPS='{county_fips}'"

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    def normalize(self, raw: dict) -> list[NfhlFloodZoneRecord]:
        records: list[NfhlFloodZoneRecord] = []
        for feature in raw.get("features", []):
            props = feature.get("properties", {}) or {}
            zone_label = props.get("FLD_ZONE") or props.get("ZONE_SUBTY") or "UNKNOWN"
            effective_raw = props.get("EFF_DATE")
            effective_date = None
            if effective_raw:
                try:
                    effective_date = date.fromisoformat(str(effective_raw)[:10])
                except ValueError:
                    effective_date = None
            records.append(
                NfhlFloodZoneRecord(
                    external_id=str(props.get("OBJECTID") or props.get("FLD_AR_ID") or ""),
                    fips=props.get("CO_FIPS"),
                    zone_label=zone_label,
                    is_special_flood_hazard_area=_is_sfha(zone_label),
                    base_flood_elevation=props.get("STATIC_BFE"),
                    geometry=feature.get("geometry") or {},
                    effective_date=effective_date,
                )
            )
        return records
