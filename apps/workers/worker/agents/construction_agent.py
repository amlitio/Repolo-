"""Construction agent (scaffold only - NOT wired into the scheduler).

Per docs/roadmap.md's "Ahead" section ("Activate the Construction Agent
against `projects` / `funding_sources` for tracked mitigation/infrastructure
projects"), this agent's eventual job is to ingest and track infrastructure
and mitigation construction projects (and their funding sources) - distinct
from the Risk Modeling agent's read of `mitigation_projects`
(FEMA HMA-funded projects already ingested via OpenFEMA), which is
real/active today.

No ingestion source for `projects` / `funding_sources` is selected or
implemented in this MVP, so `execute()` does no I/O and no database writes -
it only reports an honest "not_configured" result rather than fabricating
project data.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from worker.agents.base import Agent, AgentRunResult


class ConstructionAgent(Agent):
    name = "construction"

    async def execute(self, session: AsyncSession) -> AgentRunResult:
        started_at = datetime.now(UTC)
        finished_at = datetime.now(UTC)
        return AgentRunResult(
            agent_name=self.name,
            status="not_configured",
            started_at=started_at,
            finished_at=finished_at,
            summary=(
                "Construction agent is a scaffold: no infrastructure/mitigation project "
                "tracking source is implemented in this MVP, so projects and funding_sources "
                "are not populated. Not wired into worker.scheduler - see docs/roadmap.md."
            ),
        )
