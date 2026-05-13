"""Command-line entrypoint for runbook-rag."""

from __future__ import annotations

import click

from runbook_rag.naive import ask as _ask
from runbook_rag.naive import index_folder


@click.group()
def main() -> None:
    """The smallest useful RAG over a folder of Markdown runbooks."""


@main.command()
@click.argument("folder", type=click.Path(exists=True, file_okay=False))
@click.option("--db", default="runbooks.db", show_default=True, help="SQLite DB path.")
def index(folder: str, db: str) -> None:
    """Index every Markdown file under FOLDER."""
    count = index_folder(folder, db)
    click.echo(f"Indexed {count} file(s) into {db}")


@main.command()
@click.argument("question")
@click.option("--db", default="runbooks.db", show_default=True, help="SQLite DB path.")
def ask(question: str, db: str) -> None:
    """Ask QUESTION over the indexed runbooks."""
    answer, sources = _ask(question, db)
    click.echo(answer)
    if sources:
        click.echo("")
        click.echo("Sources:")
        for s in sources:
            click.echo(f"  - {s}")
