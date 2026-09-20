"""The Appendix D invariants, INV-01 to INV-12.

Every invariant gets both paths: an IR that satisfies it, and one changed in a single way that
does not. DP-04 governs the shape of every assertion here: a violation is returned, never
raised, so that the record is blocked and the run carries on.
"""

from __future__ import annotations

import pytest

from engine.models.conflict import Resolution, SearchRecord
from engine.models.contract import (
    AdvisoryItem,
    AppliesItem,
    Citation,
    PackageRef,
    ToolResponse,
)
from engine.models.enums import (
    UNABLE_TO_DETERMINE,
    AssertionStatus,
    ConflictStatus,
    DecidedBy,
    DecisionKind,
    ElementKind,
    EpistemicOverall,
    LicenceClass,
    NormativeForce,
    PriorityBasis,
    ProviderKind,
    ReconstructionMode,
    TriageState,
)
from engine.models.epistemic import EpistemicStatus
from engine.models.facts import ArtefactRef, ProbeResult
from engine.models.invariants import (
    INVARIANTS,
    IRIndex,
    check_ir,
    check_probe_result,
    check_record,
    check_tool_response,
)
from engine.models.judgement import JudgementOutputSchema
from engine.models.proposition import Span
from engine.models.review import Override
from engine.models.rule import Defeat
from engine.models.skeleton import Outcome, SkeletonElement
from tests.unit.ir_builders import (
    NOW,
    ORDER_QUOTE,
    ORDER_TEXT,
    PAS_ORDER,
    PROP_ORDER,
    PROP_SHORT,
    SHORT_TEXT,
    document,
    fact_type,
    gap,
    order_rule,
    passage,
    policy_log_entry,
    procedure,
    proposition,
    resolved_conflict,
    short_rule,
    skeleton,
    valid_ir,
)


def ids_of(ir_changes: dict[str, object]) -> set[str]:
    """The invariant identifiers violated by an IR built with these changes."""
    return {violation.invariant_id for violation in check_ir(valid_ir(**ir_changes))}


@pytest.mark.fast
@pytest.mark.req(
    "INV-01",
    "INV-02",
    "INV-03",
    "INV-04",
    "INV-05",
    "INV-06",
    "INV-07",
    "INV-08",
    "INV-09",
    "INV-10",
    "INV-11",
    "INV-12",
)
def test_the_registry_covers_appendix_d_and_nothing_else() -> None:
    assert set(INVARIANTS) == {f"INV-{number:02d}" for number in range(1, 13)}
    for invariant_id, spec in INVARIANTS.items():
        assert spec.invariant_id == invariant_id
        assert spec.text and spec.record_kinds


@pytest.mark.fast
@pytest.mark.req(
    "INV-01",
    "INV-02",
    "INV-03",
    "INV-04",
    "INV-05",
    "INV-06",
    "INV-07",
    "INV-08",
    "INV-09",
    "INV-10",
    "INV-11",
    "INV-12",
)
def test_a_well_formed_ir_violates_nothing() -> None:
    assert check_ir(valid_ir()) == ()


@pytest.mark.fast
@pytest.mark.req("INV-01")
def test_inv_01_an_unverified_span_is_a_violation() -> None:
    unverified = proposition(
        PROP_ORDER, PAS_ORDER, ORDER_TEXT, ORDER_QUOTE, NormativeForce.MUST_NOT
    ).model_copy(
        update={
            "span": Span(
                passage_id=PAS_ORDER,
                start=ORDER_TEXT.index(ORDER_QUOTE),
                end=ORDER_TEXT.index(ORDER_QUOTE) + len(ORDER_QUOTE),
                text=ORDER_QUOTE,
                verified=False,
            )
        }
    )
    ir = valid_ir(
        propositions=(
            unverified,
            proposition(
                PROP_SHORT,
                "PAS-0a1b2c3d4e5f6072",
                SHORT_TEXT,
                "should be short",
                NormativeForce.SHOULD,
            ),
        )
    )
    violations = [one for one in check_ir(ir) if one.invariant_id == "INV-01"]
    assert len(violations) == 1
    assert "unverified span" in violations[0].message
    assert violations[0].record_id == PROP_ORDER


