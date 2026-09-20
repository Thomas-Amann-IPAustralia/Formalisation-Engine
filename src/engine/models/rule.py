"""Rules (spec section 4, FR-CMP).

Conditions are an AND/OR/NOT tree over fact types. Exceptions are defeat relations, never
rewritten conditions (FR-CMP-02), and members of an alternatives set never defeat each other
(INV-07): a rule carries the rules it defeats, and the alternatives set it belongs to, if any.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, JsonValue, model_validator

from engine.ids import ConflictId, FactTypeId, PropositionId, RuleId
from engine.models.base import ExtensibleModel, IRModel
from engine.models.enums import ConditionOperator, Executability, PriorityBasis
from engine.models.epistemic import EpistemicStatus
from engine.models.proposition import TemporalClaim


class FactCondition(IRModel):
    """A leaf: one comparison against one fact type."""

    op: Literal["fact"] = "fact"
    fact_type_id: FactTypeId
    operator: ConditionOperator
    value: JsonValue = None
    negated: bool = False


class AllOf(IRModel):
    """Every operand must hold."""

    op: Literal["all_of"] = "all_of"
    operands: tuple[RuleCondition, ...] = Field(min_length=1)


class AnyOf(IRModel):
    """At least one operand must hold."""

    op: Literal["any_of"] = "any_of"
    operands: tuple[RuleCondition, ...] = Field(min_length=1)


class NotCondition(IRModel):
    """The operand must not hold. Three-valued, so UNKNOWN negates to UNKNOWN (FR-QRY-01)."""

    op: Literal["not"] = "not"
    operand: RuleCondition


RuleCondition = Annotated[FactCondition | AllOf | AnyOf | NotCondition, Field(discriminator="op")]


def fact_types_in(condition: RuleCondition | None) -> frozenset[str]:
    """Every fact type the condition tree references. INV-05 checks each has a provider."""
    if condition is None:
        return frozenset()
    if isinstance(condition, FactCondition):
        return frozenset({condition.fact_type_id})
    if isinstance(condition, NotCondition):
        return fact_types_in(condition.operand)
    return frozenset().union(*(fact_types_in(operand) for operand in condition.operands))


class Conclusion(IRModel):
    """What a rule concludes. A DEFINITIONAL proposition compiles to a fact derivation, which
    is a rule whose conclusion sets a fact (FR-CMP-01)."""

    statement: str = Field(min_length=1)
    derives_fact_type_id: FactTypeId | None = None
    derived_value: JsonValue = None


class Defeat(IRModel):
    """One rule defeating another, with why (spec section 4).

    The defeating rule is the rule that carries this, so only the defeated one is named.
    """

    defeated_rule_id: RuleId
    priority_basis: PriorityBasis
    rationale: str = Field(min_length=1)


class Rule(ExtensibleModel):
    """A compiled obligation, permission or derivation."""

    rule_id: RuleId
    rule_set_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    conditions: RuleCondition | None = None
    conclusion: Conclusion
    defeats: tuple[Defeat, ...] = ()
    alternatives_set_id: ConflictId | None = None
    """The conflict this rule is one alternative of, where no policy resolved it (FR-CFL-03)."""
    source_propositions: tuple[PropositionId, ...] = ()
    """INV-02: every rule has a source proposition. INV-04 checks what force it came from."""
    advisory: bool = False
    """Whether this is guidance rather than an obligation. SHOULD and SHOULD_NOT compile here,
    and INV-04 refuses any other force. This is the flag that keeps guidance out of `applies`
    (G3); `executability` below is a different question and must not be read as this one."""
    temporal: TemporalClaim = Field(default_factory=TemporalClaim)
    executability: Executability = Executability.EXECUTABLE
    """Whether the rule is live or held back, which is about freshness, not about force: a rule
    freezes on an unresolved gap, an unresolved condition or a blocked source (FR-CMP-02). An
    advisory note is normally `executable`, meaning nothing is holding it back; it still
    answers as advisory, because `advisory` decides that."""
    frozen_reason: str | None = None
    epistemic: EpistemicStatus = Field(default_factory=EpistemicStatus)

    @model_validator(mode="after")
    def _a_frozen_rule_says_why(self) -> Rule:
        if self.executability is Executability.FROZEN and not self.frozen_reason:
            raise ValueError(
                f"rule {self.rule_id} is frozen without a reason. FR-CMP-02 freezes a rule only "
                f"on an unresolved gap, an unresolved condition or a blocked source; record "
                f"which in frozen_reason."
            )
        return self

    @model_validator(mode="after")
    def _does_not_defeat_itself(self) -> Rule:
        if any(defeat.defeated_rule_id == self.rule_id for defeat in self.defeats):
            raise ValueError(
                f"rule {self.rule_id} defeats itself, which is a cycle of length one "
                f"(INV-07). An exception is a separate rule that defeats this one."
            )
        return self

    @property
    def fact_types_used(self) -> frozenset[str]:
        """Every fact type this rule's conditions reference (INV-05)."""
        return fact_types_in(self.conditions)


AllOf.model_rebuild()
AnyOf.model_rebuild()
NotCondition.model_rebuild()
