"""The append-only decision log (INV-12, FR-CFL-02, FR-JDG-01, FR-TOO-05).

Every policy invocation, judgement and override lands here with its inputs. Written as JSON
lines to the sink the domain configures, and carried in the IR so the invariant can be checked
on a stored run.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, JsonValue, model_validator

from engine.ids import DecisionId, JudgementId, PolicyId, ReviewId, RunId
from engine.models.base import IRModel
from engine.models.enums import DecisionKind


class DecisionLogEntry(IRModel):
    """One decision, with everything needed to reproduce and to audit it."""

    entry_id: DecisionId
    recorded_at: datetime
    kind: DecisionKind
    subject_id: str = Field(min_length=1)
    """The record the decision was about."""
    inputs: dict[str, JsonValue] = Field(default_factory=dict)
    """INV-12: the log carries the inputs, not only the outcome."""
    decision: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    decided_by: str = Field(min_length=1)
    run_id: RunId | None = None
    stage: str | None = None
    policy_id: PolicyId | None = None
    procedure_id: JudgementId | None = None
    override_id: ReviewId | None = None
    hook: str | None = None

    @model_validator(mode="after")
    def _names_what_made_the_decision(self) -> DecisionLogEntry:
        required = {
            DecisionKind.POLICY_INVOCATION: ("policy_id", self.policy_id),
            DecisionKind.JUDGEMENT: ("procedure_id", self.procedure_id),
            DecisionKind.OVERRIDE: ("override_id", self.override_id),
        }
        field, value = required[self.kind]
        if value is None:
            raise ValueError(
                f"decision log entry {self.entry_id} is a {self.kind.value} but names no "
                f"{field}. INV-12 wants to know what made the decision, not only that one "
                f"was made."
            )
        return self
