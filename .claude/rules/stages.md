---
paths: ["src/engine/stages/**", "src/engine/stores/**", "src/engine/retrieval/**", "src/engine/policy/**", "config/**", "prompts/**"]
---
# Pipeline stages S0 to S7 (spec section 3, FR-CFG to FR-TRI)

Every stage: reads and writes only through `engine.stores`; writes atomically; is idempotent;
records a report (counts, each failure with reason, cost, gate); records a failed record and
continues (DP-04); raises only on configuration or environment failure; never swallows an
exception. Runs replay from cache and resume from the last completed stage (FR-OPS-01).

- S0: validate config, name the bad field; backbone-led needs one backbone, framework-led none;
  every fact type exists and every probe provider is registered (FR-CFG-01). Files marked
  `origin: edited` are re-proposed only as a recorded diff (FR-CFG-02).
- S1: immutable snapshot with manifest; repositories pinned to a commit; `reference` sources never
  stored as text, `excluded` never fetched (FR-ING-01, FR-ING-04, INV-11).
- S2: structure, never token windows; every anchor resolves once (FR-SEG-01).
- S3: one passage per request with its context only; span must match exactly or the proposition
  is rejected; modal-cue detector and condition guard run in code, not the prompt (FR-EXT-01 to
  FR-EXT-04). Cue lists from the domain's `cue_lists.yaml`.
- S4: deterministic candidates first; confirm above the threshold and record it (FR-VOC-01).
- S5: derive (backbone) or propose (framework) the skeleton with every element citing passages;
  propose fact types and providers; write proposals with `origin: proposed`; classify against
  fixed label sets only (FR-SKL, FR-MAP). Report `no_relation` rate; re-propose once above threshold.
- S6: blocking, never all pairs; EXCEPTS, QUALIFIES, SUPERSEDES, ELABORATES, ALTERNATIVES before
  CONTRADICTS; panel for CONTRADICTS; resolve by policy and log policy, inputs, decision,
  rationale, hook; no policy means alternatives, nothing chosen (FR-REC-01 to FR-CFL-03). Gaps
  say what was searched and not found; loops have budgets (FR-GAP-01).
- S7: triage by configured thresholds; queued still compiles as provisional; only invariant
  failures block; overrides beat automation and are re-applied on unchanged records (FR-TRI).
- All LLM calls go through `engine.llm` (cache keyed on model, prompt ID and version, canonical
  inputs; replay is the default; live and record refuse without `ENGINE_ALLOW_LIVE_LLM=1` in the
  process environment; provider is the Gemini API per ADR-0003, with the key read from
  `ENGINE_GEMINI_API_KEY` only, never from the SDK's own `GOOGLE_API_KEY` or `GEMINI_API_KEY`,
  which it would pick up from the ambient environment). Prompts are versioned files in
  `prompts/<stage>/<name>.v<N>.md`; a used version is never edited, only succeeded.
