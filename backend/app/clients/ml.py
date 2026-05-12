from __future__ import annotations

from typing import Any

from ..core.config import settings
from .base import ServiceClient


class MlEngineClient(ServiceClient):
    def __init__(self) -> None:
        super().__init__(settings.ml_engine_url, timeout=60.0)

    async def predict_text(self, text: str) -> dict[str, Any]:
        return await self.post_json("/predict", json={"text": text})

    async def predict_file(self, filename: str, content_type: str, data: bytes) -> dict[str, Any]:
        files = {"file": (filename, data, content_type or "application/octet-stream")}
        return await self.post_json("/predict/file", files=files)

    async def model_info(self) -> dict[str, Any]:
        return await self.get_json("/model/info")
