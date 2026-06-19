"""Agent base class.

Mirrors app.connectors.base.Connector's contract: `execute()` does the real
work and may raise, while `run()` is the orchestration entrypoint used by
the scheduler - it never raises, so one failing agent can never crash the
rest of a scheduler pass.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("firip.workers.agents")


@dataclass
class AgentRunResult:
    agent_name: str
    status: str  # success | partial | failed | degraded | not_configured
    started_at: datetime
    finished_at: datetime
    summary: str
    details: dict[str, Any] = field(default_factory=dict)


class Agent(ABC):
    name: str

    @abstractmethod
    async def execute(self, session: AsyncSession) -> AgentRunResult:
        """Do the agent's work. May raise - callers should use `run()`."""

    async def run(self, session: AsyncSession) -> AgentRunResult:
        started_at = datetime.now(UTC)
        try:
            return await self.execute(session)
        except Exception as exc:  # noqa: BLE001 - intentional: never raise out of run()
            finished_at = datetime.now(UTC)
            logger.exception("Agent %s failed", self.name)
            return AgentRunResult(
                agent_name=self.name,
                status="failed",
                started_at=started_at,
                finished_at=finished_at,
                summary=f"Agent raised an unhandled exception: {exc}",
            )
