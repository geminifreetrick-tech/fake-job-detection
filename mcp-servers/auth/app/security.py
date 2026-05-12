from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt
from passlib.context import CryptContext

from .config import settings

_pwd = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_token(sub: str, role: str, kind: Literal["access", "refresh"]) -> str:
    ttl = (
        timedelta(minutes=settings.jwt_access_ttl_min)
        if kind == "access"
        else timedelta(days=settings.jwt_refresh_ttl_days)
    )
    now = _now()
    payload = {
        "sub": sub,
        "role": role,
        "kind": kind,
        "iat": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_kind: str | None = None) -> dict:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    if expected_kind and payload.get("kind") != expected_kind:
        raise jwt.InvalidTokenError(f"expected {expected_kind} token")
    return payload
