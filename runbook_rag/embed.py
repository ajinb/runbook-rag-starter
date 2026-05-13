"""Embedding model — swap freely.

Defaults to OpenAI's small embedding model since it's cheap, fast, and 1536-dim
matches what most starter examples assume. Replace with any other provider by
returning a Python list[float].
"""

from __future__ import annotations

import os

from openai import OpenAI

_EMBED_MODEL = os.environ.get("RUNBOOK_RAG_EMBED_MODEL", "text-embedding-3-small")
EMBED_DIM = 1536  # text-embedding-3-small dimension

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def embed(text: str) -> list[float]:
    """Return the embedding vector for the given text."""
    if not text.strip():
        raise ValueError("cannot embed empty text")
    response = _get_client().embeddings.create(model=_EMBED_MODEL, input=text)
    return response.data[0].embedding
