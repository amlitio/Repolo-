"""Tests for the FEMA NFHL connector. normalize() is tested against a
synthetic fixture in isolation; fetch_raw() is tested with respx mocking
httpx so no real network call is made."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from app.connectors.fema_nfhl import FemaNfhlConnector

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "fema_nfhl_query_response.json"


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text())


def test_normalize_produces_expected_records():
    connector = FemaNfhlConnector()
    records = connector.normalize(_load_fixture())
    assert len(records) == 3

    ae = next(r for r in records if r.zone_label == "AE")
    assert ae.is_special_flood_hazard_area is True
    assert ae.base_flood_elevation == 9.0
    assert ae.fips == "12086"
    assert ae.effective_date is not None

    x_zone = next(r for r in records if r.zone_label == "X")
    assert x_zone.is_special_flood_hazard_area is False
    assert x_zone.base_flood_elevation is None

    ve = next(r for r in records if r.zone_label == "VE")
    assert ve.is_special_flood_hazard_area is True
    assert ve.effective_date is None


@pytest.mark.asyncio
@respx.mock
async def test_fetch_raw_calls_documented_base_url():
    connector = FemaNfhlConnector()
    route = respx.get(url__regex=r".*hazards\.fema\.gov.*").mock(
        return_value=Response(200, json=_load_fixture())
    )
    raw = await connector.fetch_raw(county_fips="12086")
    assert route.called
    assert "features" in raw


@pytest.mark.asyncio
async def test_run_never_raises_on_upstream_failure():
    connector = FemaNfhlConnector()
    with respx.mock:
        respx.get(url__regex=r".*hazards\.fema\.gov.*").mock(return_value=Response(503))
        result = await connector.run(county_fips="12086")
    assert result.status == "failed"
    assert result.records == []
    assert result.error_message is not None
