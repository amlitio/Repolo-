"""Hybrid search and research-agent endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.schemas.search import (
    HybridSearchResult,
    ResearchAskRequest,
    ResearchAskResponse,
)
from app.services.search import hybrid_search

router = APIRouter(tags=["search"])


@router.get(
    "/search/hybrid",
    response_model=list[HybridSearchResult],
    summary="Hybrid keyword + vector search",
    description="Keyword leg (ILIKE/full-text) is live today. The vector/embedding leg is a documented "
    "no-op until document embeddings are populated - it never fabricates a similarity score.",
)
async def search_hybrid(
    db: AsyncSession = Depends(get_db),
    q: str = Query(..., min_length=1),
    top_k: int = Query(10, ge=1, le=100),
) -> list[HybridSearchResult]:
    hits = await hybrid_search(db, q, top_k=top_k)
    return [
        HybridSearchResult(type=h.type, id=h.id, title=h.title, snippet=h.snippet, score=h.score)
        for h in hits
    ]


@router.post(
    "/research/ask",
    response_model=ResearchAskResponse,
    summary="Ask the research agent a question",
    description="If no LLM provider API key is configured in this environment, returns an honestly "
    "labeled 'not configured' answer with HTTP 200 rather than a fabricated response.",
)
async def research_ask(payload: ResearchAskRequest) -> ResearchAskResponse:
    settings = get_settings()
    if not settings.openai_api_key and not settings.gemini_api_key:
        return ResearchAskResponse(
            answer="Research agent is not configured in this environment.",
            citations=[],
        )

    # An LLM key is configured; in this MVP the actual RAG pipeline lives in
    # apps/workers (research_agent.py) and is invoked out-of-band. The API
    # layer intentionally does not call a paid LLM API synchronously inside
    # a request handler - that integration point is left for the worker
    # process so retries/cost-control/observability live in one place.
    return ResearchAskResponse(
        answer="An LLM provider is configured, but synchronous research answers are served by the "
        "apps/workers research_agent pipeline in this MVP, not directly from the API process.",
        citations=[],
    )
