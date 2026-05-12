from __future__ import annotations

from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from ..clients import AuthClient
from ..deps import get_auth_client

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupBody(BaseModel):
    email: EmailStr
    password: str


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class RefreshBody(BaseModel):
    refresh_token: str


def _forward(exc: httpx.HTTPStatusError):
    try:
        detail = exc.response.json().get("detail", exc.response.text)
    except Exception:
        detail = exc.response.text
    raise HTTPException(exc.response.status_code, detail)


@router.post("/signup", status_code=201)
async def signup(
    body: SignupBody,
    client: Annotated[AuthClient, Depends(get_auth_client)],
):
    try:
        return await client.signup(body.email, body.password)
    except httpx.HTTPStatusError as e:
        _forward(e)
    finally:
        await client.aclose()


@router.post("/login")
async def login(
    body: LoginBody,
    client: Annotated[AuthClient, Depends(get_auth_client)],
):
    try:
        return await client.login(body.email, body.password)
    except httpx.HTTPStatusError as e:
        _forward(e)
    finally:
        await client.aclose()


@router.post("/refresh")
async def refresh(
    body: RefreshBody,
    client: Annotated[AuthClient, Depends(get_auth_client)],
):
    try:
        return await client.refresh(body.refresh_token)
    except httpx.HTTPStatusError as e:
        _forward(e)
    finally:
        await client.aclose()
