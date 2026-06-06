"""sqlite-vec store: one row per indexed document."""

from __future__ import annotations

import sqlite3
import struct
from collections.abc import Iterable

import sqlite_vec

from runbook_rag.embed import EMBED_DIM


def _vec_to_blob(v: Iterable[float]) -> bytes:
    return struct.pack(f"{EMBED_DIM}f", *v)


def open_db(path: str) -> sqlite3.Connection:
    """Open (or create) the database and ensure the schema exists."""
    conn = sqlite3.connect(path)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    conn.execute("CREATE TABLE IF NOT EXISTS docs (id INTEGER PRIMARY KEY, path TEXT, body TEXT)")
    conn.execute(
        f"CREATE VIRTUAL TABLE IF NOT EXISTS doc_vec USING vec0(id INTEGER PRIMARY KEY, "
        f"embedding FLOAT[{EMBED_DIM}])"
    )
    return conn


def upsert(conn: sqlite3.Connection, path: str, body: str, vector: list[float]) -> None:
    cur = conn.execute("SELECT id FROM docs WHERE path = ?", (path,))
    row = cur.fetchone()
    if row is None:
        cur = conn.execute("INSERT INTO docs (path, body) VALUES (?, ?)", (path, body))
        doc_id = cur.lastrowid
        conn.execute(
            "INSERT INTO doc_vec (id, embedding) VALUES (?, ?)",
            (doc_id, _vec_to_blob(vector)),
        )
    else:
        doc_id = row[0]
        conn.execute("UPDATE docs SET body = ? WHERE id = ?", (body, doc_id))
        conn.execute(
            "UPDATE doc_vec SET embedding = ? WHERE id = ?",
            (_vec_to_blob(vector), doc_id),
        )
    conn.commit()


def search(
    conn: sqlite3.Connection, query_vector: list[float], top_k: int = 3
) -> list[tuple[str, str, float]]:
    """Return the top_k nearest documents as (path, body, distance) tuples."""
    # sqlite-vec KNN queries require the result count as a `k = ?` constraint;
    # a bound `LIMIT ?` is not recognised by the vec0 query planner.
    rows = conn.execute(
        """
        SELECT docs.path, docs.body, doc_vec.distance
        FROM doc_vec
        JOIN docs ON docs.id = doc_vec.id
        WHERE doc_vec.embedding MATCH ? AND k = ?
        ORDER BY doc_vec.distance
        """,
        (_vec_to_blob(query_vector), top_k),
    ).fetchall()
    return [(p, b, d) for (p, b, d) in rows]