@pytest.mark.fast
@pytest.mark.req("INV-01")
def test_inv_01_a_span_that_is_not_verbatim_is_a_violation() -> None:
    """A quotation the passage does not contain at those offsets is a fabricated span (G6)."""
    changed = passage(PAS_ORDER, "Heading levels may be skipped freely.", "headings")
    violations = [
        one
        for one in check_ir(
            valid_ir(passages=(changed, passage("PAS-0a1b2c3d4e5f6072", SHORT_TEXT, "headings")))
        )
        if one.invariant_id == "INV-01"
    ]
    assert violations and "not verbatim" in violations[0].remedy


@pytest.mark.fast
@pytest.mark.req("INV-02")
def test_inv_02_a_rule_with_no_source_proposition_is_a_violation() -> None:
    assert "INV-02" not in ids_of({})
    violations = [
        one
        for one in check_ir(valid_ir(rules=(order_rule(source_propositions=()), short_rule())))
        if one.invariant_id == "INV-02"
    ]
    assert len(violations) == 1
    assert "no source proposition" in violations[0].message


@pytest.mark.fast
@pytest.mark.req("INV-02")
def test_inv_02_a_source_proposition_that_is_not_in_the_ir_is_a_violation() -> None:
    violations = [
        one
        for one in check_ir(
            valid_ir(
                rules=(order_rule(source_propositions=("PROP-ffffffffffffffff",)), short_rule())
            )
        )
        if one.invariant_id == "INV-02"
    ]
    assert violations and "is not in the IR" in violations[0].message


@pytest.mark.fast
@pytest.mark.req("INV-02")
def test_inv_02_a_gap_needs_a_search_record_that_searched_something() -> None:
    assert "INV-02" in {
        one.invariant_id for one in check_ir(valid_ir(gaps=(gap(search_record=None),)))
    }
    empty = [
        one
        for one in check_ir(valid_ir(gaps=(gap(search_record=SearchRecord()),)))
        if one.invariant_id == "INV-02"
    ]
    assert empty and "no queries" in empty[0].message


@pytest.mark.fast
@pytest.mark.req("INV-02")
def test_inv_02_a_gap_target_must_resolve() -> None:
    violations = [
        one
        for one in check_ir(valid_ir(gaps=(gap(target_id="RULE-does-not-exist"),)))
        if one.invariant_id == "INV-02"
    ]
    assert violations and "not in the IR" in violations[0].message
    assert not [
        one
        for one in check_ir(valid_ir(gaps=(gap(target_id="RULE-heading-order"),)))
        if one.invariant_id == "INV-02"
    ]


@pytest.mark.fast
@pytest.mark.req("INV-03")
def test_inv_03_a_decision_without_unable_to_determine_is_a_violation() -> None:
    elements = tuple(
        one.model_copy(
            update={"outcomes": tuple(o for o in one.outcomes if o.name != UNABLE_TO_DETERMINE)}
        )
        if one.kind is ElementKind.DECISION_POINT
        else one
        for one in skeleton().elements
    )
    violations = [
        one
        for one in check_ir(valid_ir(skeleton=skeleton(elements=elements)))
        if one.invariant_id == "INV-03"
    ]
    assert len(violations) == 1
    assert UNABLE_TO_DETERMINE in violations[0].message


@pytest.mark.fast
@pytest.mark.req("INV-03")
def test_inv_03_the_outcome_needs_an_edge_that_resolves() -> None:
    def with_outcome(target: str | None) -> tuple[SkeletonElement, ...]:
        return tuple(
            one.model_copy(
                update={
                    "outcomes": tuple(
                        Outcome(name=o.name, target_element_id=target)
                        if o.name == UNABLE_TO_DETERMINE
                        else o
                        for o in one.outcomes
                    )
                }
            )
            if one.kind is ElementKind.DECISION_POINT
            else one
            for one in skeleton().elements
        )

    no_edge = [
        one
        for one in check_ir(valid_ir(skeleton=skeleton(elements=with_outcome(None))))
        if one.invariant_id == "INV-03"
    ]
    assert no_edge and "with no edge out of it" in no_edge[0].message

    dangling = [
        one
        for one in check_ir(valid_ir(skeleton=skeleton(elements=with_outcome("EL-nowhere"))))
        if one.invariant_id == "INV-03"
    ]
    assert dangling and "not in the skeleton" in dangling[0].message


