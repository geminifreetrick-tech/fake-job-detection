"""Thin wrapper around the Chroma HTTP client.

We use Chroma's built-in default embedding function (ONNX MiniLM, no API key)
which loads the model lazily on first use.
"""
from __future__ import annotations

import logging
from typing import Any

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction
from chromadb.config import Settings as ChromaSettings

from .config import settings

logger = logging.getLogger("memory-mcp")

_EMBED_FN: EmbeddingFunction[Documents] | None = None


def _embed_fn() -> EmbeddingFunction[Documents]:
    global _EMBED_FN
    if _EMBED_FN is None:
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

        _EMBED_FN = DefaultEmbeddingFunction()  # type: ignore[assignment]
    return _EMBED_FN


_client: chromadb.api.ClientAPI | None = None


def _make_client() -> chromadb.api.ClientAPI:
    return chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def get_client() -> chromadb.api.ClientAPI:
    global _client
    if _client is None:
        _client = _make_client()
    return _client


def set_client(client: chromadb.api.ClientAPI) -> None:
    """Override the client (used by tests to point at an in-memory Chroma)."""
    global _client
    _client = client


def get_or_create(name: str):
    return get_client().get_or_create_collection(
        name=name, embedding_function=_embed_fn()
    )


def bootstrap() -> None:
    """Ensure required collections exist."""
    for name in (
        settings.collection_user_context,
        settings.collection_known_scams,
        settings.collection_articles,
    ):
        try:
            get_or_create(name)
        except Exception as exc:  # pragma: no cover - chroma transient errors
            logger.warning("could not bootstrap collection %s: %s", name, exc)


def seed_known_scams(items: list[dict[str, Any]]) -> int:
    """Seed `known_scams` with a list of dicts that include `id` and `document`."""
    coll = get_or_create(settings.collection_known_scams)
    ids = [str(i["id"]) for i in items]
    docs = [i["document"] for i in items]
    metas = [
        {k: v for k, v in i.items() if k not in ("id", "document")} or {"seeded": True}
        for i in items
    ]
    coll.upsert(ids=ids, documents=docs, metadatas=metas)
    return len(ids)
