from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

_CONFIG = ConfigDict(protected_namespaces=())


class JobCreate(BaseModel):
    user_id: str
    raw_text: str = Field(min_length=1)
    source_type: Literal["text", "pdf", "image"] = "text"
    source_uri: str | None = None
    sha256: str


class JobOut(BaseModel):
    id: str
    user_id: str
    raw_text: str
    source_type: str
    source_uri: str | None
    sha256: str
    created_at: datetime


class PredictionCreate(BaseModel):
    model_config = _CONFIG
    job_id: str
    label: Literal["fraud", "legit"]
    score: float = Field(ge=0.0, le=1.0)
    explanation: dict = Field(default_factory=dict)
    model_version: str


class PredictionOut(BaseModel):
    model_config = _CONFIG
    id: str
    job_id: str
    label: str
    score: float
    explanation: dict
    model_version: str
    created_at: datetime


class JobWithPrediction(BaseModel):
    job: JobOut
    prediction: PredictionOut | None


# ---- Scam Reports ----
class ScamReportCreate(BaseModel):
    user_id: str
    job_id: str | None = None
    title: str = Field(min_length=1, max_length=256)
    description: str = Field(min_length=1)
    company: str | None = None
    url: str | None = None


class ScamReportUpdate(BaseModel):
    status: Literal["open", "reviewed", "dismissed", "confirmed"] | None = None
    admin_notes: str | None = None


class ScamReportOut(BaseModel):
    id: str
    user_id: str
    job_id: str | None
    title: str
    description: str
    company: str | None
    url: str | None
    status: str
    admin_notes: str | None
    created_at: datetime
    updated_at: datetime


# ---- Company Verification ----
class CompanyVerificationCreate(BaseModel):
    name: str
    domain: str | None = None
    legitimacy_score: float = Field(ge=0.0, le=1.0)
    signals: dict = Field(default_factory=dict)
    whois: dict | None = None
    search_results: list = Field(default_factory=list)
    cached_until: datetime


class CompanyVerificationOut(BaseModel):
    id: str
    name: str
    domain: str | None
    legitimacy_score: float
    signals: dict
    whois: dict | None
    search_results: list
    cached_until: datetime
    created_at: datetime


# ---- Articles ----
class ArticleCreate(BaseModel):
    slug: str
    title: str
    summary: str
    body_md: str
    tags: list[str] = Field(default_factory=list)
    published: bool = True


class ArticleOut(BaseModel):
    id: str
    slug: str
    title: str
    summary: str
    body_md: str
    tags: list[str]
    published: bool
    created_at: datetime


# ---- Quizzes ----
class QuizQuestion(BaseModel):
    id: str
    prompt: str
    choices: list[str]
    correct_index: int = Field(ge=0)
    explanation: str = ""


class QuizCreate(BaseModel):
    slug: str
    title: str
    description: str
    questions: list[QuizQuestion]


class QuizOut(BaseModel):
    id: str
    slug: str
    title: str
    description: str
    questions: list[dict]
    created_at: datetime


class QuizAttemptCreate(BaseModel):
    quiz_id: str
    user_id: str
    answers: list[int]
    score: float = Field(ge=0.0, le=1.0)
    total: int = Field(ge=0)
    correct: int = Field(ge=0)


class QuizAttemptOut(BaseModel):
    id: str
    quiz_id: str
    user_id: str
    answers: list[int]
    score: float
    total: int
    correct: int
    created_at: datetime


# ---- Analytics Events ----
class AnalyticsEventCreate(BaseModel):
    user_id: str | None = None
    name: str = Field(min_length=1, max_length=64)
    props: dict = Field(default_factory=dict)


class AnalyticsEventOut(BaseModel):
    id: str
    user_id: str | None
    name: str
    props: dict
    created_at: datetime


# ---- Notifications ----
class NotificationCreate(BaseModel):
    user_id: str
    channel: Literal["email", "websocket"]
    template: str
    payload: dict = Field(default_factory=dict)
    status: Literal["sent", "failed", "queued"] = "sent"
    error: str | None = None


class NotificationOut(BaseModel):
    id: str
    user_id: str
    channel: str
    template: str
    payload: dict
    status: str
    error: str | None
    created_at: datetime


# ---- Aggregates (for analytics-mcp) ----
class TimeBucket(BaseModel):
    bucket: datetime
    count: int


class FraudOverTime(BaseModel):
    fraud: list[TimeBucket]
    legit: list[TimeBucket]


class TopFeatureBucket(BaseModel):
    feature: str
    count: int


class AnalyticsSummary(BaseModel):
    total_jobs: int
    total_fraud: int
    total_legit: int
    fraud_rate: float
    users: int
    reports_open: int
    avg_fraud_score: float
