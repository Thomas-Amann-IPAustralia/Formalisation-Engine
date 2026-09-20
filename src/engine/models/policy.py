"""Decision policies and the authority profile (spec section 4, FR-CFL-02, FR-AUT-01).

DP-10: conflicts resolve by declared policy, logged with inputs and emitting a hook. Where no
policy applies, alternatives are returned unresolved and nothing is chosen.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from engine.ids import PolicyId
from engine.models.base import ExtensibleModel, IRModel
from engine.models.enums import CorpusKind, PolicyInputSource, PolicyKind, PolicyScope


class AuthorityOrderDefinition(IRModel):
    """Rank decides, highest first. Only meaningful where the profile resolves conflicts."""

    kind: Literal["authority_order"] = "authority_order"
    order: tuple[str, ...] = Field(min_length=1)
    """Authority level keys, most authoritative first."""


class RiskMatrixDefinition(IRModel):
    """A matrix over named axes, as the pilot's POL-ux-stricter-wins uses."""

    kind: Literal["risk_matrix"] = "risk_matrix"
    axes: dict[str, tuple[str, ...]] = Field(min_length=1)
    rule: str = Field(min_length=1)
    inputs_from: dict[str, PolicyInputSource] = Field(default_factory=dict)
    defaults: dict[str, str] = Field(default_factory=dict)
    """What to assume for an axis the caller did not supply. Declared in configuration rather
    than decided in code, so DP-10's "resolve by declared policy" stays true."""


class ConservativeDefinition(IRModel):
    """An ordering, most conservative first, used when inference is off or budget is spent."""

    kind: Literal["conservative"] = "conservative"
    ordering: tuple[str, ...] = Field(min_length=1)


PolicyDefinition = Annotated[
    AuthorityOrderDefinition | RiskMatrixDefinition | ConservativeDefinition,
    Field(discriminator="kind"),
]


class DecisionPolicy(ExtensibleModel):
    """A domain's declared way to resolve conflicts and alternatives (glossary 1.5)."""

    policy_id: PolicyId
    scope: tuple[PolicyScope, ...] = Field(min_length=1)
    kind: PolicyKind
    applies_when: str = Field(min_length=1)
    definition: PolicyDefinition
    hooks: tuple[str, ...] = ()
    """Emitted on invocation (FR-CFL-02), for example `policy.invoked`."""

    @model_validator(mode="after")
    def _the_definition_matches_the_kind(self) -> DecisionPolicy:
        if self.definition.kind != self.kind.value:
            raise ValueError(
                f"policy {self.policy_id} is declared {self.kind.value} but its definition is "
                f"{self.definition.kind}. Make the two agree; the definition's shape is what "
                f"the resolver reads."
            )
        return self


class AuthorityLevel(IRModel):
    """One level in the profile. Two levels may share a rank, which makes them equal-ranked."""

    key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    document_types: tuple[str, ...] = ()
    rank: int = Field(ge=1)


class AuthorityProfile(ExtensibleModel):
    """The ordered levels a domain's documents sit in (FR-AUT-01).

    `resolves_conflicts` is what turns rank from description into policy. The pilot leaves it
    false, so WCAG and the Style Manual stay equal and a conflict between them falls through to
    the risk matrix.
    """

    corpus_kind: CorpusKind
    resolves_conflicts: bool = False
    levels: tuple[AuthorityLevel, ...] = Field(min_length=1)
    notes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _level_keys_are_unique(self) -> AuthorityProfile:
        keys = [level.key for level in self.levels]
        duplicates = sorted({key for key in keys if keys.count(key) > 1})
        if duplicates:
            raise ValueError(
                f"authority profile declares {duplicates} more than once. A level key names "
                f"one level, and documents refer to it by that key."
            )
        return self

    def level(self, key: str) -> AuthorityLevel | None:
        """The level with that key, if the profile has one. INV-06 uses this."""
        return next((level for level in self.levels if level.key == key), None)

    def rank_resolves(self, first: str, second: str) -> bool:
        """Whether rank may settle a conflict between these two levels (FR-AUT-01).

        False unless the profile declares that rank resolves conflicts, and false for
        equal-ranked levels whatever the profile says: equal ranks never resolve by rank.
        """
        if not self.resolves_conflicts:
            return False
        one, other = self.level(first), self.level(second)
        if one is None or other is None:
            return False
        return one.rank != other.rank
