"""The record models of spec section 4: documents, passages, propositions, skeleton, relations.

These test the guards the models themselves carry. The stage behaviour they support (S1 to S5)
is not built yet, so nothing here claims an FR identifier it does not implement.
"""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import TypeAdapter, ValidationError

from engine.models.enums import (
    BackboneRelation,
    ConditionOperator,
    ElementKind,
    ElementStatus,
    FrameworkRelation,
    LicenceClass,
    NormativeForce,
    Origin,
    ParseStatus,
    PassageType,
    ReconstructionMode,
    RelationMethod,
    SlotResolution,
    SourceKind,
)
from engine.models.proposition import Condition, Proposition, Slot, Span
from engine.models.relations import (
    BackboneMapping,
    FrameworkMapping,
    PropositionElementRelation,
)
from engine.models.skeleton import Outcome, Skeleton, SkeletonElement
from engine.models.source import Anchor, Document, Passage

DOCUMENT = {
    "document_id": "DOC-WCAG-22",
    "title": "Web Content Accessibility Guidelines 2.2",
    "document_type": "standard",
    "authority_level": "normative_specification",
    "source_kind": SourceKind.REPOSITORY,
    "source_uri": "https://github.com/w3c/wcag",
    "licence_class": LicenceClass.STORE,
    "parse_status": ParseStatus.PARSED,
}


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_document_carries_an_authority_level_and_a_licence_class() -> None:
    """INV-06's second clause is a required field before it is ever a check."""
    document = Document(**DOCUMENT)
    assert document.authority_level == "normative_specification"
    assert document.licence_class is LicenceClass.STORE
    with pytest.raises(ValidationError, match="authority_level"):
        Document(**{**DOCUMENT, "authority_level": ""})


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_rejected_document_says_why() -> None:
    with pytest.raises(ValidationError, match="rejected without a reason"):
        Document(**{**DOCUMENT, "parse_status": ParseStatus.REJECTED})
    ok = Document(**{**DOCUMENT, "parse_status": ParseStatus.REJECTED, "parse_note": "encrypted"})
    assert ok.parse_note == "encrypted"


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_effective_dates_are_ordered() -> None:
    with pytest.raises(ValidationError, match="before"):
        Document(
            **{
                **DOCUMENT,
                "effective_from": date(2026, 9, 1),
                "effective_to": date(2026, 8, 1),
            }
        )


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_an_anchor_locates_something() -> None:
    assert Anchor(section="headings").section == "headings"
    with pytest.raises(ValidationError, match="locates nothing"):
        Anchor()


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_passage_is_not_its_own_parent() -> None:
    with pytest.raises(ValidationError, match="its own parent"):
        Passage(
            passage_id="PAS-0000000000000001",
            document_id="DOC-WCAG-22",
            anchor=Anchor(section="headings"),
            passage_type=PassageType.BODY,
            parent_passage_id="PAS-0000000000000001",
        )


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_span_that_does_not_match_its_offsets_is_refused() -> None:
    """A quotation whose length disagrees with its offsets is how a fabricated span shows up."""
    text = "must not skip"
    assert Span(passage_id="PAS-0000000000000001", start=10, end=10 + len(text), text=text)
    with pytest.raises(ValidationError, match="offsets and the quotation disagree"):
        Span(passage_id="PAS-0000000000000001", start=10, end=15, text=text)
    with pytest.raises(ValidationError, match="at or before its start"):
        Span(passage_id="PAS-0000000000000001", start=10, end=10, text="x")


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_span_is_unverified_until_something_verifies_it() -> None:
    """INV-01 has something to check because the default is False, not True."""
    span = Span(passage_id="PAS-0000000000000001", start=0, end=4, text="must")
    assert span.verified is False


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_confirmed_slot_names_a_concept() -> None:
    assert Slot(raw_text="heading", resolution=SlotResolution.UNRESOLVED).concept_id is None
    with pytest.raises(ValidationError, match="names no concept"):
        Slot(raw_text="heading", resolution=SlotResolution.CONFIRMED)


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_propositions_span_comes_from_its_own_passage() -> None:
    """FR-EXT-01 sends one passage per request; a span from another is a mix-up."""
    with pytest.raises(ValidationError, match="span quotes"):
        Proposition(
            proposition_id="PROP-0000000000000001",
            passage_id="PAS-0000000000000001",
            span=Span(passage_id="PAS-0000000000000002", start=0, end=4, text="must"),
            normative_force=NormativeForce.MUST,
        )


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_proposition_defaults_to_not_operative() -> None:
    """Appendix B: CAN and DESCRIPTIVE compile only when marked operative, so the default
    has to be off."""
    proposition = Proposition(
        proposition_id="PROP-0000000000000001",
        passage_id="PAS-0000000000000001",
        span=Span(passage_id="PAS-0000000000000001", start=0, end=3, text="can"),
        normative_force=NormativeForce.CAN,
        conditions=(
            Condition(raw_text="where the page has headings", operator=ConditionOperator.EXISTS),
        ),
    )
    assert proposition.operative is False


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_an_element_is_not_its_own_parent_and_outcome_names_are_distinct() -> None:
    with pytest.raises(ValidationError, match="its own parent"):
        SkeletonElement(
            element_id="EL-a",
            kind=ElementKind.STEP,
            parent_element_id="EL-a",
            label="A",
            origin=Origin.PROPOSED,
        )
    with pytest.raises(ValidationError, match="more than one outcome named"):
        SkeletonElement(
            element_id="EL-a",
            kind=ElementKind.DECISION_POINT,
            label="A",
            origin=Origin.PROPOSED,
            outcomes=(Outcome(name="yes"), Outcome(name="yes")),
        )


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_an_element_finds_its_unable_to_determine_outcome() -> None:
    element = SkeletonElement(
        element_id="EL-a",
        kind=ElementKind.DECISION_POINT,
        label="A",
        origin=Origin.PROPOSED,
        outcomes=(Outcome(name="yes", target_element_id="EL-b"),),
    )
    assert element.is_decision
    assert element.unable_to_determine is None
    with_edge = element.model_copy(
        update={
            "outcomes": (
                *element.outcomes,
                Outcome(name="unable_to_determine", target_element_id="EL-c"),
            )
        }
    )
    assert with_edge.unable_to_determine is not None
    assert with_edge.unable_to_determine.target_element_id == "EL-c"


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_skeleton_declares_each_element_once() -> None:
    element = SkeletonElement(
        element_id="EL-a", kind=ElementKind.OBJECTIVE, label="A", origin=Origin.EDITED
    )
    skeleton = Skeleton(
        skeleton_id="SKEL-ux-standards",
        version=1,
        mode=ReconstructionMode.FRAMEWORK,
        origin=Origin.EDITED,
        elements=(element,),
    )
    assert skeleton.element("EL-a") is element
    assert skeleton.element("EL-missing") is None
    with pytest.raises(ValidationError, match="more than once"):
        Skeleton(
            skeleton_id="SKEL-ux-standards",
            version=1,
            mode=ReconstructionMode.FRAMEWORK,
            origin=Origin.EDITED,
            elements=(element, element),
        )


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_element_status_defaults_to_proposed() -> None:
    element = SkeletonElement(
        element_id="EL-a", kind=ElementKind.CHECK, label="A", origin=Origin.PROPOSED
    )
    assert element.status is ElementStatus.PROPOSED


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_the_mapping_union_picks_the_right_label_set() -> None:
    """`contradicts` is in both Appendix C.1 and C.3, so the mode has to decide which."""
    adapter: TypeAdapter[BackboneMapping | FrameworkMapping] = TypeAdapter(
        PropositionElementRelation
    )
    common = {
        "proposition_id": "PROP-0000000000000001",
        "element_id": "EL-a",
        "relation": "contradicts",
        "rationale": "it says the opposite",
        "method": RelationMethod.PANEL,
    }
    backbone = adapter.validate_python({**common, "mode": "backbone"})
    framework = adapter.validate_python({**common, "mode": "framework"})
    assert isinstance(backbone, BackboneMapping)
    assert backbone.relation is BackboneRelation.CONTRADICTS
    assert isinstance(framework, FrameworkMapping)
    assert framework.relation is FrameworkRelation.CONTRADICTS
    assert backbone.is_structural and framework.is_structural


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_a_label_from_the_other_modes_set_is_refused() -> None:
    """`introduces_step` is Appendix C.1 only; framework-led mode must not accept it."""
    adapter: TypeAdapter[BackboneMapping | FrameworkMapping] = TypeAdapter(
        PropositionElementRelation
    )
    with pytest.raises(ValidationError):
        adapter.validate_python(
            {
                "mode": "framework",
                "proposition_id": "PROP-0000000000000001",
                "element_id": "EL-a",
                "relation": "introduces_step",
                "rationale": "x",
                "method": RelationMethod.LLM,
            }
        )


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_context_only_is_not_structural() -> None:
    mapping = FrameworkMapping(
        proposition_id="PROP-0000000000000001",
        element_id="EL-a",
        relation=FrameworkRelation.CONTEXT_ONLY,
        rationale="background",
        method=RelationMethod.DETERMINISTIC,
    )
    assert not mapping.is_structural
