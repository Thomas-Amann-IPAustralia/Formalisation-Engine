# 0003. Models by role

- Status: Proposed
- Date: 2026-09-18
- Related: NFR-PRT-01, OQ-03, FR-RET-01

## Context

Extraction, classification, panel, critic, run-time judgement, inference and embeddings each need a model. Judgement runs at tool call time, so its cost matters most.

## Options

1. One family for every role; the panel uses different models and prompts.
2. Cheapest model per role that meets that role's gold target (0.80 judgement agreement).
3. Embeddings: local sentence-transformers model, or a hosted API.

## Decision

To be decided: roles in M2, judgement in M5, embeddings in M2. Record model IDs here and pin them in config.

## Consequences

Any model change is a prompt-set change and triggers re-evaluation.
