from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    description: str = Field(min_length=1)
    company: str | None = None
    url: str | None = None
    job_id: str | None = None


class ReportUpdate(BaseModel):
    status: Literal["open", "reviewed", "dismissed", "confirmed"] | None = None
    admin_notes: str | None = None
