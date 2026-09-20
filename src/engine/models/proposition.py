"""Propositions: the unit of truth (DP-02, spec section 4, FR-EXT)."""

from __future__ import annotations

from datetime import date

from pydantic import Field, JsonValue, model_validator

from engine.ids import ConceptId, FactTypeId, PassageId, PropositionId
from engine.models.base import ExtensibleModel, IRModel
from engine.models.enums import (
    ConditionOperator,
    NormativeForce,
    SlotResolution,
    TemporalStatus,
)
from engine.models.epistemic import EpistemicStatus


class Span(IRModel):
    """A verbatim quotation from a passage, with its offsets.

    `verified` means the text matched the passage exactly (FR-EXT-02). INV-01 requires it on
    every proposition; a mismatch rejects the proposition rather than the run (DP-04).
    """

    passage_id: PassageId
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    text: str = Field(min_length=1)
    verified: bool = False

    @model_validator(mode="after")
    def _offsets_match_the_text(self) -> Span:
        if self.end <= self.start:
            raise ValueError(
                f"span on {self.passage_id} ends at {self.end}, at or before its start "
                f"{self.start}. A span covers at least one character."
            )
        if self.end - self.start != len(self.text):
            raise ValueError(
                f"span on {self.passage_id} covers {self.end - self.start} characters but its "
                f"text is {len(self.text)} long. The offsets and the quotation disagree, which "
                f"is how a fabricated span shows up (G6); re-extract the passage."
            )
        return self


class Slot(IRModel):
    """One filled role in a proposition: actor, action, object or authority holder."""

    raw_text: str = Field(min_length=1)
    concept_id: ConceptId | None = None
    resolution: SlotResolution = SlotResolution.UNRESOLVED

    @model_validator(mode="after")
    def _confirmed_slots_name_a_concept(self) -> Slot:
        if self.resolution is SlotResolution.CONFIRMED and self.concept_id is None:
            raise ValueError(
                f"slot {self.raw_text!r} is confirmed but names no concept. A confirmed "
                f"resolution records the concept it resolved to (FR-VOC-01)."
            )
        return self


class Condition(IRModel):
    """A condition a proposition attaches to its obligation (FR-EXT-04).

    `fact_type_id` is None until a fact type exists for it; a rule compiled from such a
    condition is provisional until one is confirmed (FR-CMP-02), and INV-05 refuses a rule
    whose condition has no fact type with a provider.
    """

    raw_text: str = Field(min_length=1)
    fact_type_id: FactTypeId | None = None
    operator: ConditionOperator
    value: JsonValue = None
    negated: bool = False


class Deadline(IRModel):
    """A structured duration with the event it runs from (FR-TMP-01)."""

    duration: str = Field(min_length=1)
    """An ISO 8601 duration, such as P30D."""
    anchor_event: str = Field(min_length=1)


class TemporalClaim(IRModel):
    """When a proposition applies, and how that was established (FR-TMP-01)."""

    status: TemporalStatus = TemporalStatus.UNKNOWN
    basis: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    deadlines: tuple[Deadline, ...] = ()


class ExtractionRecord(IRModel):
    """What produced a proposition (FR-PRV-01, NFR-DET-01)."""

    model: str = Field(min_length=1)
    prompt_id: str = Field(min_length=1)
    prompt_version: int = Field(ge=1)
    request_hash: str = Field(min_length=1)


class Proposition(ExtensibleModel):
    """One structured statement from a passage (glossary 1.5)."""

    proposition_id: PropositionId
    passage_id: PassageId
    span: Span
    normative_force: NormativeForce
    force_cue: str | None = None
    """The cue that decided the force (Appendix B, FR-EXT-03)."""
    operative: bool = False
    """CAN and DESCRIPTIVE compile to a rule only when marked operative (Appendix B)."""
    actor: Slot | None = None
    action: Slot | None = None
    object: Slot | None = None
    authority_holder: Slot | None = None
    conditions: tuple[Condition, ...] = ()
    exceptions_referenced: tuple[str, ...] = ()
    temporal: TemporalClaim = Field(default_factory=TemporalClaim)
    extraction: ExtractionRecord | None = None
    epistemic: EpistemicStatus = Field(default_factory=EpistemicStatus)

    @model_validator(mode="after")
    def _span_belongs_to_the_passage(self) -> Proposition:
        if self.span.passage_id != self.passage_id:
            raise ValueError(
                f"proposition {self.proposition_id} sits in passage {self.passage_id} but its "
                f"span quotes {self.span.passage_id}. A proposition is extracted from one "
                f"passage at a time (FR-EXT-01)."
            )
        return self
