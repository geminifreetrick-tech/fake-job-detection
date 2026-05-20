"""Internal endpoints used by other services on the Docker network.

These routes are protected by the X-Service-Token header rather than by JWT.
"""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from ..core.config import settings
from ..schemas.admin import InternalWsPush
from ..ws.hub import broadcast

router = APIRouter(prefix="/internal", tags=["internal"])


def _check_token(provided: str | None) -> None:
    if not provided or provided != settings.service_token:
        raise HTTPException(status_code=401, detail="invalid service token")


@router.post("/ws/push", status_code=202)
async def ws_push(
    body: InternalWsPush,
    x_service_token: str | None = Header(default=None, alias="X-Service-Token"),
) -> dict:
    _check_token(x_service_token)
    sent = await broadcast(body.user_id, body.payload)
    return {"sent": sent}
