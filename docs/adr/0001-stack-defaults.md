# 0001. Stack defaults

- Status: Accepted
- Date: 2026-09-18
- Related: NFR-MNT-01, FR-RET-01, FR-ING-01

## Context

The spec fixes Python, git, SQLite and Parquet. Three choices remain open and are needed in M0 to M2.

## Options

1. Type checking: mypy strict with the Pydantic plugin (default), or pyright as the only checker.
2. Keyword search: SQLite FTS5 with built-in BM25 (default), or a Python BM25 library.
3. DOCX and PDF parsing: Docling run locally (default), or per-format libraries.

## Decision

Tom took all three defaults on 2026-09-18.

1. **mypy strict with the Pydantic plugin.** Configured in `pyproject.toml` (`[tool.mypy]`,
   `strict = true`, `plugins = ["pydantic.mypy"]`) and run in CI as `uv run mypy src`. Pyright
   stays available through the `pyright-lsp` plugin for in-editor feedback, but mypy is the only
   checker that gates a commit or a build: two gating checkers means two sets of ignore comments.
2. **SQLite FTS5 with built-in BM25.** No dependency: FTS5 and `bm25()` are compiled into the
   CPython `sqlite3` module (verified against SQLite 3.45.1). This is the keyword half of the
   hybrid retrieval in FR-RET-01; embeddings are the other half and the two fuse by reciprocal
   rank at `rrf_k` from the domain config.
3. **Docling, run locally.** Kept in the `office` optional extra, not the base dependencies,
   because it pulls in torch and easyocr. Install it when M2 needs DOCX and PDF ingestion
   (FR-ING-01).

Record any later change here rather than editing the decision above.

## Consequences

- No hosted services for type checking, search or parsing. `uv.lock` pins everything.
- A SQLite build without FTS5 breaks retrieval. S0 configuration validation should check for FTS5
  at startup and fail with a named field rather than at first query (FR-CFG-01).
- `uv sync` alone does not give a working M2 ingest. The `office` extra is a separate, large
  install, so document it in the M2 setup step rather than assuming it.
- FTS5 ranks with Okapi BM25 over its own tokeniser. Stemming and stop words are the tokeniser's
  behaviour, not ours to tune, so retrieval evaluation in M3 measures the fused result, not FTS5
  in isolation.
