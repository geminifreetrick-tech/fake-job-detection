from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, status

from .config import settings


class CurrentUser:
    def __init__(self, user_id: str, email: str | None, role: str):
        self.user_id = user_id
        self.email = email
        self.role = role

    def __repr__(self) -> str:  # pragma: no cover - debug only
        return f"CurrentUser(id={self.user_id!r}, role={self.role!r})"


def _decode_local(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> CurrentUser:
    """Validate the access token using the shared JWT secret.

    We deliberately decode locally for speed; for revocation we would call
    auth-mcp `/verify` instead. The secret is shared with auth-mcp via `.env`.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = _decode_local(token)
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"invalid token: {exc}")
    if payload.get("kind") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not an access token")
    return CurrentUser(
        user_id=str(payload["sub"]),
        email=payload.get("email"),
        role=str(payload.get("role", "user")),
    )


def require_admin(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "admin role required")
    return user
