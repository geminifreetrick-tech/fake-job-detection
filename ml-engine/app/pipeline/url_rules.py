"""URL / contact-channel heuristics."""
from __future__ import annotations

import math
import re

_URL_RE = re.compile(r"https?://[^\s)>\]]+", re.IGNORECASE)
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

_SUSPICIOUS_TLDS = {
    "tk", "ml", "ga", "cf", "gq", "xyz", "top", "click", "work", "loan",
    "icu", "online", "win", "men", "info",
}
_FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
    "live.com", "mail.com", "yandex.com", "protonmail.com", "icloud.com",
}
_BRAND_LOOKALIKES = {
    "linkedin", "indeed", "amazon", "google", "microsoft", "apple", "meta",
    "facebook", "netflix", "tesla",
}


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    freq: dict[str, int] = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    total = len(s)
    return -sum((c / total) * math.log2(c / total) for c in freq.values())


def _domain_of(url: str) -> str:
    no_proto = re.sub(r"^https?://", "", url, flags=re.IGNORECASE)
    return no_proto.split("/", 1)[0].split("?", 1)[0].lower()


def _tld_of(domain: str) -> str:
    return domain.rsplit(".", 1)[-1] if "." in domain else ""


def _edit_distance_le(a: str, b: str, k: int) -> bool:
    """Return True if Levenshtein distance between a and b is ≤ k. Cheap DP."""
    if abs(len(a) - len(b)) > k:
        return False
    if a == b:
        return True
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i] + [0] * len(b)
        best_in_row = curr[0]
        for j, cb in enumerate(b, start=1):
            curr[j] = min(
                prev[j] + 1,           # deletion
                curr[j - 1] + 1,       # insertion
                prev[j - 1] + (ca != cb),  # substitution
            )
            if curr[j] < best_in_row:
                best_in_row = curr[j]
        if best_in_row > k:
            return False
        prev = curr
    return prev[-1] <= k


def _is_lookalike(domain: str) -> bool:
    """Heuristic: any subdomain label or hyphen-token closely resembles a brand."""
    label = domain.split(".")[0]
    tokens = [label] + [t for t in label.split("-") if t]
    for token in tokens:
        for brand in _BRAND_LOOKALIKES:
            if token == brand:
                return False  # exact brand on its own → assume legitimate page
            if brand in token and token != brand:
                # e.g. "amazonhire" or "linkedinjobs"
                return True
            if len(brand) >= 5 and _edit_distance_le(brand, token, 1):
                # e.g. "amazn" vs "amazon"
                return True
    return False


def features(text: str) -> dict[str, float]:
    urls = _URL_RE.findall(text)
    domains = [_domain_of(u) for u in urls]
    suspicious_tld = any(_tld_of(d) in _SUSPICIOUS_TLDS for d in domains)
    lookalike = any(_is_lookalike(d) for d in domains)
    max_entropy = max((_shannon_entropy(d.split(".")[0]) for d in domains), default=0.0)

    emails = _EMAIL_RE.findall(text)
    free_email = any(e.split("@", 1)[1].lower() in _FREE_EMAIL_DOMAINS for e in emails)

    text_low = text.lower()
    has_telegram = bool(re.search(r"\btelegram\b|\bt\.me/", text_low))
    has_whatsapp = bool(re.search(r"\bwhatsapp\b|\bwa\.me/", text_low))

    return {
        "num_urls": float(len(urls)),
        "url_suspicious_tld": 1.0 if suspicious_tld else 0.0,
        "url_max_entropy": float(max_entropy),
        "url_brand_lookalike": 1.0 if lookalike else 0.0,
        "contact_free_email": 1.0 if free_email else 0.0,
        "contact_telegram": 1.0 if has_telegram else 0.0,
        "contact_whatsapp": 1.0 if has_whatsapp else 0.0,
    }
