from __future__ import annotations

from pydantic import BaseModel


class InternalWsPush(BaseModel):
    user_id: str
    payload: dict
