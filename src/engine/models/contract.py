"""The tool contract (spec Appendix E).

DP-11: one contract, fixed first and shared by every domain. The shape here is Appendix E's;
a domain adds content, never fields. One implementation stands behind three surfaces, so these
models are the Python surface's types as well as the MCP and CLI payloads (FR-TOO-01).

The field names match the appendix exactly. The one addition is an optional `passage_id` on a
citation: INV-10 requires every assertion's citation to *resolve to a passage*, and `document`
plus `anchor` are how a person reads a citation, not how a machine resolves one. It is optional
and additive, so an existing consumer is unaffected (ADR-0005).
"""

from __future__ import annotations

from datetime import date
from typing import Final, Literal

from pydantic import Field, JsonValue

from engine.ids import JudgementId, PassageId, PolicyId, ProbeId, RuleId, SnapshotId
from engine.models.base import IRModel
from engine.models.enums import (
    AssertionStatus,
    EpistemicOverall,
    FactProvenance,
    ProbeCost,
    ProviderKind,
    RequestMode,
)

#: Semantic. A breaking change updates every consumer (Appendix E).
CONTRACT_VERSION: Final = "1.0"

#: FR-TOO-02 requires this note on every response.
BEST_EFFORT_NOTE: Final = (
    "Best-effort approximation of the sources; status is attached to every item."
)


class ArtefactInput(IRModel):
    """An artefact the caller offers for probing."""

    kind: str = Field(min_length=1)
    path: str | None = None
    sha256: str | None = None


class CallerFact(IRModel):
    """A fact the caller supplies."""

    value: JsonValue = None
    source: Literal["caller"] = "caller"


class CallerOverride(IRModel):
    """A value the caller insists on. Overrides win and show as `overridden` (FR-JDG-04)."""

    value: JsonValue = None
    source: Literal["override"] = "override"
    by: str = Field(min_length=1)


class RequestOptions(IRModel):
    """FR-TOO-04: the tool honours all four."""

    mode: RequestMode = RequestMode.ANSWER
    no_inference: bool = False
    max_probe_cost: ProbeCost = ProbeCost.CHEAP
    as_at: date | None = None
    """Evaluation accepts an "as at" date (FR-TMP-01, FR-QRY-04)."""


class ToolRequest(IRModel):
    """Appendix E request. Facts and overrides are keyed by fact type name."""

    contract_version: str = CONTRACT_VERSION
    objective: str = Field(min_length=1)
    artefacts: tuple[ArtefactInput, ...] = ()
    facts: dict[str, CallerFact] = Field(default_factory=dict)
    overrides: dict[str, CallerOverride] = Field(default_factory=dict)
    options: RequestOptions = Field(default_factory=RequestOptions)


class PackageRef(IRModel):
    """Which package answered (FR-TOO-01)."""

    domain: str = Field(min_length=1)
    ir_version: str = Field(min_length=1)
    snapshot_id: SnapshotId


class Citation(IRModel):
    """Where an assertion comes from (INV-10, FR-TOO-03).

    `quote` is absent for a `reference` source, which keeps anchor and link but stores no text
    (FR-ING-04, INV-11, G11).
    """

    document: str = Field(min_length=1)
    anchor: str = Field(min_length=1)
    quote: str | None = None
    passage_id: PassageId | None = None
    link: str | None = None


class FactUsed(IRModel):
    """A fact an answer rested on, with its provenance (FR-QRY-03)."""

    fact_type: str = Field(min_length=1)
    value: JsonValue = None
    source: FactProvenance
    probe_id: ProbeId | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class AppliesItem(IRModel):
    """A rule that applies, with its status and the state of the claim (FR-TOO-02)."""

    rule_id: RuleId
    statement: str = Field(min_length=1)
    status: AssertionStatus
    state: EpistemicOverall
    facts_used: tuple[FactUsed, ...] = ()
    citations: tuple[Citation, ...] = ()


class AdvisoryItem(IRModel):
    """Guidance, never an executable obligation (G3)."""

    rule_id: RuleId
    statement: str = Field(min_length=1)
    citations: tuple[Citation, ...] = ()


