from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class UpsertItem(BaseModel):
    id: str
    document: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class UpsertRequest(BaseModel):
    items: list[UpsertItem] = Field(min_length=1)


class QueryRequest(BaseModel):
    query_texts: list[str] = Field(min_length=1)
    n_results: int = Field(default=5, ge=1, le=50)
    where: dict[str, Any] | None = None


class QueryMatch(BaseModel):
    id: str
    document: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    distance: float | None = None


class QueryResponse(BaseModel):
    matches: list[QueryMatch]


class ContextResponse(BaseModel):
    recent: list[QueryMatch]
    similar_scams: list[QueryMatch]


class DeleteRequest(BaseModel):
    ids: list[str] = Field(min_length=1)
