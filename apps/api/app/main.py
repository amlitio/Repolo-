"""FastAPI application entrypoint.

Wires together: CORS, the unified error-envelope exception handlers, every
domain router, and (idempotent) startup bootstrap of the `map_layers`
catalog table - one row per packages/shared/src/constants/layers.ts
MAP_LAYER_IDS entry, so GET /map/layers is never empty in a fresh
environment even before any real ingestion has run.
"""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.config import get_settings
from app.core.errors import register_exception_handlers
from app.db import AsyncSessionLocal, init_models
from app.models.geo import MapLayer
from app.routers import (
    admin,
    alerts,
    auth,
    flood,
    map as map_router,
    procurement,
    risk,
    search,
    subscriptions,
    system,
    water,
)

logger = logging.getLogger("firip.main")

# One row per packages/shared/src/constants/layers.ts::MAP_LAYER_IDS. Each
# entry's source_id must exist in packages/shared/data/sources.json.
_MAP_LAYER_SEED: list[dict] = [
    {
        "id": "fema-flood-zones",
        "name": "FEMA Flood Zones",
        "category": "flood",
        "source_id": "fema-nfhl",
        "default_visible": True,
        "min_zoom": 0,
        "max_zoom": 22,
        "legend": [
            {"label": "Special Flood Hazard Area (A/V zones)", "color": "#d73027"},
            {"label": "Moderate/Minimal Hazard (X zone)", "color": "#1a9850"},
        ],
    },
    {
        "id": "noaa-alerts",
        "name": "NOAA/NWS Active Alerts",
        "category": "weather",
        "source_id": "nws-alerts",
        "default_visible": True,
        "min_zoom": 0,
        "max_zoom": 22,
        "legend": [
            {"label": "Extreme", "color": "#7f0000"},
            {"label": "Severe", "color": "#d7301f"},
            {"label": "Moderate", "color": "#fc8d59"},
            {"label": "Minor", "color": "#fdd49e"},
        ],
    },
    {
        "id": "hurricane-tracks",
        "name": "Hurricane Tracks",
        "category": "hurricane",
        "source_id": "nhc-gis",
        "default_visible": False,
        "min_zoom": 0,
        "max_zoom": 22,
        "legend": [{"label": "Active storm track", "color": "#2166ac"}],
    },
    {
        "id": "usgs-water-stations",
        "name": "USGS Water Stations",
        "category": "water",
        "source_id": "usgs-water-data-ogcapi",
        "default_visible": False,
        "min_zoom": 0,
        "max_zoom": 22,
        "legend": [{"label": "Monitoring station", "color": "#4575b4"}],
    },
    {
        "id": "sfwmd-stations",
        "name": "South Florida WMD Stations",
        "category": "water",
        "source_id": "sfwmd-gis-open-data",
        "default_visible": False,
        "min_zoom": 0,
        "max_zoom": 22,
        "legend": [{"label": "SFWMD station", "color": "#74add1"}],
    },
    {
        "id": "sjrwmd-stations",
        "name": "St. Johns River WMD Stations",
        "category": "water",
        "source_id": "sjrwmd-gis-open-data",
        "default_visible": False,
        "min_zoom": 0,
        "max_zoom": 22,
        "legend": [{"label": "SJRWMD station", "color": "#abd9e9"}],
    },
    {
        "id": "swfwmd-stations",
        "name": "Southwest Florida WMD Stations",
        "category": "water",
        "source_id": "swfwmd-gis-open-data",
        "default_visible": False,
        "min_zoom": 0,
        "max_zoom": 22,
        "legend": [{"label": "SWFWMD station", "color": "#e0f3f8"}],
    },
    {
        "id": "county-risk-heatmap",
        "name": "County Risk Heatmap",
        "category": "risk",
        "source_id": "fema-nfhl",
        "default_visible": False,
        "min_zoom": 0,
        "max_zoom": 22,
        "legend": [
            {"label": "Grade A", "color": "#1a9850"},
            {"label": "Grade B", "color": "#91cf60"},
            {"label": "Grade C", "color": "#fee08b"},
            {"label": "Grade D", "color": "#fc8d59"},
            {"label": "Grade F", "color": "#d73027"},
        ],
    },
    {
        "id": "procurement-locations",
        "name": "Procurement Opportunity Locations",
        "category": "procurement",
        "source_id": "fema-openfema-hazard-mitigation",
        "default_visible": False,
        "min_zoom": 0,
        "max_zoom": 22,
        "legend": [{"label": "Open opportunity", "color": "#984ea3"}],
    },
    {
        "id": "county-boundaries",
        "name": "County Boundaries",
        "category": "boundary",
        "source_id": "fema-nfhl",
        "default_visible": True,
        "min_zoom": 0,
        "max_zoom": 22,
        "legend": [{"label": "County boundary", "color": "#636363"}],
    },
]


async def _seed_map_layers() -> None:
    """Idempotently insert any missing map_layers rows. Safe to call on every
    startup - never overwrites an existing row, only fills in gaps."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(MapLayer.id))
        existing_ids = {row[0] for row in result.all()}
        created = 0
        for entry in _MAP_LAYER_SEED:
            if entry["id"] in existing_ids:
                continue
            session.add(
                MapLayer(
                    id=entry["id"],
                    name=entry["name"],
                    category=entry["category"],
                    source_id=entry["source_id"],
                    default_visible=entry["default_visible"],
                    min_zoom=entry["min_zoom"],
                    max_zoom=entry["max_zoom"],
                    legend_json=json.dumps(entry["legend"]),
                )
            )
            created += 1
        if created:
            await session.commit()
            logger.info("Seeded %d map_layers row(s)", created)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    if settings.database_url.startswith("sqlite"):
        # Unit tests create tables themselves via the `_initialize_schema`
        # fixture; calling init_models() again here is harmless (CREATE
        # TABLE IF NOT EXISTS semantics via create_all) but in production
        # schema changes should go through Alembic instead, never create_all.
        await init_models()
    await _seed_map_layers()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="FIRIP API",
        version=settings.app_version,
        description="Florida flood/water risk intelligence platform API.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(system.router)
    app.include_router(auth.router)
    app.include_router(map_router.router)
    app.include_router(water.router)
    app.include_router(flood.router)
    app.include_router(risk.router)
    app.include_router(alerts.router)
    app.include_router(subscriptions.router)
    app.include_router(procurement.router)
    app.include_router(search.router)
    app.include_router(admin.router)

    return app


app = create_app()
