# Formalisation Engine

Source documents for a domain go in one end. Out the other end: a tool package (rules as code that
a specialist agent calls), the IR it was compiled from, and a retrieval index. The pipeline runs
without a person; review is optional and can override anything. Pilot: the Australian Government
Style Manual and WCAG 2.2, for a UX-Designer agent.

The spec is `spec-src/formalisation-engine-spec.md`. Everything else in this repo exists to build
against it. Current state: `docs/STATUS.md`. Working brief for Claude Code: `CLAUDE.md`.

## Setup

Prerequisites: git, [uv](https://docs.astral.sh/uv/), `jq`, and `pyright` on PATH for the
`pyright-lsp` plugin. uv installs Python 3.12 itself.

```sh
uv sync                      # base install, about 170 MB
cp .env.example .env         # then fill in FORMAL_ENGINE_GEMINI
uv run pytest -m fast -x     # should pass
```

Do not export a provider API key into the shell you start Claude Code from. The key belongs in
`.env`, which is gitignored and which Claude Code is denied read access to.

Then start Claude Code and check `/hooks`, `/skills` and `/permissions`. If `/hooks` shows nothing
running, confirm the hook scripts are still executable (`ls -l .claude/hooks/`); they are committed
mode 755 and are inert without it.

Four extras are deliberately not in the base install, all of them large. Add each when its
milestone needs it:

```sh
uv sync --extra nlp                # spacy, for segmentation and vocabulary (M2); 230 MB
uv sync --extra office             # Docling, for DOCX and PDF ingestion (M2); pulls torch
uv sync --extra embeddings-local   # nomic-embed-text-v1.5, for retrieval (M3); pulls torch
uv sync --extra solver             # z3-solver, for rule-overlap checks (M5); 49 MB
```

CI installs the base only, and caches uv's downloads against `uv.lock`. When an M5 test needs Z3,
add `--extra solver` to the install step.

## Layout

| Path | Purpose |
|---|---|
| `CLAUDE.md` | Working brief, loaded every session |
| `.claude/settings.json`, `.claude/hooks/` | Permissions, replay mode, and 5 hooks: status at start, Bash guard, protected paths, lint on edit, fast checks on stop |
| `.claude/rules/` | 5 path-scoped rule files: models, stages, compile, tool, tests |
| `.claude/skills/` | `/implement-req`, `/milestone-check`, `/wrap-up`, `/new-domain`; `prompt-authoring` loads by path |
| `.claude/agents/` | `test-runner`, `spec-auditor` |
| `spec-src/` | The spec. Claude is denied read access; it uses the generated files instead |
| `docs/spec/` | Generated index (123 records) and sections; `scripts/spec_tools.py build\|show\|list\|coverage` |
| `docs/milestones.json`, `docs/STATUS.md`, `docs/adr/` | Milestone map, current state, decisions |
| `config/domains/style-manual-wcag/` | Pilot domain: config, authority profile, decision policy, cue lists, seed skeleton, fact schema, providers |
| `tests/` | `conftest.py` records results per requirement; `gates/test_gates.py` has G1 to G12 as strict xfail stubs |
| `pyproject.toml`, `uv.lock`, `.github/workflows/ci.yml` | Toolchain and CI (lint, types, tests, spec freshness, coverage, audit) |

## Working

`/implement-req <IDs>`, commit, `/wrap-up`; `/milestone-check M1` when a milestone looks done.

Spec changes are Tom's: edit `spec-src/`, run `python3 scripts/spec_tools.py build`, commit both.
CI fails if the generated files are stale.

Live and record LLM runs are Tom's too. Claude runs in replay mode against
`tests/fixtures/llm_cache/`, and the Bash guard blocks it from doing otherwise.

## State of the kit

Verified working: install, lint, types, tests, the spec build, the CLI stub, and all five hooks.

Not yet built: everything in `src/engine/` beyond the CLI stub. M0 is the IR models, the invariant
checks and the gold slice. M1 hand-builds an IR and compiles a package before any pipeline code, so
the tool contract is tested while it is still cheap to change.

All three ADRs are Accepted, so M1 has an objective (page structure and headings), a conflict
policy and triage thresholds. Known gaps, in rough priority order:

- `domain_config.yaml` still has TODOs for source pins, a licence note, cost caps and the
  vocabulary seed.
- Two edits in `docs/adr/0004-no-push-block.md` are waiting on Tom; Claude cannot make them.
- Skills and agents are drafts, tuned after real use rather than before it.
- The secret scan reads the working tree, not git history, so a secret committed and later
  removed would not be caught. See `docs/STATUS.md`.
