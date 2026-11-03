"""naive.ask() control-flow tests — embedding stubbed so no API is called."""

from __future__ import annotations

import sqlite3

import pytest

from runbook_rag import naive
from runbook_rag.embed import EMBED_DIM


@pytest.mark.skipif(
    not hasattr(sqlite3.connect(":memory:"), "enable_load_extension"),
    reason="this Python's sqlite3 cannot load extensions (python.org macOS build)",
)
def test_ask_on_empty_index_returns_guidance(tmp_path, monkeypatch):
    # Stub embed so ask() never reaches the OpenAI API; the DB is empty so
    # search returns no hits and ask() should short-circuit with guidance.
    monkeypatch.setattr(naive, "embed", lambda _text: [0.0] * EMBED_DIM)

    answer, sources = naive.ask("how do I fail over the db?", str(tmp_path / "empty.db"))

    assert sources == []
    assert "index" in answer.lower()
