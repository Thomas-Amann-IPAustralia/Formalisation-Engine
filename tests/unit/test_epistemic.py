"""The epistemic status function (spec section 4, FR-EPI-01, DP-05). Truth table in ADR-0005."""

from __future__ import annotations

import itertools
from typing import Any

import pytest
from pydantic import ValidationError

from engine.models.enums import (
    ConfidenceBand,
    ConsistencyState,
    EpistemicOverall,
    ProvenanceKind,
    TriageState,
)
from engine.models.epistemic import SETTLED_CONSISTENCY, EpistemicStatus, overall_status

DIMENSIONS = (
    "extraction_confidence",
    "interpretation_confidence",
    "source_authority",
    "consistency",
    "provenance_kind",
    "triage",
)

#: Every dimension at its best, so each case below can change exactly one thing.
VERIFIED: dict[str, Any] = {
    "extraction_confidence": ConfidenceBand.HIGH,
    "interpretation_confidence": ConfidenceBand.HIGH,
    "source_authority": "normative_specification",
    "consistency": ConsistencyState.CONSISTENT,
    "provenance_kind": ProvenanceKind.EXTRACTED,
    "triage": TriageState.AUTO_APPROVED,
}

#: The whole input space: 4 x 4 x 2 x 5 x 5 x 4 = 3,200 combinations.
EVERY_COMBINATION: list[dict[str, Any]] = [
    dict(zip(DIMENSIONS, values, strict=True))
    for values in itertools.product(
        ConfidenceBand,
        ConfidenceBand,
        ("normative_specification", None),
        ConsistencyState,
        ProvenanceKind,
        TriageState,
    )
]


def overall_for(**changes: Any) -> EpistemicOverall:
    """The status for the all-good inputs with `changes` applied."""
    return overall_status(**{**VERIFIED, **changes})


@pytest.mark.fast
@pytest.mark.req("FR-EPI-01")
def test_everything_good_is_verified() -> None:
    assert overall_for() is EpistemicOverall.VERIFIED


@pytest.mark.fast
@pytest.mark.req("FR-EPI-01")
@pytest.mark.parametrize(
    ("change", "expected"),
    [
        ({"provenance_kind": ProvenanceKind.OVERRIDDEN}, EpistemicOverall.OVERRIDDEN),
        ({"triage": TriageState.BLOCKED}, EpistemicOverall.BLOCKED),
        ({"provenance_kind": ProvenanceKind.JUDGED}, EpistemicOverall.JUDGED),
        ({"provenance_kind": ProvenanceKind.INFERRED}, EpistemicOverall.INFERRED),
        ({"provenance_kind": ProvenanceKind.DERIVED}, EpistemicOverall.VERIFIED),
        ({"extraction_confidence": ConfidenceBand.MEDIUM}, EpistemicOverall.PROVISIONAL),
        ({"extraction_confidence": ConfidenceBand.UNKNOWN}, EpistemicOverall.PROVISIONAL),
        ({"interpretation_confidence": ConfidenceBand.LOW}, EpistemicOverall.PROVISIONAL),
        ({"consistency": ConsistencyState.QUALIFIED}, EpistemicOverall.VERIFIED),
        ({"consistency": ConsistencyState.RESOLVED_BY_POLICY}, EpistemicOverall.VERIFIED),
        ({"consistency": ConsistencyState.ALTERNATIVES}, EpistemicOverall.PROVISIONAL),
        ({"consistency": ConsistencyState.CONFLICTED}, EpistemicOverall.PROVISIONAL),
        ({"source_authority": None}, EpistemicOverall.PROVISIONAL),
        ({"triage": TriageState.QUEUED}, EpistemicOverall.PROVISIONAL),
        ({"triage": TriageState.PROVISIONAL}, EpistemicOverall.PROVISIONAL),
    ],
)
def test_truth_table(change: dict[str, Any], expected: EpistemicOverall) -> None:
    """One row per rule in ADR-0005, moving a single dimension away from verified."""
    assert overall_for(**change) is expected


