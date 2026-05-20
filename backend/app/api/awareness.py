from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ..clients import DbClient
from ..core.security import CurrentUser, get_current_user
from ..deps import get_db_client
from ..schemas.awareness import QuizResult, QuizSubmission

router = APIRouter(prefix="/awareness", tags=["awareness"])


@router.get("/articles")
async def list_articles(
    db: Annotated[DbClient, Depends(get_db_client)],
    tag: str | None = None,
) -> list[dict]:
    try:
        return await db.list_articles(tag=tag)
    finally:
        await db.aclose()


@router.get("/articles/{slug}")
async def get_article(
    slug: str,
    db: Annotated[DbClient, Depends(get_db_client)],
) -> dict:
    try:
        return await db.get_article(slug)
    finally:
        await db.aclose()


def _strip_answers(quiz: dict) -> dict:
    """Hide correct_index/explanation from quiz payloads served to learners."""
    out = dict(quiz)
    out["questions"] = [
        {"id": q.get("id"), "prompt": q.get("prompt"), "choices": q.get("choices", [])}
        for q in quiz.get("questions", [])
    ]
    return out


@router.get("/quizzes")
async def list_quizzes(
    db: Annotated[DbClient, Depends(get_db_client)],
) -> list[dict]:
    try:
        quizzes = await db.list_quizzes()
    finally:
        await db.aclose()
    return [_strip_answers(q) for q in quizzes]


@router.get("/quizzes/{slug}")
async def get_quiz(
    slug: str,
    db: Annotated[DbClient, Depends(get_db_client)],
) -> dict:
    try:
        quiz = await db.get_quiz(slug)
    finally:
        await db.aclose()
    return _strip_answers(quiz)


@router.post("/quizzes/submit", response_model=QuizResult)
async def submit_quiz(
    body: QuizSubmission,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[DbClient, Depends(get_db_client)],
) -> QuizResult:
    try:
        quiz = await db.get_quiz(body.quiz_slug)
        questions: list[dict] = quiz["questions"]
        if len(body.answers) != len(questions):
            raise HTTPException(400, "answer count mismatch")

        correct = 0
        breakdown: list[dict] = []
        for q, ans in zip(questions, body.answers):
            ci = int(q.get("correct_index", -1))
            is_correct = ans == ci
            if is_correct:
                correct += 1
            breakdown.append(
                {
                    "question_id": q.get("id"),
                    "user_answer": ans,
                    "correct_index": ci,
                    "is_correct": is_correct,
                    "explanation": q.get("explanation", ""),
                }
            )
        total = len(questions)
        score = correct / total if total else 0.0

        attempt = await db.submit_quiz_attempt(
            {
                "quiz_id": quiz["id"],
                "user_id": user.user_id,
                "answers": body.answers,
                "score": score,
                "total": total,
                "correct": correct,
            }
        )
        try:
            await db.record_event(
                {
                    "user_id": user.user_id,
                    "name": "quiz.completed",
                    "props": {"quiz_slug": body.quiz_slug, "score": score},
                }
            )
        except Exception:
            pass
    finally:
        await db.aclose()
    return QuizResult(
        quiz_slug=body.quiz_slug,
        score=score,
        total=total,
        correct=correct,
        breakdown=breakdown,
        attempt_id=attempt.get("id"),
    )


@router.get("/me/quiz-attempts")
async def my_attempts(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[DbClient, Depends(get_db_client)],
) -> list[dict]:
    try:
        return await db.list_user_quiz_attempts(user.user_id)
    finally:
        await db.aclose()
