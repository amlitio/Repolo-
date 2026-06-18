"""Document store + chunking + embeddings for hybrid keyword/vector search
and the research agent's RAG scaffold.

`Embedding.vector` uses PortableVector: a real pgvector column on Postgres,
a JSON list-of-floats column on SQLite (unit tests never need real cosine
similarity at the DB layer - that exercise is `@pytest.mark.integration`).
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import TimestampMixin, new_uuid
from app.models.types import GUID, PortableVector


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    source_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("sources.id"), nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    doc_type: Mapped[str] = mapped_column(String(100), nullable=False, default="generic")


class DocumentChunk(Base, TimestampMixin):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    document_id: Mapped[str] = mapped_column(GUID(), ForeignKey("documents.id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(nullable=False, default=0)
    text: Mapped[str] = mapped_column(Text, nullable=False)


class Embedding(Base, TimestampMixin):
    __tablename__ = "embeddings"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    document_chunk_id: Mapped[str] = mapped_column(GUID(), ForeignKey("document_chunks.id"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    vector = mapped_column(PortableVector(dim=1536), nullable=True)
