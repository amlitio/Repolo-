"""Search and research-agent schemas."""

from __future__ import annotations

from pydantic import BaseModel


class HybridSearchResult(BaseModel):
    type: str
    id: str
    title: str
    snippet: str
    score: float


class ResearchAskRequest(BaseModel):
    question: str
    context_filters: dict | None = None


class ResearchCitation(BaseModel):
    source_id: str
    url: str
    snippet: str


class ResearchAskResponse(BaseModel):
    answer: str
    citations: list[ResearchCitation]
