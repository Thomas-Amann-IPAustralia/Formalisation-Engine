# 0001. Stack defaults

- Status: Proposed
- Date: 2026-09-18
- Related: NFR-MNT-01, FR-RET-01, FR-ING-01

## Context

The spec fixes Python, git, SQLite and Parquet. Three choices remain open and are needed in M0 to M2.

## Options

1. Type checking: mypy strict with the Pydantic plugin (default), or pyright as the only checker.
2. Keyword search: SQLite FTS5 with built-in BM25 (default), or a Python BM25 library.
3. DOCX and PDF parsing: Docling run locally (default), or per-format libraries.

## Decision

Take the defaults unless a milestone shows a problem. Record any change here.

## Consequences

No hosted services. The uv lock file pins everything.
