"""Lexical scam-marker features.

A small hand-curated lexicon of phrases that show up frequently in fraudulent
job postings. We compute (a) a count of matched markers and (b) a normalized
score giving more weight to markers with higher prior signal.
"""
from __future__ import annotations

import re
from pathlib import Path

_LEX_PATH = Path(__file__).resolve().parents[2] / "datasets" / "scam_lexicon.tsv"


def _load_lexicon() -> dict[str, float]:
    if not _LEX_PATH.exists():
        return {}
    out: dict[str, float] = {}
    for line in _LEX_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            continue
        phrase, weight = parts[0].lower(), parts[1]
        try:
            out[phrase] = float(weight)
        except ValueError:
            continue
    return out


_LEX = _load_lexicon()
# Pre-compile word-boundary regexes for each phrase for speed.
_PATTERNS = {
    phrase: re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE)
    for phrase in _LEX
}


def features(text: str) -> dict[str, float]:
    if not text or not _LEX:
        return {"scam_marker_count": 0.0, "scam_marker_score": 0.0, "asks_for_payment": 0.0}
    total_weight = 0.0
    count = 0
    for phrase, weight in _LEX.items():
        if _PATTERNS[phrase].search(text):
            count += 1
            total_weight += weight
    text_low = text.lower()
    asks_for_payment = 1.0 if any(
        kw in text_low
        for kw in (
            "registration fee", "application fee", "training fee", "processing fee",
            "send money", "pay upfront", "deposit required", "buy a kit",
        )
    ) else 0.0
    return {
        "scam_marker_count": float(count),
        "scam_marker_score": float(total_weight),
        "asks_for_payment": asks_for_payment,
    }
