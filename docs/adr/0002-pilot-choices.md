# 0002. Pilot choices: objective, policy, triage thresholds

- Status: Proposed
- Date: 2026-09-18
- Related: OQ-01, OQ-02, FR-CFL-02, FR-TRI-01

## Context

M1 needs one objective with cheap probes, a real judgement point and an alternatives case. WCAG and the Style Manual are equal-ranked, so a policy must resolve their differences. Triage needs thresholds.

## Options

1. Objective: page structure and headings (default); link text; plain language.
2. Policy: risk matrix over user impact and effort, serving the stricter requirement unless impact is low and effort high (default, drafted in `config/domains/style-manual-wcag/decision_policy.yaml`); always the stricter.
3. Thresholds: auto-approve when guards agree, confidence high, no open conflict, temporal current (default); extraction confidence alone.

## Decision

Defaults, confirmed by Tom in M0 and tuned on gold in M4.

## Consequences

The pilot exercises alternatives and policy early.
