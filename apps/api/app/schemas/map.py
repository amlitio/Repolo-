"""Map layer schemas, mirroring packages/shared/src/types/api.ts::MapLayerDefinition."""

from __future__ import annotations

from pydantic import BaseModel

MapLayerCategory = str  # "flood" | "weather" | "water" | "risk" | "hurricane" | "procurement" | "boundary"


class LegendEntry(BaseModel):
    label: str
    color: str


class MapLayerDefinition(BaseModel):
    id: str
    name: str
    category: MapLayerCategory
    source_id: str
    default_visible: bool
    min_zoom: int
    max_zoom: int
    legend: list[LegendEntry]


class MapSearchResult(BaseModel):
    type: str
    id: str
    name: str
    fips: str | None
    centroid: tuple[float, float]
