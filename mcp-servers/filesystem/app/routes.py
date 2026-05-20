from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _common.security import require_service_token  # noqa: E402

from .config import settings
from .pdf import build_report
from .storage import (
    is_allowed_mime,
    read_bytes,
    reports_root,
    save_bytes,
    upload_root,
)

router = APIRouter(dependencies=[Depends(require_service_token)])

_SHA_RE = re.compile(r"^[a-f0-9]{64}$")


@router.post("/uploads", status_code=201)
async def create_upload(file: UploadFile = File(...)) -> dict:
    data = await file.read()
    if not data:
        raise HTTPException(400, "empty file")
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(413, f"file exceeds {settings.max_upload_bytes} bytes")
    if not is_allowed_mime(file.content_type):
        raise HTTPException(415, f"content type {file.content_type!r} not allowed")
    sha, path = save_bytes(data, upload_root())
    return {
        "sha256": sha,
        "size": len(data),
        "content_type": file.content_type,
        "filename": file.filename,
        "path": str(path.relative_to(upload_root())),
    }


@router.get("/uploads/{sha}")
async def get_upload(sha: str) -> Response:
    if not _SHA_RE.match(sha):
        raise HTTPException(400, "invalid sha")
    data = read_bytes(sha, upload_root())
    if data is None:
        raise HTTPException(404, "not found")
    return Response(content=data, media_type="application/octet-stream")


@router.post("/reports")
async def render_report(body: Annotated[dict, Body()]) -> dict:
    """Render a PDF detection report. Body is the AnalysisResponse shape from backend."""
    if not isinstance(body, dict):
        raise HTTPException(400, "body must be an object")
    pdf = build_report(body)
    sha, _path = save_bytes(pdf, reports_root())
    return {"sha256": sha, "size": len(pdf), "content_type": "application/pdf"}


@router.get("/reports/{sha}")
async def get_report(sha: str, download: bool = Query(default=False)) -> Response:
    if not _SHA_RE.match(sha):
        raise HTTPException(400, "invalid sha")
    data = read_bytes(sha, reports_root())
    if data is None:
        raise HTTPException(404, "not found")
    headers = {}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="report-{sha[:12]}.pdf"'
    return Response(content=data, media_type="application/pdf", headers=headers)