@pytest.mark.fast
@pytest.mark.req("INV-03")
def test_inv_03_a_judgement_procedure_must_be_able_to_decline() -> None:
    violations = [
        one
        for one in check_ir(
            valid_ir(
                judgement_procedures=(
                    procedure(output_schema=JudgementOutputSchema(outcomes=("yes", "no"))),
                )
            )
        )
        if one.invariant_id == "INV-03"
    ]
    assert violations and "will invent an answer" in violations[0].remedy


@pytest.mark.fast
@pytest.mark.req("INV-04")
def test_inv_04_a_rule_from_a_non_compilable_force_is_a_violation() -> None:
    """G3: a SHOULD restatement never yields an executable obligation."""
    violations = [
        one
        for one in check_ir(
            valid_ir(rules=(order_rule(source_propositions=(PROP_SHORT,)), short_rule()))
        )
        if one.invariant_id == "INV-04"
    ]
    assert violations and "whose force is SHOULD" in violations[0].message


@pytest.mark.fast
@pytest.mark.req("INV-04")
def test_inv_04_an_advisory_note_from_a_must_is_a_violation() -> None:
    violations = [
        one
        for one in check_ir(
            valid_ir(rules=(order_rule(), short_rule(source_propositions=(PROP_ORDER,))))
        )
        if one.invariant_id == "INV-04"
    ]
    assert violations and "Only SHOULD and SHOULD_NOT" in violations[0].remedy


@pytest.mark.fast
@pytest.mark.req("INV-04")
def test_inv_04_can_compiles_only_when_marked_operative() -> None:
    def ir_with(operative: bool) -> set[str]:
        blocked_source = proposition(
            PROP_ORDER,
            PAS_ORDER,
            ORDER_TEXT,
            ORDER_QUOTE,
            NormativeForce.CAN,
            operative=operative,
        )
        return {
            one.invariant_id
            for one in check_ir(
                valid_ir(
                    propositions=(
                        blocked_source,
                        proposition(
                            PROP_SHORT,
                            "PAS-0a1b2c3d4e5f6072",
                            SHORT_TEXT,
                            "should be short",
                            NormativeForce.SHOULD,
                        ),
                    )
                )
            )
        }

    assert "INV-04" in ir_with(operative=False)
    assert "INV-04" not in ir_with(operative=True)


@pytest.mark.fast
@pytest.mark.req("INV-04")
def test_inv_04_a_blocked_proposition_never_compiles() -> None:
    blocked = proposition(
        PROP_ORDER, PAS_ORDER, ORDER_TEXT, ORDER_QUOTE, NormativeForce.MUST_NOT
    ).model_copy(update={"epistemic": EpistemicStatus(triage=TriageState.BLOCKED)})
    violations = [
        one
        for one in check_ir(
            valid_ir(
                propositions=(
                    blocked,
                    proposition(
                        PROP_SHORT,
                        "PAS-0a1b2c3d4e5f6072",
                        SHORT_TEXT,
                        "should be short",
                        NormativeForce.SHOULD,
                    ),
                )
            )
        )
        if one.invariant_id == "INV-04"
    ]
    assert violations and "which is blocked" in violations[0].message


@pytest.mark.fast
@pytest.mark.req("INV-05")
def test_inv_05_a_condition_on_an_unknown_fact_type_is_a_violation() -> None:
    violations = [one for one in check_ir(valid_ir(fact_types=())) if one.invariant_id == "INV-05"]
    assert violations and "is not in the IR" in violations[0].message


@pytest.mark.fast
@pytest.mark.req("INV-05")
def test_inv_05_a_fact_type_with_no_provider_is_a_violation() -> None:
    violations = [
        one
        for one in check_ir(
            valid_ir(fact_types=(fact_type(providers=(), probe_id=None),), probes=())
        )
        if one.invariant_id == "INV-05"
    ]
    assert violations and "has no provider" in violations[0].message


