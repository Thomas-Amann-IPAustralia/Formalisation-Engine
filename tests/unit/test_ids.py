"""Identifiers: prefixes, content hashes and IRI conversion (spec section 4, NFR-INT-01)."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from engine.ids import (
    BASE_IRI,
    CONTENT_HASH_LENGTH,
    IdKind,
    PassageId,
    content_id,
    from_iri,
    is_id,
    kind_of,
    make_id,
    parse_id,
    to_iri,
)


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
def test_every_spec_prefix_is_a_kind() -> None:
    """Spec section 4 lists thirteen prefixes; ADR-0005 adds four the spec uses but omits."""
    spec_prefixes = {
        "DOC",
        "PAS",
        "PROP",
        "CON",
        "EL",
        "RULE",
        "JDG",
        "FACT",
        "PRB",
        "CFL",
        "GAP",
        "POL",
        "REV",
    }
    values = {kind.value for kind in IdKind}
    assert spec_prefixes <= values
    assert values - spec_prefixes == {"SNAP", "SKEL", "RUN", "DEC"}


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
@pytest.mark.parametrize(
    "value",
    [
        "EL-page-structure",
        "POL-ux-stricter-wins",
        "FACT-heading_levels_skipped",
        "PRB-html-heading-outline",
        "DOC-WCAG-22",
        "SKEL-ux-standards",
        "PAS-3f9a1c0b7e2d4a58",
    ],
)
def test_identifiers_in_use_are_well_formed(value: str) -> None:
    """Every identifier the pilot configuration already uses parses."""
    assert is_id(value)
    kind, suffix = parse_id(value)
    assert value == f"{kind.value}-{suffix}"


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
@pytest.mark.parametrize(
    "value",
    [
        "",
        "page-structure",  # no prefix
        "XYZ-thing",  # unknown prefix
        "EL-",  # empty suffix
        "EL--leading-dash",  # suffix must start with a letter or digit
        "el-page-structure",  # prefixes are upper case
        "EL-page structure",  # no spaces
        "EL-page/structure",  # no slashes: they would break the IRI
    ],
)
def test_malformed_identifiers_are_rejected(value: str) -> None:
    """The failure path: a malformed identifier is named, with what a good one looks like."""
    assert not is_id(value)
    with pytest.raises(ValueError, match="is not an identifier"):
        parse_id(value)


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
def test_is_id_can_require_one_kind() -> None:
    assert is_id("PAS-3f9a1c0b7e2d4a58", IdKind.PASSAGE)
    assert not is_id("PAS-3f9a1c0b7e2d4a58", IdKind.PROPOSITION)
    assert kind_of("PROP-abc") is IdKind.PROPOSITION


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
def test_make_id_rejects_a_suffix_that_would_not_parse() -> None:
    assert make_id(IdKind.ELEMENT, "page-structure") == "EL-page-structure"
    with pytest.raises(ValueError, match="cannot follow EL-"):
        make_id(IdKind.ELEMENT, "page structure")


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
def test_content_id_is_stable_for_the_same_content() -> None:
    """Spec section 4: re-runs yield the same identifier for the same content."""
    first = content_id(IdKind.PASSAGE, "DOC-WCAG-22", "headings", "Headings must not skip levels.")
    second = content_id(IdKind.PASSAGE, "DOC-WCAG-22", "headings", "Headings must not skip levels.")
    assert first == second
    assert first.startswith("PAS-")
    assert len(first) == len("PAS-") + CONTENT_HASH_LENGTH
    assert is_id(first, IdKind.PASSAGE)


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
def test_content_id_changes_when_the_content_changes() -> None:
    base = content_id(IdKind.PASSAGE, "DOC-WCAG-22", "headings", "Headings must not skip levels.")
    assert base != content_id(IdKind.PASSAGE, "DOC-WCAG-22", "headings", "Headings may skip.")
    assert base != content_id(
        IdKind.PASSAGE, "DOC-STYLE-MANUAL", "headings", "Headings must not skip levels."
    )


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
def test_content_id_does_not_confuse_part_boundaries() -> None:
    """Length framing keeps ('ab', 'c') distinct from ('a', 'bc'), and survives a part that
    contains the framing characters or a separator an attacker might try (G6)."""
    assert content_id(IdKind.PASSAGE, "ab", "c") != content_id(IdKind.PASSAGE, "a", "bc")
    assert content_id(IdKind.PASSAGE, "1:a", "b") != content_id(IdKind.PASSAGE, "1:ab")
    assert content_id(IdKind.PASSAGE, "a\x1fb") != content_id(IdKind.PASSAGE, "a", "b")


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
def test_content_id_normalises_unicode() -> None:
    """UTF-8 text that is the same after NFC gets the same identifier (NFR-INT-01)."""
    composed = "résumé"  # é as one code point
    decomposed = "résumé"  # e + combining acute
    assert composed != decomposed
    assert content_id(IdKind.PASSAGE, composed) == content_id(IdKind.PASSAGE, decomposed)


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
def test_content_id_needs_something_to_hash() -> None:
    with pytest.raises(ValueError, match="needs at least one part"):
        content_id(IdKind.PASSAGE)


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
@pytest.mark.parametrize("kind", list(IdKind))
def test_identifiers_convert_to_an_iri_and_back(kind: IdKind) -> None:
    """NFR-INT-01: identifiers are convertible to IRIs."""
    identifier = make_id(kind, "example.1")
    iri = to_iri(identifier)
    assert iri == f"{BASE_IRI}{identifier}"
    assert from_iri(iri) == identifier


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
def test_iri_conversion_rejects_bad_input() -> None:
    """The failure path both ways."""
    with pytest.raises(ValueError, match="is not an identifier"):
        to_iri("not-an-identifier")
    with pytest.raises(ValueError, match="is not an Engine identifier IRI"):
        from_iri("https://example.org/id/EL-page-structure")
    with pytest.raises(ValueError, match="is not an identifier"):
        from_iri(f"{BASE_IRI}nonsense")


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
def test_annotated_identifier_types_constrain_a_model_field() -> None:
    """The per-kind aliases carry the pattern into both mypy and the generated JSON Schema."""

    class Holder(BaseModel):
        passage_id: PassageId

    assert Holder(passage_id="PAS-3f9a1c0b7e2d4a58").passage_id == "PAS-3f9a1c0b7e2d4a58"
    with pytest.raises(ValidationError):
        Holder(passage_id="PROP-3f9a1c0b7e2d4a58")

    schema = Holder.model_json_schema()
    assert schema["properties"]["passage_id"]["pattern"].startswith("^PAS-")
