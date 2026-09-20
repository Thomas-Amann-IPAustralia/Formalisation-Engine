# Status

Milestone: M0 Contract and models
Updated: 2026-09-19

## Done recently
- Starter kit reviewed and made runnable: `uv.lock` committed, hooks committed executable (they
  were mode 644 and doing nothing), `.pytest_cache/` untracked, `.env.example` added,
  `README-STARTER.md` became `README.md`.
- ADRs 0001 to 0003 Accepted: mypy strict with the Pydantic plugin, SQLite FTS5 with built-in
  BM25, Docling local; page structure and headings as the M1 objective with
  `POL-ux-stricter-wins` and all five triage signals required; `gemini-2.5-flash` for every
  inference role and `nomic-embed-text-v1.5` self-hosted.
- ADR-0004 Accepted: the push block goes, the rest of the Bash guard stays.
- Secret scan added to CI (`detect-secrets` over tracked files), which closes the NFR-SEC-01 gap.
  Verified both ways: clean on this tree, and it fails the step on a planted key.
- uv download cache enabled in CI, keyed on `uv.lock`.
- `spacy` and `z3-solver` moved to the `nlp` and `solver` extras. Base install 462 MB to 170 MB.
- Key names aligned with the repository secrets and variables: `FORMAL_ENGINE_GEMINI`,
  `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_BASE_URL`.

## In progress
- Nothing in code. M0 is the contract, the models and the gold slice.

## Next up
- IR models with invariant checks (INV-01 to INV-12); JSON Schema export.
- Decision log schema and policy format.
- Gold slice: propositions, rules, a judgement point, an alternatives set, fact sets, question set.
- S0 config validation should check SQLite has FTS5 at startup, not at first query (ADR-0001).

## Blocked or failing
- Nothing failing.

## Questions for Tom
- **Five edits only you can make**, written out in full in `docs/adr/0004-no-push-block.md`:
  remove the push rule from `guard-bash.sh`, narrow its live-LLM matcher, move the push entry from
  deny to allow in `settings.json`, and drop "never push" from `CLAUDE.md` line 71 and from step 8
  of the `implement-req` skill. Claude is blocked from editing its own permission files and its own
  instructions by a harness-level check, which is working as intended. Until they are applied the
  hook still refuses pushes and the written rules still say not to. The edits were tested on a
  scratch copy first: the live-run, pip and recursive-delete rules all still fire, and only the
  push rule stops. Evidence is in the ADR.
- **Branch protection on `main`.** Removing the push block means nothing local stops a force-push
  to `main` any more. The old rule only stopped a careless one anyway. A branch protection rule in
  the GitHub settings (require a pull request, block force-pushes) is the control that actually
  holds, because it applies server-side to every actor. Five minutes in Settings then Branches.
- **The stale spec sentence.** Section 2 describes the stack as "Anthropic API behind a provider
  abstraction"; ADR-0003 changed that to Gemini. Claude's attempt to read `spec-src/` was refused
  by the permission layer, so this one is yours. Suggested replacement for that clause: "a model
  provider API behind a provider abstraction (currently Gemini; see ADR-0003)". NFR-PRT-01 names
  no vendor, so nothing normative is affected. Run `python3 scripts/spec_tools.py build` after.
- The secret scan reads the working tree, not git history, so a secret committed and later removed
  would not be caught. Add `gitleaks` or `trufflehog` over full history if that matters.
- `detect-secrets` and `pip-audit` both run unpinned through `uvx`, so a new release could change
  CI behaviour without a commit. Pin both if CI stability matters more than currency.
- `POL-ux-stricter-wins` needs a defined answer for a missing `effort_to_fix` from the caller.
  Conservative reading: treat absent effort as not-high, so the stricter requirement wins.
- HTML parser for the first probe (ADR-0001 default: a standard HTML parser; Docling for documents).
- Judgement cost caps are still TODO in `domain_config.yaml` (OQ-03); they need an M5 measurement.
- `spacy` is in an extra but is not referenced by any rule file or requirement yet. If segmentation
  turns out not to need it, drop it rather than carrying 230 MB into M2.
