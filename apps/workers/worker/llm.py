"""Pluggable embedding-provider interface for the Research agent.

No third-party LLM SDK is added as a dependency here - every other
connector in this codebase (FEMA/NOAA/USGS/WMD) talks to its upstream API
directly over httpx rather than through a vendor SDK, so this follows the
same pattern for OpenAI's/Gemini's embeddings endpoints.

`Embedding.vector` (app/models/search.py) is a PortableVector(dim=1536), so
both providers below are configured to return exactly 1536-dimensional
vectors regardless of which one is active.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import httpx
from app.config import Settings

EMBEDDING_DIM = 1536


class EmbeddingProvider(ABC):
    model_name: str

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text, same order, each of length EMBEDDING_DIM."""


class OpenAiEmbeddingProvider(EmbeddingProvider):
    model_name = "text-embedding-3-small"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def embed(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": self.model_name, "input": texts, "dimensions": EMBEDDING_DIM},
            )
            response.raise_for_status()
            payload = response.json()
            return [item["embedding"] for item in payload["data"]]


class GeminiEmbeddingProvider(EmbeddingProvider):
    model_name = "text-embedding-004"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def embed(self, texts: list[str]) -> list[list[float]]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:batchEmbedContents"
        requests_payload = [
            {
                "model": f"models/{self.model_name}",
                "content": {"parts": [{"text": text}]},
                "outputDimensionality": EMBEDDING_DIM,
            }
            for text in texts
        ]
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url, params={"key": self._api_key}, json={"requests": requests_payload}
            )
            response.raise_for_status()
            payload = response.json()
            return [item["values"] for item in payload["embeddings"]]


def get_embedding_provider(settings: Settings) -> EmbeddingProvider | None:
    """Returns the configured provider, preferring OpenAI - mirrors the
    configured-provider check order in app/routers/search.py::research_ask."""

    if settings.openai_api_key:
        return OpenAiEmbeddingProvider(settings.openai_api_key)
    if settings.gemini_api_key:
        return GeminiEmbeddingProvider(settings.gemini_api_key)
    return None
