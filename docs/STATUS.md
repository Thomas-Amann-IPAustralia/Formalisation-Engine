# Status

Milestone: M0 Contract and models
Updated: 2026-09-20

## Done recently
- The IR spine: `engine.ids`, `engine.models` (spec section 4), the epistemic status function,
  the Appendix D invariant checks, the Appendix E contract, and JSON Schema generated from all
  of it. 186 tests; mypy strict and ruff clean.
- `schema/` is generated and committed by `uv run engine schema export`; `--check` diffs it and
  exits non-zero, and both a unit test and CI run that.
- M0 coverage: INV-01 to INV-12 and NFR-INT-01 passing, NFR-MNT-01 evidence-needed.
- ADR-0005 (Accepted 2026-09-23 by Tom) records the eight points where the spec is silent and
  this stage chose.
- The spec-auditor pass found three real gaps, all fixed: INV-12 never checked judgements,
  it accepted an input-less log entry if a sibling entry had inputs, and one Appendix E
  tightening was unrecorded.

## In progress
- Nothing. The branch is clean and pushed.

## Next up
- S0 configuration validation: FR-CFG-01 to FR-CFG-03 over the seven domain files, naming the
  bad field, with the FTS5 startup check from ADR-0001.
- The gold slice (FR-EVL-01). The models validate it; `gold/` is yours to write.
- `engine.stores`, which implements the `IRLookup` protocol the invariant checks take.

## Coverage that is narrower than it reads
- `coverage` counts a requirement passing as soon as one test claims it. Three claims here are
  partial: **NFR-INT-01** (schemas, ISO 8601, UTF-8 and IRIs are done; "usable as a LangGraph
  tool, MCP exposes the same operations" needs the package, M1/M5), **FR-EPI-01** (the `overall`
  function only, not propagation, M4) and **NFR-PRT-01** (the `extensions` point only, not the
  provider abstraction, M2). **INV-12** checks that policy invocations, judgements and overrides
  reach the log with their inputs, and that an override beats a policy resolution, but not the
  "on an unchanged record" qualifier; ADR-0005 says why that waits for M4.

## Blocked or failing
- Nothing failing.

## Questions for Tom
- **Three spellings for "could not decide".** INV-03 says `unable_to_determine`,
  `POL-ux-conservative-default` says `undetermined`, FR-QRY-01 and FR-PRB-01 say UNKNOWN. I
  implemented INV-03's spelling and left the config alone. The first two should converge.
- **Appendix E's sample shows uncited assertions** (`"citations": []` on advisory and
  judgements) against INV-10, FR-TOO-03 and Appendix A, which says the advisory is cited. I read
  the empty arrays as abbreviation and check INV-10 strictly.
- **`POL-ux-stricter-wins` with a missing `effort_to_fix`.** `RiskMatrixDefinition` now takes a
  `defaults` mapping so the answer is declared in configuration, not decided in code. What
  should the pilot's be? Conservative reading: absent effort is not-high, so stricter wins.
- Still open: branch protection on `main`; spec section 2 still says "Anthropic API" where
  ADR-0003 says Gemini; `detect-secrets` and `pip-audit` run unpinned through `uvx`; `spacy` is
  in an extra and referenced by nothing.
