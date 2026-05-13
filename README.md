# runbook-rag-starter

> The smallest useful RAG, in about 40 lines of Python — a folder of Markdown, sqlite-vec, and a CLI. Companion to *[What is Retrieval-Augmented Generation?](https://cloudandsre.com/blog/what-is-retrieval-augmented-generation/)* on cloudandsre.com.

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

This repo is deliberately mediocre. The naïve implementation in [`runbook_rag/naive.py`](runbook_rag/naive.py) is the smallest working RAG that returns a useful answer over your runbooks. The point is to read it, run it, see *exactly* where it falls down, and then graduate to chunking, hybrid retrieval, and reranking — each of which is a separate concern, not a separate library.

## What you get

- A CLI: `runbook-rag index <folder>` and `runbook-rag ask "..."`.
- A single SQLite file (`runbooks.db`) holding the embedded chunks via [`sqlite-vec`](https://github.com/asg017/sqlite-vec) — no Postgres, no separate vector service, no Docker.
- A handful of example runbook Markdown files under [`examples/runbooks/`](examples/runbooks/) so you can try it without your own data.

## Install

Requires Python 3.11+, an Anthropic API key, and an OpenAI key (used only for the embedding model — swap to any other in `runbook_rag/embed.py` if you'd rather).

```bash
git clone https://github.com/ajinb/runbook-rag-starter
cd runbook-rag-starter
python -m venv .venv && source .venv/bin/activate
pip install -e .
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
```

## Use

```bash
# Index a folder of Markdown files
runbook-rag index examples/runbooks/

# Ask a question — top-k chunks are retrieved and stuffed into the prompt
runbook-rag ask "what do we do when checkout-svc latency spikes?"
```

The answer includes the source files it used, so you can verify the model didn't make anything up.

## What's deliberately missing

Every one of these is in the blog post for a reason — the naïve version skipping them is the *lesson*:

- **Chunking.** Each file is one chunk. A 50-page runbook is one vector. Obvious failure mode.
- **Hybrid retrieval.** No BM25 keyword fallback. Exact-match queries like ticket IDs or hostnames will miss.
- **Reranking.** Top-k is returned in pure cosine order; no cross-encoder second pass.
- **Empty-retrieval handling.** If nothing relevant comes back, the model still gets the prompt and may fabricate. Inspect the cited sources every time.
- **Freshness signal.** No "last indexed" tag on the response.
- **Embedding-version tracking.** Re-embedding on model swap is a manual `index --rebuild`.

When any of these starts costing you in practice, that's the order to fix them.

## Layout

```
runbook_rag/
├── cli.py        # entrypoint: index + ask
├── embed.py      # embedding model (swap freely)
├── naive.py      # the 40-line core
└── store.py      # sqlite-vec read/write
examples/
└── runbooks/     # 3 sample Markdown files
```

## License

[Apache-2.0](LICENSE).
