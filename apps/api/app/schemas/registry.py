"""Registry passthrough schemas, mirroring packages/shared/src/types/registry.ts."""

from __future__ import annotations

from pydantic import BaseModel

DataQualityStatus = str
SourceLevel = str
WaterManagementDistrict = str


class SourceRegistryEntry(BaseModel):
    id: str
    name: str
    agency: str
    level: SourceLevel
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


class CountyRegistryEntry(BaseModel):
    fips: str
    name: str
    state: str
    region: str
    water_management_districts: list[WaterManagementDistrict]
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
