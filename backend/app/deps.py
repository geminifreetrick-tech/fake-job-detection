"""Dependency factories used by FastAPI routers."""
from __future__ import annotations

from .clients import AuthClient, DbClient, MemoryClient, MlEngineClient


def get_auth_client() -> AuthClient:
    return AuthClient()


def get_db_client() -> DbClient:
    return DbClient()


def get_ml_client() -> MlEngineClient:
    return MlEngineClient()


def get_memory_client() -> MemoryClient:
    return MemoryClient()
