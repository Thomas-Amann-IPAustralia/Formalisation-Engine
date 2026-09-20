"""The tool contract (spec Appendix E, DP-11, NFR-INT-01).

The fixtures are Appendix E's own request and response, filled in. They differ from the
appendix in one way: the `advisory` and `judgements` entries carry real citations, because
INV-10 and FR-TOO-03 require a citation on every assertion, and Appendix A's worked example of
this very call says the advisory is cited. The appendix's empty arrays read as abbreviation in
an illustrative sample; ADR-0005 records the reading and docs/STATUS.md asks Tom to confirm it.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from engine.models.contract import (
    BEST_EFFORT_NOTE,
    CONTRACT_VERSION,
    AlternativeOption,
    AlternativesItem,
    HowToObtain,
    NeededFact,
    PackageRef,
    StatusSummary,
    ToolRequest,
    ToolResponse,
    UndeterminedItem,
)
from engine.models.enums import (
    AssertionStatus,
    EpistemicOverall,
    FactProvenance,
    ProbeCost,
    ProviderKind,
    RequestMode,
)

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "contract"


def load(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def carries(dumped: Any, expected: Any, path: str = "$") -> None:
    """Assert `dumped` holds everything `expected` does, with the same values.

    The appendix leaves optional fields out where a model dumps them as null, so a plain
    equality check would fail on absence rather than on difference. This checks the thing that
    matters: nothing the appendix states is lost or altered on the way through the models.
    """
    if isinstance(expected, dict):
        assert isinstance(dumped, dict), f"{path}: expected an object, got {type(dumped)}"
        for key, value in expected.items():
            assert key in dumped, f"{path}.{key} is missing from the dump"
            carries(dumped[key], value, f"{path}.{key}")
    elif isinstance(expected, list):
        assert isinstance(dumped, list), f"{path}: expected an array, got {type(dumped)}"
        assert len(dumped) == len(expected), (
            f"{path}: {len(dumped)} items, expected {len(expected)}"
        )
        for index, value in enumerate(expected):
            carries(dumped[index], value, f"{path}[{index}]")
    else:
        assert dumped == expected, f"{path}: {dumped!r} != {expected!r}"


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
def test_the_appendix_e_request_parses_and_round_trips() -> None:
    payload = load("appendix_e_request.json")
    request = ToolRequest.model_validate(payload)
    assert request.contract_version == CONTRACT_VERSION
    assert request.objective == "page-structure"
    assert request.options.mode is RequestMode.ANSWER
    assert request.options.max_probe_cost is ProbeCost.CHEAP
    assert request.options.as_at == date(2026, 9, 18)
    assert request.facts["audience"].value == "general_public"
    assert request.overrides["heading_describes_section"].value is False
    assert request.overrides["heading_describes_section"].by == "ux-designer"
    carries(request.model_dump(mode="json"), payload)
    assert ToolRequest.model_validate(request.model_dump(mode="json")) == request


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
def test_the_appendix_e_response_parses_and_round_trips() -> None:
    payload = load("appendix_e_response.json")
    response = ToolResponse.model_validate(payload)
    assert response.package.ir_version == "1.3.0"
    assert response.applies[0].status is AssertionStatus.NOT_SATISFIED
    assert response.applies[0].state is EpistemicOverall.VERIFIED
    assert response.applies[0].facts_used[0].source is FactProvenance.PROBE
    assert response.judgements[0].source == "judged"
    assert response.undetermined[0].needs[0].how_to_obtain.kind is ProviderKind.PROBE
    assert response.alternatives[0].unresolved_because == "no policy applies"
    assert response.plan is None
    carries(response.model_dump(mode="json"), payload)
    assert ToolResponse.model_validate(response.model_dump(mode="json")) == response


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
def test_the_worked_examples_status_summary_matches_appendix_a() -> None:
    """Appendix A: verified 1, judged 1, advisory 1, and nothing undetermined about them."""
    response = ToolResponse.model_validate(load("appendix_e_response.json"))
    assert response.status_summary == StatusSummary(verified=1, judged=1, advisory=1)


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
def test_every_assertion_is_listed_for_citation_checking() -> None:
    """INV-10 works over this: rules that apply, advisory notes, judgements and options."""
    response = ToolResponse.model_validate(load("appendix_e_response.json"))
    assertions = dict(response.assertions_with_citations)
    assert "RULE-heading-order" in assertions
    assert "RULE-heading-short" in assertions
    assert "JDG-heading-describes" in assertions
    assert all(citations for citations in assertions.values())


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
def test_the_best_effort_note_is_always_present() -> None:
    """FR-TOO-02 names it as part of every response."""
    response = ToolResponse(
        package=PackageRef(
            domain="style-manual-wcag", ir_version="0.1.0", snapshot_id="SNAP-0000000000000001"
        ),
        objective="page-structure",
    )
    assert response.note == BEST_EFFORT_NOTE
    assert response.limits == ()
    assert response.status_summary == StatusSummary()


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
def test_an_undetermined_item_must_say_what_it_needs() -> None:
    """G2: undetermined items list the facts and how to obtain each."""
    with pytest.raises(ValidationError):
        UndeterminedItem(item="RULE-heading-case", needs=())
    item = UndeterminedItem(
        item="RULE-heading-case",
        needs=(
            NeededFact(
                fact_type="audience",
                how_to_obtain=HowToObtain(
                    kind=ProviderKind.CALLER, question="Who is the page for?"
                ),
            ),
        ),
    )
    assert item.needs[0].how_to_obtain.question


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
def test_alternatives_need_more_than_one_option() -> None:
    """An alternatives set with one member has chosen, which DP-10 forbids."""
    option = AlternativeOption(name="wcag", conditions="always")
    with pytest.raises(ValidationError):
        AlternativesItem(
            question="How long may a heading be?",
            options=(option,),
            unresolved_because="no policy applies",
        )


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
def test_the_contract_refuses_a_field_it_does_not_know() -> None:
    """DP-11: the shape is fixed. A domain adds content, never fields."""
    payload = load("appendix_e_request.json")
    with pytest.raises(ValidationError):
        ToolRequest.model_validate({**payload, "extensions": {"style-manual-wcag.x": 1}})
