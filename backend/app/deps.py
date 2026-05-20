"""Dependency factories used by FastAPI routers."""
from __future__ import annotations

from fastapi import Depends  # noqa: F401  (kept for downstream importers)

from .clients import (
    AnalyticsClient,
    AuthClient,
    DbClient,
    FilesystemClient,
    MemoryClient,
    MlEngineClient,
    NotificationClient,
    WebSearchClient,
)


def get_auth_client() -> AuthClient:
    return AuthClient()


def get_db_client() -> DbClient:
    return DbClient()


def get_ml_client() -> MlEngineClient:
    return MlEngineClient()


def get_memory_client() -> MemoryClient:
    return MemoryClient()


def get_filesystem_client() -> FilesystemClient:
    return FilesystemClient()


def get_websearch_client() -> WebSearchClient:
    return WebSearchClient()


def get_notification_client() -> NotificationClient:
    return NotificationClient()


def get_analytics_client() -> AnalyticsClient:
    return AnalyticsClient()
