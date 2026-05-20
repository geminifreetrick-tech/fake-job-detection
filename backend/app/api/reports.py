from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ..clients import DbClient, NotificationClient
from ..core.security import CurrentUser, get_current_user
from ..deps import get_db_client, get_notification_client
from ..schemas.reports import ReportCreate

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", status_code=201)
async def submit_report(
    body: ReportCreate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[DbClient, Depends(get_db_client)],
    notif: Annotated[NotificationClient, Depends(get_notification_client)],
) -> dict:
    try:
        report = await db.create_report({"user_id": user.user_id, **body.model_dump()})
    finally:
        pass

    # Best-effort notification to the submitter; fire-and-forget.
    if user.email:
        try:
            await notif.send_email(
                user_id=user.user_id,
                to=user.email,
                template="report_submitted",
                context={"user": {"email": user.email}, "report": report},
            )
        except Exception:
            pass

    try:
        await db.record_event(
            {"user_id": user.user_id, "name": "report.submitted", "props": {"id": report["id"]}}
        )
    except Exception:
        pass

    try:
        await db.aclose()
    finally:
        await notif.aclose()
    return report


@router.get("/mine")
async def my_reports(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[DbClient, Depends(get_db_client)],
) -> list[dict]:
    try:
        return await db.list_user_reports(user.user_id)
    finally:
        await db.aclose()