@pytest.mark.fast
@pytest.mark.req("INV-05")
def test_inv_05_is_satisfied_by_any_provider_not_only_a_probe() -> None:
    caller_only = fact_type(providers=(ProviderKind.CALLER,), probe_id=None)
    assert "INV-05" not in {
        one.invariant_id for one in check_ir(valid_ir(fact_types=(caller_only,)))
    }


@pytest.mark.fast
@pytest.mark.req("INV-06")
def test_inv_06_framework_led_has_no_backbone() -> None:
    violations = [
        one
        for one in check_ir(valid_ir(documents=(document(is_backbone=True),)))
        if one.invariant_id == "INV-06"
    ]
    assert violations and "as a backbone" in violations[0].message


@pytest.mark.fast
@pytest.mark.req("INV-06")
def test_inv_06_backbone_led_has_exactly_one_backbone() -> None:
    none_marked = [
        one
        for one in check_ir(valid_ir(reconstruction_mode=ReconstructionMode.BACKBONE))
        if one.invariant_id == "INV-06"
    ]
    assert none_marked and "0 backbone documents" in none_marked[0].message

    exactly_one = check_ir(
        valid_ir(
            reconstruction_mode=ReconstructionMode.BACKBONE,
            documents=(document(is_backbone=True),),
        )
    )
    assert "INV-06" not in {one.invariant_id for one in exactly_one}


@pytest.mark.fast
@pytest.mark.req("INV-06")
def test_inv_06_an_authority_level_outside_the_profile_is_a_violation() -> None:
    violations = [
        one
        for one in check_ir(valid_ir(documents=(document(authority_level="invented"),)))
        if one.invariant_id == "INV-06"
    ]
    assert violations and "does not define" in violations[0].message

    missing_profile = [
        one for one in check_ir(valid_ir(authority_profile=None)) if one.invariant_id == "INV-06"
    ]
    assert missing_profile and "no authority profile" in missing_profile[0].message


@pytest.mark.fast
@pytest.mark.req("INV-07")
def test_inv_07_a_defeat_cycle_is_a_violation() -> None:
    first = order_rule(
        defeats=(
            Defeat(
                defeated_rule_id="RULE-heading-short",
                priority_basis=PriorityBasis.EXCEPTION,
                rationale="the exception wins",
            ),
        )
    )
    second = short_rule(
        defeats=(
            Defeat(
                defeated_rule_id="RULE-heading-order",
                priority_basis=PriorityBasis.POLICY,
                rationale="and back again",
            ),
        )
    )
    violations = [
        one for one in check_ir(valid_ir(rules=(first, second))) if one.invariant_id == "INV-07"
    ]
    assert len(violations) == 1
    assert "form a cycle" in violations[0].message


@pytest.mark.fast
@pytest.mark.req("INV-07")
def test_inv_07_a_defeat_chain_without_a_cycle_is_fine() -> None:
    first = order_rule(
        defeats=(
            Defeat(
                defeated_rule_id="RULE-heading-short",
                priority_basis=PriorityBasis.EXCEPTION,
                rationale="the exception wins",
            ),
        )
    )
    assert "INV-07" not in {
        one.invariant_id for one in check_ir(valid_ir(rules=(first, short_rule())))
    }


@pytest.mark.fast
@pytest.mark.req("INV-07")
def test_inv_07_alternatives_never_defeat_each_other() -> None:
    first = order_rule(
        alternatives_set_id="CFL-heading-length",
        defeats=(
            Defeat(
                defeated_rule_id="RULE-heading-short",
                priority_basis=PriorityBasis.POLICY,
                rationale="chose one",
            ),
        ),
    )
    second = short_rule(alternatives_set_id="CFL-heading-length")
    violations = [
        one for one in check_ir(valid_ir(rules=(first, second))) if one.invariant_id == "INV-07"
    ]
    assert violations and "alternatives in" in violations[0].message


@pytest.mark.fast
@pytest.mark.req("INV-08")
def test_inv_08_a_judgement_node_is_not_decided_by_a_rule_set() -> None:
    elements = tuple(
        one.model_copy(update={"rule_set_id": "page-structure"})
        if one.kind is ElementKind.JUDGEMENT
        else one
        for one in skeleton().elements
    )
    violations = [
        one
        for one in check_ir(valid_ir(skeleton=skeleton(elements=elements)))
        if one.invariant_id == "INV-08"
    ]
    assert violations and "never by rules" in violations[0].remedy


