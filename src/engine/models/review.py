"""Review decisions and overrides (spec section 4, FR-REV-01, FR-CFL-04, FR-JDG-04).

Overrides beat automated decisions and are re-applied on re-runs while the record is unchanged
(INV-12), which is what `target_record_hash` is for: a changed record returns to the queue with
a diff rather than silently keeping a decision made about something else (FR-TRI-02).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, JsonValue, model_validator

from engine.ids import ReviewId
from engine.models.base import ExtensibleModel, IRModel
from engine.models.enums import ReviewOutcome

#: FR-REV-01: these three require a rationale.
OUTCOMES_NEEDING_A_RATIONALE = frozenset(
    {ReviewOutcome.REJECT, ReviewOutcome.MODIFY, ReviewOutcome.OVERRIDE}
)


class FieldChange(IRModel):
    """One field-level change a reviewer made (FR-REV-01)."""

    field: str = Field(min_length=1)
    before: JsonValue = None
    after: JsonValue = None


class ReviewDecision(ExtensibleModel):
    """What a reviewer decided about one record."""

    review_id: ReviewId
    target_id: str = Field(min_length=1)
    outcome: ReviewOutcome
    changes: tuple[FieldChange, ...] = ()
    rationale: str | None = None
    decided_by: str = Field(min_length=1)
    decided_at: datetime
    target_record_hash: str | None = None

    @model_validator(mode="after")
    def _the_outcomes_that_need_a_reason_have_one(self) -> ReviewDecision:
        if self.outcome in OUTCOMES_NEEDING_A_RATIONALE and not self.rationale:
            raise ValueError(
                f"review {self.review_id} is a {self.outcome.value} with no rationale. "
                f"FR-REV-01 requires one for reject, modify and override."
            )
        return self


class Override(ExtensibleModel):
    """A caller's or reviewer's replacement for an automated decision (FR-JDG-04).

    Overrides always win, and show in the response as `overridden` (FR-TOO-02).
    """

    override_id: ReviewId
    target_id: str = Field(min_length=1)
    target_kind: str = Field(min_length=1)
    """`fact`, `judgement`, `resolution` or `rule`."""
    value: JsonValue = None
    rationale: str = Field(min_length=1)
    decided_by: str = Field(min_length=1)
    decided_at: datetime
    target_record_hash: str | None = None
