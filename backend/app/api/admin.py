from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ..clients import AnalyticsClient, DbClient, NotificationClient
from ..core.security import CurrentUser, require_admin
from ..deps import get_analytics_client, get_db_client, get_notification_client
from ..schemas.reports import ReportUpdate

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard")
async def dashboard(
    _admin: Annotated[CurrentUser, Depends(require_admin)],
    analytics: Annotated[AnalyticsClient, Depends(get_analytics_client)],
) -> dict:
    try:
        return await analytics.dashboard()
    finally:
        await analytics.aclose()


@router.get("/reports")
async def list_reports(
    _admin: Annotated[CurrentUser, Depends(require_admin)],
    db: Annotated[DbClient, Depends(get_db_client)],
    status: str | None = None,
    limit: int = 50,
) -> list[dict]:
    try:
        return await db.list_reports(status=status, limit=limit)
    finally:
        await db.aclose()


@router.patch("/reports/{report_id}")
async def update_report(
    report_id: str,
    body: ReportUpdate,
    _admin: Annotated[CurrentUser, Depends(require_admin)],
    db: Annotated[DbClient, Depends(get_db_client)],
    notif: Annotated[NotificationClient, Depends(get_notification_client)],
) -> dict:
    payload = body.model_dump(exclude_unset=True)
    if not payload:
        raise HTTPException(400, "no fields to update")
    try:
        updated = await db.update_report(report_id, payload)
    finally:
        await db.aclose()

    # Notify owner if status changed.
    if "status" in payload:
        try:
            # We don't have the owner's email — admin UI can pass it later.
            # Still log a ws notification.
            await notif.send_ws(
                updated["user_id"],
                event="report.updated",
                payload={"report_id": updated["id"], "status": updated["status"]},
            )
        except Exception:
            pass
        finally:
            await notif.aclose()
    return updated