@pytest.mark.fast
@pytest.mark.req("INV-08")
def test_inv_08_a_judgement_node_names_a_procedure_that_exists() -> None:
    def elements_with(procedure_id: str | None) -> tuple[SkeletonElement, ...]:
        return tuple(
            one.model_copy(update={"judgement_procedure_id": procedure_id})
            if one.kind is ElementKind.JUDGEMENT
            else one
            for one in skeleton().elements
        )

    missing = [
        one
        for one in check_ir(valid_ir(skeleton=skeleton(elements=elements_with(None))))
        if one.invariant_id == "INV-08"
    ]
    assert missing and "names no judgement procedure" in missing[0].message

    dangling = [
        one
        for one in check_ir(valid_ir(skeleton=skeleton(elements=elements_with("JDG-nowhere"))))
        if one.invariant_id == "INV-08"
    ]
    assert dangling and "not in the IR" in dangling[0].message


@pytest.mark.fast
@pytest.mark.req("INV-09")
def test_inv_09_a_value_carries_its_artefact() -> None:
    lookup = IRIndex(valid_ir())
    good = ProbeResult(
        probe_id="PRB-html-heading-outline",
        probe_version=1,
        fact_type_id="FACT-heading_levels_skipped",
        value=1,
        artefact=ArtefactRef(kind="html", sha256="abc"),
    )
    assert tuple(check_probe_result(good, lookup)) == ()

    without = good.model_copy(update={"artefact": None})
    violations = list(check_probe_result(without, lookup))
    assert violations and "with no artefact reference" in violations[0].message


@pytest.mark.fast
@pytest.mark.req("INV-09")
def test_inv_09_an_abstention_gives_a_declared_reason() -> None:
    lookup = IRIndex(valid_ir())
    declared = ProbeResult(
        probe_id="PRB-html-heading-outline",
        probe_version=1,
        fact_type_id="FACT-heading_levels_skipped",
        unknown_reason="no_headings_found",
    )
    assert tuple(check_probe_result(declared, lookup)) == ()

    invented = declared.model_copy(update={"unknown_reason": "felt uncertain"})
    violations = list(check_probe_result(invented, lookup))
    assert violations and "does not declare" in violations[0].message


@pytest.mark.fast
@pytest.mark.req("INV-09")
def test_inv_09_neither_a_value_nor_a_reason_is_a_violation() -> None:
    """FR-PRB-01: never a default or an estimate. An empty result is neither answer."""
    lookup = IRIndex(valid_ir())
    empty = ProbeResult(
        probe_id="PRB-html-heading-outline",
        probe_version=1,
        fact_type_id="FACT-heading_levels_skipped",
    )
    messages = [one.message for one in check_probe_result(empty, lookup)]
    assert any("neither a value nor an abstain reason" in one for one in messages)


@pytest.mark.fast
@pytest.mark.req("INV-09")
def test_inv_09_a_probe_returning_a_fact_it_does_not_declare_is_a_violation() -> None:
    lookup = IRIndex(valid_ir())
    wrong = ProbeResult(
        probe_id="PRB-html-heading-outline",
        probe_version=1,
        fact_type_id="FACT-audience",
        value="general_public",
        artefact=ArtefactRef(kind="html", sha256="abc"),
    )
    violations = list(check_probe_result(wrong, lookup))
    assert violations and "does not declare computing" in violations[0].message


def response_with(**changes: object) -> ToolResponse:
    base = {
        "package": PackageRef(
            domain="style-manual-wcag", ir_version="0.1.0", snapshot_id="SNAP-0a1b2c3d4e5f6071"
        ),
        "objective": "page-structure",
    }
    return ToolResponse(**{**base, **changes})


@pytest.mark.fast
@pytest.mark.req("INV-10")
def test_inv_10_an_uncited_assertion_is_a_violation() -> None:
    lookup = IRIndex(valid_ir())
    uncited = response_with(
        advisory=(AdvisoryItem(rule_id="RULE-heading-short", statement=SHORT_TEXT),)
    )
    violations = list(check_tool_response(uncited, lookup))
    assert violations and "no citation" in violations[0].message


