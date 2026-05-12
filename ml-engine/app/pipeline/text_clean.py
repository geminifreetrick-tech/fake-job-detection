"""Lightweight text normalization shared by all extractors."""
from __future__ import annotations

import re
import unicodedata


_WHITESPACE_RE = re.compile(r"\s+")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_NON_PRINTABLE_RE = re.compile(r"[^\x09\x0a\x0d\x20-\x7e\u00a0-\uffff]")


def clean(text: str) -> str:
    if not text:
        return ""
    text = _HTML_TAG_RE.sub(" ", text)
    text = unicodedata.normalize("NFKC", text)
    text = _NON_PRINTABLE_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text


def word_tokens(text: str) -> list[str]:
    """Cheap whitespace + punctuation tokenizer; deliberately avoids spaCy dependency."""
    return re.findall(r"[A-Za-z][A-Za-z'’\-]*", text)
