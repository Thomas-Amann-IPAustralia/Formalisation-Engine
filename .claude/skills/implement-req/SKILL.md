---
name: implement-req
description: Implement one or more spec requirements test-first, audit against the spec, and commit. Use when Tom asks to implement a requirement ID such as FR-EXT-02 or INV-01.
argument-hint: "<ID> [ID ...]"
disable-model-invocation: true
allowed-tools: Bash(python3 scripts/spec_tools.py *) Bash(uv run pytest *) Bash(uv run ruff *) Bash(uv run mypy *) Bash(git status *) Bash(git diff *) Bash(git add *) Bash(git commit *)
---

Implement $ARGUMENTS.

1. `python3 scripts/spec_tools.py show $ARGUMENTS --refs`. Read only the sections and ADRs it points to.
2. If a requirement is ambiguous, conflicts with another, or depends on an open OQ or a Proposed
   ADR, stop and ask Tom what needs deciding.
3. State the plan in a few lines: what, where, and how each ID is verified (T needs a test).
4. Write failing tests marked `@pytest.mark.req("<ID>")` (and `fast` if quick). Assert the stated
   behaviour including the failure path. Confirm they fail for the right reason.
5. Implement the smallest change that passes. Do not implement neighbouring requirements.
6. `uv run pytest -x -q --tb=short`, `uv run ruff check .`, `uv run mypy src` until clean.
7. Ask the spec-auditor subagent to review the diff against $ARGUMENTS; fix every FAIL and PARTIAL.
8. Commit with the IDs first. Push to the working branch; never to `main` (ADR-0004).
9. Report in five lines: IDs done, tests added, deferred, questions for Tom.