@pytest.mark.fast
@pytest.mark.req("INV-10")
def test_inv_10_a_citation_resolves_to_a_passage_in_the_snapshot() -> None:
    lookup = IRIndex(valid_ir())
    resolving = response_with(
        applies=(
            AppliesItem(
                rule_id="RULE-heading-order",
                statement=ORDER_TEXT,
                status=AssertionStatus.NOT_SATISFIED,
                state=EpistemicOverall.VERIFIED,
                citations=(
                    Citation(document="Style Manual", anchor="headings", passage_id=PAS_ORDER),
                ),
            ),
        )
    )
    assert tuple(check_tool_response(resolving, lookup)) == ()

    dangling = response_with(
        applies=(
            AppliesItem(
                rule_id="RULE-heading-order",
                statement=ORDER_TEXT,
                status=AssertionStatus.NOT_SATISFIED,
                state=EpistemicOverall.VERIFIED,
                citations=(
                    Citation(
                        document="Style Manual",
                        anchor="headings",
                        passage_id="PAS-ffffffffffffffff",
                    ),
                ),
            ),
        )
    )
    violations = list(check_tool_response(dangling, lookup))
    assert violations and "is not in the snapshot" in violations[0].message


@pytest.mark.fast
@pytest.mark.req("INV-10")
def test_inv_10_a_citation_without_a_passage_cannot_resolve() -> None:
    lookup = IRIndex(valid_ir())
    unresolvable = response_with(
        advisory=(
            AdvisoryItem(
                rule_id="RULE-heading-short",
                statement=SHORT_TEXT,
                citations=(Citation(document="Style Manual", anchor="headings"),),
            ),
        )
    )
    violations = list(check_tool_response(unresolvable, lookup))
    assert violations and "cannot be resolved" in violations[0].message


@pytest.mark.fast
@pytest.mark.req("INV-11")
def test_inv_11_a_reference_source_stores_no_text() -> None:
    for licence in (LicenceClass.REFERENCE, LicenceClass.EXCLUDED):
        violations = [
            one
            for one in check_ir(valid_ir(documents=(document(licence_class=licence),)))
            if one.invariant_id == "INV-11"
        ]
        assert len(violations) == 2, licence
        assert "stores text" in violations[0].message


@pytest.mark.fast
@pytest.mark.req("INV-11")
def test_inv_11_a_reference_source_with_no_stored_text_is_fine() -> None:
    """G11: anchors and links survive; text does not."""
    ir = valid_ir(
        documents=(document(licence_class=LicenceClass.REFERENCE),),
        passages=(
            passage(PAS_ORDER, ORDER_TEXT, "headings").model_copy(update={"text": None}),
            passage("PAS-0a1b2c3d4e5f6072", SHORT_TEXT, "headings").model_copy(
                update={"text": None}
            ),
        ),
    )
    assert "INV-11" not in {one.invariant_id for one in check_ir(ir)}


@pytest.mark.fast
@pytest.mark.req("INV-12")
def test_inv_12_a_policy_resolution_must_be_in_the_decision_log() -> None:
    violations = [
        one for one in check_ir(valid_ir(decision_log=())) if one.invariant_id == "INV-12"
    ]
    assert violations and "not in the decision log" in violations[0].message


@pytest.mark.fast
@pytest.mark.req("INV-12")
def test_inv_12_a_log_entry_without_inputs_is_a_violation() -> None:
    violations = [
        one
        for one in check_ir(valid_ir(decision_log=(policy_log_entry(inputs={}),)))
        if one.invariant_id == "INV-12"
    ]
    assert violations and "without its inputs" in violations[0].message


