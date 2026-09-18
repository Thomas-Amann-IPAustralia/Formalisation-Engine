"""Gate tests (spec 7.3). Strict xfail stubs: delete a gate's `@PENDING` line when implemented."""

import pytest

pytestmark = pytest.mark.gate

PENDING = pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="gate not implemented")


@PENDING
@pytest.mark.req("G1")
def test_g01_abstention_by_deletion() -> None:
    """Abstention by deletion. Remove the only source for an element; re-run. Pass when: Gap
    raised; dependent rules frozen; tool returns UNKNOWN with the gap; nothing invented.
    """
    raise NotImplementedError


@PENDING
@pytest.mark.req("G2")
def test_g02_tool_asks_for_what_it_needs() -> None:
    """Tool asks for what it needs. Call an objective with no facts and no artefact. Pass when:
    Undetermined items list the facts and how to obtain each.
    """
    raise NotImplementedError


@PENDING
@pytest.mark.req("G3")
def test_g03_guidance_not_promoted() -> None:
    """Guidance not promoted. Add a "should" restatement of a requirement. Pass when: No executable
    obligation derives from it; it is advisory.
    """
    raise NotImplementedError


@PENDING
@pytest.mark.req("G4")
def test_g04_conflict_by_policy() -> None:
    """Conflict by policy. Seed a threshold conflict with an authority-order policy, then without
    one. Pass when: Resolved and logged with policy and inputs, hook emitted; then recorded as
    alternatives and returned with conditions, nothing chosen.
    """
    raise NotImplementedError


@PENDING
@pytest.mark.req("G5")
def test_g05_change_resilience() -> None:
    """Change resilience. Amend one passage in a new snapshot. Pass when: Only dependants go stale;
    overrides on unchanged records survive.
    """
    raise NotImplementedError


@PENDING
@pytest.mark.req("G6")
def test_g06_fabricated_provenance_and_injection() -> None:
    """Fabricated provenance and injection. Inject a cached response whose span is not in the
    source; put instruction-like text in a passage and an artefact. Pass when: Proposition
    rejected and logged; pipeline and probes unchanged.
    """
    raise NotImplementedError


@PENDING
@pytest.mark.req("G7")
def test_g07_judgement_at_run_time() -> None:
    """Judgement at run time. Call an objective that reaches a judgement point. Pass when: Outcome
    tagged `judged` with rationale and confidence, logged; a caller override replaces it on the
    next call and shows as `overridden`.
    """
    raise NotImplementedError


@PENDING
@pytest.mark.req("G8")
def test_g08_replay() -> None:
    """Replay. Replay a run and a tool call from cache. Pass when: Identical outputs, including
    judgements.
    """
    raise NotImplementedError


@PENDING
@pytest.mark.req("G9")
def test_g09_exception_precedence() -> None:
    """Exception precedence. A rule and its exception both apply; then the exception's fact is
    UNKNOWN. Pass when: Exception wins, defeat shown; then UNKNOWN with the exception's facts
    listed.
    """
    raise NotImplementedError


@PENDING
@pytest.mark.req("G10")
def test_g10_probe_abstains() -> None:
    """Probe abstains. Run every probe on a malformed artefact. Pass when: UNKNOWN with a declared
    reason, carried into the response; no value invented.
    """
    raise NotImplementedError


@PENDING
@pytest.mark.req("G11")
def test_g11_reference_source() -> None:
    """Reference source. Configure a `reference` source. Pass when: No text stored; citations give
    anchor and link.
    """
    raise NotImplementedError


@PENDING
@pytest.mark.req("G12")
def test_g12_provisional_carries_status() -> None:
    """Provisional carries status. Lower a rule below the auto-approval threshold. Pass when: It
    still compiles and answers, tagged provisional, and is queued.
    """
    raise NotImplementedError
