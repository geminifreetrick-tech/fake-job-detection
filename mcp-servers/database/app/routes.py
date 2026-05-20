from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _common.security import require_service_token  # noqa: E402

from .db import get_session
from .models import (
    AnalyticsEvent,
    Article,
    CompanyVerification,
    Job,
    Notification,
    Prediction,
    Quiz,
    QuizAttempt,
    ScamReport,
)
from .schemas import (
    AnalyticsEventCreate,
    AnalyticsEventOut,
    AnalyticsSummary,
    ArticleCreate,
    ArticleOut,
    CompanyVerificationCreate,
    CompanyVerificationOut,
    FraudOverTime,
    JobCreate,
    JobOut,
    JobWithPrediction,
    NotificationCreate,
    NotificationOut,
    PredictionCreate,
    PredictionOut,
    QuizAttemptCreate,
    QuizAttemptOut,
    QuizCreate,
    QuizOut,
    ScamReportCreate,
    ScamReportOut,
    ScamReportUpdate,
    TimeBucket,
    TopFeatureBucket,
)

router = APIRouter(dependencies=[Depends(require_service_token)])


# ---------------------------------------------------------------------- Jobs


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


# ----------------------------------------------------------------- Reports


@router.post("/reports", response_model=ScamReportOut, status_code=201)
async def create_report(
    body: ScamReportCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ScamReportOut:
    report = ScamReport(**body.model_dump())
    session.add(report)
    await session.commit()
    await session.refresh(report)
    return ScamReportOut.model_validate(report, from_attributes=True)


@router.get("/reports", response_model=list[ScamReportOut])
async def list_reports(
    session: Annotated[AsyncSession, Depends(get_session)],
    status: str | None = Query(default=None),
    limit: int = Query(50, ge=1, le=500),
) -> list[ScamReportOut]:
    stmt = select(ScamReport).order_by(desc(ScamReport.created_at)).limit(limit)
    if status:
        stmt = stmt.where(ScamReport.status == status)
    res = await session.execute(stmt)
    return [ScamReportOut.model_validate(r, from_attributes=True) for r in res.scalars().all()]


@router.get("/users/{user_id}/reports", response_model=list[ScamReportOut])
async def list_user_reports(
    user_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(50, ge=1, le=500),
) -> list[ScamReportOut]:
    res = await session.execute(
        select(ScamReport)
        .where(ScamReport.user_id == user_id)
        .order_by(desc(ScamReport.created_at))
        .limit(limit)
    )
    return [ScamReportOut.model_validate(r, from_attributes=True) for r in res.scalars().all()]


@router.patch("/reports/{report_id}", response_model=ScamReportOut)
async def update_report(
    report_id: str,
    body: ScamReportUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ScamReportOut:
    res = await session.execute(select(ScamReport).where(ScamReport.id == report_id))
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(404, "report not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(report, k, v)
    report.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(report)
    return ScamReportOut.model_validate(report, from_attributes=True)


# ------------------------------------------------------- Company verifications


@router.post("/company-verifications", response_model=CompanyVerificationOut, status_code=201)
async def create_company_verification(
    body: CompanyVerificationCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CompanyVerificationOut:
    cv = CompanyVerification(**body.model_dump())
    session.add(cv)
    await session.commit()
    await session.refresh(cv)
    return CompanyVerificationOut.model_validate(cv, from_attributes=True)


@router.get("/company-verifications", response_model=CompanyVerificationOut | None)
async def get_company_verification(
    session: Annotated[AsyncSession, Depends(get_session)],
    name: str = Query(..., min_length=1),
    domain: str | None = Query(default=None),
) -> CompanyVerificationOut | None:
    stmt = (
        select(CompanyVerification)
        .where(func.lower(CompanyVerification.name) == name.lower())
        .order_by(desc(CompanyVerification.created_at))
        .limit(1)
    )
    if domain:
        stmt = (
            select(CompanyVerification)
            .where(
                and_(
                    func.lower(CompanyVerification.name) == name.lower(),
                    CompanyVerification.domain == domain.lower(),
                )
            )
            .order_by(desc(CompanyVerification.created_at))
            .limit(1)
        )
    res = await session.execute(stmt)
    cv = res.scalar_one_or_none()
    if cv is None:
        return None
    return CompanyVerificationOut.model_validate(cv, from_attributes=True)


# ------------------------------------------------------------------ Articles


@router.post("/articles", response_model=ArticleOut, status_code=201)
async def create_article(
    body: ArticleCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ArticleOut:
    res = await session.execute(select(Article).where(Article.slug == body.slug))
    existing = res.scalar_one_or_none()
    if existing:
        # Idempotent upsert.
        for k, v in body.model_dump().items():
            setattr(existing, k, v)
        await session.commit()
        await session.refresh(existing)
        return ArticleOut.model_validate(existing, from_attributes=True)
    article = Article(**body.model_dump())
    session.add(article)
    await session.commit()
    await session.refresh(article)
    return ArticleOut.model_validate(article, from_attributes=True)


@router.get("/articles", response_model=list[ArticleOut])
async def list_articles(
    session: Annotated[AsyncSession, Depends(get_session)],
    tag: str | None = Query(default=None),
    limit: int = Query(50, ge=1, le=500),
) -> list[ArticleOut]:
    stmt = (
        select(Article)
        .where(Article.published.is_(True))
        .order_by(desc(Article.created_at))
        .limit(limit)
    )
    res = await session.execute(stmt)
    items = res.scalars().all()
    if tag:
        items = [a for a in items if tag in (a.tags or [])]
    return [ArticleOut.model_validate(a, from_attributes=True) for a in items]


@router.get("/articles/{slug}", response_model=ArticleOut)
async def get_article(
    slug: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ArticleOut:
    res = await session.execute(select(Article).where(Article.slug == slug))
    a = res.scalar_one_or_none()
    if not a:
        raise HTTPException(404, "article not found")
    return ArticleOut.model_validate(a, from_attributes=True)


# ------------------------------------------------------------------- Quizzes


@router.post("/quizzes", response_model=QuizOut, status_code=201)
async def create_quiz(
    body: QuizCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> QuizOut:
    res = await session.execute(select(Quiz).where(Quiz.slug == body.slug))
    existing = res.scalar_one_or_none()
    payload: dict[str, Any] = body.model_dump()
    payload["questions"] = [q.model_dump() if hasattr(q, "model_dump") else q for q in body.questions]
    if existing:
        for k, v in payload.items():
            setattr(existing, k, v)
        await session.commit()
        await session.refresh(existing)
        return QuizOut.model_validate(existing, from_attributes=True)
    quiz = Quiz(**payload)
    session.add(quiz)
    await session.commit()
    await session.refresh(quiz)
    return QuizOut.model_validate(quiz, from_attributes=True)


@router.get("/quizzes", response_model=list[QuizOut])
async def list_quizzes(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[QuizOut]:
    res = await session.execute(select(Quiz).order_by(desc(Quiz.created_at)))
    return [QuizOut.model_validate(q, from_attributes=True) for q in res.scalars().all()]


@router.get("/quizzes/{slug}", response_model=QuizOut)
async def get_quiz(
    slug: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> QuizOut:
    res = await session.execute(select(Quiz).where(Quiz.slug == slug))
    q = res.scalar_one_or_none()
    if not q:
        raise HTTPException(404, "quiz not found")
    return QuizOut.model_validate(q, from_attributes=True)


@router.post("/quiz-attempts", response_model=QuizAttemptOut, status_code=201)
async def create_quiz_attempt(
    body: QuizAttemptCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> QuizAttemptOut:
    attempt = QuizAttempt(**body.model_dump())
    session.add(attempt)
    await session.commit()
    await session.refresh(attempt)
    return QuizAttemptOut.model_validate(attempt, from_attributes=True)


@router.get("/users/{user_id}/quiz-attempts", response_model=list[QuizAttemptOut])
async def list_user_quiz_attempts(
    user_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(50, ge=1, le=500),
) -> list[QuizAttemptOut]:
    res = await session.execute(
        select(QuizAttempt)
        .where(QuizAttempt.user_id == user_id)
        .order_by(desc(QuizAttempt.created_at))
        .limit(limit)
    )
    return [QuizAttemptOut.model_validate(a, from_attributes=True) for a in res.scalars().all()]


# ------------------------------------------------------ Analytics events


@router.post("/analytics-events", response_model=AnalyticsEventOut, status_code=201)
async def create_event(
    body: AnalyticsEventCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AnalyticsEventOut:
    e = AnalyticsEvent(**body.model_dump())
    session.add(e)
    await session.commit()
    await session.refresh(e)
    return AnalyticsEventOut.model_validate(e, from_attributes=True)


@router.get("/analytics/summary", response_model=AnalyticsSummary)
async def analytics_summary(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AnalyticsSummary:
    total_jobs = (await session.execute(select(func.count(Job.id)))).scalar_one() or 0
    total_fraud = (
        await session.execute(
            select(func.count(Prediction.id)).where(Prediction.label == "fraud")
        )
    ).scalar_one() or 0
    total_legit = (
        await session.execute(
            select(func.count(Prediction.id)).where(Prediction.label == "legit")
        )
    ).scalar_one() or 0
    users = (
        await session.execute(select(func.count(func.distinct(Job.user_id))))
    ).scalar_one() or 0
    reports_open = (
        await session.execute(
            select(func.count(ScamReport.id)).where(ScamReport.status == "open")
        )
    ).scalar_one() or 0
    avg_fraud_score = (
        await session.execute(
            select(func.coalesce(func.avg(Prediction.score), 0.0)).where(
                Prediction.label == "fraud"
            )
        )
    ).scalar_one() or 0.0
    denom = total_fraud + total_legit
    fraud_rate = (total_fraud / denom) if denom else 0.0
    return AnalyticsSummary(
        total_jobs=total_jobs,
        total_fraud=total_fraud,
        total_legit=total_legit,
        fraud_rate=fraud_rate,
        users=users,
        reports_open=reports_open,
        avg_fraud_score=float(avg_fraud_score),
    )


@router.get("/analytics/fraud-over-time", response_model=FraudOverTime)
async def fraud_over_time(
    session: Annotated[AsyncSession, Depends(get_session)],
    days: int = Query(default=30, ge=1, le=365),
) -> FraudOverTime:
    """Daily counts of fraud vs legit predictions for the last `days` days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    # Group by date(created_at) — portable across SQLite/Postgres via func.date()
    stmt = (
        select(
            func.date(Prediction.created_at).label("d"),
            Prediction.label,
            func.count(Prediction.id),
        )
        .where(Prediction.created_at >= cutoff)
        .group_by(func.date(Prediction.created_at), Prediction.label)
        .order_by(func.date(Prediction.created_at))
    )
    res = await session.execute(stmt)
    fraud: list[TimeBucket] = []
    legit: list[TimeBucket] = []
    for d, label, count in res.all():
        # `d` is a date or string depending on the dialect; normalize to datetime.
        if isinstance(d, str):
            dt = datetime.fromisoformat(d).replace(tzinfo=timezone.utc)
        elif isinstance(d, datetime):
            dt = d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        else:
            dt = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
        bucket = TimeBucket(bucket=dt, count=count)
        if label == "fraud":
            fraud.append(bucket)
        else:
            legit.append(bucket)
    return FraudOverTime(fraud=fraud, legit=legit)


@router.get("/analytics/top-scam-features", response_model=list[TopFeatureBucket])
async def top_scam_features(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(default=10, ge=1, le=50),
    sample: int = Query(default=500, ge=10, le=5000),
) -> list[TopFeatureBucket]:
    """Approximate frequency of "fraud-direction" features in the top
    explanations of recent fraud predictions."""
    res = await session.execute(
        select(Prediction.explanation)
        .where(Prediction.label == "fraud")
        .order_by(desc(Prediction.created_at))
        .limit(sample)
    )
    counts: dict[str, int] = {}
    for (exp,) in res.all():
        if not isinstance(exp, dict):
            continue
        for e in (exp.get("explanations") or [])[:5]:
            if e.get("direction") == "fraud":
                feat = str(e.get("feature", ""))
                if feat:
                    counts[feat] = counts.get(feat, 0) + 1
    items = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    return [TopFeatureBucket(feature=k, count=v) for k, v in items]


# --------------------------------------------------------------- Notifications


@router.post("/notifications", response_model=NotificationOut, status_code=201)
async def create_notification(
    body: NotificationCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> NotificationOut:
    n = Notification(**body.model_dump())
    session.add(n)
    await session.commit()
    await session.refresh(n)
    return NotificationOut.model_validate(n, from_attributes=True)


@router.get("/users/{user_id}/notifications", response_model=list[NotificationOut])
async def list_user_notifications(
    user_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(50, ge=1, le=500),
) -> list[NotificationOut]:
    res = await session.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(desc(Notification.created_at))
        .limit(limit)
    )
    return [NotificationOut.model_validate(n, from_attributes=True) for n in res.scalars().all()]
