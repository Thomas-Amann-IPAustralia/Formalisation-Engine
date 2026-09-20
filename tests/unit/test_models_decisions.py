"""Conflicts, gaps, policies, review, the decision log and the IR envelope (spec section 4)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from engine.models.conflict import (
    Alternative,
    Conflict,
    Gap,
    Resolution,
    SearchQuery,
    SearchRecord,
)
from engine.models.decision_log import DecisionLogEntry
from engine.models.enums import (
    ConflictKind,
    CorpusKind,
    DecidedBy,
    DecisionKind,
    GapKind,
    PolicyInputSource,
    PolicyKind,
    PolicyScope,
    ReconstructionMode,
    ReviewOutcome,
)
from engine.models.ir import IR, IR_SCHEMA_VERSION
from engine.models.policy import (
    AuthorityLevel,
    AuthorityProfile,
    ConservativeDefinition,
    DecisionPolicy,
    RiskMatrixDefinition,
)
from engine.models.review import Override, ReviewDecision

NOW = datetime(2026, 9, 20, tzinfo=UTC)
PAIR = ("PROP-0000000000000001", "PROP-0000000000000002")


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_conflict_needs_two_propositions() -> None:
    """INV-02: every conflict has a source proposition, and a conflict is between two."""
    assert Conflict(conflict_id="CFL-1", kind=ConflictKind.NUMERIC, proposition_ids=PAIR)
    with pytest.raises(ValidationError):
        Conflict(
            conflict_id="CFL-1",
            kind=ConflictKind.NUMERIC,
            proposition_ids=("PROP-0000000000000001",),
        )


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_policy_resolution_records_policy_decision_and_rationale() -> None:
    with pytest.raises(ValidationError, match="resolved by policy records"):
        Resolution(decided_by=DecidedBy.POLICY, policy_id="POL-ux-stricter-wins")
    resolved = Resolution(
        decided_by=DecidedBy.POLICY,
        policy_id="POL-ux-stricter-wins",
        decision="serve the stricter requirement",
        rationale="equal-ranked sources, impact high",
        inputs={"impact_on_users": "high", "effort_to_fix": "low"},
        hook="policy.invoked",
    )
    assert resolved.inputs["impact_on_users"] == "high"


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_an_unresolved_conflict_chooses_nothing() -> None:
    """DP-10 and FR-CFL-03: no policy means alternatives, and nothing is silently chosen."""
    with pytest.raises(ValidationError, match="carries the decision"):
        Resolution(decided_by=DecidedBy.UNRESOLVED, decision="the stricter one")
    conflict = Conflict(
        conflict_id="CFL-1",
        kind=ConflictKind.NUMERIC,
        proposition_ids=PAIR,
        alternatives=(
            Alternative(
                name="wcag",
                proposition_ids=("PROP-0000000000000001",),
                conditions="where the page targets AA",
            ),
            Alternative(
                name="style-manual",
                proposition_ids=("PROP-0000000000000002",),
                conditions="where the audience is the general public",
            ),
        ),
    )
    assert conflict.resolution.decided_by is DecidedBy.UNRESOLVED
    assert conflict.resolution.decision is None


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_each_alternative_is_named_once() -> None:
    member = Alternative(
        name="wcag", proposition_ids=("PROP-0000000000000001",), conditions="always"
    )
    with pytest.raises(ValidationError, match="more than once"):
        Conflict(
            conflict_id="CFL-1",
            kind=ConflictKind.NUMERIC,
            proposition_ids=PAIR,
            alternatives=(member, member),
        )


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_search_record_knows_whether_it_searched_anything() -> None:
    """A gap says what was searched and not found; an empty record says nothing at all."""
    assert not SearchRecord().searched_something
    assert SearchRecord(
        queries=(SearchQuery(query="heading contrast threshold", method="hybrid"),)
    ).searched_something


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_gap_carries_a_target() -> None:
    gap = Gap(gap_id="GAP-1", kind=GapKind.MISSING_THRESHOLD, target="contrast threshold")
    assert gap.search_record is None
    with pytest.raises(ValidationError):
        Gap(gap_id="GAP-1", kind=GapKind.MISSING_THRESHOLD, target="")


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_policys_definition_matches_its_kind() -> None:
    """The definition's shape is what the resolver reads, so the two cannot disagree."""
    with pytest.raises(ValidationError, match="but its definition is"):
        DecisionPolicy(
            policy_id="POL-ux-stricter-wins",
            scope=(PolicyScope.CONFLICTS,),
            kind=PolicyKind.RISK_MATRIX,
            applies_when="equal-ranked sources",
            definition=ConservativeDefinition(ordering=("not_satisfied", "satisfied")),
        )


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_the_pilots_risk_matrix_policy_round_trips() -> None:
    policy = DecisionPolicy(
        policy_id="POL-ux-stricter-wins",
        scope=(PolicyScope.CONFLICTS, PolicyScope.ALTERNATIVES),
        kind=PolicyKind.RISK_MATRIX,
        applies_when="both sources are equal-ranked and both bear on the same requirement",
        definition=RiskMatrixDefinition(
            axes={
                "impact_on_users": ("low", "moderate", "high"),
                "effort_to_fix": ("low", "moderate", "high"),
            },
            rule="choose the option that satisfies the stricter requirement",
            inputs_from={
                "impact_on_users": PolicyInputSource.JUDGEMENT,
                "effort_to_fix": PolicyInputSource.CALLER,
            },
        ),
        hooks=("policy.invoked", "policy.tradeoff_recorded"),
    )
    assert DecisionPolicy.model_validate(policy.model_dump(mode="json")) == policy


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_equal_ranks_never_resolve_by_rank() -> None:
    """FR-AUT-01, and the pilot depends on it: WCAG and the Style Manual share rank 3."""
    levels = (
        AuthorityLevel(key="normative_specification", label="WCAG", rank=1),
        AuthorityLevel(key="understanding_techniques", label="Understanding", rank=3),
        AuthorityLevel(key="style_manual", label="Style Manual", rank=3),
    )
    descriptive = AuthorityProfile(corpus_kind=CorpusKind.STANDARD, levels=levels)
    assert not descriptive.rank_resolves("normative_specification", "style_manual")

    resolving = AuthorityProfile(
        corpus_kind=CorpusKind.STANDARD, resolves_conflicts=True, levels=levels
    )
    assert resolving.rank_resolves("normative_specification", "style_manual")
    assert not resolving.rank_resolves("understanding_techniques", "style_manual")
    assert not resolving.rank_resolves("style_manual", "unknown_level")
    assert resolving.level("style_manual") is not None
    assert resolving.level("nope") is None


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_level_key_names_one_level() -> None:
    with pytest.raises(ValidationError, match="more than once"):
        AuthorityProfile(
            corpus_kind=CorpusKind.STANDARD,
            levels=(
                AuthorityLevel(key="a", label="A", rank=1),
                AuthorityLevel(key="a", label="A again", rank=2),
            ),
        )


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_reject_modify_and_override_need_a_rationale() -> None:
    for outcome in (ReviewOutcome.REJECT, ReviewOutcome.MODIFY, ReviewOutcome.OVERRIDE):
        with pytest.raises(ValidationError, match="no rationale"):
            ReviewDecision(
                review_id="REV-1",
                target_id="RULE-heading-order",
                outcome=outcome,
                decided_by="tom",
                decided_at=NOW,
            )
    assert ReviewDecision(
        review_id="REV-1",
        target_id="RULE-heading-order",
        outcome=ReviewOutcome.APPROVE,
        decided_by="tom",
        decided_at=NOW,
    )


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_an_override_records_the_record_it_was_made_about() -> None:
    """FR-TRI-02: an override is re-applied while the record is unchanged."""
    override = Override(
        override_id="REV-2",
        target_id="FACT-heading_describes_section",
        target_kind="fact",
        value=False,
        rationale="the designer checked the page",
        decided_by="ux-designer",
        decided_at=NOW,
        target_record_hash="abc123",
    )
    assert override.target_record_hash == "abc123"
    assert override.value is False


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
@pytest.mark.parametrize(
    ("kind", "field"),
    [
        (DecisionKind.POLICY_INVOCATION, "policy_id"),
        (DecisionKind.JUDGEMENT, "procedure_id"),
        (DecisionKind.OVERRIDE, "override_id"),
    ],
)
def test_a_log_entry_names_what_made_the_decision(kind: DecisionKind, field: str) -> None:
    with pytest.raises(ValidationError, match=f"names no {field}"):
        DecisionLogEntry(
            entry_id="DEC-1",
            recorded_at=NOW,
            kind=kind,
            subject_id="CFL-1",
            decision="x",
            rationale="y",
            decided_by="engine",
        )


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_log_entry_carries_its_inputs() -> None:
    """INV-12 wants the inputs, not only the outcome."""
    entry = DecisionLogEntry(
        entry_id="DEC-1",
        recorded_at=NOW,
        kind=DecisionKind.POLICY_INVOCATION,
        subject_id="CFL-1",
        policy_id="POL-ux-stricter-wins",
        inputs={"impact_on_users": "high", "effort_to_fix": "low"},
        decision="serve the stricter requirement",
        rationale="equal-ranked sources",
        decided_by="engine",
        hook="policy.invoked",
    )
    assert entry.inputs == {"impact_on_users": "high", "effort_to_fix": "low"}


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01", "NFR-INT-01")
def test_an_empty_ir_carries_its_versions_and_hashes() -> None:
    """FR-CFG-03 and NFR-DET-01: a run is reproducible from what the envelope records."""
    ir = IR(
        ir_version="0.1.0",
        run_id="RUN-20260920T0000Z",
        snapshot_id="SNAP-0000000000000001",
        domain="style-manual-wcag",
        reconstruction_mode=ReconstructionMode.FRAMEWORK,
        config_hash="c0ffee",
        policy_hash="beef",
        prompt_set_version="1",
        created_at=NOW,
    )
    assert ir.schema_version == IR_SCHEMA_VERSION
    assert ir.propositions == ()
    assert ir.skeleton is None
    payload = ir.model_dump(mode="json")
    assert payload["created_at"] == "2026-09-20T00:00:00Z"
    assert IR.model_validate(payload) == ir
