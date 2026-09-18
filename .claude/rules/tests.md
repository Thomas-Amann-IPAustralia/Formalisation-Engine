---
paths: ["tests/**"]
---
# Tests

- `@pytest.mark.req("ID", ...)` links a test to requirements; results land in
  `var/req_results.json` for `python3 scripts/spec_tools.py coverage`.
- `@pytest.mark.fast`: deterministic, under a second, no network (the Stop hook runs these).
- `@pytest.mark.live` skips unless Tom sets `ENGINE_ALLOW_LIVE_LLM=1`. Never set it.
- LLM responses come from `tests/fixtures/llm_cache/`; never hand-edit them. Gate stubs in
  `tests/gates/` are strict xfail until implemented.
- Test the behaviour the requirement states, including the failure path. Unit tests use the
  synthetic corpus; the pilot snapshot is for integration tests only.
