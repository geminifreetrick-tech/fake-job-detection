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
