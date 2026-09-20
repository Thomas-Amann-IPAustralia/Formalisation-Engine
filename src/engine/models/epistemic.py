"""Epistemic status: the status that travels with every claim (DP-05, spec section 4).

`overall` is a deterministic function of the other dimensions and is never set by hand. The
spec requires the function but does not define it; the table below is ADR-0005's, chosen to be
conservative — nothing reaches `verified` unless every dimension agrees.
"""

from __future__ import annotations

from typing import Any, Final

from pydantic import ValidatorFunctionWrapHandler, computed_field, model_validator

from engine.models.base import ExtensibleModel
from engine.models.enums import (
    ConfidenceBand,
    ConsistencyState,
    EpistemicOverall,
    ProvenanceKind,
    TriageState,
)

_ABSENT: Final = object()

#: Consistency states that do not by themselves hold a record back. `alternatives` and
#: `conflicted` do, because in both the Engine is knowingly carrying more than one position.
SETTLED_CONSISTENCY: Final[frozenset[ConsistencyState]] = frozenset(
    {
        ConsistencyState.CONSISTENT,
        ConsistencyState.QUALIFIED,
        ConsistencyState.RESOLVED_BY_POLICY,
    }
)


def overall_status(
    *,
    extraction_confidence: ConfidenceBand,
    interpretation_confidence: ConfidenceBand,
    source_authority: str | None,
    consistency: ConsistencyState,
    provenance_kind: ProvenanceKind,
    triage: TriageState,
) -> EpistemicOverall:
    """The one function that decides `overall` (spec section 4, FR-EPI-01).

    The rules, in order, first match wins:

    1. An override wins over everything. CLAUDE.md, DP-08 and INV-12 all say so, and FR-TRI-02
       puts overrides ahead of triage. A blocked record still never compiles, but that is
       enforced separately at compile time (INV-04, FR-TRI-01), not by relabelling it here.
    2. A blocked record is `blocked`. Triage blocks only when an invariant failed (FR-TRI-01).
    3. A judged record is `judged` and an inferred one `inferred`, so that DP-05's distinctions
       survive into the response whatever the confidence attached to them.
    4. Otherwise `verified` only when every remaining dimension is good: both confidences high,
       consistency settled, an authority level established, and triage auto-approved.
    5. Anything less is `provisional`: usable, with the uncertainty attached.

    Rule 4 is what keeps FR-EPI-01's "LLM self-reported confidence is never the sole input"
    true. Confidence alone cannot reach `verified`; consistency, authority and triage, none of
    which a model reports about itself, must agree as well.
    """
    if provenance_kind is ProvenanceKind.OVERRIDDEN:
        return EpistemicOverall.OVERRIDDEN
    if triage is TriageState.BLOCKED:
        return EpistemicOverall.BLOCKED
    if provenance_kind is ProvenanceKind.JUDGED:
        return EpistemicOverall.JUDGED
    if provenance_kind is ProvenanceKind.INFERRED:
        return EpistemicOverall.INFERRED
    settled = (
        extraction_confidence is ConfidenceBand.HIGH
        and interpretation_confidence is ConfidenceBand.HIGH
        and consistency in SETTLED_CONSISTENCY
        and source_authority is not None
        and triage is TriageState.AUTO_APPROVED
    )
    return EpistemicOverall.VERIFIED if settled else EpistemicOverall.PROVISIONAL


class EpistemicStatus(ExtensibleModel):
    """The status carried by every record (spec section 4, DP-05)."""

    extraction_confidence: ConfidenceBand = ConfidenceBand.UNKNOWN
    interpretation_confidence: ConfidenceBand = ConfidenceBand.UNKNOWN
    source_authority: str | None = None
    """The authority level key of the source document, or None where none is established."""
    consistency: ConsistencyState = ConsistencyState.CONSISTENT
    provenance_kind: ProvenanceKind = ProvenanceKind.EXTRACTED
    triage: TriageState = TriageState.QUEUED

    @computed_field  # type: ignore[prop-decorator]
    @property
    def overall(self) -> EpistemicOverall:
        """Computed, never stored (spec section 4, `.claude/rules/models.md`)."""
        return overall_status(
            extraction_confidence=self.extraction_confidence,
            interpretation_confidence=self.interpretation_confidence,
            source_authority=self.source_authority,
            consistency=self.consistency,
            provenance_kind=self.provenance_kind,
            triage=self.triage,
        )

    @model_validator(mode="wrap")
    @classmethod
    def _overall_is_not_an_input(
        cls, data: Any, handler: ValidatorFunctionWrapHandler
    ) -> EpistemicStatus:
        """Accept a serialised `overall` on the way back in, but only if it is the right one.

        `overall` is written on dump, so a stored IR round-trips through here and `extra`
        would otherwise reject it. Dropping it silently would let a hand-written record claim
        a status its dimensions do not support; checking it instead is what makes "overall
        comes only from the status function" enforceable rather than merely stated.
        """
        supplied: Any = _ABSENT
        if isinstance(data, dict) and "overall" in data:
            supplied = data["overall"]
            data = {key: value for key, value in data.items() if key != "overall"}
        result: EpistemicStatus = handler(data)
        if supplied is not _ABSENT and str(supplied) != result.overall.value:
            raise ValueError(
                f"overall was given as {supplied!r} but this record's dimensions make it "
                f"{result.overall.value!r}. Remove the field and let the status function "
                f"compute it, or correct the dimensions it is drawn from."
            )
        return result
