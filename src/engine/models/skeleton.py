"""The skeleton: the structure a domain is organised by (spec section 4, FR-SKL).

Elements assert nothing of their own (glossary 1.5). The tree is stored flat, each element
naming its parent, because the invariants and the M5 graph checks both want a node list and an
edge list rather than nesting. The domain's `framework_skeleton.yaml` stays nested for a person
to read; S5 flattens it on the way in.
"""

from __future__ import annotations

from pydantic import Field, model_validator

from engine.ids import DocumentId, ElementId, JudgementId, PassageId, PropositionId, SkeletonId
from engine.models.base import ExtensibleModel, IRModel
from engine.models.enums import (
    UNABLE_TO_DETERMINE,
    ElementKind,
    ElementStatus,
    Origin,
    ReconstructionMode,
)
from engine.models.epistemic import EpistemicStatus


class Outcome(IRModel):
    """One way out of a decision point, and where it leads.

    INV-03 requires every decision to carry an `unable_to_determine` outcome *with an edge*,
    so the target is what makes the outcome more than a label.
    """

    name: str = Field(min_length=1)
    target_element_id: ElementId | None = None
    description: str | None = None


class SkeletonElement(ExtensibleModel):
    """One node of the skeleton."""

    element_id: ElementId
    kind: ElementKind
    parent_element_id: ElementId | None = None
    label: str = Field(min_length=1)
    question: str | None = None
    selection_facts: tuple[str, ...] = ()
    """Fact type names that decide which branch applies."""
    expected_sources: tuple[DocumentId, ...] = ()
    outcomes: tuple[Outcome, ...] = ()
    origin: Origin
    status: ElementStatus = ElementStatus.PROPOSED
    citing_passages: tuple[PassageId, ...] = ()
    """The passages that suggested this element (FR-SKL-02)."""
    source_propositions: tuple[PropositionId, ...] = ()
    """INV-02: every node has a source proposition."""
    judgement_procedure_id: JudgementId | None = None
    """INV-08: a judgement node is decided by its procedure, never a rule set."""
    rule_set_id: str | None = None
    notes: str | None = None
    epistemic: EpistemicStatus = Field(default_factory=EpistemicStatus)

    @model_validator(mode="after")
    def _is_not_its_own_parent(self) -> SkeletonElement:
        if self.parent_element_id == self.element_id:
            raise ValueError(
                f"element {self.element_id} is its own parent. Give it the element above it, "
                f"or none if it is the objective."
            )
        return self

    @model_validator(mode="after")
    def _outcome_names_are_distinct(self) -> SkeletonElement:
        names = [outcome.name for outcome in self.outcomes]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValueError(
                f"element {self.element_id} has more than one outcome named {duplicates}. An "
                f"outcome name picks exactly one edge."
            )
        return self

    @property
    def is_decision(self) -> bool:
        """Whether INV-03 applies to this element."""
        return self.kind is ElementKind.DECISION_POINT

    def outcome(self, name: str) -> Outcome | None:
        """The outcome of this element with that name, if it has one."""
        return next((outcome for outcome in self.outcomes if outcome.name == name), None)

    @property
    def unable_to_determine(self) -> Outcome | None:
        """The outcome INV-03 requires on a decision."""
        return self.outcome(UNABLE_TO_DETERMINE)


class Skeleton(ExtensibleModel):
    """The whole structure, derived from a backbone or proposed by the Engine (FR-SKL)."""

    skeleton_id: SkeletonId
    version: int = Field(ge=1)
    mode: ReconstructionMode
    origin: Origin
    elements: tuple[SkeletonElement, ...] = ()
    epistemic: EpistemicStatus = Field(default_factory=EpistemicStatus)

    @model_validator(mode="after")
    def _element_ids_are_unique(self) -> Skeleton:
        ids = [element.element_id for element in self.elements]
        duplicates = sorted({one for one in ids if ids.count(one) > 1})
        if duplicates:
            raise ValueError(
                f"skeleton {self.skeleton_id} declares {duplicates} more than once. Every "
                f"element identifier names one element."
            )
        return self

    def element(self, element_id: str) -> SkeletonElement | None:
        """The element with that identifier, if the skeleton has one."""
        return next((one for one in self.elements if one.element_id == element_id), None)
