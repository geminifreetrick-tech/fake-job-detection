from __future__ import annotations

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    num: int = Field(default=5, ge=1, le=10)


class SearchResultItem(BaseModel):
    title: str
    snippet: str
    url: str
    display_link: str = ""


class SearchResponse(BaseModel):
    results: list[SearchResultItem]
    provider: str  # "google_cse" | "fallback"


class VerifyCompanyRequest(BaseModel):
    name: str = Field(min_length=1)
    domain: str | None = None


class VerifyCompanyResponse(BaseModel):
    name: str
    domain: str | None
    legitimacy_score: float
    signals: dict
    whois: dict | None
    search_results: list[SearchResultItem]
    provider: str
