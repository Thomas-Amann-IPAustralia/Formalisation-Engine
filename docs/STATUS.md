# Status

Milestone: M0 Contract and models
Updated: 2026-09-18

## Done recently
- Starter kit reviewed against the spec and made runnable: `uv.lock` committed, the five hook
  scripts committed executable (they were mode 644 and silently doing nothing), `.pytest_cache/`
  untracked, `.env.example` added, `README-STARTER.md` became `README.md`.
- ADR-0001 Accepted: mypy strict with the Pydantic plugin, SQLite FTS5 with built-in BM25
  (confirmed present in the stdlib build), Docling run locally in the `office` extra.
- ADR-0003 Accepted: `gemini-2.5-flash` for every inference role, `nomic-embed-text-v1.5`
  self-hosted for embeddings. `google-genai` replaces `anthropic`; model IDs pinned in
  `domain_config.yaml`; `prompt-authoring` and the S8 rule retargeted.
- ADR-0002 rewritten in plain words; the three questions are on their own in the file.

## In progress
- Nothing in code. M0 is the contract, the models and the gold slice.

## Next up
- Answer ADR-0002 (first topic, tie-breaking rule, review thresholds), then start M1.
- IR models with invariant checks (INV-01 to INV-12); JSON Schema export.
- Decision log schema and policy format.
- Gold slice: propositions, rules, a judgement point, an alternatives set, fact sets, question set.
- S0 config validation should check SQLite has FTS5 at startup, not at first query (ADR-0001).

## Blocked or failing
- Nothing failing. M1 is blocked on ADR-0002.

## Questions for Tom
- ADR-0002, the three questions in `docs/adr/0002-pilot-choices.md`.
- Spec section 2 describes the stack as "Anthropic API behind a provider abstraction". ADR-0003
  changed that to Gemini. NFR-PRT-01 names no vendor, so nothing normative is contradicted, but
  the sentence in `spec-src/` is now stale and only you can edit it.
- The base install carries `spacy`, `fastapi`, `uvicorn` and `z3-solver`, none of which is used
  before M3. Worth moving to extras? It is 460 MB and a large audit surface for M0 to M2.
- The Bash guard does not cover shell writes. `protect-paths.sh` only runs on `Edit`, `Write` and
  `NotebookEdit`, so `sed -i docs/spec/...` or `cat > gold/...` is unguarded, as is `cat
  spec-src/...` against the `Read` deny rule. Adding a protected-path check to `guard-bash.sh`
  would close it; the hooks are yours to edit.
- `guard-bash.sh` matches its trigger strings anywhere in a command, so writing documentation that
  merely mentions the live-run flag is blocked. It hit this session twice. Matching only an actual
  assignment or export would fix it.
- HTML parser for the first probe (ADR-0001 default: a standard HTML parser; Docling for documents).
- Judgement cost caps are still TODO in `domain_config.yaml` (OQ-03); they need an M5 measurement.
