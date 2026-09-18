---
paths: ["src/engine/evaluator/**", "src/engine/compile/**", "src/engine/validate/**"]
---
# Evaluator, compile, validate (FR-QRY, FR-CMP, FR-VAL)

- The evaluator is pure: no I/O, clocks, randomness or LLM calls; strong Kleene three-valued
  logic; missing fact is UNKNOWN unless `closed_world`; no negation as failure (FR-QRY-01,
  FR-QRY-04). Judgement and inference enter as tagged facts. Property-based tests for truth
  tables, defeat ordering and UNKNOWN propagation (NFR-TST-01).
- UNKNOWN lists what would resolve it and how to obtain each. Explanations list rules fired,
  defeated and by what, policies, judgements, facts with provenance, citations (FR-QRY-03).
- Force decides the target (FR-CMP-01). Exceptions are defeat relations; alternatives are guarded
  option sets with no defeat between members (INV-07). Freeze only on unresolved gap, unresolved
  condition or blocked source; unresolved conflict is alternatives (FR-CMP-02).
- Package, index and rule set from the same IR in the same run (FR-CMP-03).
- NetworkX for graph checks, Z3 for satisfiability and overlap; a seeded-defect test per check
  (FR-VAL-01, NFR-TST-01). The critic checks two things and only lowers to provisional (FR-VAL-02).
  Blocking failures stop that rule set, not the run; the contract test runs before publishing.
