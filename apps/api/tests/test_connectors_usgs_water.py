"""Tests for the USGS Water Data OGC API connectors."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from app.connectors.usgs_water import UsgsDailyValuesConnector, UsgsWaterStationsConnector

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_stations_normalize():
    connector = UsgsWaterStationsConnector()
    records = connector.normalize(_load("usgs_monitoring_locations.json"))
    assert len(records) == 2
    station = next(r for r in records if r.external_id == "USGS-02289500")
    assert station.county_fips == "12097"
    assert station.latitude == pytest.approx(28.064)
    assert "00060" in station.parameter_types


def test_daily_values_normalize():
    connector = UsgsDailyValuesConnector()
    records = connector.normalize(_load("usgs_daily_values.json"))
    assert len(records) == 2
    assert records[0].value == pytest.approx(12.4)
    assert records[1].qualifier == "P"


@pytest.mark.asyncio
@respx.mock
async def test_fetch_raw_mocked_stations():
    connector = UsgsWaterStationsConnector()
    respx.get(url__regex=r".*api\.waterdata\.usgs\.gov.*").mock(
        return_value=Response(200, json=_load("usgs_monitoring_locations.json"))
    )
    raw = await connector.fetch_raw()
    assert "features" in raw


@pytest.mark.asyncio
async def test_run_degrades_gracefully_on_connection_error():
    import httpx

    connector = UsgsWaterStationsConnector()
    with respx.mock:
        respx.get(url__regex=r".*api\.waterdata\.usgs\.gov.*").mock(side_effect=httpx.ConnectError("dns fail"))
        result = await connector.run()
    assert result.status == "failed"
    assert result.records == []
