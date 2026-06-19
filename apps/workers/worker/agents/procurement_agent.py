"""Procurement agent (scaffold only - NOT wired into the scheduler).

docs/architecture.md and docs/roadmap.md both document that the Procurement
and Construction agents are "production-scaffolded" (real tables, real model
classes, agent stubs) but intentionally not part of this MVP's acceptance
gate, which is Risk + Water. app/models/procurement.py, app/schemas/procurement.py,
and app/routers/procurement.py all already point back at this module as the
future home of SAM.gov/Grants.gov/MyFloridaMarketPlace ingestion into
`procurement_opportunities` and the ranking logic behind
`GET /opportunities/rank` / `opportunity_scores`.

None of those connectors exist yet, so `execute()` does no I/O and no
database writes - it only reports an honest "not_configured" result. This
keeps the class importable and unit-testable today (and `worker.scheduler`
can name it explicitly as "scaffolded, not scheduled") without pretending
to ingest data it cannot yet fetch.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from worker.agents.base import Agent, AgentRunResult


class ProcurementAgent(Agent):
    name = "procurement"

    async def execute(self, session: AsyncSession) -> AgentRunResult:
        started_at = datetime.now(UTC)
        finished_at = datetime.now(UTC)
        return AgentRunResult(
            agent_name=self.name,
            status="not_configured",
            started_at=started_at,
            finished_at=finished_at,
            summary=(
                "Procurement agent is a scaffold: no SAM.gov/Grants.gov/MyFloridaMarketPlace "
                "connector is implemented in this MVP, so procurement_opportunities and "
                "opportunity_scores are not populated. Not wired into worker.scheduler - "
                "see docs/roadmap.md."
            ),
        )
