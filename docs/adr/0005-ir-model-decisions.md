# 0005. IR model decisions the spec leaves open

- Status: Proposed
- Date: 2026-09-20
- Related: NFR-INT-01, NFR-MNT-01, NFR-PRT-01, INV-01 to INV-12, FR-EPI-01, FR-TOO-02, DP-11

## Context

M0 builds the IR models, the invariant checks and the generated JSON Schema. Spec section 4
gives field lists and says they are minimums; Appendix D gives the invariants; Appendix E gives
the contract. Several things the code has to settle are not settled anywhere, and CLAUDE.md says
to ask rather than invent. This records what was chosen, so the choice is reviewable and so the
next domain does not have to re-derive it.

Each decision below is implemented and tested. Setting this ADR to Accepted confirms them;
rejecting any one of them is a small change, because each is behind a named constant, a single
function, or one field.

## Options

1. Decide each point in code and leave no record, which is how a convention becomes folklore.
2. Decide each point conservatively, implement it, and record it here for Tom to accept or
   change.
3. Stop and ask on each point before writing anything, which stalls the stage eight times.

## Decision

Option 2. The eight points, with what was chosen and why.

### 1. Four identifier prefixes the spec uses but does not list

Spec section 4 lists thirteen prefixes. The spec uses four more: `SNAP` (Appendix E's
`"snapshot_id": "SNAP-..."`), `SKEL` (`framework_skeleton.yaml` carries
`skeleton_id: SKEL-ux-standards`), `RUN` (section 4 says the IR carries a `run_id`) and, for
the decision log INV-12 requires, `DEC`. All four are in `IdKind`. Identifier suffixes allow
underscores, because the pilot's fact types use them (`FACT-heading_levels_skipped`).

### 2. The content-hash scheme

SHA-256 over each part normalised to Unicode NFC, each part length-framed (`<byte length>:`
then the bytes), truncated to 16 hex characters.

Framing rather than a separator because source text is untrusted: with a separator, a passage
containing that character could shift a boundary and collide with other content, which is the
kind of thing G6 is about. Sixteen hex characters is 64 bits; at the pilot's order of 3,000
passages the chance of any collision is about 2.4e-13, and at a million identifiers about
2.7e-8. Widening to 24 characters is a one-constant change if a domain ever needs it, but it
lengthens every citation in every response for a risk that is already negligible.

### 3. Identifiers as IRIs

`https://formalisation.engine/id/<identifier>`, with `to_iri` and `from_iri` inverse and
round-trip tested (NFR-INT-01). The domain is a namespace, not a location; nothing fetches it.
Identifier suffixes exclude `/` and whitespace so that the IRI needs no escaping.

### 4. The epistemic `overall` function

Spec section 4 says `overall` is "a deterministic function of the rest" and stops there. The
labels are `verified`, `provisional`, `inferred`, `judged`, `overridden` and `blocked`, which
are DP-05's list plus `blocked` from the triage states. The rules, first match wins:

1. `provenance_kind` is `overridden` → **overridden**.
2. `triage` is `blocked` → **blocked**.
3. `provenance_kind` is `judged` → **judged**; `inferred` → **inferred**.
4. Otherwise **verified** only when both confidences are `high`, consistency is one of
   `consistent`, `qualified` or `resolved_by_policy`, an authority level is established, and
   triage is `auto_approved`.
5. Anything else → **provisional**.

An override beats a blocked record because CLAUDE.md, DP-08, INV-12 and FR-TRI-02 all say
overrides win. That is a labelling decision only: a blocked record still never compiles, because
INV-04 and FR-TRI-01 refuse it separately at compile time. Rule 4 is what keeps FR-EPI-01's
"LLM self-reported confidence is never the sole input" true — consistency, authority and triage
are not things a model reports about itself, and without all three there is no `verified`.

The truth table is asserted over all 3,200 combinations of the dimensions. Status *propagation*
("a rule takes the weakest status of its sources") is FR-EPI-01 and belongs to M4; it is not
implemented here.

### 5. `extensions` as the only extension point

NFR-PRT-01 says "a domain adds fields only inside declared extension points" without saying
where they are. Every IR record inherits one `extensions` mapping keyed `<namespace>.<field>`;
everywhere else refuses unknown fields. The namespace is normally the domain slug, so two
domains cannot collide on one field name. The contract models deliberately do **not** have it:
DP-11 fixes the contract shape across every domain.

### 6. Frozen records, unknown fields refused

Every model is `frozen=True` and `extra="forbid"`, and sequence fields are tuples. DP-03 makes
the IR canonical and NFR-DET-01 wants byte-identical replay; a record that cannot be mutated
cannot drift from the identifier hashed out of it. Freezing is shallow, so mappings inside a
record are still mutable — nothing hashes a record, so this is a caveat rather than a hole.

`EpistemicStatus.overall` is a computed field, which means it is written on dump and would then
be refused on load. Rather than dropping it silently, the model checks a supplied `overall`
against the computed one and fails when they disagree, so a hand-written gold IR cannot claim a
status its dimensions do not support.

### 7. The skeleton is stored flat

`framework_skeleton.yaml` is nested for a person to read. The IR stores elements flat, each
naming its parent. The invariants and M5's graph checks both want a node list and an edge list,
and a nested tree makes every lookup a traversal. S5 flattens on the way in.

### 8. `schema/` layout, and one addition to the contract

Published per version at `schema/ir/<schema_version>/ir.schema.json` and
`schema/contract/<contract_version>/{request,response}.schema.json`, each with an `$id` under
`https://formalisation.engine/schema/`. Written only by `uv run engine schema export`, which is
why the path is protected from hand-editing; `--check` prints a diff and exits non-zero, and
both a unit test and CI run it.

The IR and the response are generated in serialisation mode so that the computed `overall`
appears; the request in validation mode, because that is what a caller constructs.

One field is added to Appendix E: `Citation.passage_id`, optional. INV-10 requires every
assertion's citation to *resolve to a passage*, and `document` plus `anchor` is how a person
reads a citation, not how a machine resolves one. It is optional and additive, so an existing
consumer is unaffected — "add content, never change shape".

`ToolResponse.plan` is left untyped. Appendix E shows `null` and FR-TOO-04 says the tool honours
`mode: plan`, but neither says what a plan contains, and inventing a structure for it is not a
model decision.

### Two smaller notes

INV-07's cycle detection is written out rather than taken from NetworkX. NetworkX is a base
dependency but belongs to the compile and validate toolchain, and NFR-PRT-01 keeps the IR free
of it. It is iterative rather than recursive, so a deep graph cannot raise out of a checker that
DP-04 requires never to stop the run. A property test cross-checks it against Kahn's algorithm.

INV-03 is read as covering both decision-point elements and judgement procedures. Both are
decisions the facts may fail to settle, and a procedure that cannot decline will invent an
answer.

## Consequences

- Renaming or removing a field in `engine.models` changes `IR_SCHEMA_VERSION` and regenerates
  `schema/`. The unit test and CI both fail until the export is committed, which is the point.
- A domain that needs a field the IR does not have puts it under `extensions`, or the field
  belongs in the core models and this ADR is superseded. There is no third way.
- Where a model makes an invariant unrepresentable, the invariant check covers what a single
  record cannot know about itself. Both layers are load-bearing: the model raises on
  construction, which a stage catches per record (DP-04), and the check returns violations,
  which a stage records and blocks on.
- Two readings of the spec are recorded in `docs/STATUS.md` for Tom rather than settled here:
  the three spellings of "could not decide", and Appendix E's sample showing uncited advisory
  and judgement entries against INV-10.
