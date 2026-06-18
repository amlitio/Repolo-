"""Generic ArcGIS Hub/FeatureServer client, reused by the four Florida Water
Management District connectors that expose an ArcGIS Hub
(SFWMD/SJRWMD/SWFWMD/NWFWMD). Each instance is parameterized by the
district's `base_url` taken directly from sources.json - no per-district
subclassing needed since the access pattern is identical.

SRWMD ("srwmd-gis-data") is marked "degraded" in sources.json: it has no
public ArcGIS Hub at verification time, only a document center with zipped
shapefile archives. `SrwmdConnector` below subclasses Connector and overrides
`is_supported()` to return False so `run()` reports a clean "degraded"
status (not an error, not fake data) rather than attempting an API call
that doesn't exist.
"""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel

from app.connectors.base import Connector
from app.core.registry import get_registry


class WmdFeatureRecord(BaseModel):
    external_id: str
    layer_name: str
    geometry: dict[str, Any]
    properties: dict[str, Any]


class WmdArcGisConnector(Connector[WmdFeatureRecord]):
    """Generic ArcGIS FeatureServer query client.

    `source_id` must be one of the WMD GIS hub entries in sources.json
    (sfwmd-gis-open-data, sjrwmd-gis-open-data, swfwmd-gis-open-data,
    nwfwmd-gis-open-data). `feature_server_url` may be supplied directly when
    the specific FeatureServer layer URL differs from the Hub's base_url
    (ArcGIS Hub portals typically front many distinct FeatureServer
    services; the Hub base_url alone is not a queryable REST endpoint).
    """

    def __init__(self, source_id: str, feature_server_url: str | None = None) -> None:
        super().__init__(source_id=source_id)
        self._feature_server_url_override = feature_server_url

    def _base_url(self) -> str:
        if self._feature_server_url_override:
            return self._feature_server_url_override
        source = get_registry().get_source_by_id(self.source_id)
        if source is None:
            raise ValueError(f"Unknown source id: {self.source_id}")
        return source["base_url"]

    async def fetch_raw(
        self,
        layer_id: int = 0,
        where: str = "1=1",
        out_fields: str = "*",
        timeout: float = 30.0,
    ) -> dict:
        url = f"{self._base_url().rstrip('/')}/{layer_id}/query"
        params: dict[str, Any] = {"f": "geojson", "where": where, "outFields": out_fields}
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    def normalize(self, raw: dict) -> list[WmdFeatureRecord]:
        records: list[WmdFeatureRecord] = []
        for feature in raw.get("features", []):
            props = feature.get("properties", {}) or {}
            records.append(
                WmdFeatureRecord(
                    external_id=str(props.get("OBJECTID", feature.get("id", ""))),
                    layer_name=props.get("LAYER_NAME", self.source_id),
                    geometry=feature.get("geometry") or {},
                    properties=props,
                )
            )
        return records


def make_sfwmd_connector() -> WmdArcGisConnector:
    return WmdArcGisConnector(source_id="sfwmd-gis-open-data")


def make_sjrwmd_connector() -> WmdArcGisConnector:
    return WmdArcGisConnector(source_id="sjrwmd-gis-open-data")


def make_swfwmd_connector() -> WmdArcGisConnector:
    return WmdArcGisConnector(source_id="swfwmd-gis-open-data")


def make_nwfwmd_connector() -> WmdArcGisConnector:
    return WmdArcGisConnector(source_id="nwfwmd-gis-open-data")


class SrwmdConnector(Connector[WmdFeatureRecord]):
    """SRWMD has no public ArcGIS Hub at verification time (sources.json
    marks "srwmd-gis-data" as data_quality_status="degraded", access_method
    "Document Center (shapefile archives)"). This connector always reports
    unsupported/degraded rather than guessing at an API that doesn't exist
    or fabricating data."""

    def __init__(self) -> None:
        super().__init__(source_id="srwmd-gis-data")

    def is_supported(self) -> bool:
        return False

    async def fetch_raw(self, **kwargs: Any) -> Any:
        raise NotImplementedError(
            "SRWMD has no public ArcGIS API; data is distributed as zipped shapefile "
            "archives via the District's document center. Manual/batch ingestion only."
        )

    def normalize(self, raw: Any) -> list[WmdFeatureRecord]:
        return []
