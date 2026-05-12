from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _common.security import require_service_token  # noqa: E402

from .db import get_session
from .models import Job, Prediction
from .schemas import (
    JobCreate,
    JobOut,
    JobWithPrediction,
    PredictionCreate,
    PredictionOut,
)

router = APIRouter(dependencies=[Depends(require_service_token)])


@router.post("/jobs", response_model=JobOut, status_code=201)
async def create_job(
    body: JobCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> JobOut:
    res = await session.execute(
        select(Job).where(Job.user_id == body.user_id, Job.sha256 == body.sha256)
    )
    existing = res.scalar_one_or_none()
    if existing:
        return JobOut.model_validate(existing, from_attributes=True)
    job = Job(**body.model_dump())
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return JobOut.model_validate(job, from_attributes=True)


@router.get("/jobs/{job_id}", response_model=JobOut)
async def get_job(
    job_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> JobOut:
    res = await session.execute(select(Job).where(Job.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "job not found")
    return JobOut.model_validate(job, from_attributes=True)


@router.post("/predictions", response_model=PredictionOut, status_code=201)
async def create_prediction(
    body: PredictionCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PredictionOut:
    res = await session.execute(select(Job).where(Job.id == body.job_id))
    if not res.scalar_one_or_none():
        raise HTTPException(404, "job not found")
    pred = Prediction(**body.model_dump())
    session.add(pred)
    await session.commit()
    await session.refresh(pred)
    return PredictionOut.model_validate(pred, from_attributes=True)


@router.get("/users/{user_id}/jobs", response_model=list[JobWithPrediction])
async def list_user_jobs(
    user_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(20, ge=1, le=200),
) -> list[JobWithPrediction]:
    res = await session.execute(
        select(Job).where(Job.user_id == user_id).order_by(desc(Job.created_at)).limit(limit)
    )
    jobs = res.scalars().all()
    out: list[JobWithPrediction] = []
    for j in jobs:
        pr = await session.execute(
            select(Prediction)
            .where(Prediction.job_id == j.id)
            .order_by(desc(Prediction.created_at))
            .limit(1)
        )
        pred = pr.scalar_one_or_none()
        out.append(
            JobWithPrediction(
                job=JobOut.model_validate(j, from_attributes=True),
                prediction=(
                    PredictionOut.model_validate(pred, from_attributes=True) if pred else None
                ),
            )
        )
    return out