@pytest.mark.fast
@pytest.mark.req("FR-EPI-01")
def test_an_override_beats_everything_including_a_blocked_record() -> None:
    """CLAUDE.md, DP-08, INV-12 and FR-TRI-02 all say overrides win. Compilation still refuses
    a blocked record separately (INV-04, FR-TRI-01), so nothing unsafe follows from the label."""
    assert (
        overall_for(
            provenance_kind=ProvenanceKind.OVERRIDDEN,
            triage=TriageState.BLOCKED,
            consistency=ConsistencyState.CONFLICTED,
            extraction_confidence=ConfidenceBand.LOW,
        )
        is EpistemicOverall.OVERRIDDEN
    )


@pytest.mark.fast
@pytest.mark.req("FR-EPI-01")
def test_confidence_is_never_the_sole_input_to_verified() -> None:
    """FR-EPI-01. Across all 3,200 combinations, confidence alone never reaches `verified`:
    consistency, authority and triage, none of which a model reports about itself, must agree."""
    verified = [
        inputs
        for inputs in EVERY_COMBINATION
        if overall_status(**inputs) is EpistemicOverall.VERIFIED
    ]
    assert verified, "the all-good case should be reachable"
    for inputs in verified:
        assert inputs["consistency"] in SETTLED_CONSISTENCY
        assert inputs["source_authority"] is not None
        assert inputs["triage"] is TriageState.AUTO_APPROVED
        assert inputs["extraction_confidence"] is ConfidenceBand.HIGH
        assert inputs["interpretation_confidence"] is ConfidenceBand.HIGH
        assert inputs["provenance_kind"] in {ProvenanceKind.EXTRACTED, ProvenanceKind.DERIVED}


@pytest.mark.fast
@pytest.mark.req("FR-EPI-01")
def test_the_function_is_total_and_deterministic() -> None:
    """Every combination yields a label, and the same one twice."""
    for inputs in EVERY_COMBINATION:
        first = overall_status(**inputs)
        assert first in set(EpistemicOverall)
        assert first is overall_status(**inputs)


@pytest.mark.fast
@pytest.mark.req("FR-EPI-01")
def test_blocked_survives_unless_overridden() -> None:
    """The only way past a blocked triage is an override."""
    for inputs in EVERY_COMBINATION:
        if inputs["triage"] is not TriageState.BLOCKED:
            continue
        expected = (
            EpistemicOverall.OVERRIDDEN
            if inputs["provenance_kind"] is ProvenanceKind.OVERRIDDEN
            else EpistemicOverall.BLOCKED
        )
        assert overall_status(**inputs) is expected


@pytest.mark.fast
@pytest.mark.req("FR-EPI-01")
def test_overall_is_computed_and_not_settable() -> None:
    status = EpistemicStatus(**VERIFIED)
    assert status.overall is EpistemicOverall.VERIFIED
    with pytest.raises(ValidationError):
        status.overall = EpistemicOverall.PROVISIONAL  # type: ignore[misc]


@pytest.mark.fast
@pytest.mark.req("FR-EPI-01")
def test_overall_round_trips_through_serialisation() -> None:
    """A stored IR carries `overall`, so it has to be accepted on the way back in."""
    status = EpistemicStatus(**VERIFIED)
    payload = status.model_dump(mode="json")
    assert payload["overall"] == "verified"
    assert EpistemicStatus.model_validate(payload) == status


@pytest.mark.fast
@pytest.mark.req("FR-EPI-01")
def test_a_supplied_overall_that_contradicts_the_dimensions_is_refused() -> None:
    """The failure path: `overall` comes only from the status function, and that is enforced."""
    payload = EpistemicStatus(**VERIFIED).model_dump(mode="json")
    payload["triage"] = "queued"
    with pytest.raises(ValidationError, match="overall was given as"):
        EpistemicStatus.model_validate(payload)


@pytest.mark.fast
@pytest.mark.req("FR-EPI-01")
def test_the_default_status_is_not_verified() -> None:
    """An unexamined record is provisional, never verified by omission (DP-05)."""
    assert EpistemicStatus().overall is EpistemicOverall.PROVISIONAL
