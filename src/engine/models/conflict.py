"""Conflicts, alternatives and gaps (spec section 4, FR-CFL, FR-GAP).

A gap says what was searched and not found. It never says the information does not exist, which
is why the search record, not the absence, is the evidence (spec section 4).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, JsonValue, model_validator

from engine.ids import ConflictId, DocumentId, GapId, PassageId, PolicyId, PropositionId
from engine.models.base import ExtensibleModel, IRModel
from engine.models.enums import ConflictKind, ConflictStatus, DecidedBy, GapKind, GapStatus
from engine.models.epistemic import EpistemicStatus


class Alternative(IRModel):
    """One supportable position on a question, where no policy chose between them
    (FR-CFL-03)."""

    name: str = Field(min_length=1)
    proposition_ids: tuple[PropositionId, ...] = Field(min_length=1)
    conditions: str = Field(min_length=1)
    """When this option applies. Returned to the caller so nothing is silently chosen."""
    source_documents: tuple[DocumentId, ...] = ()


class Resolution(IRModel):
    """How a conflict was resolved, or that it was not (FR-CFL-02, DP-10)."""

    decided_by: DecidedBy = DecidedBy.UNRESOLVED
    policy_id: PolicyId | None = None
    inputs: dict[str, JsonValue] = Field(default_factory=dict)
    decision: str | None = None
    rationale: str | None = None
    decided_at: datetime | None = None
    hook: str | None = None

    @model_validator(mode="after")
    def _a_policy_decision_names_its_policy_and_reasoning(self) -> Resolution:
        if self.decided_by is DecidedBy.POLICY and not (
            self.policy_id and self.decision and self.rationale
        ):
            raise ValueError(
                "a conflict resolved by policy records the policy, the decision and the "
                "rationale (FR-CFL-02). One of the three is missing."
            )
        return self

    @model_validator(mode="after")
    def _an_unresolved_conflict_chose_nothing(self) -> Resolution:
        if self.decided_by is DecidedBy.UNRESOLVED and self.decision is not None:
            raise ValueError(
                f"an unresolved conflict carries the decision {self.decision!r}. Where no "
                f"policy applies, nothing is chosen and the alternatives are returned "
                f"(FR-CFL-03, DP-10)."
            )
        return self


class Conflict(ExtensibleModel):
    """Two or more propositions that cannot both be followed (FR-CFL-01)."""

    conflict_id: ConflictId
    kind: ConflictKind
    proposition_ids: tuple[PropositionId, ...] = Field(min_length=2)
    """INV-02: every conflict has a source proposition. A conflict needs at least two."""
    resolution: Resolution = Field(default_factory=Resolution)
    alternatives: tuple[Alternative, ...] = ()
    status: ConflictStatus = ConflictStatus.OPEN
    panel_votes: tuple[str, ...] = ()
    """FR-CFL-01: a CONTRADICTS pair goes to a panel and disagreement is recorded."""
    epistemic: EpistemicStatus = Field(default_factory=EpistemicStatus)

    @model_validator(mode="after")
    def _alternatives_are_distinct(self) -> Conflict:
        names = [alternative.name for alternative in self.alternatives]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValueError(
                f"conflict {self.conflict_id} offers {duplicates} more than once. Each "
                f"alternative is one position, named once."
            )
        return self


class SearchQuery(IRModel):
    """One retrieval call made while looking for what a gap is missing (FR-GAP-01)."""

    query: str = Field(min_length=1)
    method: str = Field(min_length=1)
    """`fts5`, `embedding` or `hybrid` (FR-RET-01)."""
    filters: dict[str, JsonValue] = Field(default_factory=dict)


class SearchCandidate(IRModel):
    """Something the search turned up, and what was made of it."""

    passage_id: PassageId
    score: float | None = None
    verdict: str = Field(min_length=1)
    rationale: str | None = None


class SearchRecord(IRModel):
    """What was searched and what came back. The evidence behind a gap."""

    queries: tuple[SearchQuery, ...] = ()
    candidates: tuple[SearchCandidate, ...] = ()
    calls_spent: int = Field(default=0, ge=0)
    budget_exhausted: bool = False

    @property
    def searched_something(self) -> bool:
        """What INV-02 asks of a gap's search record."""
        return bool(self.queries)


class Gap(ExtensibleModel):
    """Something the corpus does not settle (FR-GAP-01, FR-GAP-02)."""

    gap_id: GapId
    kind: GapKind
    target: str = Field(min_length=1)
    """What is missing, in words."""
    target_id: str | None = None
    """The record the gap is about, where there is one. INV-02 checks it resolves."""
    search_record: SearchRecord | None = None
    """INV-02: every gap has a search record, and the record says what was searched."""
    status: GapStatus = GapStatus.OPEN
    effect: str | None = None
    """How this gap shows up as a limit in the package (FR-GAP-02)."""
    epistemic: EpistemicStatus = Field(default_factory=EpistemicStatus)
