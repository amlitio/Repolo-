"""Connector base class.

Each connector separates fetching raw data from normalizing it into our
Pydantic models, so `normalize()` can be unit-tested against a fixture
without ever making a network call. `run()` is the orchestration entrypoint
used by apps/workers jobs: it calls fetch_raw() then normalize(), and NEVER
raises an upstream failure out to the caller - it catches, logs, and reports
a degraded ConnectorRunResult instead, so one flaky source never crashes the
ingestion scheduler.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

logger = logging.getLogger("firip.connectors")

T = TypeVar("T")


@dataclass
class ConnectorRunResult(Generic[T]):
    source_id: str
    status: str  # "success" | "partial" | "failed" | "degraded"
    started_at: datetime
    finished_at: datetime
    records: list[T] = field(default_factory=list)
    error_message: str | None = None

    @property
    def records_fetched(self) -> int:
        return len(self.records)


class Connector(ABC, Generic[T]):
    """Abstract base for all data-source connectors.

    Subclasses implement `fetch_raw()` (I/O) and `normalize(raw)` (pure
    transform), and may override `is_supported()` for sources that are
    documented as manual/degraded (e.g. SRWMD, NHC) rather than API-driven.
    """

    source_id: str

    def __init__(self, source_id: str) -> None:
        self.source_id = source_id

    def is_supported(self) -> bool:
        """Return False for sources that cannot be fetched via API (e.g. a
        document-center-only source). Default: supported."""
        return True

    @abstractmethod
    async def fetch_raw(self, **kwargs: Any) -> Any:
        """Fetch raw bytes/JSON from the documented base_url. May raise on
        network/HTTP failure - callers should use `run()` to get a
        non-raising wrapper."""

    @abstractmethod
    def normalize(self, raw: Any) -> list[T]:
        """Pure transform: raw payload -> list of normalized Pydantic models.
        Must not perform I/O so it can be exercised directly against fixtures."""

    async def run(self, **kwargs: Any) -> ConnectorRunResult[T]:
        """Fetch + normalize, never raising. Used by ingestion jobs."""

        started_at = datetime.now(UTC)
        if not self.is_supported():
            finished_at = datetime.now(UTC)
            logger.info("Connector %s is not supported (manual/degraded source)", self.source_id)
            return ConnectorRunResult(
                source_id=self.source_id,
                status="degraded",
                started_at=started_at,
                finished_at=finished_at,
                records=[],
                error_message="Source is degraded/manual - no API available for automated ingestion.",
            )

        try:
            raw = await self.fetch_raw(**kwargs)
        except Exception as exc:  # noqa: BLE001 - intentional: never raise out of run()
            finished_at = datetime.now(UTC)
            logger.warning("Connector %s fetch_raw failed: %s", self.source_id, exc)
            return ConnectorRunResult(
                source_id=self.source_id,
                status="failed",
                started_at=started_at,
                finished_at=finished_at,
                records=[],
                error_message=str(exc),
            )

        try:
            records = self.normalize(raw)
        except Exception as exc:  # noqa: BLE001
            finished_at = datetime.now(UTC)
            logger.warning("Connector %s normalize failed: %s", self.source_id, exc)
            return ConnectorRunResult(
                source_id=self.source_id,
                status="failed",
                started_at=started_at,
                finished_at=finished_at,
                records=[],
                error_message=f"Normalization error: {exc}",
            )

        finished_at = datetime.now(UTC)
        return ConnectorRunResult(
            source_id=self.source_id,
            status="success",
            started_at=started_at,
            finished_at=finished_at,
            records=records,
        )
