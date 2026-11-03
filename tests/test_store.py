"""Store tests — real sqlite-vec, hand-made vectors, no embedding API."""

from __future__ import annotations

import sqlite3 as _sqlite3

import pytest as _pytest

from runbook_rag.embed import EMBED_DIM
from runbook_rag.store import _vec_to_blob, open_db, search, upsert

needs_extensions = _pytest.mark.skipif(
    not hasattr(_sqlite3.connect(":memory:"), "enable_load_extension"),
    reason="this Python's sqlite3 cannot load extensions (python.org macOS build)",
)


def _vec(*leading: float) -> list[float]:
    """A full EMBED_DIM vector with `leading` values, zero-padded."""
    v = list(leading)
    return v + [0.0] * (EMBED_DIM - len(v))


@needs_extensions
def test_vec_to_blob_is_four_bytes_per_dim():
    blob = _vec_to_blob(_vec(1.0))
    assert len(blob) == EMBED_DIM * 4


@needs_extensions
def test_search_returns_nearest_document_first(tmp_path):
    conn = open_db(str(tmp_path / "rb.db"))
    upsert(conn, "a.md", "alpha runbook", _vec(1.0, 0.0))
    upsert(conn, "b.md", "beta runbook", _vec(0.0, 1.0))

    hits = search(conn, _vec(0.9, 0.1), top_k=2)

    assert [path for (path, _b, _d) in hits] == ["a.md", "b.md"]


@needs_extensions
def test_upsert_updates_body_without_duplicating_row(tmp_path):
    conn = open_db(str(tmp_path / "rb.db"))
    upsert(conn, "a.md", "first version", _vec(1.0))
    upsert(conn, "a.md", "second version", _vec(1.0))

    rows = conn.execute("SELECT body FROM docs WHERE path = 'a.md'").fetchall()
    assert rows == [("second version",)]


def test_python_without_extension_loading_gets_a_clear_error(monkeypatch, tmp_path):
    import sqlite3

    import pytest

    from runbook_rag import store

    class NoExtConn:
        def __getattr__(self, name):
            if name == "enable_load_extension":
                raise AttributeError(name)
            return getattr(sqlite3.connect(":memory:"), name)

    monkeypatch.setattr(store.sqlite3, "connect", lambda _p: NoExtConn())
    with pytest.raises(RuntimeError, match="cannot load extensions"):
        store.open_db(str(tmp_path / "x.db"))
