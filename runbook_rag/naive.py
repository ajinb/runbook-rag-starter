"""The 40-line core: index a folder of Markdown files, answer questions from them.

This is deliberately minimal. See the README for the production knobs this skips.
"""

from __future__ import annotations

import os
from pathlib import Path

from anthropic import Anthropic

from runbook_rag.embed import embed
from runbook_rag.store import open_db, search, upsert

_ANSWER_MODEL = os.environ.get("RUNBOOK_RAG_ANSWER_MODEL", "claude-sonnet-4-6")
_TOP_K = int(os.environ.get("RUNBOOK_RAG_TOP_K", "3"))

_SYSTEM_PROMPT = """You are an SRE assistant answering questions from a curated set of runbooks.

Rules:
- Answer ONLY from the provided runbook excerpts.
- If the excerpts do not contain the answer, say so plainly. Do not guess.
- Quote the source file path for each claim.
"""


def index_folder(folder: str, db_path: str) -> int:
    """Index every Markdown file under `folder`. Returns the number indexed."""
    conn = open_db(db_path)
    count = 0
    for md_path in sorted(Path(folder).rglob("*.md")):
        body = md_path.read_text(encoding="utf-8")
        if not body.strip():
            continue
        upsert(conn, str(md_path), body, embed(body))
        count += 1
    return count


def ask(question: str, db_path: str) -> tuple[str, list[str]]:
    """Answer `question` from the indexed runbooks. Returns (answer, sources)."""
    conn = open_db(db_path)
    hits = search(conn, embed(question), top_k=_TOP_K)
    if not hits:
        return ("No runbooks have been indexed yet. Run `runbook-rag index <folder>` first.", [])

    context = "\n\n---\n\n".join(f"# Source: {p}\n\n{b}" for (p, b, _d) in hits)
    user = f"Question: {question}\n\nRunbook excerpts:\n\n{context}"

    client = Anthropic()
    response = client.messages.create(
        model=_ANSWER_MODEL,
        max_tokens=1024,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user}],
    )
    answer = "".join(block.text for block in response.content if block.type == "text")
    return (answer.strip(), [p for (p, _b, _d) in hits])
