from __future__ import annotations

from pydantic import BaseModel


class VerifyCompanyRequest(BaseModel):
    name: str
    domain: str | None = None
