# 0002. Pilot choices: first topic, tie-breaking rule, and what gets reviewed

- Status: Accepted
- Date: 2026-09-18
- Related: OQ-01, OQ-02, FR-CFL-02, FR-TRI-01

## Context

Three choices need making before M1 can start. They were first written in spec shorthand, which
was not clear enough to answer; this version says the same thing in plain words. Each one is
reversible: they set where the pilot starts, not where it ends up.

Background, in one paragraph. The Engine reads the Style Manual and WCAG 2.2 and turns them into
a set of rules that a UX-Designer agent can call. Three things were undecided: which slice of those
documents to do first; what the Engine should do when the two documents disagree; and how sure
the Engine has to be before it accepts a rule without anyone looking at it.

## Question 1: which topic should the pilot cover first?

The pilot does one narrow topic end to end before widening. The topic needs a real judgement call
in it (something no amount of code can settle) and cheap automated checks (things a script can
measure from an HTML page).

1. **Page structure and headings** (chosen). Does the page use headings, in order, and do they
   describe what follows? Two parts are machine-checkable (are levels skipped, is the capitalisation
   sentence case); one part needs judgement (does the heading actually describe its section).
2. **Link text.** Is link text meaningful out of context? Mostly judgement; fewer machine checks.
3. **Plain language.** Reading level, sentence length, jargon. Lots of machine checks, but almost
   every rule is advisory, so the pilot would not exercise conflicts or obligations.

## Question 2: when WCAG and the Style Manual disagree, what should the Engine do?

The two documents are equal in authority here, so neither automatically wins. Say WCAG requires a
colour contrast of 4.5:1 and the Style Manual illustrates a palette that only reaches 3.8:1. The
Engine has to do something with that.

1. **Weigh it up** (chosen). Serve the stricter requirement, except when meeting it would matter
   little to users and cost a lot of effort; in that case serve the looser one and record the
   trade-off. Needs two inputs: how much it affects users (the Engine estimates this) and how much
   work it is (the calling agent says). Drafted in `decision_policy.yaml` as
   `POL-ux-stricter-wins`.
2. **Always the stricter one.** Simpler, never needs an estimate, and never has to explain itself.
   Costs nothing to implement and cannot be accused of lowering a standard. It will sometimes
   insist on a change that nobody would make.

Either way the Engine records what it did and why, so the answer can be audited and overridden.

## Question 3: when should a rule go into a review queue instead of being used straight away?

Nothing blocks on a person: a rule in the queue is still served, just marked provisional
(DP-01, FR-TRI-01). This is about which ones get flagged for you to look at.

1. **Only accept a rule silently when every signal is good** (chosen): the Engine is confident it
   read the passage correctly, confident it understood what the passage means, two independent
   checks agree, nothing else in the corpus contradicts it, and it is the current version of the
   document. Anything less goes in the queue. Safer; a bigger queue at the start.
2. **Accept on reading confidence alone.** Only ask "am I sure I read this correctly?" Smaller
   queue, but a rule that was read correctly and interpreted wrongly goes through unflagged.

## Decision

Tom chose option 1 on all three, on 2026-09-18. These were the drafted defaults, so the pilot
configuration already matches; it is now confirmed rather than provisional.

- **M1 objective: page structure and headings.** `objectives.active: ["page-structure"]` in
  `domain_config.yaml`, with `EL-page-structure` in `framework_skeleton.yaml` as the tree.
- **Conflict policy: `POL-ux-stricter-wins`**, the risk matrix over user impact and effort, in
  `decision_policy.yaml`. `impact_on_users` comes from a judgement procedure, `effort_to_fix` from
  the caller.
- **Triage: all five signals must be good** to auto-approve. In `domain_config.yaml` under
  `triage.auto_approve`: extraction confidence high, interpretation confidence high, guards agree,
  consistency in {consistent, qualified, resolved_by_policy}, temporal current.

All three are tuned against gold in M4 (OQ-01, OQ-02).

## Consequences

- The pilot exercises alternatives and policy early, which is the point of choosing a topic with
  a judgement point in it. `EL-heading-describes` is that judgement point, and it is the first
  thing M1 has to make work end to end.
- `POL-ux-stricter-wins` cannot run until a judgement procedure can estimate `impact_on_users`.
  Until then the policy has an input it cannot fill, so a conflict falls through to unresolved
  alternatives (DP-10). That is the correct behaviour, not a bug, but it means M4 needs the
  judgement path before the policy path can be measured.
- `effort_to_fix` comes from the caller and callers will often omit it. The policy needs a defined
  answer for a missing input; the conservative reading is to treat absent effort as not-high, so
  the stricter requirement is served. Settle this when `POL-ux-stricter-wins` is implemented.
- Requiring all five signals means the M4 queue will be large at first. That is expected: the
  queue is the tuning signal, and thresholds move down once gold says which signal was carrying
  the weight.
- Nothing in the triage choice blocks a run. Queued records still compile as provisional and are
  still served (FR-TRI-01), so a large queue costs review attention, never availability.
