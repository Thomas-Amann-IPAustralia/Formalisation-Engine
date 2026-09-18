# Formalisation Engine

Source documents for a domain go in one end. Out the other end: a **tool package** (rules as code a
specialist agent calls), the **IR** it was compiled from (every rule traceable to its passage;
conflicts, gaps, confidence and decisions as data), and a **retrieval index** for the agent's squire.
The pipeline runs without a person; review is optional and can override anything. LLMs interpret
and judge; deterministic code checks, stores, compiles and runs. Outputs are best-effort with status
on every claim. Pilot: Style Manual and WCAG 2.2 for the UX-Designer agent. This repo ends at the
package; agents are built elsewhere. Current state: docs/STATUS.md (loaded at session start).

## Commands

- Fast tests: `uv run pytest -m fast -x --tb=short`. All (replay only): `uv run pytest -x --tb=short`
- Lint and format: `uv run ruff check --fix . && uv run ruff format .`. Types: `uv run mypy src`
- CLI: `uv run engine --help`
- Requirement text: `python3 scripts/spec_tools.py show FR-TOO-02 INV-10` (add `--refs`)
- Area: `python3 scripts/spec_tools.py list --area JDG`. Coverage: `... coverage --milestone M1`

Keep output small (`-q`, `-x`, `--tb=short`). Full-suite and gate runs go to the test-runner subagent.

## Where things are

- `spec-src/`: the spec. Do not read it; use `docs/spec/requirements.jsonl` and `docs/spec/sections/`.
- `docs/milestones.json`, `docs/adr/`, `docs/STATUS.md`.
- `config/domains/<domain>/`: config, authority profile, decision policies, cue lists, and the
  Engine-proposed skeleton, fact schema and providers.
- `prompts/` versioned templates; `gold/`; `snapshots/`; `schema/` generated; `tool/` built packages.
- `src/engine/`: `models/`, `stores/`, `llm/`, `retrieval/`, `stages/s0_configure` to `s9_evaluate`,
  `policy/`, `evaluator/`, `judgement/`, `probes/`, `validate/`, `compile/`, `tool/`, `review/`, `cli.py`
- `tests/`: `unit/`, `property/`, `probes/`, `seeded_defects/`, `gates/`, `fixtures/`. `var/`: outputs.

## Principles (spec 1.4)

DP-01 deterministic where possible, inference where required; human confirmation never blocks.
DP-02 propositions with verified spans are the unit of truth. DP-03 the IR is canonical.
DP-04 loud, not fatal: record the failed record, continue the run. DP-05 status travels with every
claim. DP-06 classify, don't generate. DP-07 stages with contracts; loops with budgets.
DP-08 judgement is automated at run time, recorded, overridable. DP-09 everything versioned.
DP-10 conflicts resolve by declared policy, logged; no policy means alternatives unresolved.
DP-11 the tool contract comes first and is shared.

## Invariants (spec Appendix D; a violation blocks the record, never the run)

INV-01 verified span on every proposition. INV-02 source proposition on every node, rule, procedure
and conflict; target and search record on every gap. INV-03 every decision has `unable_to_determine`.
INV-04 no rule from a non-compilable force or blocked proposition. INV-05 every rule condition has a
fact type with a provider. INV-06 one backbone in backbone-led, none in framework-led; every document
has an authority level and licence class. INV-07 defeats acyclic; alternatives never defeat each
other. INV-08 judgements decided only by their procedure or an override. INV-09 probe result is a
value with artefact reference or UNKNOWN with a declared reason. INV-10 every tool assertion cited.
INV-11 no stored text for `reference` or `excluded` sources. INV-12 every policy invocation,
judgement and override logged with inputs; overrides beat automation on unchanged records.

## Hard rules

- Never call a live LLM API; everything runs in replay mode. Live and record runs are Tom's.
- Never edit `spec-src/`, `docs/spec/`, `gold/`, `snapshots/`, `schema/`, `tool/`,
  `tests/fixtures/llm_cache/`, `.claude/settings.json`, `.claude/hooks/`. Describe the change.
- Domain files marked `origin: edited` are only re-proposed as a diff.
- Probes compute or abstain; estimation belongs to the `inferred` provider and is tagged.
- The evaluator is pure and never fills a fact. Every assertion is cited. Overrides always win.
- The contract shape (Appendix E) is fixed across domains. Add content, never change shape.
- All LLM calls through `engine.llm`; prompts in `prompts/`; models defined once in `engine.models`;
  stages talk only through `engine.stores`; no silent skips.
- No new dependencies without asking; `uv add`, never pip. Ask before changing `docs/milestones.json`
  or an Accepted ADR. If the spec is silent or contradictory, ask; do not invent requirements.

## Method

- `/implement-req <ID ...>` per requirement group; test first with `@pytest.mark.req`; quick tests
  also `@pytest.mark.fast`; spec-auditor checks the diff; commit with IDs first; never push.
- `/wrap-up` ends a session. Open points go under "Questions for Tom" in docs/STATUS.md.
- Python 3.12, mypy strict, ruff, Pydantic v2. ISO 8601, UTF-8, atomic writes, JSON-lines logs with
  run, stage and record IDs. Errors name the record, the stage and what to do. Australian English.
