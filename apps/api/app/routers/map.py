"""Map layer catalog, feature queries, and map search. All public, no auth."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.registry import get_registry
from app.db import get_db
from app.models.geo import GisFeature, LayerVersion, MapLayer
from app.schemas.flood import GeoJSONFeature, GeoJSONFeatureCollection
from app.schemas.map import LegendEntry, MapLayerDefinition, MapSearchResult

router = APIRouter(tags=["map"])


@router.get(
    "/map/layers",
    response_model=list[MapLayerDefinition],
    summary="List available map layers",
    description="Returns the seeded catalog of map layers (FEMA flood zones, NOAA alerts, "
    "hurricane tracks, USGS/WMD stations, county risk heatmap, procurement locations, "
    "county boundaries).",
)
async def list_map_layers(db: AsyncSession = Depends(get_db)) -> list[MapLayerDefinition]:
    result = await db.execute(select(MapLayer))
    layers = result.scalars().all()
    return [
        MapLayerDefinition(
            id=layer.id,
            name=layer.name,
            category=layer.category,
            source_id=layer.source_id,
            default_visible=layer.default_visible,
            min_zoom=layer.min_zoom,
            max_zoom=layer.max_zoom,
            legend=[LegendEntry(**entry) for entry in json.loads(layer.legend_json)],
        )
        for layer in layers
    ]


@router.get(
    "/map/features/query",
    response_model=GeoJSONFeatureCollection,
    summary="Query GIS features for a layer within a bounding box",
    description="Returns a GeoJSON FeatureCollection of gis_features linked to the active "
    "layer_version for the given layer_id, optionally filtered by bbox. Note: bbox filtering "
    "is applied at the application layer when running on SQLite (unit tests); on Postgres+PostGIS "
    "this should be pushed down to a real ST_Intersects predicate (see integration tests).",
)
async def query_map_features(
    db: AsyncSession = Depends(get_db),
    layer_id: str = Query(..., description="Map layer id, e.g. 'fema-flood-zones'"),
    bbox: str | None = Query(None, description="minLon,minLat,maxLon,maxLat"),
    zoom: int | None = Query(None, ge=0, le=22),
) -> GeoJSONFeatureCollection:
    stmt = (
        select(GisFeature)
        .join(LayerVersion, LayerVersion.id == GisFeature.layer_version_id)
        .where(LayerVersion.layer_id == layer_id, LayerVersion.is_active.is_(True))
    )
    result = await db.execute(stmt)
    features = result.scalars().all()

    parsed_bbox: tuple[float, float, float, float] | None = None
    if bbox:
        parts = [float(p) for p in bbox.split(",")]
        if len(parts) == 4:
            parsed_bbox = (parts[0], parts[1], parts[2], parts[3])

    geojson_features: list[GeoJSONFeature] = []
    for feature in features:
        geometry = feature.geometry or {}
        if parsed_bbox and isinstance(geometry, dict) and geometry.get("type") == "Point":
            lon, lat = geometry.get("coordinates", [None, None])
            if lon is None or lat is None:
                continue
            min_lon, min_lat, max_lon, max_lat = parsed_bbox
            if not (min_lon <= lon <= max_lon and min_lat <= lat <= max_lat):
                continue
        properties = json.loads(feature.properties_json) if feature.properties_json else {}
        geojson_features.append(
            GeoJSONFeature(geometry=geometry if isinstance(geometry, dict) else {}, properties=properties)
        )

    return GeoJSONFeatureCollection(features=geojson_features)


@router.get(
    "/map/search",
    response_model=list[MapSearchResult],
    summary="Search the map index (counties, stations, etc.)",
    description="Matches against the 67-county registry by name/fips at minimum.",
)
async def map_search(q: str = Query(..., min_length=1)) -> list[MapSearchResult]:
    registry = get_registry()
    matches = registry.search_counties(q)
    results: list[MapSearchResult] = []
    for county in matches:
        results.append(
            MapSearchResult(
                type="county",
                id=county["fips"],
                name=f"{county['name']} County",
                fips=county["fips"],
                # Centroid data is not in counties.json; (0.0, 0.0) is an
                # explicit placeholder, not a fabricated coordinate - the
                # frontend should treat (0,0) + type=="county" as "needs
                # geocoding" until geographies are populated from a real
                # boundary dataset.
                centroid=(0.0, 0.0),
            )
        )
    return results
