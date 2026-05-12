"""Composition of feature extractors → ordered feature vector."""
from __future__ import annotations

from typing import Iterable

import numpy as np

from . import grammar, lexical, salary, text_clean, url_rules


# Ordered list of features the model expects. Keeping the order stable is
# critical because the saved model is indexed positionally.
FEATURE_NAMES: list[str] = [
    "salary_z_score",
    "salary_unrealistic_flag",
    "num_urls",
    "url_suspicious_tld",
    "url_max_entropy",
    "url_brand_lookalike",
    "contact_free_email",
    "contact_telegram",
    "contact_whatsapp",
    "caps_ratio",
    "repeat_punct_ratio",
    "oov_ratio",
    "exclaim_density",
    "num_tokens",
    "scam_marker_count",
    "scam_marker_score",
    "asks_for_payment",
]

# Human-readable label for each feature (used in API explanations).
FEATURE_LABELS: dict[str, str] = {
    "salary_z_score": "Advertised salary vs. typical range for the role",
    "salary_unrealistic_flag": "Salary is implausibly high",
    "num_urls": "Number of URLs in the posting",
    "url_suspicious_tld": "Links use a high-risk TLD",
    "url_max_entropy": "Domain name looks randomly generated",
    "url_brand_lookalike": "Link mimics a well-known brand",
    "contact_free_email": "Contact is a free email (e.g. Gmail) instead of corporate",
    "contact_telegram": "Asks to continue on Telegram",
    "contact_whatsapp": "Asks to continue on WhatsApp",
    "caps_ratio": "Excessive ALL-CAPS words",
    "repeat_punct_ratio": "Repeated punctuation (e.g. '!!!')",
    "oov_ratio": "High share of unusual/misspelled words",
    "exclaim_density": "Density of exclamation marks",
    "num_tokens": "Length of the posting",
    "scam_marker_count": "Number of scam-marker phrases matched",
    "scam_marker_score": "Weighted score of scam-marker phrases",
    "asks_for_payment": "Asks the applicant to pay money",
}


class FeaturePipeline:
    """Stateless feature extractor."""

    feature_names: list[str] = FEATURE_NAMES

    def extract(self, text: str) -> dict[str, float]:
        cleaned = text_clean.clean(text)
        feats: dict[str, float] = {}
        feats.update(salary.features(cleaned))
        feats.update(url_rules.features(cleaned))
        feats.update(grammar.features(cleaned))
        feats.update(lexical.features(cleaned))
        # Defensive: ensure every expected feature is present.
        for name in FEATURE_NAMES:
            feats.setdefault(name, 0.0)
        return {k: float(feats[k]) for k in FEATURE_NAMES}

    def vectorize(self, text: str) -> np.ndarray:
        feats = self.extract(text)
        return np.array([feats[name] for name in FEATURE_NAMES], dtype=np.float64)

    def vectorize_many(self, texts: Iterable[str]) -> np.ndarray:
        return np.vstack([self.vectorize(t) for t in texts])
