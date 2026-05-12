from __future__ import annotations

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from ..core.config import settings
from .hub import broadcast, subscribe, unsubscribe

router = APIRouter()


@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    token = ws.query_params.get("token")
    if not token:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    if payload.get("kind") != "access":
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = str(payload["sub"])
    await ws.accept()
    await subscribe(user_id, ws)
    try:
        await ws.send_json({"type": "hello", "user_id": user_id})
        while True:
            # Keep-alive: ignore any client text, optionally support a "ping" command.
            msg = await ws.receive_text()
            if msg == "ping":
                await ws.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        await unsubscribe(user_id, ws)


# Re-export for `from ..ws.hub import broadcast` style usage.
__all__ = ["router", "broadcast"]
