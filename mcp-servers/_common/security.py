"""Shared service-to-service authentication helpers."""
from __future__ import annotations

import os
from typing import Annotated

from fastapi import Header, HTTPException, status


SERVICE_TOKEN_ENV = "SERVICE_TOKEN"
SERVICE_TOKEN_HEADER = "X-Service-Token"


def require_service_token(
    x_service_token: Annotated[str | None, Header(alias=SERVICE_TOKEN_HEADER)] = None,
) -> None:
    expected = os.environ.get(SERVICE_TOKEN_ENV)
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SERVICE_TOKEN not configured",
        )
    if not x_service_token or x_service_token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid service token",
        )
