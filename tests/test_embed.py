"""Embed guard tests — the empty-text check runs before any API call."""

from __future__ import annotations

import pytest

from runbook_rag.embed import embed


def test_embed_rejects_empty_string():
    with pytest.raises(ValueError, match="empty text"):
        embed("")


def test_embed_rejects_whitespace_only():
    with pytest.raises(ValueError, match="empty text"):
        embed("   \n\t ")
