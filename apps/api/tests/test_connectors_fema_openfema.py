"""Tests for the OpenFEMA disaster declarations and hazard mitigation connectors."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from app.connectors.fema_openfema import (
    FemaOpenFemaDisasterDeclarationsConnector,
    FemaOpenFemaHazardMitigationConnector,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_disaster_declarations_normalize_skips_malformed_records():
    connector = FemaOpenFemaDisasterDeclarationsConnector()
    records = connector.normalize(_load("fema_openfema_disaster_declarations.json"))
    # Third record has declarationDate=null and must be skipped, not crash.
    assert len(records) == 2
    assert {r.disaster_number for r in records} == {"4750", "4751"}
    hurricane = next(r for r in records if r.disaster_number == "4750")
    assert hurricane.incident_type == "Hurricane"
    assert hurricane.county_fips == "12086"


def test_hazard_mitigation_normalize():
    connector = FemaOpenFemaHazardMitigationConnector()
    records = connector.normalize(_load("fema_openfema_hazard_mitigation.json"))
    assert len(records) == 1
    assert records[0].program == "BRIC"
    assert records[0].federal_share_obligated == 2500000.0


@pytest.mark.asyncio
@respx.mock
async def test_disaster_declarations_fetch_raw_mocked():
    connector = FemaOpenFemaDisasterDeclarationsConnector()
    respx.get(url__regex=r".*fema\.gov.*").mock(
        return_value=Response(200, json=_load("fema_openfema_disaster_declarations.json"))
    )
    raw = await connector.fetch_raw()
    assert "DisasterDeclarationsSummaries" in raw


@pytest.mark.asyncio
async def test_run_degrades_gracefully_on_timeout():
    import httpx

    connector = FemaOpenFemaHazardMitigationConnector()
    with respx.mock:
        respx.get(url__regex=r".*fema\.gov.*").mock(side_effect=httpx.ConnectTimeout("boom"))
        result = await connector.run()
    assert result.status == "failed"
    assert result.records == []
