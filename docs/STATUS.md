# Status

Milestone: M0 Contract and models
Updated: 2026-09-18

## Done recently
- Starter kit reviewed against the spec and made runnable: `uv.lock` committed, the five hook
  scripts committed executable (they were mode 644 and silently doing nothing), `.pytest_cache/`
  untracked, `.env.example` added, `README-STARTER.md` became `README.md`.
- All three ADRs Accepted. 0001: mypy strict with the Pydantic plugin, SQLite FTS5 with built-in
  BM25 (confirmed present in the stdlib build), Docling local in the `office` extra. 0002: page
  structure and headings as the M1 objective, `POL-ux-stricter-wins` as the conflict policy, and
  all five signals required to auto-approve. 0003: `gemini-2.5-flash` for every inference role,
  `nomic-embed-text-v1.5` self-hosted for embeddings.
- `google-genai` replaces `anthropic`; model IDs pinned in `domain_config.yaml`;
  `prompt-authoring` and the S8 LLM rule retargeted at the Gemini API.

## In progress
- Nothing in code. M0 is the contract, the models and the gold slice.

## Next up
- IR models with invariant checks (INV-01 to INV-12); JSON Schema export.
- Decision log schema and policy format.
- Gold slice: propositions, rules, a judgement point, an alternatives set, fact sets, question set.
- S0 config validation should check SQLite has FTS5 at startup, not at first query (ADR-0001).

## Blocked or failing
- Nothing.

## Questions for Tom
- Spec section 2 describes the stack as "Anthropic API behind a provider abstraction". ADR-0003
  changed that to Gemini. NFR-PRT-01 names no vendor, so nothing normative is contradicted, but
  the sentence in `spec-src/` is now stale and only you can edit it.
- The base install carries `spacy`, `fastapi`, `uvicorn` and `z3-solver`, none of which is used
  before M3. Worth moving to extras? It is 460 MB and a large audit surface for M0 to M2.
- NFR-SEC-01 asks for a secret scan and a dependency scan in CI. `ci.yml` runs `pip-audit` but has
  no secret scan. One step, and it is a Must-have.
- The Bash guard does not cover shell writes. `protect-paths.sh` only runs on `Edit`, `Write` and
  `NotebookEdit`, so `sed -i docs/spec/...` or `cat > gold/...` is unguarded, as is `cat
  spec-src/...` against the `Read` deny rule. Adding a protected-path check to `guard-bash.sh`
  would close it; the hooks are yours to edit.
- `guard-bash.sh` matches its trigger strings anywhere in a command, so writing documentation that
  merely mentions the live-run flag is blocked. It hit this session twice. Matching only an actual
  assignment or export would fix it.
- `protect-paths.sh` does not cover `.claude/settings.local.json`, which can add permission rules.
  Deny still beats allow, so this is hardening rather than a hole.
- `POL-ux-stricter-wins` needs a defined answer for a missing `effort_to_fix` from the caller.
  Conservative reading: treat absent effort as not-high, so the stricter requirement wins. Confirm
  when the policy is implemented (ADR-0002 consequences).
- HTML parser for the first probe (ADR-0001 default: a standard HTML parser; Docling for documents).
- Judgement cost caps are still TODO in `domain_config.yaml` (OQ-03); they need an M5 measurement.
