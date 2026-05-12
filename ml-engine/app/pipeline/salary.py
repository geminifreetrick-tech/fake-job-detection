"""Salary realism feature extractor.

We pull dollar-denominated salary mentions out of the posting and compare them
against a small built-in reference table for common roles. The output is a pair
of features:

- ``salary_z_score`` — z-score vs the role's reference distribution (0 if unknown).
- ``salary_unrealistic_flag`` — 1 when the posting advertises an outlier (very
  high) salary, or when *any* salary is mentioned but no role can be inferred.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Role keyword -> (mean, std) annual USD, derived from US BLS 2023 ranges.
ROLE_REFERENCE: dict[str, tuple[float, float]] = {
    "data entry": (38_000, 6_000),
    "customer service": (40_000, 8_000),
    "warehouse": (38_000, 7_000),
    "software engineer": (130_000, 35_000),
    "developer": (120_000, 35_000),
    "designer": (85_000, 25_000),
    "product manager": (140_000, 35_000),
    "analyst": (80_000, 25_000),
    "marketing": (75_000, 25_000),
    "accountant": (78_000, 20_000),
    "teacher": (60_000, 15_000),
    "nurse": (80_000, 20_000),
    "driver": (45_000, 10_000),
    "secretary": (42_000, 8_000),
    "assistant": (45_000, 12_000),
    "intern": (40_000, 12_000),
    "remote": (65_000, 25_000),
}

# Matches "$3,000", "$3000/week", "USD 5000 weekly", "5,000 per month", "$120k", etc.
_SALARY_RE = re.compile(
    r"""(?ix)
    (?:\$|USD\s?|US\$\s?)?           # optional currency
    (\d{1,3}(?:[,\s]\d{3})+|\d{2,7}) # amount
    \s*(k)?\s*                       # optional k suffix
    (?:                              # optional period qualifier
        (?:/|\sper\s)\s?(hour|hr|h|day|d|week|wk|w|month|mo|m|year|yr|y|annum)
        | \s?(hourly|daily|weekly|monthly|annually)
    )?
    """,
    re.VERBOSE,
)


@dataclass(frozen=True)
class SalaryMention:
    raw: str
    amount_annual: float
    period: str | None


_PERIOD_MULTIPLIERS: dict[str, float] = {
    "hour": 2080, "hr": 2080, "h": 2080, "hourly": 2080,
    "day": 250, "d": 250, "daily": 250,
    "week": 52, "wk": 52, "w": 52, "weekly": 52,
    "month": 12, "mo": 12, "m": 12, "monthly": 12,
    "year": 1, "yr": 1, "y": 1, "annum": 1, "annually": 1,
}


def _to_annual(amount: float, period: str | None) -> float:
    if not period:
        # Without a period and amount very large -> assume annual; small -> ambiguous.
        return amount if amount >= 10_000 else amount * 52  # treat as weekly
    return amount * _PERIOD_MULTIPLIERS.get(period.lower(), 1)


def extract_mentions(text: str) -> list[SalaryMention]:
    mentions: list[SalaryMention] = []
    for m in _SALARY_RE.finditer(text):
        raw_amount = m.group(1)
        k_suffix = bool(m.group(2))
        period = m.group(3) or m.group(4)
        try:
            amount = float(raw_amount.replace(",", "").replace(" ", ""))
        except ValueError:
            continue
        if k_suffix:
            amount *= 1000
        # Filter out implausibly tiny matches (e.g. years like "2024").
        if amount < 100 and not period:
            continue
        annual = _to_annual(amount, period)
        if annual < 5_000:
            # almost certainly not a salary
            continue
        mentions.append(SalaryMention(raw=m.group(0).strip(), amount_annual=annual, period=period))
    return mentions


def detect_role(text: str) -> str | None:
    lower = text.lower()
    # Match the longest role keyword first to prefer "software engineer" over "engineer".
    for role in sorted(ROLE_REFERENCE, key=len, reverse=True):
        if role in lower:
            return role
    return None


def features(text: str) -> dict[str, float]:
    mentions = extract_mentions(text)
    if not mentions:
        return {"salary_z_score": 0.0, "salary_unrealistic_flag": 0.0}

    role = detect_role(text)
    max_annual = max(m.amount_annual for m in mentions)
    if role is None:
        # Salary mentioned but no anchor → suspicious if it's high.
        unrealistic = 1.0 if max_annual > 150_000 else 0.0
        return {"salary_z_score": 0.0, "salary_unrealistic_flag": unrealistic}

    mean, std = ROLE_REFERENCE[role]
    z = (max_annual - mean) / max(std, 1.0)
    return {
        "salary_z_score": float(z),
        "salary_unrealistic_flag": 1.0 if z >= 3.0 else 0.0,
    }
