"""Judgement procedures and their run-time results (spec section 4, FR-JDG).

A judgement procedure is what an EVALUATIVE_JUDGEMENT proposition compiles to (Appendix B): a
question facts alone cannot decide, which the tool puts to a model at run time, records, and
lets a caller override (DP-08).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, JsonValue, model_validator

from engine.ids import FactTypeId, JudgementId, PropositionId
from engine.models.base import ExtensibleModel, IRModel
from engine.models.enums import UNABLE_TO_DETERMINE, ProbeCost, ProvenanceKind
from engine.models.epistemic import EpistemicStatus


class Consideration(IRModel):
    """One thing the procedure weighs, and the proposition it comes from.

    Spec section 4 says considerations are "each sourced", so the source is required: a
    judgement that weighs something no passage supports is the tool adding content (FR-TOO-03).
    """

    text: str = Field(min_length=1)
    source_proposition_id: PropositionId


class JudgementOutputSchema(IRModel):
    """The shape of an outcome. INV-03 checks that `unable_to_determine` is among them."""

    outcomes: tuple[str, ...] = Field(min_length=1)
    requires_rationale: bool = True
    requires_confidence: bool = True

    @property
    def can_decline(self) -> bool:
        """Whether this schema offers the outcome INV-03 requires."""
        return UNABLE_TO_DETERMINE in self.outcomes


class JudgementProcedure(ExtensibleModel):
    """A question the tool decides at run time (FR-JDG-01)."""

    procedure_id: JudgementId
    question: str = Field(min_length=1)
    considerations: tuple[Consideration, ...] = ()
    inputs: tuple[FactTypeId, ...] = ()
    prompt_id: str = Field(min_length=1)
    """A versioned template file under `prompts/`, never inline text (FR-CFG-03)."""
    prompt_version: int = Field(ge=1)
    output_schema: JudgementOutputSchema
    cost_class: ProbeCost = ProbeCost.CHEAP
    cache_by: tuple[str, ...] = ("artefact_hash", "inputs", "prompt_version")
    """FR-JDG-03. Replaying these three reproduces the judgement exactly (G8)."""
    source_propositions: tuple[PropositionId, ...] = ()
    """INV-02: every judgement procedure has a source proposition."""
    epistemic: EpistemicStatus = Field(default_factory=EpistemicStatus)

    @model_validator(mode="after")
    def _considerations_are_sourced(self) -> JudgementProcedure:
        unsourced = [
            consideration.text
            for consideration in self.considerations
            if not consideration.source_proposition_id
        ]
        if unsourced:
            raise ValueError(
                f"judgement procedure {self.procedure_id} weighs {unsourced} with no source "
                f"proposition. Every consideration is sourced (spec section 4)."
            )
        return self


class JudgementRecord(IRModel):
    """What a procedure actually returned, logged in full (FR-JDG-01, INV-12)."""

    procedure_id: JudgementId
    outcome: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    model: str = Field(min_length=1)
    prompt_version: int = Field(ge=1)
    inputs: dict[str, JsonValue] = Field(default_factory=dict)
    artefact_sha256: str | None = None
    provenance: ProvenanceKind = ProvenanceKind.JUDGED
    decided_at: datetime | None = None

    @model_validator(mode="after")
    def _is_judged_or_overridden(self) -> JudgementRecord:
        if self.provenance not in {ProvenanceKind.JUDGED, ProvenanceKind.OVERRIDDEN}:
            raise ValueError(
                f"judgement on {self.procedure_id} is tagged {self.provenance.value}. A "
                f"judgement is `judged`, or `overridden` where a caller replaced it "
                f"(FR-JDG-01, FR-JDG-04)."
            )
        return self
