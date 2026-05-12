"""Grammar / style anomaly features.

We deliberately keep this dependency-free and rely on simple text statistics
that correlate with low-quality scam postings. The features are intentionally
descriptive (caps ratio, repeated punctuation, OOV ratio against a small word
list) rather than a full grammar model.
"""
from __future__ import annotations

import re
from pathlib import Path

from .text_clean import word_tokens

_REPEATED_PUNCT_RE = re.compile(r"([!?.])\1{1,}")
_DICT_PATH = Path(__file__).resolve().parents[2] / "datasets" / "common_words.txt"


def _load_dict() -> set[str]:
    if not _DICT_PATH.exists():
        return set()
    return {w.strip().lower() for w in _DICT_PATH.read_text().splitlines() if w.strip()}


_DICT = _load_dict()


def features(text: str) -> dict[str, float]:
    if not text:
        return {
            "caps_ratio": 0.0,
            "repeat_punct_ratio": 0.0,
            "oov_ratio": 0.0,
            "exclaim_density": 0.0,
            "num_tokens": 0.0,
        }
    tokens = word_tokens(text)
    n = len(tokens) or 1
    caps_tokens = sum(1 for t in tokens if len(t) >= 3 and t.isupper())
    caps_ratio = caps_tokens / n
    repeated = len(_REPEATED_PUNCT_RE.findall(text))
    repeat_punct_ratio = repeated / max(len(text), 1)
    exclaim_density = text.count("!") / max(len(text), 1)
    if _DICT:
        oov = sum(1 for t in tokens if t.lower() not in _DICT)
        oov_ratio = oov / n
    else:
        oov_ratio = 0.0
    return {
        "caps_ratio": float(caps_ratio),
        "repeat_punct_ratio": float(repeat_punct_ratio),
        "oov_ratio": float(oov_ratio),
        "exclaim_density": float(exclaim_density),
        "num_tokens": float(n),
    }
