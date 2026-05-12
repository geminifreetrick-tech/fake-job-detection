from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_session
from .models import User
from .schemas import LoginRequest, RefreshRequest, SignupRequest, TokenPair, UserOut
from .security import create_token, decode_token, hash_password, verify_password

router = APIRouter()


async def _get_user_by_email(session: AsyncSession, email: str) -> User | None:
    res = await session.execute(select(User).where(User.email == email.lower()))
    return res.scalar_one_or_none()


def _issue_tokens(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_token(user.id, user.role, "access"),
        refresh_token=create_token(user.id, user.role, "refresh"),
    )


@router.post("/signup", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def signup(
    body: SignupRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenPair:
    user = User(email=body.email.lower(), password_hash=hash_password(body.password))
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="email already registered")
    await session.refresh(user)
    return _issue_tokens(user)


@router.post("/login", response_model=TokenPair)
async def login(
    body: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenPair:
    user = await _get_user_by_email(session, body.email)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")
    return _issue_tokens(user)


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    body: RefreshRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenPair:
    try:
        payload = decode_token(body.refresh_token, expected_kind="refresh")
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail=f"invalid refresh token: {exc}")
    res = await session.execute(select(User).where(User.id == payload["sub"]))
    user = res.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="user not found")
    return _issue_tokens(user)


def _bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    return authorization.split(" ", 1)[1].strip()


@router.get("/me", response_model=UserOut)
async def me(
    session: Annotated[AsyncSession, Depends(get_session)],
    authorization: Annotated[str | None, Header()] = None,
) -> UserOut:
    token = _bearer(authorization)
    try:
        payload = decode_token(token, expected_kind="access")
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail=f"invalid access token: {exc}")
    res = await session.execute(select(User).where(User.id == payload["sub"]))
    user = res.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="user not found")
    return UserOut(id=user.id, email=user.email, role=user.role, created_at=user.created_at)


@router.post("/verify")
async def verify(
    session: Annotated[AsyncSession, Depends(get_session)],
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    """Internal helper used by the gateway to validate an access token in one hop."""
    token = _bearer(authorization)
    try:
        payload = decode_token(token, expected_kind="access")
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail=f"invalid access token: {exc}")
    res = await session.execute(select(User).where(User.id == payload["sub"]))
    user = res.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="user not found")
    return {"user_id": user.id, "email": user.email, "role": user.role}
