from __future__ import annotations

import hashlib
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..clients import DbClient, MemoryClient, MlEngineClient
from ..core.security import CurrentUser, get_current_user
from ..deps import get_db_client, get_memory_client, get_ml_client
from ..schemas.jobs import AnalysisResponse, AnalyzeTextRequest
from ..ws.hub import broadcast

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


async def _record(
    user: CurrentUser,
    pred: dict,
    *,
    raw_text: str,
    source_type: str,
    source_uri: str | None,
    db: DbClient,
    memory: MemoryClient,
) -> AnalysisResponse:
    digest = _sha256(raw_text)
    job = await db.create_job(
        {
            "user_id": user.user_id,
            "raw_text": raw_text,
            "source_type": source_type,
            "source_uri": source_uri,
            "sha256": digest,
        }
    )
    prediction = await db.create_prediction(
        {
            "job_id": job["id"],
            "label": pred["label"],
            "score": pred["score"],
            "explanation": {
                "explanations": pred["explanations"],
                "features": pred["features"],
            },
            "model_version": pred["model_version"],
        }
    )
    # Best-effort memory upsert; do not fail the request if memory is down.
    try:
        await memory.upsert(
            "user_context",
            [
                {
                    "id": f"job-{job['id']}",
                    "document": raw_text[:4000],
                    "metadata": {
                        "user_id": user.user_id,
                        "label": pred["label"],
                        "score": pred["score"],
                        "model_version": pred["model_version"],
                        "source_type": source_type,
                    },
                }
            ],
        )
    except Exception:
        pass

    # Best-effort WebSocket broadcast to the owning user.
    try:
        await broadcast(
            user.user_id,
            {
                "type": "prediction.completed",
                "job_id": job["id"],
                "prediction_id": prediction["id"],
                "label": pred["label"],
                "score": pred["score"],
            },
        )
    except Exception:
        pass

    return AnalysisResponse(
        job_id=job["id"],
        prediction_id=prediction["id"],
        label=pred["label"],
        score=pred["score"],
        explanations=pred["explanations"],
        features=pred["features"],
        model_version=pred["model_version"],
        source_type=pred.get("source_type", source_type),
        ocr=pred.get("ocr"),
    )


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_text(
    body: AnalyzeTextRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[DbClient, Depends(get_db_client)],
    ml: Annotated[MlEngineClient, Depends(get_ml_client)],
    memory: Annotated[MemoryClient, Depends(get_memory_client)],
) -> AnalysisResponse:
    try:
        pred = await ml.predict_text(body.text)
    except httpx.HTTPStatusError as e:
        raise HTTPException(e.response.status_code, e.response.text)
    finally:
        await ml.aclose()
    try:
        return await _record(
            user, pred, raw_text=body.text, source_type="text", source_uri=None, db=db, memory=memory
        )
    finally:
        await db.aclose()
        await memory.aclose()


@router.post("/analyze-file", response_model=AnalysisResponse)
async def analyze_file(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[DbClient, Depends(get_db_client)],
    ml: Annotated[MlEngineClient, Depends(get_ml_client)],
    memory: Annotated[MemoryClient, Depends(get_memory_client)],
    file: UploadFile = File(...),
) -> AnalysisResponse:
    data = await file.read()
    if not data:
        raise HTTPException(400, "empty file")
    try:
        pred = await ml.predict_file(
            file.filename or "upload.bin", file.content_type or "application/octet-stream", data
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(e.response.status_code, e.response.text)
    finally:
        await ml.aclose()
    text = pred.get("text_excerpt") or ""
    try:
        return await _record(
            user,
            pred,
            raw_text=text,
            source_type=pred.get("source_type", "text"),
            source_uri=file.filename,
            db=db,
            memory=memory,
        )
    finally:
        await db.aclose()
        await memory.aclose()
