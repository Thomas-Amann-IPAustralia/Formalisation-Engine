---
paths: ["src/engine/models/**", "src/engine/ids.py", "schema/**"]
---
# IR models (spec section 4)

- Pydantic v2 models in `engine.models` are the only definition of the IR; JSON Schema is
  generated (NFR-MNT-01). Removing or renaming a field is a schema version change.
- IDs are type-prefixed; passages and propositions are content hashes (spec 4).
- Every record carries epistemic status with `triage` and `provenance_kind`; `overall` comes only
  from the status function, which has a truth-table test (FR-EPI-01).
- Decisions always include `unable_to_determine` (INV-03). Judgement nodes link to a procedure,
  never a rule set (INV-08). `closed_world` defaults to false; `providers` is ordered.
- Skeleton elements assert nothing of their own. Policies, judgements and overrides write to the
  decision log (INV-12).
- Check Appendix D invariants on every IR write; a violation blocks the record, not the run.
