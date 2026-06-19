"""Research agent.

Per docs/architecture.md, the Research agent performs RAG over
`documents`/`embeddings` behind a pluggable LLMProvider interface
(worker.llm.EmbeddingProvider) that returns an honest "not configured"
result when neither OPENAI_API_KEY nor GEMINI_API_KEY is set - this agent
never fabricates a vector.

It runs the batch/ingestion half of RAG: computing embeddings for
DocumentChunks that don't have one yet. Answering a user's question
synchronously is handled by app/routers/search.py::research_ask, which
explicitly defers the live LLM call to this agent's pipeline rather than
calling a paid API inline inside a request handler.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.config import get_settings
from app.models.mixins import new_uuid
from app.models.search import DocumentChunk, Embedding
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from worker.agents.base import Agent, AgentRunResult
from worker.llm import get_embedding_provider

# Bounds embedding-API spend/latency per scheduler pass, matching the
# bounding pattern used by water_intelligence_agent's daily-value fetches.
MAX_CHUNKS_PER_RUN = 50


class ResearchAgent(Agent):
    name = "research"

    async def execute(self, session: AsyncSession) -> AgentRunResult:
        started_at = datetime.now(UTC)
        settings = get_settings()
        provider = get_embedding_provider(settings)

        if provider is None:
            finished_at = datetime.now(UTC)
            return AgentRunResult(
                agent_name=self.name,
                status="not_configured",
                started_at=started_at,
                finished_at=finished_at,
                summary="No OPENAI_API_KEY or GEMINI_API_KEY configured; research agent is not "
                "configured in this environment.",
            )

        embedded_chunk_ids = select(Embedding.document_chunk_id)
        pending = await session.execute(
            select(DocumentChunk).where(DocumentChunk.id.not_in(embedded_chunk_ids)).limit(MAX_CHUNKS_PER_RUN)
        )
        chunks = pending.scalars().all()

        details: dict[str, Any] = {"provider": provider.model_name, "pending_chunks": len(chunks)}
        if not chunks:
            finished_at = datetime.now(UTC)
            return AgentRunResult(
                agent_name=self.name,
                status="success",
                started_at=started_at,
                finished_at=finished_at,
                summary="No document chunks pending embedding.",
                details=details,
            )

        try:
            vectors = await provider.embed([chunk.text for chunk in chunks])
        except Exception as exc:  # noqa: BLE001 - report as a failed run, never fabricate a vector
            finished_at = datetime.now(UTC)
            return AgentRunResult(
                agent_name=self.name,
                status="failed",
                started_at=started_at,
                finished_at=finished_at,
                summary=f"Embedding provider call failed: {exc}",
                details=details,
            )

        for chunk, vector in zip(chunks, vectors, strict=True):
            session.add(
                Embedding(
                    id=new_uuid(),
                    document_chunk_id=chunk.id,
                    model_name=provider.model_name,
                    vector=vector,
                )
            )
        await session.flush()

        finished_at = datetime.now(UTC)
        details["embedded"] = len(chunks)
        return AgentRunResult(
            agent_name=self.name,
            status="success",
            started_at=started_at,
            finished_at=finished_at,
            summary=f"Embedded {len(chunks)} document chunk(s) using {provider.model_name}.",
            details=details,
        )
