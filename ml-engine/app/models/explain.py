"""SHAP wrapper used by the inference server."""
from __future__ import annotations

from typing import Any

import numpy as np
import shap


class Explainer:
    def __init__(self, model: Any) -> None:
        self._explainer = shap.TreeExplainer(model)

    def explain(
        self,
        x: np.ndarray,
        feature_names: list[str],
        feature_labels: dict[str, str],
        top_k: int = 5,
    ) -> list[dict]:
        """Return top-K features by absolute SHAP value contribution."""
        if x.ndim == 1:
            x = x.reshape(1, -1)
        values = self._explainer.shap_values(x)
        # TreeExplainer for binary XGBoost returns a (n_samples, n_features) array.
        if isinstance(values, list):
            values = values[1] if len(values) > 1 else values[0]
        row = values[0]
        idx = np.argsort(-np.abs(row))[:top_k]
        explanations: list[dict] = []
        for i in idx:
            name = feature_names[int(i)]
            explanations.append(
                {
                    "feature": name,
                    "label": feature_labels.get(name, name),
                    "value": float(x[0, int(i)]),
                    "contribution": float(row[int(i)]),
                    "direction": "fraud" if row[int(i)] > 0 else "legit",
                }
            )
        return explanations
