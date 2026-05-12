from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AnalyzeTextRequest(BaseModel):
    text: str = Field(min_length=1)


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    job_id: str
    prediction_id: str
    label: str
    score: float
    explanations: list[dict[str, Any]]
    features: dict[str, float]
    model_version: str
    source_type: str
    ocr: dict[str, Any] | None = None
