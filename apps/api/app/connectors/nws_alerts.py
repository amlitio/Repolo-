"""NOAA/NWS Alerts API connector.

Per NOAA's documented requirement (https://www.weather.gov/documentation/services-web-api),
every request MUST send a descriptive User-Agent identifying the application
and a contact method. We read it from Settings.nws_user_agent
(NWS_USER_AGENT env var) rather than hardcoding it, so it can be tuned per
deployment without a code change, but it always defaults to a real contact.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx
from pydantic import BaseModel

from app.config import get_settings
from app.connectors.base import Connector
from app.core.registry import get_registry


class WeatherAlertRecord(BaseModel):
    external_id: str
    event: str
    severity: str
    certainty: str
    urgency: str
    headline: str
    description: str
    area_desc: str
    county_fips: list[str]
    effective_at: datetime
    expires_at: datetime


# NWS UGC/geocode "SAME" FIPS codes are prefixed; Florida county FIPS in NWS
# alert geocodes appear as 5-digit SAME codes equal to the standard county
# FIPS for the "Land" geocode type.
def _extract_county_fips(properties: dict) -> list[str]:
    geocode = properties.get("geocode") or {}
    same_codes = geocode.get("SAME") or []
    return [code[-5:] for code in same_codes if isinstance(code, str) and len(code) >= 5]


class NwsAlertsConnector(Connector[WeatherAlertRecord]):
    def __init__(self) -> None:
        super().__init__(source_id="nws-alerts")

    def _base_url(self) -> str:
        source = get_registry().get_source_by_id(self.source_id)
        if source is None:
            raise ValueError(f"Unknown source id: {self.source_id}")
        return source["base_url"]

    async def fetch_raw(self, area: str = "FL", timeout: float = 30.0) -> dict:
        settings = get_settings()
        url = f"{self._base_url()}/alerts/active/area/{area}"
        headers = {
            "User-Agent": settings.nws_user_agent,
            "Accept": "application/geo+json",
        }
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

    def normalize(self, raw: dict) -> list[WeatherAlertRecord]:
        records: list[WeatherAlertRecord] = []
        for feature in raw.get("features", []):
            props: dict[str, Any] = feature.get("properties", {}) or {}
            effective_raw = props.get("effective") or props.get("onset")
            expires_raw = props.get("expires") or props.get("ends")
            if not effective_raw or not expires_raw:
                continue
            records.append(
                WeatherAlertRecord(
                    external_id=props.get("id", feature.get("id", "")),
                    event=props.get("event", "Unknown"),
                    severity=props.get("severity", "Unknown"),
                    certainty=props.get("certainty", "Unknown"),
                    urgency=props.get("urgency", "Unknown"),
                    headline=props.get("headline") or "",
                    description=props.get("description") or "",
                    area_desc=props.get("areaDesc") or "",
                    county_fips=_extract_county_fips(props),
                    effective_at=datetime.fromisoformat(effective_raw),
                    expires_at=datetime.fromisoformat(expires_raw),
                )
            )
        return records
