"""CLI entrypoint for the ingestion/agent scheduler.

Runs the four agents docs/architecture.md names as scheduled
(Data Discovery, Water Intelligence, Risk Modeling, Research), each in its
own session/transaction so one agent's failure can never roll back another
agent's already-flushed work. Procurement and Construction are intentionally
excluded - they're scaffolds (see worker/agents/procurement_agent.py and
worker/agents/construction_agent.py), not part of this MVP's scheduled run.

Usage:
    python -m worker.scheduler              # run once per agent, then exit
    python -m worker.scheduler --interval 3600   # loop forever, sleeping
                                                  # `interval` seconds between passes
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from app.db import AsyncSessionLocal, init_models

from worker.agents.base import Agent, AgentRunResult
from worker.agents.data_discovery_agent import DataDiscoveryAgent
from worker.agents.research_agent import ResearchAgent
from worker.agents.risk_modeling_agent import RiskModelingAgent
from worker.agents.water_intelligence_agent import WaterIntelligenceAgent

logger = logging.getLogger("firip.workers.scheduler")

# Exactly the four agents docs/architecture.md documents as scheduled.
# Order matters: Risk Modeling reads flood_zones/weather_alerts/etc, so it
# runs after Water Intelligence (which doesn't feed it, but keeping
# ingestion agents before the agent that scores against their output is the
# more sensible default pass order).
SCHEDULED_AGENTS: list[type[Agent]] = [
    DataDiscoveryAgent,
    WaterIntelligenceAgent,
    RiskModelingAgent,
    ResearchAgent,
]


async def _run_agent(agent_cls: type[Agent]) -> AgentRunResult:
    agent = agent_cls()
    async with AsyncSessionLocal() as session:
        result = await agent.run(session)
        await session.commit()
        return result


async def run_once() -> list[AgentRunResult]:
    await init_models()
    results: list[AgentRunResult] = []
    for agent_cls in SCHEDULED_AGENTS:
        result = await _run_agent(agent_cls)
        logger.info("%s: %s - %s", result.agent_name, result.status, result.summary)
        results.append(result)
    return results


async def run_forever(interval_seconds: float) -> None:
    while True:
        await run_once()
        await asyncio.sleep(interval_seconds)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FIRIP ingestion/agent scheduler")
    parser.add_argument(
        "--interval",
        type=float,
        default=None,
        help="Seconds to sleep between passes. Omit to run every scheduled agent exactly once and exit.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    if args.interval is None:
        results = asyncio.run(run_once())
        return 0 if all(r.status in ("success", "partial", "not_configured") for r in results) else 1

    asyncio.run(run_forever(args.interval))
    return 0


if __name__ == "__main__":
    sys.exit(main())