class JudgementItem(IRModel):
    """A judgement made at run time, or the override that replaced it (FR-JDG-01, G7)."""

    procedure_id: JudgementId
    question: str = Field(min_length=1)
    outcome: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    source: Literal["judged", "overridden"] = "judged"
    model: str | None = None
    prompt_version: int | None = Field(default=None, ge=1)
    citations: tuple[Citation, ...] = ()


class PolicyDecisionItem(IRModel):
    """A policy invocation, with what it was given (FR-CFL-02, DP-10)."""

    policy_id: PolicyId
    inputs: dict[str, JsonValue] = Field(default_factory=dict)
    decision: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    hook: str | None = None


class HowToObtain(IRModel):
    """How the caller could settle a fact the tool is missing (G2, FR-QRY-01)."""

    kind: ProviderKind
    question: str | None = None
    probe_id: ProbeId | None = None
    artefact_kind: str | None = None


class NeededFact(IRModel):
    """A fact that would resolve an undetermined item."""

    fact_type: str = Field(min_length=1)
    how_to_obtain: HowToObtain


class UndeterminedItem(IRModel):
    """Something the tool could not settle, and what would settle it.

    The evaluator never fills a missing fact; it says what it needs (FR-QRY-01, G2).
    """

    item: str = Field(min_length=1)
    needs: tuple[NeededFact, ...] = Field(min_length=1)


class AlternativeOption(IRModel):
    """One option of an unresolved alternatives set (FR-CFL-03)."""

    name: str = Field(min_length=1)
    conditions: str = Field(min_length=1)
    citations: tuple[Citation, ...] = ()


class AlternativesItem(IRModel):
    """Alternatives returned with their conditions, nothing chosen (DP-10, G4)."""

    question: str = Field(min_length=1)
    options: tuple[AlternativeOption, ...] = Field(min_length=2)
    unresolved_because: str = Field(min_length=1)


class LimitItem(IRModel):
    """A gap or a blocked record, carried into the response (FR-GAP-02)."""

    kind: str = Field(min_length=1)
    id: str = Field(min_length=1)
    effect: str = Field(min_length=1)


class StatusSummary(IRModel):
    """Counts by state, so provisional and verified content stay distinguishable
    (FR-TOO-02)."""

    verified: int = Field(default=0, ge=0)
    provisional: int = Field(default=0, ge=0)
    inferred: int = Field(default=0, ge=0)
    judged: int = Field(default=0, ge=0)
    overridden: int = Field(default=0, ge=0)
    advisory: int = Field(default=0, ge=0)


class ToolResponse(IRModel):
    """Appendix E response."""

    contract_version: str = CONTRACT_VERSION
    package: PackageRef
    objective: str = Field(min_length=1)
    applies: tuple[AppliesItem, ...] = ()
    advisory: tuple[AdvisoryItem, ...] = ()
    judgements: tuple[JudgementItem, ...] = ()
    policy_decisions: tuple[PolicyDecisionItem, ...] = ()
    undetermined: tuple[UndeterminedItem, ...] = ()
    alternatives: tuple[AlternativesItem, ...] = ()
    limits: tuple[LimitItem, ...] = ()
    status_summary: StatusSummary = Field(default_factory=StatusSummary)
    note: str = BEST_EFFORT_NOTE
    plan: JsonValue = None
    """Appendix E shows `null` and FR-TOO-04 says the tool honours `mode: plan`, but neither
    specifies a plan's shape. Left untyped rather than invented; see ADR-0005."""

    @property
    def assertions_with_citations(self) -> tuple[tuple[str, tuple[Citation, ...]], ...]:
        """Every item INV-10 calls an assertion, with the citations it carries."""
        return (
            *((item.rule_id, item.citations) for item in self.applies),
            *((item.rule_id, item.citations) for item in self.advisory),
            *((item.procedure_id, item.citations) for item in self.judgements),
            *(
                (f"{alternatives.question}::{option.name}", option.citations)
                for alternatives in self.alternatives
                for option in alternatives.options
            ),
        )
