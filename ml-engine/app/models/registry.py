from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib


MANIFEST_NAME = "manifest.json"


@dataclass
class ModelArtifact:
    model: Any
    version: str
    feature_names: list[str]
    trained_at: str
    metrics: dict[str, float]
    path: Path


def save_model(
    model: Any,
    out_dir: Path,
    feature_names: list[str],
    metrics: dict[str, float],
) -> ModelArtifact:
    out_dir.mkdir(parents=True, exist_ok=True)
    version = f"v{int(time.time())}"
    model_path = out_dir / f"model_{version}.joblib"
    joblib.dump(model, model_path)
    manifest = {
        "version": version,
        "model_path": model_path.name,
        "feature_names": feature_names,
        "trained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "metrics": metrics,
    }
    (out_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2))
    return ModelArtifact(
        model=model,
        version=version,
        feature_names=feature_names,
        trained_at=manifest["trained_at"],
        metrics=metrics,
        path=model_path,
    )


def load_latest(out_dir: Path) -> ModelArtifact:
    manifest_path = out_dir / MANIFEST_NAME
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"No model manifest at {manifest_path}. "
            f"Train one first: `python -m app.models.train --data datasets/sample_jobs.csv --out {out_dir}`"
        )
    manifest = json.loads(manifest_path.read_text())
    model_path = out_dir / manifest["model_path"]
    if not model_path.exists():
        raise FileNotFoundError(f"Manifest references missing artifact {model_path}")
    model = joblib.load(model_path)
    return ModelArtifact(
        model=model,
        version=manifest["version"],
        feature_names=manifest["feature_names"],
        trained_at=manifest["trained_at"],
        metrics=manifest["metrics"],
        path=model_path,
    )


def model_store_dir() -> Path:
    return Path(os.environ.get("MODEL_STORE_DIR", "/app/model_store"))
