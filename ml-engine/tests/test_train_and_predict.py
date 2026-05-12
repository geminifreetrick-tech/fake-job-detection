"""End-to-end smoke test: train on the bundled CSV → load → predict."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "datasets" / "sample_jobs.csv"
GEN_SCRIPT = ROOT / "datasets" / "generate_dataset.py"


def _ensure_dataset() -> None:
    if DATASET.exists():
        return
    import runpy

    runpy.run_path(str(GEN_SCRIPT), run_name="__main__")


@pytest.fixture(scope="module")
def trained_artifact(tmp_path_factory):
    _ensure_dataset()
    out = tmp_path_factory.mktemp("model_store")
    # Invoke train.py via runpy so we exercise the CLI path.
    import sys as _sys

    saved_argv = _sys.argv[:]
    _sys.argv = ["train", "--data", str(DATASET), "--out", str(out)]
    try:
        import runpy
        runpy.run_module("app.models.train", run_name="__main__")
    finally:
        _sys.argv = saved_argv
    return out


def test_manifest_written(trained_artifact: Path):
    manifest_path = trained_artifact / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text())
    assert manifest["feature_names"]
    assert manifest["metrics"]["pr_auc"] >= 0.7  # synthetic dataset, easy task


def test_load_and_predict(trained_artifact: Path):
    sys.path.insert(0, str(ROOT))
    from app.models.registry import load_latest
    from app.models.explain import Explainer
    from app.pipeline import FEATURE_LABELS, FEATURE_NAMES, FeaturePipeline

    art = load_latest(trained_artifact)
    pipe = FeaturePipeline()
    expl = Explainer(art.model)

    fraud_text = (
        "URGENT!!! Work from home and make money fast. Earn $5000 per week! "
        "Send your CV to recruit@gmail.com or contact us on Telegram @hire. "
        "Pay a small $49 registration fee to start."
    )
    legit_text = (
        "Acme Inc is hiring a Senior Software Engineer in NYC. "
        "Salary $140,000/year. Requirements: 5+ years Python experience, "
        "strong communication skills, bachelor's degree."
    )
    v_fraud = pipe.vectorize(fraud_text)
    v_legit = pipe.vectorize(legit_text)
    p_fraud = float(art.model.predict_proba(v_fraud.reshape(1, -1))[0, 1])
    p_legit = float(art.model.predict_proba(v_legit.reshape(1, -1))[0, 1])
    assert p_fraud > p_legit
    assert p_fraud > 0.6
    assert p_legit < 0.4

    explanations = expl.explain(v_fraud, FEATURE_NAMES, FEATURE_LABELS, top_k=5)
    assert len(explanations) == 5
    assert all("contribution" in e for e in explanations)
