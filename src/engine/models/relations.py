"""Relations (Appendix C).

Two kinds: a proposition to a skeleton element (C.1 in backbone-led mode, C.3 in framework-led),
and a proposition to a proposition (C.2). The label sets are fixed and classification chooses
from them; there is no free-form restructuring (DP-06, FR-MAP-01).
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from engine.ids import ElementId, PropositionId
from engine.models.base import ExtensibleModel
from engine.models.enums import (
    STRUCTURAL_BACKBONE_RELATIONS,
    STRUCTURAL_FRAMEWORK_RELATIONS,
    BackboneRelation,
    FrameworkRelation,
    PropositionRelation,
    RelationMethod,
)
from engine.models.epistemic import EpistemicStatus


class BackboneMapping(ExtensibleModel):
    """A proposition mapped to a step, in backbone-led mode (Appendix C.1)."""

    mode: Literal["backbone"] = "backbone"
    proposition_id: PropositionId
    element_id: ElementId
    relation: BackboneRelation
    rationale: str = Field(min_length=1)
    method: RelationMethod
    epistemic: EpistemicStatus = Field(default_factory=EpistemicStatus)

    @property
    def is_structural(self) -> bool:
        """Structural relations go to triage (FR-MAP-01)."""
        return self.relation in STRUCTURAL_BACKBONE_RELATIONS


class FrameworkMapping(ExtensibleModel):
    """A proposition mapped to an element, in framework-led mode (Appendix C.3)."""

    mode: Literal["framework"] = "framework"
    proposition_id: PropositionId
    element_id: ElementId
    relation: FrameworkRelation
    rationale: str = Field(min_length=1)
    method: RelationMethod
    epistemic: EpistemicStatus = Field(default_factory=EpistemicStatus)

    @property
    def is_structural(self) -> bool:
        """Structural relations go to triage (FR-MAP-01)."""
        return self.relation in STRUCTURAL_FRAMEWORK_RELATIONS


#: Which label set applies depends on the reconstruction mode, so `mode` discriminates. Several
#: labels (`contradicts`, `defines_term`, `context_only`, `no_relation`) appear in both sets,
#: which is exactly why the union cannot be left to guess.
PropositionElementRelation = Annotated[
    BackboneMapping | FrameworkMapping, Field(discriminator="mode")
]


class PropositionPropositionRelation(ExtensibleModel):
    """A relation between two propositions (Appendix C.2).

    FR-REC-01: EXCEPTS, QUALIFIES, SUPERSEDES, ELABORATES and ALTERNATIVES are all considered
    before CONTRADICTS, and a CONTRADICTS pair goes to a panel (FR-CFL-01).
    """

    source_proposition_id: PropositionId
    target_proposition_id: PropositionId
    relation: PropositionRelation
    rationale: str = Field(min_length=1)
    method: RelationMethod
    epistemic: EpistemicStatus = Field(default_factory=EpistemicStatus)
