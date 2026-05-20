"""Tiny content-addressed file store. SHA-256 hex → fan-out path."""
from __future__ import annotations

import hashlib
from pathlib import Path

from .config import settings

_ALLOWED_PREFIXES = {"application/pdf", "image/", "text/"}


def is_allowed_mime(content_type: str | None) -> bool:
    if not content_type:
        return False
    ct = content_type.lower()
    return any(ct.startswith(p) for p in _ALLOWED_PREFIXES)


def _path_for_sha(sha: str, root: Path) -> Path:
    return root / sha[:2] / sha[2:4] / sha


def save_bytes(data: bytes, root: Path) -> tuple[str, Path]:
    sha = hashlib.sha256(data).hexdigest()
    p = _path_for_sha(sha, root)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_bytes(data)
    return sha, p


def read_bytes(sha: str, root: Path) -> bytes | None:
    p = _path_for_sha(sha, root)
    if not p.exists():
        return None
    return p.read_bytes()


def upload_root() -> Path:
    return Path(settings.upload_dir)


def reports_root() -> Path:
    return Path(settings.reports_dir)
