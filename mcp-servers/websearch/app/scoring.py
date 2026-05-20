"""Combine CSE + WHOIS signals into a 0..1 legitimacy score."""
from __future__ import annotations

import math
import re
from urllib.parse import urlparse

_OFFICIAL_RE = re.compile(r"\b(careers?|jobs?|about|contact)\b", re.IGNORECASE)


def _domain_of(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return ""
    return host.lstrip("www.")


def compute(name: str, domain: str | None, results: list[dict], whois_blob: dict | None) -> dict:
    """Return {legitimacy_score, signals}.

    Heuristics:
    - Domain age ≥ 730 days → +0.4
    - 200..30 days → +0.1
    - <30 days → -0.3
    - At least one CSE result with the same domain → +0.25
    - 'careers'/'about' page link → +0.15
    - LinkedIn / Crunchbase / Wikipedia result → +0.1 (cap 1)
    - No results AND no whois → fallback baseline 0.4
    """
    signals: dict[str, float] = {}
    score = 0.5

    age = None
    if whois_blob and whois_blob.get("creation_date"):
        from .whois_lookup import age_days

        age = age_days(whois_blob)
        signals["whois_age_days"] = float(age) if age is not None else 0.0
        if age is not None:
            if age >= 730:
                score += 0.4
            elif age >= 30:
                score += 0.1
            else:
                score -= 0.3

    if domain and results:
        same_domain_hits = sum(
            1 for r in results if _domain_of(r.get("url", "")) == domain.lower()
        )
        signals["results_same_domain"] = float(same_domain_hits)
        if same_domain_hits > 0:
            score += 0.25

    if results:
        career_hits = sum(
            1 for r in results if _OFFICIAL_RE.search(r.get("title", "") + " " + r.get("snippet", ""))
        )
        signals["career_or_about_hits"] = float(career_hits)
        if career_hits > 0:
            score += 0.15

        reputable = ("linkedin.com", "crunchbase.com", "wikipedia.org", "bloomberg.com")
        if any(any(rep in r.get("url", "").lower() for rep in reputable) for r in results):
            score += 0.1
            signals["found_in_reputable_source"] = 1.0
        signals["results_count"] = float(len(results))

    if not results and not whois_blob:
        score = 0.4
        signals["fallback"] = 1.0

    score = max(0.0, min(1.0, score))
    # Smooth a little so values aren't too crunchy near boundaries.
    score = round(1.0 / (1.0 + math.exp(-6 * (score - 0.5))), 3)
    return {"legitimacy_score": score, "signals": signals}
