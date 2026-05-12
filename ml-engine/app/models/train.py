"""Train the fraud classifier.

Usage:
    python -m app.models.train --data datasets/sample_jobs.csv --out model_store/
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

# Allow `python -m app.models.train` from the ml-engine root.
_HERE = Path(__file__).resolve()
sys.path.insert(0, str(_HERE.parents[2]))

from app.pipeline import FEATURE_NAMES, FeaturePipeline  # noqa: E402

from .registry import save_model  # noqa: E402


def load_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}. Run `python datasets/generate_dataset.py` to create it."
        )
    df = pd.read_csv(path)
    if "text" not in df.columns or "label" not in df.columns:
        raise ValueError("Dataset must include `text` and `label` columns.")
    return df


def featurize(df: pd.DataFrame, pipe: FeaturePipeline) -> np.ndarray:
    return pipe.vectorize_many(df["text"].astype(str).tolist())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--test-size", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    df = load_dataset(args.data)
    pipe = FeaturePipeline()
    X = featurize(df, pipe)
    y = df["label"].astype(int).to_numpy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=args.seed, stratify=y
    )

    model = XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.1,
        objective="binary:logistic",
        eval_metric="aucpr",
        random_state=args.seed,
        n_jobs=2,
    )
    model.fit(X_train, y_train)

    proba = model.predict_proba(X_test)[:, 1]
    preds = (proba >= 0.5).astype(int)
    metrics = {
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "roc_auc": float(roc_auc_score(y_test, proba)),
        "pr_auc": float(average_precision_score(y_test, proba)),
        "precision": float(precision_score(y_test, preds, zero_division=0)),
        "recall": float(recall_score(y_test, preds, zero_division=0)),
        "f1": float(f1_score(y_test, preds, zero_division=0)),
    }

    artifact = save_model(model, args.out, FEATURE_NAMES, metrics)
    print(f"Saved {artifact.path}")
    print(f"Metrics: {metrics}")


if __name__ == "__main__":
    main()
