"""Tests for ResearchAgent: the not-configured path when no embedding
provider is available, the embed-pending-chunks pipeline, dedupe of chunks
that already have an embedding, the per-run chunk bound, and honest failure
(never a fabricated vector) when the provider call raises.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.models.mixins import new_uuid
from app.models.search import Document, DocumentChunk, Embedding
from sqlalchemy import select

from worker.agents import research_agent as research_agent_module
from worker.agents.research_agent import ResearchAgent

NOW = datetime.now(UTC)


class _FakeEmbeddingProvider:
    model_name = "fake-embedding-model"

    def __init__(self, vector_for: dict[str, list[float]] | None = None, *, fail: bool = False):
        self._vector_for = vector_for or {}
        self._fail = fail
        self.embedded_texts: list[str] = []

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.embedded_texts.extend(texts)
        if self._fail:
            raise RuntimeError("embedding API unavailable")
        return [self._vector_for.get(text, [0.1, 0.2, 0.3]) for text in texts]


async def _make_chunk(db_session, text: str) -> DocumentChunk:
    document = Document(id=new_uuid(), title="Test Doc", doc_type="generic")
    db_session.add(document)
    await db_session.flush()
    chunk = DocumentChunk(id=new_uuid(), document_id=document.id, chunk_index=0, text=text)
    db_session.add(chunk)
    await db_session.flush()
    return chunk


@pytest.mark.asyncio
async def test_not_configured_when_no_provider_available(db_session, monkeypatch):
    monkeypatch.setattr(research_agent_module, "get_embedding_provider", lambda settings: None)

    result = await ResearchAgent().run(db_session)

    assert result.status == "not_configured"
    assert (await db_session.execute(select(Embedding))).scalars().all() == []


@pytest.mark.asyncio
async def test_embeds_pending_chunks_and_persists_vectors(db_session, monkeypatch):
    chunk = await _make_chunk(db_session, "flood risk in Miami-Dade")
    provider = _FakeEmbeddingProvider()
    monkeypatch.setattr(research_agent_module, "get_embedding_provider", lambda settings: provider)

    result = await ResearchAgent().run(db_session)

    assert result.status == "success"
    assert result.details["embedded"] == 1
    embeddings = (await db_session.execute(select(Embedding))).scalars().all()
    assert len(embeddings) == 1
    assert embeddings[0].document_chunk_id == chunk.id
    assert embeddings[0].model_name == "fake-embedding-model"
    assert embeddings[0].vector == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_chunks_with_existing_embeddings_are_not_reembedded(db_session, monkeypatch):
    already_embedded = await _make_chunk(db_session, "already embedded chunk")
    pending = await _make_chunk(db_session, "pending chunk")
    db_session.add(
        Embedding(
            id=new_uuid(),
            document_chunk_id=already_embedded.id,
            model_name="prior-model",
            vector=[0.9],
        )
    )
    await db_session.flush()

    provider = _FakeEmbeddingProvider()
    monkeypatch.setattr(research_agent_module, "get_embedding_provider", lambda settings: provider)

    result = await ResearchAgent().run(db_session)

    assert result.status == "success"
    assert result.details["pending_chunks"] == 1
    assert provider.embedded_texts == ["pending chunk"]
    embeddings = (await db_session.execute(select(Embedding))).scalars().all()
    assert len(embeddings) == 2  # the pre-existing one, plus exactly one new one
    assert {e.document_chunk_id for e in embeddings} == {already_embedded.id, pending.id}


@pytest.mark.asyncio
async def test_run_is_bounded_to_max_chunks_per_run(db_session, monkeypatch):
    monkeypatch.setattr(research_agent_module, "MAX_CHUNKS_PER_RUN", 1)
    await _make_chunk(db_session, "chunk one")
    await _make_chunk(db_session, "chunk two")

    provider = _FakeEmbeddingProvider()
    monkeypatch.setattr(research_agent_module, "get_embedding_provider", lambda settings: provider)

    result = await ResearchAgent().run(db_session)

    assert result.status == "success"
    assert result.details["embedded"] == 1
    assert len((await db_session.execute(select(Embedding))).scalars().all()) == 1


@pytest.mark.asyncio
async def test_no_chunks_pending_reports_success_without_calling_provider(db_session, monkeypatch):
    provider = _FakeEmbeddingProvider()
    monkeypatch.setattr(research_agent_module, "get_embedding_provider", lambda settings: provider)

    result = await ResearchAgent().run(db_session)

    assert result.status == "success"
    assert result.details["pending_chunks"] == 0
    assert provider.embedded_texts == []


@pytest.mark.asyncio
async def test_provider_failure_is_reported_as_failed_and_no_vector_is_fabricated(db_session, monkeypatch):
    await _make_chunk(db_session, "will fail to embed")
    provider = _FakeEmbeddingProvider(fail=True)
    monkeypatch.setattr(research_agent_module, "get_embedding_provider", lambda settings: provider)

    result = await ResearchAgent().run(db_session)

    assert result.status == "failed"
    assert (await db_session.execute(select(Embedding))).scalars().all() == []
