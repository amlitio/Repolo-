"""Shared response envelope schemas, mirroring packages/shared/src/types/api.ts."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ApiErrorBody(BaseModel):
    code: str
    message: str
    details: list = []


class ApiErrorResponse(BaseModel):
    success: bool = False
    error: ApiErrorBody


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
