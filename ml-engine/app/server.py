"""FastAPI inference server for the fake-job detector."""
from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Body, FastAPI, File, HTTPException, UploadFile

# Make the bundled `_common` module importable when running outside Docker.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mcp-servers"))
try:
    from _common.logging import configure_logging  # type: ignore
except Exception:  # pragma: no cover
    def configure_logging() -> None:
        logging.basicConfig(level=logging.INFO)

from .config import settings
from .models.explain import Explainer
from .models.registry import load_latest, model_store_dir
from .ocr import extract_text_from_bytes
from .pipeline import FEATURE_LABELS, FEATURE_NAMES, FeaturePipeline

logger = logging.getLogger("ml-engine")


class _State:
    pipeline: FeaturePipeline | None = None
    artifact: object | None = None
    explainer: Explainer | None = None


_state = _State()


def _load() -> None:
    artifact = load_latest(Path(settings.model_store_dir or model_store_dir()))
    _state.pipeline = FeaturePipeline()
    _state.artifact = artifact
    _state.explainer = Explainer(artifact.model)
    logger.info("loaded model %s (trained_at=%s)", artifact.version, artifact.trained_at)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    configure_logging()
    _load()
    yield


app = FastAPI(title="ml-engine", version="0.1.0", lifespan=_lifespan)


@app.get("/healthz")
async def healthz() -> dict:
    ready = _state.pipeline is not None and _state.artifact is not None
    return {"status": "ok" if ready else "loading", "service": "ml-engine"}


@app.get("/model/info")
async def model_info() -> dict:
    art = _state.artifact
    if art is None:
        raise HTTPException(503, "model not loaded")
    return {
        "version": art.version,  # type: ignore[attr-defined]
        "trained_at": art.trained_at,  # type: ignore[attr-defined]
        "metrics": art.metrics,  # type: ignore[attr-defined]
        "features": FEATURE_NAMES,
    }


@app.post("/model/reload")
async def model_reload() -> dict:
    _load()
    return {"status": "reloaded", "version": _state.artifact.version}  # type: ignore[attr-defined]


def _predict_text(text: str, *, source_type: str = "text", ocr_meta: dict | None = None) -> dict:
    if _state.pipeline is None or _state.artifact is None or _state.explainer is None:
        raise HTTPException(503, "model not loaded")
    vec = _state.pipeline.vectorize(text)
    proba = float(_state.artifact.model.predict_proba(vec.reshape(1, -1))[0, 1])  # type: ignore[attr-defined]
    label = "fraud" if proba >= 0.5 else "legit"
    explanations = _state.explainer.explain(vec, FEATURE_NAMES, FEATURE_LABELS, top_k=5)
    features = {name: float(v) for name, v in zip(FEATURE_NAMES, vec.tolist())}
    out = {
        "label": label,
        "score": proba,
        "explanations": explanations,
        "features": features,
        "model_version": _state.artifact.version,  # type: ignore[attr-defined]
        "source_type": source_type,
        "text_excerpt": text[:500],
    }
    if ocr_meta:
        out["ocr"] = ocr_meta
    return out


@app.post("/predict")
async def predict(payload: Annotated[dict, Body()]) -> dict:
    text = (payload or {}).get("text") or ""
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(400, "text is required")
    return _predict_text(text, source_type="text")


@app.post("/predict/file")
async def predict_file(file: UploadFile = File(...)) -> dict:
    data = await file.read()
    if not data:
        raise HTTPException(400, "empty file")
    try:
        ocr = extract_text_from_bytes(data, file.content_type)
    except Exception as exc:
        raise HTTPException(400, f"OCR failed: {exc}")
    if not ocr.text.strip():
        raise HTTPException(422, "no text extracted from file")
    return _predict_text(
        ocr.text,
        source_type=ocr.source_type,
        ocr_meta={"pages": ocr.pages, "used_ocr": ocr.used_ocr},
    )
