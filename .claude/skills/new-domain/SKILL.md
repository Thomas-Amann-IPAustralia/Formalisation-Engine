---
name: new-domain
description: Scaffold a new domain (config, authority profile, decision policy, empty proposal files, gold folder) so the Engine can propose its skeleton, fact schema and providers. Use when Tom wants to start a domain such as Data-Analyst or Security-Architect.
argument-hint: "<domain-slug> <agent>"
disable-model-invocation: true
---

Scaffold "$ARGUMENTS". Onboarding is configuration, sources and policies only (NFR-EXT-01).

Ask Tom in one message for: corpus kind (policy, standard, methodology); sources with licence
classes (flag anything subscription-only); the decision policy (authority order, risk matrix,
conservative; Security-Architect uses ASD principles, then Australian, then international); the
first objective.

Create under `config/domains/<slug>/`: `domain_config.yaml` (copy the pilot's shape),
`authority_profile.yaml` (`resolves_conflicts` matching the policy), `decision_policy.yaml`,
`cue_lists.yaml` (copy the pilot's and note this corpus's drafting conventions), and empty
`framework_skeleton.yaml`, `fact_schema.yaml`, `fact_providers.yaml` with `origin: proposed`
headers. Create `gold/<slug>/<objective>/`. Report in five lines: created, to decide, restricted
sources, fact types you expect to be caller or inferred rather than probed. Do not start a run.

The gold folder takes an acceptance set, not a full gold slice (ADR-0006): 5 to 10 questions with
gold answers and citations, 2 or 3 fact sets with at least one leaving a fact out and expecting
UNKNOWN, and at least 2 questions the sources do not answer. The full 7.2 measurement was done on
the pilot and is repeated only on a model change, a corpus kind the Engine has not seen, or a
`contract_version` change. Tell Tom which of those three this domain trips, if any. Gold is his to
write either way.
