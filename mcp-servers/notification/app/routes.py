from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, Depends

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _common.security import require_service_token  # noqa: E402

from .clients import log_notification, push_ws
from .email import send as send_email
from .schemas import EmailRequest, NotifyResponse, WsRequest
from .templates import get as get_template, render

router = APIRouter(dependencies=[Depends(require_service_token)])


def _explanations_text(ctx: dict) -> str:
    items = ctx.get("explanations") or []
    if not items:
        return "(no top features supplied)"
    return "\n".join(
        f"- {i.get('label', i.get('feature', '?'))} (contribution {i.get('contribution', 0):+.2f})"
        for i in items[:5]
    )


@router.post("/email", response_model=NotifyResponse)
async def send_email_route(body: EmailRequest) -> NotifyResponse:
    tpl = get_template(body.template)
    ctx = dict(body.context)
    ctx.setdefault("user", {"email": str(body.to)})
    ctx["explanations_text"] = _explanations_text(ctx)
    subject = render(tpl["subject"], ctx)
    text = render(tpl["body"], ctx)
    ok, err = await send_email(str(body.to), subject, text)
    await log_notification(
        {
            "user_id": body.user_id,
            "channel": "email",
            "template": body.template,
            "payload": {"to": str(body.to), "subject": subject},
            "status": "sent" if ok else "failed",
            "error": err,
        }
    )
    return NotifyResponse(status="sent" if ok else "failed", channel="email", error=err)


@router.post("/ws", response_model=NotifyResponse)
async def push_ws_route(body: WsRequest) -> NotifyResponse:
    payload = {"event": body.event, **body.payload}
    ok = await push_ws(body.user_id, payload)
    await log_notification(
        {
            "user_id": body.user_id,
            "channel": "websocket",
            "template": body.event,
            "payload": payload,
            "status": "sent" if ok else "failed",
            "error": None if ok else "backend ws push failed",
        }
    )
    return NotifyResponse(
        status="sent" if ok else "failed",
        channel="websocket",
        error=None if ok else "backend ws push failed",
    )
