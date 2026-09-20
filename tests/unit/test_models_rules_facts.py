"""Fact types, probes, rules and judgement procedures (spec section 4)."""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from engine.models.enums import (
    UNABLE_TO_DETERMINE,
    ConditionOperator,
    DataType,
    Executability,
    FactProvenance,
    Origin,
    PriorityBasis,
    ProbeCost,
    ProvenanceKind,
    ProviderKind,
)
from engine.models.facts import ArtefactRef, FactType, FactValue, Probe, ProbeResult
from engine.models.judgement import (
    Consideration,
    JudgementOutputSchema,
    JudgementProcedure,
    JudgementRecord,
)
from engine.models.rule import (
    AllOf,
    AnyOf,
    Conclusion,
    Defeat,
    FactCondition,
    NotCondition,
    Rule,
    RuleCondition,
    fact_types_in,
)

PROBE_FACT = {
    "fact_type_id": "FACT-heading_levels_skipped",
    "name": "heading_levels_skipped",
    "data_type": DataType.NUMBER,
    "providers": (ProviderKind.PROBE,),
    "probe_id": "PRB-html-heading-outline",
    "artefact_kind": "html",
    "origin": Origin.EDITED,
}


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_closed_world_defaults_to_false() -> None:
    """FR-QRY-01: a missing fact is UNKNOWN unless its type is closed world."""
    assert FactType(**PROBE_FACT).closed_world is False


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_providers_keep_their_declared_order() -> None:
    """FR-TOO-04 runs providers in order, so the order has to survive the model."""
    fact = FactType(
        fact_type_id="FACT-heading_describes_section",
        name="heading_describes_section",
        data_type=DataType.BOOLEAN,
        providers=(ProviderKind.CALLER, ProviderKind.INFERRED),
        allow_inference=True,
        artefact_kind="html",
        origin=Origin.EDITED,
    )
    assert fact.providers == (ProviderKind.CALLER, ProviderKind.INFERRED)
    assert fact.has_provider


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_an_enum_fact_type_lists_its_values() -> None:
    with pytest.raises(ValidationError, match="enum with no allowed_values"):
        FactType(
            fact_type_id="FACT-heading_case",
            name="heading_case",
            data_type=DataType.ENUM,
            providers=(ProviderKind.CALLER,),
            origin=Origin.EDITED,
        )


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_probe_provider_names_its_probe() -> None:
    with pytest.raises(ValidationError, match="names no probe_id"):
        FactType(**{**PROBE_FACT, "probe_id": None})


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_inference_is_declared_in_one_place_only() -> None:
    """allow_inference and the `inferred` provider say the same thing; they must agree."""
    with pytest.raises(ValidationError, match="does not list `inferred`"):
        FactType(**{**PROBE_FACT, "allow_inference": True})
    with pytest.raises(ValidationError, match="lists `inferred`"):
        FactType(
            fact_type_id="FACT-x",
            name="x",
            data_type=DataType.BOOLEAN,
            providers=(ProviderKind.INFERRED,),
            allow_inference=False,
            origin=Origin.PROPOSED,
        )


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_probe_computes_something() -> None:
    probe = Probe(
        probe_id="PRB-html-heading-outline",
        implementation="engine.probes.html.heading_outline",
        computes=("FACT-heading_levels_skipped",),
        artefact_kind="html",
        cost=ProbeCost.CHEAP,
        abstain_reasons=("artefact_not_parseable", "no_headings_found"),
    )
    assert probe.version == 1
    with pytest.raises(ValidationError):
        Probe(
            probe_id="PRB-empty",
            implementation="engine.probes.html.nothing",
            computes=(),
            artefact_kind="html",
            cost=ProbeCost.CHEAP,
        )


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_probe_result_is_not_both_a_value_and_an_abstention() -> None:
    with pytest.raises(ValidationError, match="both a value"):
        ProbeResult(
            probe_id="PRB-html-heading-outline",
            probe_version=1,
            fact_type_id="FACT-heading_levels_skipped",
            value=1,
            unknown_reason="artefact_not_parseable",
        )


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_false_probe_value_is_a_value_not_an_absence() -> None:
    """`False` and `0` are answers; only None is the absence of one."""
    result = ProbeResult(
        probe_id="PRB-html-heading-outline",
        probe_version=1,
        fact_type_id="FACT-heading_describes_section",
        value=False,
        artefact=ArtefactRef(kind="html", sha256="abc"),
    )
    assert result.is_abstention is False
    assert result.value is False
    assert (
        FactValue(
            fact_type_id="FACT-heading_describes_section",
            value=False,
            provenance=FactProvenance.PROBE,
        ).is_unknown
        is False
    )


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_fact_with_no_value_is_unknown() -> None:
    assert FactValue(fact_type_id="FACT-audience", provenance=FactProvenance.CALLER).is_unknown


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_condition_tree_nests_and_reports_its_fact_types() -> None:
    """INV-05 needs every fact type a rule's conditions reach, however deep."""
    adapter: TypeAdapter[RuleCondition] = TypeAdapter(RuleCondition)
    tree = adapter.validate_python(
        {
            "op": "all_of",
            "operands": [
                {"op": "fact", "fact_type_id": "FACT-a", "operator": "gt", "value": 0},
                {
                    "op": "not",
                    "operand": {
                        "op": "any_of",
                        "operands": [
                            {"op": "fact", "fact_type_id": "FACT-b", "operator": "exists"},
                            {"op": "fact", "fact_type_id": "FACT-c", "operator": "eq"},
                        ],
                    },
                },
            ],
        }
    )
    assert isinstance(tree, AllOf)
    assert fact_types_in(tree) == frozenset({"FACT-a", "FACT-b", "FACT-c"})
    assert fact_types_in(None) == frozenset()


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_an_empty_branch_is_refused() -> None:
    with pytest.raises(ValidationError):
        AnyOf(operands=())


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_frozen_rule_says_why() -> None:
    conclusion = Conclusion(statement="Heading levels must not be skipped.")
    with pytest.raises(ValidationError, match="frozen without a reason"):
        Rule(
            rule_id="RULE-heading-order",
            rule_set_id="page-structure",
            statement="Heading levels must not be skipped.",
            conclusion=conclusion,
            executability=Executability.FROZEN,
        )
    ok = Rule(
        rule_id="RULE-heading-order",
        rule_set_id="page-structure",
        statement="Heading levels must not be skipped.",
        conclusion=conclusion,
        executability=Executability.FROZEN,
        frozen_reason="depends on unresolved gap GAP-threshold",
    )
    assert ok.frozen_reason


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_rule_does_not_defeat_itself() -> None:
    with pytest.raises(ValidationError, match="defeats itself"):
        Rule(
            rule_id="RULE-a",
            rule_set_id="page-structure",
            statement="A",
            conclusion=Conclusion(statement="A"),
            defeats=(
                Defeat(
                    defeated_rule_id="RULE-a",
                    priority_basis=PriorityBasis.EXCEPTION,
                    rationale="x",
                ),
            ),
        )


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_rule_reports_the_fact_types_it_uses() -> None:
    rule = Rule(
        rule_id="RULE-heading-order",
        rule_set_id="page-structure",
        statement="Heading levels must not be skipped.",
        conditions=FactCondition(
            fact_type_id="FACT-heading_levels_skipped",
            operator=ConditionOperator.GT,
            value=0,
        ),
        conclusion=Conclusion(statement="not satisfied"),
    )
    assert rule.fact_types_used == frozenset({"FACT-heading_levels_skipped"})
    assert rule.advisory is False
    assert rule.executability is Executability.EXECUTABLE


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_negation_keeps_its_operand() -> None:
    node = NotCondition(
        operand=FactCondition(fact_type_id="FACT-a", operator=ConditionOperator.EXISTS)
    )
    assert fact_types_in(node) == frozenset({"FACT-a"})


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_judgement_output_schema_knows_whether_it_can_decline() -> None:
    """INV-03 checks this; the model only reports it."""
    assert not JudgementOutputSchema(outcomes=("yes", "no")).can_decline
    assert JudgementOutputSchema(outcomes=("yes", "no", UNABLE_TO_DETERMINE)).can_decline


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_judgement_procedure_caches_on_the_three_things_that_decide_it() -> None:
    procedure = JudgementProcedure(
        procedure_id="JDG-heading-describes",
        question="Do the headings describe their sections?",
        considerations=(
            Consideration(
                text="A heading names what follows it.",
                source_proposition_id="PROP-0000000000000001",
            ),
        ),
        prompt_id="judgement/heading-describes",
        prompt_version=1,
        output_schema=JudgementOutputSchema(outcomes=("yes", "mostly", "no", UNABLE_TO_DETERMINE)),
        source_propositions=("PROP-0000000000000001",),
    )
    assert procedure.cache_by == ("artefact_hash", "inputs", "prompt_version")
    assert procedure.cost_class is ProbeCost.CHEAP


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_judgement_record_is_judged_or_overridden_and_nothing_else() -> None:
    record = JudgementRecord(
        procedure_id="JDG-heading-describes",
        outcome="mostly",
        rationale="Most headings name what follows.",
        confidence=0.7,
        model="gemini-2.5-flash",
        prompt_version=1,
    )
    assert record.provenance is ProvenanceKind.JUDGED
    with pytest.raises(ValidationError, match="is tagged extracted"):
        JudgementRecord(
            procedure_id="JDG-heading-describes",
            outcome="mostly",
            rationale="x",
            confidence=0.7,
            model="gemini-2.5-flash",
            prompt_version=1,
            provenance=ProvenanceKind.EXTRACTED,
        )


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_judgement_confidence_stays_within_range() -> None:
    with pytest.raises(ValidationError):
        JudgementRecord(
            procedure_id="JDG-heading-describes",
            outcome="mostly",
            rationale="x",
            confidence=1.4,
            model="gemini-2.5-flash",
            prompt_version=1,
        )
