# 0003. Models by role

- Status: Accepted
- Date: 2026-09-18
- Related: NFR-PRT-01, OQ-03, FR-RET-01, FR-JDG-01

## Context

Extraction, classification, panel, critic, run-time judgement, inference and embeddings each need a
model. Judgement runs at tool call time, so its cost matters most.

## Options

1. One family for every role; the panel uses different models and prompts.
2. Cheapest model per role that meets that role's gold target (0.80 judgement agreement).
3. Embeddings: local sentence-transformers model, or a hosted API.

## Decision

Tom decided on 2026-09-18: start with one model for every inference role, and a self-hosted
embedding model. This is option 1 as a starting point, with option 2 as the tuning method once M4
and M5 produce gold numbers.

- **Every inference role: `gemini-2.5-flash`.** Extraction, classification, panel, critic,
  judgement and inference all start here. If it does not meet a role's gold target, move that
  role to a newer or larger model rather than moving all of them.
- **Embeddings: `nomic-ai/nomic-embed-text-v1.5`, self-hosted** through the `embeddings-local`
  extra. 768 dimensions, Matryoshka-truncatable, 8192-token context, Apache-2.0.
- **Compute.** Local CPU first. If embedding a full snapshot is too slow, the fallback is a free
  Google Compute Engine instance rather than a hosted embedding API, so that no source text has
  to leave our control to be indexed.

Model IDs are pinned in `config/domains/<domain>/domain_config.yaml` under `models`, never in
code and never in a prompt template (NFR-PRT-01).

### Panel composition is still open

The spec's panel for CONTRADICTS (FR-REC-01, `.claude/rules/stages.md` S6) assumes members that
disagree independently. A panel of one model called three times does not give that. For M4 the
panel is `gemini-2.5-flash` with three different prompts, and its disagreement rate is measured on
gold; if agreement turns out to be near-total, a second family gets added then. Recorded here so
the limitation is not mistaken for a design.

### This supersedes a descriptive line in the spec

Spec section 2 (Roles) describes the stack as "Anthropic API behind a provider abstraction".
The normative requirement, NFR-PRT-01, names no vendor: it requires a provider abstraction with
model IDs in configuration. This ADR changes the vendor, not the requirement. Section 2's stack
sentence is now stale and only Tom can edit `spec-src/`.

## Consequences

- `google-genai` replaces `anthropic` in `pyproject.toml`. The provider abstraction in
  `engine.llm` must keep the vendor SDK behind it (NFR-PRT-01), so a later swap is one adapter.
- The API key is read from `FORMAL_ENGINE_GEMINI` only, never from `GOOGLE_API_KEY` or
  `GEMINI_API_KEY`: the Google SDK reads those from the ambient environment by itself, which would
  let a live call happen without the run being in live mode. The same name is set as a repository
  secret on GitHub, so it means the same thing locally and in Actions. Langfuse uses its own SDK
  names (`LANGFUSE_SECRET_KEY` secret; `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_BASE_URL` variables),
  which is the ambient-pickup pattern this bullet warns against; it is accepted there because the
  worst case is a trace written to the wrong project, not a paid model call.

  This risk is not new to Gemini. The `anthropic` SDK reads `ANTHROPIC_API_KEY` the same way, and
  the starter kit already guarded against it by prefixing the name. Two things did change: the
  Google SDK reads two names rather than one, and `GOOGLE_API_KEY` is generic enough to be set for
  an unrelated Google service, so the chance of an accidental collision is higher.
- Any model change is a prompt-set change and triggers re-evaluation (NFR-PRT-01).
- `nomic-embed-text-v1.5` loads with `trust_remote_code`, so `einops` is in the extra and the
  model revision should be pinned when M3 wires retrieval up: remote code at an unpinned revision
  is an unpinned dependency.
- Structured output, prompt caching and batching all differ between vendors. The
  `prompt-authoring` skill and `engine.llm` now target the Gemini API, and the bundled
  `/claude-api` skill no longer applies to this project.
- Judgement cost caps (OQ-03) are still unset: `judgement_cost_cap_per_call` and
  `judgement_cost_cap_per_package_day` in `domain_config.yaml` remain TODO until M5 measures a
  per-call cost.
