# Formalisation Engine: starter kit

Copy into the repo root. Then: `uv sync`, commit `uv.lock`, `chmod +x .claude/hooks/*.sh`, copy
`.env.example` to `.env` with `ENGINE_ANTHROPIC_API_KEY` (keep `ANTHROPIC_API_KEY` out of the shell
you run Claude Code from), start Claude Code, check `/hooks`, `/skills`, `/permissions`.
Prerequisites: git, uv, Python 3.12, `jq`, pyright on PATH (for the pyright-lsp plugin).

| Path | Purpose |
|---|---|
| `CLAUDE.md` | Brief (74 lines), loaded every session |
| `.claude/settings.json`, `.claude/hooks/` | Permissions, replay mode, and 5 hooks: status at start, Bash guard, protected paths, lint on edit, fast checks on stop |
| `.claude/rules/` | 5 path-scoped rule files: models, stages, compile, tool, tests |
| `.claude/skills/` | `/implement-req`, `/milestone-check`, `/wrap-up`, `/new-domain`; `prompt-authoring` loads by path |
| `.claude/agents/` | `test-runner`, `spec-auditor` |
| `spec-src/` | The spec (read access denied to Claude; it uses the generated files) |
| `docs/spec/` | Generated index (123 records) and sections; `scripts/spec_tools.py build|show|list|coverage` |
| `docs/milestones.json`, `docs/STATUS.md`, `docs/adr/` | Milestone map, current state, 3 open decisions |
| `config/domains/style-manual-wcag/` | Pilot domain: config, authority profile, decision policy, cue lists, seed skeleton, fact schema, providers |
| `tests/` | `conftest.py` records results per requirement; `gates/test_gates.py` has G1 to G12 as strict xfail stubs |
| `pyproject.toml`, `.github/workflows/ci.yml` | Toolchain and CI (lint, types, tests, spec freshness, coverage, audit) |

**Work loop.** `/implement-req <IDs>`, commit, `/wrap-up`; `/milestone-check M1` when a milestone
looks done. Spec changes: edit `spec-src/`, run `python3 scripts/spec_tools.py build`, commit both.
Live or record LLM runs are yours: `ENGINE_ALLOW_LIVE_LLM=1 ... --llm-mode record`.

**M0 order.** Confirm ADR-0002; build the IR models and invariants; draft the gold slice. M1
hand-builds an IR and compiles the package before any pipeline code, so the contract is tested while
cheap to change.

**Known limits.** Hooks, install, lint, types, tests and the spec build are tested. Skills and
agents are drafts (tune with skill-creator after real use). The `engine` CLI is a stub. Config
carries TODOs for source pins, licence notes, models and caps.
