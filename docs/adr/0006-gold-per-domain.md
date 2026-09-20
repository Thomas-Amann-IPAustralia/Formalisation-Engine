# 0006. Gold after the pilot: full once, acceptance set thereafter

- Status: Proposed
- Date: 2026-09-20
- Related: FR-EVL-01, FR-EVL-02, NFR-EXT-01, OQ-05, spec 7.1, 7.2, 7.4

## Context

The pilot's gold slice does two jobs, and only one of them recurs.

**Does the Engine work?** Proposition recall and precision, force accuracy, judgement point
recall, skeleton element F1, relation macro-F1, and the gates in 7.3. These are properties of the
Engine, not of the Style Manual. Once force accuracy reaches 0.90 on the pilot, that is a fact
about the Engine; measuring it again on WCAG, then on OWASP, re-learns it.

**Is this domain's output right?** That recurs with every corpus, because every corpus is a fresh
chance to be confidently wrong.

The spec answers the resulting question three ways. NFR-EXT-01 says onboarding a domain needs
"only configuration, sources and policies", and gold is not in that list. `gold/README.md` lays
gold out as `gold/<domain>/<objective>/`, so a domain axis exists. And
`.claude/skills/new-domain/SKILL.md` creates a gold folder for every new domain in the same
breath as citing NFR-EXT-01, so one file holds both readings. Spec 7.1 leans the other way again:
gold is "built with the orchestrator for the pilot objective, before extraction exists", and
extraction only fails to exist once.

Nothing breaks whichever way this goes, which is exactly why it will be answered differently each
time someone asks. M6 recommends the next domain, so the question becomes real then.

## Options

1. A full gold slice per domain per objective, as the pilot builds one.
2. A full gold slice once, for the pilot. Each domain after it gets a small acceptance set, with a
   full re-measure only on a named trigger.
3. No gold after the pilot at all. The Engine is trusted once it passes the gates.

## Decision

Option 2.

Option 1 charges every domain for a measurement that is already done, and the cost lands on the
one person who cannot be parallelised. Option 3 removes the only check that a new corpus did not
quietly break something, and NFR-SAF-01's whole posture is that nothing is trusted without a
source.

**An acceptance set** is what a new domain gets. Roughly:

- 5 to 10 questions with gold answers and citations;
- 2 or 3 fact sets, at least one of which leaves a fact out and expects UNKNOWN;
- at least 2 questions the sources genuinely do not answer.

That is hours, not days, and it catches the failure that matters most: a tool that invents an
answer rather than abstaining.

**A full re-measure** is triggered by any of:

- **A model change.** ADR-0003 already says a model change triggers re-evaluation. The 7.2
  metrics are the re-evaluation.
- **A new corpus kind.** `policy`, `standard` and `methodology` corpora are drafted differently,
  and the cue lists and force detection are tuned to drafting conventions. The first domain of a
  kind the Engine has not seen is re-testing the Engine, not just the domain.
- **A `contract_version` change.** A breaking contract change updates every consumer, so every
  package's answers are worth re-checking.

NFR-EXT-01 stands under this decision. An acceptance set is domain content, in the same class as
sources and policies. It is not core code, an IR schema change or a contract change, which is
what NFR-EXT-01 actually rules out.

## Consequences

- The evaluation harness (FR-EVL-01) must accept a gold directory holding `questions.json` and
  `fact_sets/` with **no** `ir.json`, and report the 7.2 metrics it can compute rather than
  failing on the ones it cannot. Alignment metrics need a gold IR; answer quality, citation
  validity and correct abstention do not. This is a constraint on how M6 builds the harness, and
  it is cheap to honour now and expensive to retrofit.
- `.claude/skills/new-domain/SKILL.md` still creates `gold/<slug>/<objective>/`, but now says what
  belongs in it, so running the skill does not imply a week of work.
- The pilot's gold slice carries more weight than any later one, because the Engine-level numbers
  are measured once and then relied on. A thin pilot gold is a false economy; this decision is
  what makes it worth doing properly.
- If a later domain's acceptance set fails in a way that looks like an Engine problem rather than
  a corpus problem, that is a trigger to build a fuller gold slice for it. Judgement, not a rule,
  and recorded here so the judgement is at least a conscious one.
