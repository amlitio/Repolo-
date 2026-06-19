"""Tests for the generic ArcGIS WMD connector, including the SRWMD degraded
no-API path."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from app.connectors.wmd_arcgis import (
    SrwmdConnector,
    WmdArcGisConnector,
    make_nwfwmd_connector,
    make_sfwmd_connector,
    make_sjrwmd_connector,
    make_swfwmd_connector,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "wmd_arcgis_feature_query.json"


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text())


def test_normalize_generic_feature():
    connector = make_sfwmd_connector()
    records = connector.normalize(_load_fixture())
    assert len(records) == 2
    assert records[0].properties["STRUCT_NAME"] == "S-65A"


@pytest.mark.parametrize(
    "factory",
    [make_sfwmd_connector, make_sjrwmd_connector, make_swfwmd_connector, make_nwfwmd_connector],
)
def test_all_four_districts_construct_with_correct_source_id(factory):
    connector = factory()
    assert connector.is_supported() is True
    assert connector.source_id.endswith("-gis-open-data")


@pytest.mark.asyncio
@respx.mock
async def test_fetch_raw_uses_feature_server_override():
    connector = WmdArcGisConnector(
        source_id="sfwmd-gis-open-data",
        feature_server_url="https://example.test/arcgis/rest/services/Hydro/FeatureServer",
    )
    route = respx.get(url__regex=r".*example\.test.*").mock(return_value=Response(200, json=_load_fixture()))
    raw = await connector.fetch_raw(layer_id=3)
    assert route.called
    assert "features" in raw


@pytest.mark.asyncio
async def test_srwmd_connector_reports_degraded_not_error():
    connector = SrwmdConnector()
    assert connector.is_supported() is False
    result = await connector.run()
    assert result.status == "degraded"
    assert result.records == []
    assert "no public ArcGIS" in (result.error_message or "").lower() or "degraded" in (
        result.error_message or ""
    ).lower()
