---
paths: ["src/engine/tool/**", "src/engine/judgement/**", "src/engine/probes/**", "tool/**", "config/domains/*/fact_providers.yaml"]
---
# Tool package, judgement, probes (FR-TOO, FR-JDG, FR-PRB, spec Appendix E)

- One contract for every domain, one implementation behind Python, MCP and CLI (FR-TOO-01).
  Every assertion cited (INV-10). Unknown objective or version mismatch: refuse (FR-TOO-03).
- Providers in order per fact type: probe, caller, inferred, derived (FR-TOO-04). Never block on a
  person: a missing caller fact is undetermined with what is needed.
- Judgement only when rules cannot decide and no override exists; through `engine.llm`; logged
  with outcome, rationale, confidence, model, prompt version, inputs, artefact hash; returned
  tagged `judged`; cached; cost-capped (FR-JDG-01, FR-JDG-03). Inference only where the fact type
  allows and no probe or caller value exists (FR-JDG-02). Overrides win and show as `overridden`.
- Probes: deterministic, read-only, no scripts, no links, no LLM; a value with artefact reference
  or UNKNOWN with a declared reason, never a default or estimate; preconditions first; results
  record probe version and artefact hash; abstentions reach the response as reasons (FR-PRB-01,
  FR-PRB-02, INV-09). Register through the registry; one value test and one abstention test each.
- Verified, provisional, inferred, judged and overridden are always distinguishable; the
  best-effort note is always present (FR-TOO-02). Run-time log entries go to the configured sink
  in the pipeline's schema; the package runs offline against recorded artefacts (FR-TOO-05).
