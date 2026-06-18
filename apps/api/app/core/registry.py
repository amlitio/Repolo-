"""Loads the shared JSON registries (counties, sources, scoring) once at import
time and exposes typed accessors.

These files live in packages/shared/data/*.json and are the single source of
truth shared with the TypeScript frontend (packages/shared/src/registry,
packages/shared/src/constants/scoring.ts). This module treats them as
read-only inputs - never write back to packages/shared.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Literal, TypedDict

from app.config import get_settings

DataQualityStatus = Literal[
    "verified", "partially_verified", "needs_verification", "degraded", "unavailable"
]


class CountyEntry(TypedDict):
    fips: str
    name: str
    state: str
    region: str
    water_management_districts: list[str]
    gis_open_data_url: str | None
    procurement_url: str | None
    permits_url: str | None
    parcels_url: str | None
    access_method: str | None
    license: str | None
    refresh_cadence: str
    schema_notes: str | None
    data_quality_status: DataQualityStatus
    verified_at: str | None


class SourceEntry(TypedDict):
    id: str
    name: str
    agency: str
    level: str
    category: str
    access_method: str
    base_url: str
    docs_url: str
    auth_required: bool
    license: str
    refresh_cadence: str
    data_quality_status: DataQualityStatus
    verified_at: str | None
    notes: str


class GradeThreshold(TypedDict):
    max: float | None
    grade: str


class ScoringConfig(TypedDict):
    model_version: str
    property_risk_weights: dict[str, float]
    county_risk_weights: dict[str, float]
    grade_thresholds: list[GradeThreshold]


def _load_json(path) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


class Registry:
    """Typed, cached access to the three shared JSON registries."""

    def __init__(self) -> None:
        settings = get_settings()
        self._counties: list[CountyEntry] = _load_json(settings.counties_json_path)
        self._sources: list[SourceEntry] = _load_json(settings.sources_json_path)
        self._scoring: ScoringConfig = _load_json(settings.scoring_json_path)

        self._counties_by_fips = {c["fips"]: c for c in self._counties}
        self._counties_by_name = {c["name"].lower(): c for c in self._counties}
        self._sources_by_id = {s["id"]: s for s in self._sources}

    # Counties -----------------------------------------------------------
    @property
    def counties(self) -> list[CountyEntry]:
        return self._counties

    def get_county_by_fips(self, fips: str) -> CountyEntry | None:
        return self._counties_by_fips.get(fips)

    def get_county_by_name(self, name: str) -> CountyEntry | None:
        return self._counties_by_name.get(name.lower())

    def search_counties(self, query: str) -> list[CountyEntry]:
        q = query.lower().strip()
        if not q:
            return []
        return [
            c
            for c in self._counties
            if q in c["name"].lower() or q == c["fips"] or c["fips"].startswith(q)
        ]

    # Sources --------------------------------------------------------------
    @property
    def sources(self) -> list[SourceEntry]:
        return self._sources

    def get_source_by_id(self, source_id: str) -> SourceEntry | None:
        return self._sources_by_id.get(source_id)

    def get_sources_by_category(self, category: str) -> list[SourceEntry]:
        return [s for s in self._sources if s["category"] == category]

    # Scoring ----------------------------------------------------------------
    @property
    def scoring(self) -> ScoringConfig:
        return self._scoring

    @property
    def model_version(self) -> str:
        return self._scoring["model_version"]

    @property
    def property_risk_weights(self) -> dict[str, float]:
        return self._scoring["property_risk_weights"]

    @property
    def county_risk_weights(self) -> dict[str, float]:
        return self._scoring["county_risk_weights"]

    @property
    def grade_thresholds(self) -> list[GradeThreshold]:
        return self._scoring["grade_thresholds"]


@lru_cache
def get_registry() -> Registry:
    return Registry()
