"""The base every IR record is built on.

Records are frozen and reject unknown fields. Frozen because DP-03 makes the IR canonical and
NFR-DET-01 wants byte-identical replay: a record that cannot be mutated in place cannot drift
from the identifier hashed out of it. `extra="forbid"` because a field the models do not know
about is either a typo or a schema change, and both should be loud (DP-04).

Note that freezing is shallow. Sequence fields are declared as tuples so that they are immutable
too; `extensions` is a mapping and is not, so nothing hashes an extensible record.
"""

from __future__ import annotations

import re
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator

#: An extension key is `<namespace>.<field>`, where the namespace is normally the domain slug.
#: Namespacing is what makes this a *declared* extension point rather than a loophole: two
#: domains can add a field of the same name without colliding (NFR-PRT-01, NFR-EXT-01).
EXTENSION_KEY_PATTERN: Final = re.compile(r"^[a-z0-9][a-z0-9_-]*\.[A-Za-z0-9][A-Za-z0-9_.-]*$")


class IRModel(BaseModel):
    """Every record in the IR and in the tool contract."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        validate_default=True,
        use_enum_values=False,
        str_strip_whitespace=False,
    )


class ExtensibleModel(IRModel):
    """An IR record with the one extension point a domain may add fields inside.

    NFR-PRT-01: "a domain adds fields only inside declared extension points". This is that
    point, and there is no other: everywhere else `extra="forbid"` refuses an unknown field.
    The contract models deliberately do not inherit from this, because DP-11 fixes the contract
    shape across every domain.
    """

    extensions: dict[str, JsonValue] = Field(
        default_factory=dict,
        description=(
            "Domain-specific fields, keyed '<namespace>.<field>'. The only place a domain may "
            "add to a record without a core change (NFR-PRT-01)."
        ),
    )

    @field_validator("extensions")
    @classmethod
    def _keys_are_namespaced(cls, value: dict[str, JsonValue]) -> dict[str, JsonValue]:
        bad = sorted(key for key in value if EXTENSION_KEY_PATTERN.match(key) is None)
        if bad:
            raise ValueError(
                f"extension keys {bad} on {cls.__name__} are not namespaced. Use "
                f"'<namespace>.<field>', for example 'style-manual-wcag.wcag_level', so two "
                f"domains cannot collide."
            )
        return value
