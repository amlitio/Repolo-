"""Hybrid keyword + vector search scaffold.

Keyword leg: works today, ILIKE-style substring match across documents and
the county/source registries (good enough for MVP; swap for Postgres
full-text `tsvector`/`tsquery` once we're on real Postgres).

Vector leg: a documented no-op until `embeddings` rows are actually
populated by the research/ingestion agents. We intentionally do NOT
fabricate a similarity score here - an empty vector result set with a
score of 0.0 is more honest than a made-up cosine value computed against
nothing.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.registry import get_registry
from app.models.search import Document


@dataclass(frozen=True)
class HybridSearchHit:
    type: str
    id: str
    title: str
    snippet: str
    score: float


async def keyword_search(db: AsyncSession, query: str, top_k: int = 10) -> list[HybridSearchHit]:
    """Simple substring/ILIKE-style match across documents, then the static
    county/source registries, ranked by a naive relevance heuristic
    (exact name match > prefix match > substring match)."""

    hits: list[HybridSearchHit] = []
    q = query.strip()
    if not q:
        return []
    q_lower = q.lower()

    result = await db.execute(select(Document))
    for doc in result.scalars().all():
        if q_lower in doc.title.lower():
            hits.append(
                HybridSearchHit(
                    type="document",
                    id=doc.id,
                    title=doc.title,
                    snippet=doc.title,
                    score=1.0 if doc.title.lower() == q_lower else 0.6,
                )
            )

    registry = get_registry()
    for county in registry.search_counties(q):
        hits.append(
            HybridSearchHit(
                type="county",
                id=county["fips"],
                title=f"{county['name']} County, FL",
                snippet=f"FIPS {county['fips']}, {county['region']} region",
                score=1.0 if county["name"].lower() == q_lower else 0.7,
            )
        )

    for source in registry.sources:
        if q_lower in source["name"].lower() or q_lower in source["id"].lower():
            hits.append(
                HybridSearchHit(
                    type="source",
                    id=source["id"],
                    title=source["name"],
                    snippet=source["notes"][:200],
                    score=0.5,
                )
            )

    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:top_k]


async def vector_search(db: AsyncSession, query: str, top_k: int = 10) -> list[HybridSearchHit]:
    """Documented no-op: returns an empty result set until embeddings are
    populated. Never fabricates a similarity score."""

    return []


async def hybrid_search(db: AsyncSession, query: str, top_k: int = 10) -> list[HybridSearchHit]:
    keyword_hits = await keyword_search(db, query, top_k=top_k)
    vector_hits = await vector_search(db, query, top_k=top_k)
    combined = keyword_hits + vector_hits
    combined.sort(key=lambda h: h.score, reverse=True)
    return combined[:top_k]
