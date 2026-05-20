from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from ..clients import DbClient, FilesystemClient
from ..core.security import CurrentUser, get_current_user
from ..deps import get_db_client, get_filesystem_client

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/reports/{job_id}", status_code=201)
async def generate_report(
    job_id: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[DbClient, Depends(get_db_client)],
    fs: Annotated[FilesystemClient, Depends(get_filesystem_client)],
) -> dict:
    """Render a PDF detection report for one of the user's jobs."""
    try:
        items = await db.list_user_jobs(user.user_id, limit=200)
        match = next((i for i in items if i.get("job", {}).get("id") == job_id), None)
        if not match:
            raise HTTPException(404, "job not found for current user")
        job = match["job"]
        pred = match.get("prediction") or {}
        explanation = pred.get("explanation") or {}
        body = {
            "user_email": user.email,
            "source_type": job.get("source_type", "text"),
            "text_excerpt": (job.get("raw_text") or "")[:1800],
            "prediction": {
                "label": pred.get("label"),
                "score": pred.get("score"),
                "model_version": pred.get("model_version"),
            },
            "explanations": explanation.get("explanations", []),
            "features": explanation.get("features", {}),
        }
        return await fs.render_report(body)
    finally:
        await db.aclose()
        await fs.aclose()


@router.get("/reports/{sha}", response_class=Response)
async def get_report(
    sha: str,
    _user: Annotated[CurrentUser, Depends(get_current_user)],
    fs: Annotated[FilesystemClient, Depends(get_filesystem_client)],
) -> Response:
    try:
        data = await fs.fetch_report(sha, download=True)
        if not data:
            raise HTTPException(404, "report not found")
        return Response(
            content=data,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="report-{sha[:12]}.pdf"'},
        )
    finally:
        await fs.aclose()
