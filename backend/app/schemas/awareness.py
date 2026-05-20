from __future__ import annotations

from pydantic import BaseModel, Field


class QuizSubmission(BaseModel):
    quiz_slug: str = Field(min_length=1)
    answers: list[int] = Field(min_length=1)


class QuizResult(BaseModel):
    quiz_slug: str
    score: float
    total: int
    correct: int
    breakdown: list[dict]
    attempt_id: str | None = None
