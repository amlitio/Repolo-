"""OpenFEMA v2 connectors for disaster declarations and hazard mitigation
projects.

Both use the same OData-flavored query style documented at
https://www.fema.gov/about/openfema/api - `$filter`, `$top` (max 10000),
`$skip` for pagination.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import httpx
from pydantic import BaseModel

from app.connectors.base import Connector
from app.core.registry import get_registry


class DisasterDeclarationRecord(BaseModel):
    external_id: str
    disaster_number: str
    county_fips: str | None
    state: str
    declaration_type: str
    incident_type: str
    title: str
    declaration_date: date


class FemaOpenFemaDisasterDeclarationsConnector(Connector[DisasterDeclarationRecord]):
    def __init__(self) -> None:
        super().__init__(source_id="fema-openfema-disaster-declarations")

    def _base_url(self) -> str:
        source = get_registry().get_source_by_id(self.source_id)
        if source is None:
            raise ValueError(f"Unknown source id: {self.source_id}")
        return source["base_url"]

    async def fetch_raw(
        self, state: str = "FL", top: int = 1000, skip: int = 0, timeout: float = 30.0
    ) -> dict:
        params: dict[str, Any] = {
            "$filter": f"state eq '{state}'",
            "$top": top,
            "$skip": skip,
            "$format": "json",
        }
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(self._base_url(), params=params)
            response.raise_for_status()
            return response.json()

    def normalize(self, raw: dict) -> list[DisasterDeclarationRecord]:
        records: list[DisasterDeclarationRecord] = []
        for item in raw.get("DisasterDeclarationsSummaries", []):
            decl_date_raw = item.get("declarationDate")
            try:
                decl_date = date.fromisoformat(str(decl_date_raw)[:10]) if decl_date_raw else None
            except ValueError:
                decl_date = None
            if decl_date is None:
                continue
            records.append(
                DisasterDeclarationRecord(
                    external_id=str(item.get("id") or item.get("disasterNumber")),
                    disaster_number=str(item.get("disasterNumber")),
                    county_fips=item.get("fipsCountyCode"),
                    state=item.get("state", "FL"),
                    declaration_type=item.get("declarationType", "unknown"),
                    incident_type=item.get("incidentType", "unknown"),
                    title=item.get("declarationTitle", ""),
                    declaration_date=decl_date,
                )
            )
        return records


class HazardMitigationProjectRecord(BaseModel):
    external_id: str
    project_id: str
    county_fips: str | None
    program: str
    status: str
    title: str
    federal_share_obligated: float | None
    approval_date: date | None


class FemaOpenFemaHazardMitigationConnector(Connector[HazardMitigationProjectRecord]):
    def __init__(self) -> None:
        super().__init__(source_id="fema-openfema-hazard-mitigation")

    def _base_url(self) -> str:
        source = get_registry().get_source_by_id(self.source_id)
        if source is None:
            raise ValueError(f"Unknown source id: {self.source_id}")
        return source["base_url"]

    async def fetch_raw(
        self, state: str = "FL", top: int = 1000, skip: int = 0, timeout: float = 30.0
    ) -> dict:
        params: dict[str, Any] = {
            "$filter": f"state eq '{state}'",
            "$top": top,
            "$skip": skip,
            "$format": "json",
        }
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(self._base_url(), params=params)
            response.raise_for_status()
            return response.json()

    def normalize(self, raw: dict) -> list[HazardMitigationProjectRecord]:
        records: list[HazardMitigationProjectRecord] = []
        for item in raw.get("HazardMitigationAssistanceProjects", []):
            approval_raw = item.get("dateApproved")
            try:
                approval_date = date.fromisoformat(str(approval_raw)[:10]) if approval_raw else None
            except ValueError:
                approval_date = None
            records.append(
                HazardMitigationProjectRecord(
                    external_id=str(item.get("id") or item.get("projectIdentifier")),
                    project_id=str(item.get("projectIdentifier", "")),
                    county_fips=item.get("countyCode"),
                    program=item.get("programArea", "unknown"),
                    status=item.get("status", "unknown"),
                    title=item.get("projectTitle", item.get("programFy", "")),
                    federal_share_obligated=item.get("federalShareObligated"),
                    approval_date=approval_date,
                )
            )
        return records