@pytest.mark.fast
@pytest.mark.req("INV-12")
def test_inv_12_an_override_beats_an_automated_decision() -> None:

    override = Override(
        override_id="REV-0a1b2c3d4e5f6071",
        target_id="CFL-heading-length",
        target_kind="resolution",
        value="the less strict option",
        rationale="the designer accepted the trade-off",
        decided_by="ux-designer",
        decided_at=NOW,
    )
    from tests.unit.ir_builders import policy_log_entry

    override_entry = policy_log_entry().model_copy(
        update={
            "entry_id": "DEC-0a1b2c3d4e5f6072",
            "kind": DecisionKind.OVERRIDE,
            "policy_id": None,
            "override_id": "REV-0a1b2c3d4e5f6071",
            "decision": "the less strict option",
        }
    )
    still_resolved = valid_ir(
        overrides=(override,), decision_log=(policy_log_entry(), override_entry)
    )
    violations = [one for one in check_ir(still_resolved) if one.invariant_id == "INV-12"]
    assert violations and "still stands as resolved by policy" in violations[0].message

    overridden = valid_ir(
        overrides=(override,),
        conflicts=(resolved_conflict(status=ConflictStatus.OVERRIDDEN),),
        decision_log=(policy_log_entry(), override_entry),
    )
    assert "INV-12" not in {one.invariant_id for one in check_ir(overridden)}


@pytest.mark.fast
@pytest.mark.req("INV-12")
def test_inv_12_an_unresolved_conflict_needs_no_log_entry() -> None:
    """DP-10: where no policy applies, nothing was decided, so nothing is logged."""
    unresolved = resolved_conflict(
        resolution=Resolution(decided_by=DecidedBy.UNRESOLVED), status=ConflictStatus.OPEN
    )
    assert "INV-12" not in {
        one.invariant_id for one in check_ir(valid_ir(conflicts=(unresolved,), decision_log=()))
    }


@pytest.mark.fast
@pytest.mark.req(
    "INV-01",
    "INV-02",
    "INV-03",
    "INV-04",
    "INV-05",
    "INV-06",
    "INV-07",
    "INV-08",
    "INV-09",
    "INV-10",
    "INV-11",
    "INV-12",
)
def test_a_violation_blocks_the_record_and_never_the_run() -> None:
    """DP-04. Even an IR that breaks several invariants at once returns violations rather
    than raising, so the stage records them and carries on."""
    broken = valid_ir(
        documents=(document(authority_level="invented", is_backbone=True),),
        rules=(order_rule(source_propositions=()), short_rule(source_propositions=())),
        fact_types=(),
        gaps=(gap(search_record=None),),
        decision_log=(),
    )
    violations = check_ir(broken)
    assert {one.invariant_id for one in violations} >= {
        "INV-02",
        "INV-05",
        "INV-06",
        "INV-12",
    }
    for violation in violations:
        assert violation.record_id
        assert violation.message.endswith(".")
        assert violation.remedy


@pytest.mark.fast
@pytest.mark.req(
    "INV-01",
    "INV-02",
    "INV-03",
    "INV-04",
    "INV-05",
    "INV-06",
    "INV-08",
    "INV-09",
    "INV-10",
    "INV-11",
)
def test_check_record_dispatches_to_the_right_invariants() -> None:
    """What a store calls on each write: one record in, its violations out (`models.md`)."""
    lookup = IRIndex(valid_ir())
    for record in (
        document(),
        passage(PAS_ORDER, ORDER_TEXT, "headings"),
        proposition(PROP_ORDER, PAS_ORDER, ORDER_TEXT, ORDER_QUOTE, NormativeForce.MUST_NOT),
        order_rule(),
        procedure(),
        resolved_conflict(),
        gap(),
        *skeleton().elements,
    ):
        assert check_record(record, lookup) == (), record

    bad = order_rule(source_propositions=())
    violations = check_record(bad, lookup)
    assert [one.invariant_id for one in violations] == ["INV-02"]
    assert violations[0].record_id == "RULE-heading-order"


@pytest.mark.fast
@pytest.mark.req("INV-06", "INV-07", "INV-12")
def test_check_record_leaves_the_whole_ir_invariants_to_check_ir() -> None:
    """The backbone count, the defeat graph and log coverage cannot be decided from one
    record, so check_record does not pretend to."""
    lookup = IRIndex(valid_ir())
    backbone = document(is_backbone=True)
    assert check_record(backbone, lookup) == ()
    assert "INV-06" in {one.invariant_id for one in check_ir(valid_ir(documents=(backbone,)))}
