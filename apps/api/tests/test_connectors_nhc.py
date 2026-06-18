"""Tests for the best-effort NHC connector (metadata-level only, see nhc.py
docstring for documented limitations on shapefile/KMZ track products)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from app.connectors.nhc import NhcConnector

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "nhc_current_storms.json"


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text())


def test_normalize_produces_point_geometry():
    connector = NhcConnector()
    records = connector.normalize(_load_fixture())
    assert len(records) == 1
    storm = records[0]
    assert storm.name == "Test Storm Iris"
    assert storm.geometry["type"] == "Point"
    assert storm.geometry["coordinates"] == [-82.1, 25.8]


@pytest.mark.asyncio
@respx.mock
async def test_fetch_raw_mocked():
    connector = NhcConnector()
    respx.get(url__regex=r".*nhc\.noaa\.gov.*").mock(return_value=Response(200, json=_load_fixture()))
    raw = await connector.fetch_raw()
    assert "activeStorms" in raw


@pytest.mark.asyncio
async def test_run_handles_no_active_storms_gracefully():
    connector = NhcConnector()
    with respx.mock:
        respx.get(url__regex=r".*nhc\.noaa\.gov.*").mock(
            return_value=Response(200, json={"activeStorms": []})
        )
        result = await connector.run()
    assert result.status == "success"
    assert result.records == []
