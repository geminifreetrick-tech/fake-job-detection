from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class EmailRequest(BaseModel):
    user_id: str
    to: EmailStr
    template: str = Field(min_length=1)
    context: dict = Field(default_factory=dict)


class WsRequest(BaseModel):
    user_id: str
    event: Literal["fraud.detected", "analysis.completed", "report.updated", "ping"] = "analysis.completed"
    payload: dict = Field(default_factory=dict)


class NotifyResponse(BaseModel):
    status: Literal["sent", "failed", "queued"]
    channel: Literal["email", "websocket"]
    error: str | None = None
