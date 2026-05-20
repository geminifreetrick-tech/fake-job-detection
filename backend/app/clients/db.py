from __future__ import annotations

from typing import Any

from ..core.config import settings
from .base import ServiceClient


class DbClient(ServiceClient):
    def __init__(self) -> None:
        super().__init__(settings.db_mcp_url)

    # ---- Jobs / predictions
    async def create_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.post_json("/jobs", json=payload)

    async def create_prediction(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.post_json("/predictions", json=payload)

    async def list_user_jobs(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        return await self.get_json(f"/users/{user_id}/jobs", params={"limit": limit})

    # ---- Scam reports
    async def create_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.post_json("/reports", json=payload)

    async def list_reports(self, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        params = {"limit": limit}
        if status:
            params["status"] = status
        return await self.get_json("/reports", params=params)

    async def list_user_reports(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        return await self.get_json(f"/users/{user_id}/reports", params={"limit": limit})

    async def update_report(self, report_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        r = await self.http.patch(f"/reports/{report_id}", json=payload)
        r.raise_for_status()
        return r.json()

    # ---- Articles
    async def list_articles(self, tag: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if tag:
            params["tag"] = tag
        return await self.get_json("/articles", params=params)

    async def get_article(self, slug: str) -> dict[str, Any]:
        return await self.get_json(f"/articles/{slug}")

    # ---- Quizzes
    async def list_quizzes(self) -> list[dict[str, Any]]:
        return await self.get_json("/quizzes")

    async def get_quiz(self, slug: str) -> dict[str, Any]:
        return await self.get_json(f"/quizzes/{slug}")

    async def submit_quiz_attempt(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.post_json("/quiz-attempts", json=payload)

    async def list_user_quiz_attempts(self, user_id: str) -> list[dict[str, Any]]:
        return await self.get_json(f"/users/{user_id}/quiz-attempts")

    # ---- Company verification cache
    async def get_company_verification(
        self, name: str, domain: str | None = None
    ) -> dict[str, Any] | None:
        params: dict[str, Any] = {"name": name}
        if domain:
            params["domain"] = domain
        return await self.get_json("/company-verifications", params=params)

    async def save_company_verification(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.post_json("/company-verifications", json=payload)

    # ---- Notifications
    async def list_user_notifications(
        self, user_id: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        return await self.get_json(
            f"/users/{user_id}/notifications", params={"limit": limit}
        )

    # ---- Analytics events
    async def record_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.post_json("/analytics-events", json=payload)
