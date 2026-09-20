"""The base every IR record is built on (NFR-MNT-01, NFR-INT-01, NFR-PRT-01)."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from engine.models.base import ExtensibleModel, IRModel


class Sample(IRModel):
    name: str
    effective_from: date
    recorded_at: datetime
    tags: tuple[str, ...] = ()


class Extensible(ExtensibleModel):
    name: str


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_an_unknown_field_is_refused_and_named() -> None:
    """`extra="forbid"`: a field the models do not know is a typo or a schema change (DP-04)."""
    with pytest.raises(ValidationError, match="nmae"):
        Sample(
            name="x",
            effective_from=date(2026, 1, 1),
            recorded_at=datetime(2026, 1, 1, tzinfo=UTC),
            nmae="typo",  # type: ignore[call-arg]
        )


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_records_are_frozen() -> None:
    """DP-03 and NFR-DET-01: a record cannot drift from the identifier hashed out of it."""
    sample = Sample(
        name="x",
        effective_from=date(2026, 1, 1),
        recorded_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    with pytest.raises(ValidationError):
        sample.name = "y"  # type: ignore[misc]


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
def test_dates_serialise_as_iso_8601_and_text_stays_utf_8() -> None:
    """NFR-INT-01: ISO 8601 dates, UTF-8 text."""
    sample = Sample(
        name="Sébastien — résumé",
        effective_from=date(2026, 9, 20),
        recorded_at=datetime(2026, 9, 20, 4, 30, tzinfo=UTC),
        tags=("a", "b"),
    )
    payload = json.loads(sample.model_dump_json())
    assert payload["effective_from"] == "2026-09-20"
    assert payload["recorded_at"] == "2026-09-20T04:30:00Z"
    assert payload["name"] == sample.name
    assert Sample.model_validate(payload) == sample


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_sequence_fields_come_back_as_tuples() -> None:
    """Declared as tuples so that freezing is not undone by a mutable list underneath."""
    sample = Sample(
        name="x",
        effective_from=date(2026, 1, 1),
        recorded_at=datetime(2026, 1, 1, tzinfo=UTC),
        tags=("a",),
    )
    assert isinstance(sample.tags, tuple)


@pytest.mark.fast
@pytest.mark.req("NFR-PRT-01")
def test_extensions_are_the_declared_extension_point() -> None:
    """NFR-PRT-01: a domain adds fields only inside a declared extension point."""
    record = Extensible(name="x", extensions={"style-manual-wcag.wcag_level": "AA"})
    assert record.extensions["style-manual-wcag.wcag_level"] == "AA"
    assert Extensible(name="x").extensions == {}


@pytest.mark.fast
@pytest.mark.req("NFR-PRT-01")
def test_an_unnamespaced_extension_key_is_refused() -> None:
    """The failure path: without a namespace two domains could collide on one field name."""
    with pytest.raises(ValidationError, match="not namespaced"):
        Extensible(name="x", extensions={"wcag_level": "AA"})


@pytest.mark.fast
@pytest.mark.req("NFR-PRT-01")
def test_a_record_without_an_extension_point_still_refuses_extra_fields() -> None:
    """There is exactly one extension point, and `IRModel` is not it."""
    with pytest.raises(ValidationError):
        Sample(
            name="x",
            effective_from=date(2026, 1, 1),
            recorded_at=datetime(2026, 1, 1, tzinfo=UTC),
            extensions={"style-manual-wcag.x": 1},  # type: ignore[call-arg]
        )
