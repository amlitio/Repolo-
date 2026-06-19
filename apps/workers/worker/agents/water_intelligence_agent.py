"""Water Intelligence agent.

Runs the USGS Water Data OGC API connectors (stations, then daily values for
a bounded set of stations) and the four Florida Water Management District
ArcGIS connectors (SFWMD/SJRWMD/SWFWMD/NWFWMD) plus the degraded-by-design
SRWMD connector, persisting results into `water_stations` /
`water_observations`. WMD features don't map to a bespoke domain table in
this MVP, so they land in `normalized_records` (record_type="wmd_feature")
per app/models/admin.py::NormalizedRecord's documented purpose as the
connector-agnostic landing zone.

Every connector call goes through Connector.run(), which never raises, and
every run is recorded via worker.persistence.record_connector_run - a
network failure or an unsupported source (SRWMD) shows up as a `degraded`/
`failed` source_runs row and a data_quality_event, never as fabricated data.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from app.connectors.usgs_water import (
    UsgsDailyValuesConnector,
    UsgsObservationRecord,
    UsgsStationRecord,
    UsgsWaterStationsConnector,
)
from app.connectors.wmd_arcgis import (
    SrwmdConnector,
    WmdFeatureRecord,
    make_nwfwmd_connector,
    make_sfwmd_connector,
    make_sjrwmd_connector,
    make_swfwmd_connector,
)
from app.models.admin import NormalizedRecord
from app.models.mixins import new_uuid
from app.models.water import WaterObservation, WaterStation
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from worker.agents.base import Agent, AgentRunResult
from worker.persistence import record_connector_run

# Daily-value fetches are one HTTP call per station; bounded here so a single
# agent pass stays fast and polite to the upstream API rather than fetching
# observations for every Florida station on every run.
MAX_STATIONS_FOR_DAILY_VALUES = 25


async def _upsert_water_station(
    session: AsyncSession, source_id: str, record: UsgsStationRecord
) -> WaterStation:
    result = await session.execute(
        select(WaterStation).where(
            WaterStation.source_id == source_id, WaterStation.external_id == record.external_id
        )
    )
    station = result.scalar_one_or_none()
    if station is None:
        station = WaterStation(
            id=new_uuid(),
            source_id=source_id,
            external_id=record.external_id,
            name=record.name,
            agency="USGS",
            county_fips=record.county_fips,
            latitude=record.latitude,
            longitude=record.longitude,
            parameter_types_json=json.dumps(record.parameter_types),
        )
        session.add(station)
    else:
        station.name = record.name
        station.county_fips = record.county_fips
        station.latitude = record.latitude
        station.longitude = record.longitude
        station.parameter_types_json = json.dumps(record.parameter_types)
    await session.flush()
    return station


async def _insert_water_observation_if_new(
    session: AsyncSession, station_id: str, record: UsgsObservationRecord
) -> bool:
    existing = await session.execute(
        select(WaterObservation).where(
            WaterObservation.station_id == station_id,
            WaterObservation.parameter == record.parameter,
            WaterObservation.observed_at == record.observed_at,
        )
    )
    if existing.scalar_one_or_none() is not None:
        return False
    session.add(
        WaterObservation(
            id=new_uuid(),
            station_id=station_id,
            parameter=record.parameter,
            value=record.value,
            unit=record.unit,
            observed_at=record.observed_at,
            qualifier=record.qualifier,
        )
    )
    await session.flush()
    return True


async def _land_normalized_record(session: AsyncSession, source_id: str, record: WmdFeatureRecord) -> bool:
    existing = await session.execute(
        select(NormalizedRecord).where(
            NormalizedRecord.source_id == source_id,
            NormalizedRecord.external_id == record.external_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        return False
    session.add(
        NormalizedRecord(
            id=new_uuid(),
            source_id=source_id,
            record_type="wmd_feature",
            external_id=record.external_id,
            data=record.model_dump_json(),
        )
    )
    await session.flush()
    return True


class WaterIntelligenceAgent(Agent):
    name = "water_intelligence"

    async def execute(self, session: AsyncSession) -> AgentRunResult:
        started_at = datetime.now(UTC)
        details: dict[str, Any] = {}

        stations_result = await UsgsWaterStationsConnector().run(state_fips="12")
        await record_connector_run(session, stations_result)
        stations_upserted = 0
        if stations_result.status == "success":
            for record in stations_result.records:
                await _upsert_water_station(session, stations_result.source_id, record)
                stations_upserted += 1
        details["usgs_stations"] = {"status": stations_result.status, "upserted": stations_upserted}

        observations_inserted = 0
        if stations_result.status == "success":
            station_rows = await session.execute(
                select(WaterStation)
                .where(WaterStation.source_id == "usgs-water-data-ogcapi")
                .limit(MAX_STATIONS_FOR_DAILY_VALUES)
            )
            for station in station_rows.scalars().all():
                daily_result = await UsgsDailyValuesConnector().run(
                    monitoring_location_id=station.external_id
                )
                await record_connector_run(session, daily_result)
                if daily_result.status == "success":
                    for record in daily_result.records:
                        inserted = await _insert_water_observation_if_new(session, station.id, record)
                        observations_inserted += int(inserted)
        details["usgs_daily_values"] = {"observations_inserted": observations_inserted}

        wmd_connectors = [
            make_sfwmd_connector(),
            make_sjrwmd_connector(),
            make_swfwmd_connector(),
            make_nwfwmd_connector(),
            SrwmdConnector(),
        ]
        wmd_summary: dict[str, Any] = {}
        normalized_records_landed = 0
        for connector in wmd_connectors:
            result = await connector.run()
            await record_connector_run(session, result)
            landed = 0
            for record in result.records:
                landed += int(await _land_normalized_record(session, result.source_id, record))
            normalized_records_landed += landed
            wmd_summary[result.source_id] = {"status": result.status, "landed": landed}
        details["wmd_districts"] = wmd_summary

        finished_at = datetime.now(UTC)
        overall_status = "success" if stations_result.status == "success" else "partial"
        return AgentRunResult(
            agent_name=self.name,
            status=overall_status,
            started_at=started_at,
            finished_at=finished_at,
            summary=(
                f"Upserted {stations_upserted} USGS station(s), inserted {observations_inserted} "
                f"observation(s), landed {normalized_records_landed} WMD feature record(s)."
            ),
            details=details,
        )
