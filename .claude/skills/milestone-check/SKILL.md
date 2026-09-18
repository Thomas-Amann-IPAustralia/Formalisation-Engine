---
name: milestone-check
description: Check a milestone's exit condition and requirement coverage and report ready or not ready without changing anything. Use when Tom asks whether a milestone (M0 to M6) is done.
argument-hint: "<M0..M6>"
disable-model-invocation: true
context: fork
agent: test-runner
background: false
allowed-tools: Bash(python3 scripts/spec_tools.py *) Bash(uv run pytest *) Bash(uv run mypy *) Bash(uv run ruff *)
---

Check milestone $ARGUMENTS. Edit nothing.

1. Read its row in `docs/spec/sections/08-delivery-plan.md`.
2. `uv run pytest -q --tb=line`; `python3 scripts/spec_tools.py coverage --milestone $ARGUMENTS`;
   `uv run mypy src`; `uv run ruff check .`.

Report exactly:

```
Milestone $ARGUMENTS: READY | NOT READY
Exit: <quoted> -> MET | NOT MET | NEEDS TOM (<why>)
Tests: <passed> passed, <failed> failed, <xfailed> xfailed
Must-have: <n> passing, <n> failing, <n> without tests, <n> needing I/D/A evidence
Failing: <ID: node id> (max 10)
Without tests: <IDs>
Types: clean | <n> errors. Lint: clean | <n> problems.
```

Anything needing a person (sign-off, a go or no-go) is NEEDS TOM, never MET.
