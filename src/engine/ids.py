"""Type-prefixed identifiers (spec section 4).

Passage and proposition identifiers are content hashes, so a re-run over unchanged content
yields the same identifier. Every identifier converts to an IRI and back (NFR-INT-01).

The prefix set, the hash scheme and the base IRI are recorded in ADR-0005.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from enum import StrEnum
from typing import Annotated, Final

from pydantic import StringConstraints


class IdKind(StrEnum):
    """Identifier prefixes.

    The first thirteen are the list in spec section 4. The last four are used by the spec
    without appearing in that list, and are added by ADR-0005.
    """

    DOCUMENT = "DOC"
    PASSAGE = "PAS"
    PROPOSITION = "PROP"
    CONCEPT = "CON"
    ELEMENT = "EL"
    RULE = "RULE"
    JUDGEMENT = "JDG"
    FACT_TYPE = "FACT"
    PROBE = "PRB"
    CONFLICT = "CFL"
    GAP = "GAP"
    POLICY = "POL"
    REVIEW = "REV"

    SNAPSHOT = "SNAP"
    """Appendix E carries `"snapshot_id": "SNAP-..."`."""

    SKELETON = "SKEL"
    """`framework_skeleton.yaml` carries `skeleton_id: SKEL-ux-standards`."""

    RUN = "RUN"
    """Spec section 4: the IR carries a `run_id`."""

    DECISION = "DEC"
    """An entry in the append-only decision log (INV-12)."""


#: The identifier part after the prefix. Underscores are allowed because the pilot's fact type
#: identifiers use them (`FACT-heading_levels_skipped`).
SUFFIX_PATTERN: Final = r"[A-Za-z0-9][A-Za-z0-9._-]*"

#: Identifiers resolve under this base (NFR-INT-01, "IDs convertible to IRIs").
BASE_IRI: Final = "https://formalisation.engine/id/"

#: Hex characters kept from the SHA-256 digest of a content hash. Sixteen is 64 bits: for the
#: pilot's order of 3,000 passages the chance of any collision is about 2.4e-13 (ADR-0005).
CONTENT_HASH_LENGTH: Final = 16

_PREFIXES: Final = "|".join(sorted((k.value for k in IdKind), key=len, reverse=True))
_ID_RE: Final = re.compile(rf"^(?P<kind>{_PREFIXES})-(?P<suffix>{SUFFIX_PATTERN})$")
_SUFFIX_RE: Final = re.compile(rf"^{SUFFIX_PATTERN}$")


def _pattern_for(kind: IdKind) -> str:
    """The anchored regular expression one kind of identifier must match."""
    return rf"^{kind.value}-{SUFFIX_PATTERN}$"


def is_id(value: str, kind: IdKind | None = None) -> bool:
    """Whether `value` is a well-formed identifier, optionally of one kind."""
    match = _ID_RE.match(value)
    if match is None:
        return False
    return kind is None or match.group("kind") == kind.value


def parse_id(value: str) -> tuple[IdKind, str]:
    """Split an identifier into its kind and suffix.

    Raises `ValueError` naming the value and what a well-formed identifier looks like.
    """
    match = _ID_RE.match(value)
    if match is None:
        raise ValueError(
            f"{value!r} is not an identifier. Expected one of "
            f"{', '.join(k.value for k in IdKind)} followed by '-' and "
            f"{SUFFIX_PATTERN}, for example 'EL-page-structure'."
        )
    return IdKind(match.group("kind")), match.group("suffix")


def kind_of(value: str) -> IdKind:
    """The kind of an identifier. Raises `ValueError` if it is not well formed."""
    return parse_id(value)[0]


def make_id(kind: IdKind, suffix: str) -> str:
    """Build an identifier from a kind and an author-chosen suffix.

    Use this for identifiers a person or the Engine names, such as `EL-page-structure`. Use
    `content_id` for passages and propositions, whose identifiers are content hashes.
    """
    if _SUFFIX_RE.match(suffix) is None:
        raise ValueError(
            f"{suffix!r} cannot follow {kind.value}-. A suffix starts with a letter or digit "
            f"and continues with letters, digits, '.', '_' or '-'."
        )
    return f"{kind.value}-{suffix}"


def content_id(kind: IdKind, *parts: str) -> str:
    """Build a content-hash identifier, so the same content yields the same identifier.

    Each part is normalised to Unicode NFC and joined with the unit separator before hashing,
    so the separator can never appear inside a part and change what a boundary means.
    """
    if not parts:
        raise ValueError(
            f"content_id({kind.value}) needs at least one part to hash. Pass the fields that "
            f"identify the record, in a fixed order."
        )
    canonical = "\x1f".join(unicodedata.normalize("NFC", part) for part in parts)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:CONTENT_HASH_LENGTH]
    return f"{kind.value}-{digest}"


def to_iri(identifier: str) -> str:
    """The IRI for an identifier (NFR-INT-01). Raises `ValueError` if it is not well formed."""
    parse_id(identifier)
    return f"{BASE_IRI}{identifier}"


def from_iri(iri: str) -> str:
    """The identifier an IRI denotes. The inverse of `to_iri`."""
    if not iri.startswith(BASE_IRI):
        raise ValueError(
            f"{iri!r} is not an Engine identifier IRI. Engine identifiers start with {BASE_IRI}."
        )
    identifier = iri.removeprefix(BASE_IRI)
    parse_id(identifier)
    return identifier


DocumentId = Annotated[str, StringConstraints(pattern=_pattern_for(IdKind.DOCUMENT))]
PassageId = Annotated[str, StringConstraints(pattern=_pattern_for(IdKind.PASSAGE))]
PropositionId = Annotated[str, StringConstraints(pattern=_pattern_for(IdKind.PROPOSITION))]
ConceptId = Annotated[str, StringConstraints(pattern=_pattern_for(IdKind.CONCEPT))]
ElementId = Annotated[str, StringConstraints(pattern=_pattern_for(IdKind.ELEMENT))]
RuleId = Annotated[str, StringConstraints(pattern=_pattern_for(IdKind.RULE))]
JudgementId = Annotated[str, StringConstraints(pattern=_pattern_for(IdKind.JUDGEMENT))]
FactTypeId = Annotated[str, StringConstraints(pattern=_pattern_for(IdKind.FACT_TYPE))]
ProbeId = Annotated[str, StringConstraints(pattern=_pattern_for(IdKind.PROBE))]
ConflictId = Annotated[str, StringConstraints(pattern=_pattern_for(IdKind.CONFLICT))]
GapId = Annotated[str, StringConstraints(pattern=_pattern_for(IdKind.GAP))]
PolicyId = Annotated[str, StringConstraints(pattern=_pattern_for(IdKind.POLICY))]
ReviewId = Annotated[str, StringConstraints(pattern=_pattern_for(IdKind.REVIEW))]
SnapshotId = Annotated[str, StringConstraints(pattern=_pattern_for(IdKind.SNAPSHOT))]
SkeletonId = Annotated[str, StringConstraints(pattern=_pattern_for(IdKind.SKELETON))]
RunId = Annotated[str, StringConstraints(pattern=_pattern_for(IdKind.RUN))]
DecisionId = Annotated[str, StringConstraints(pattern=_pattern_for(IdKind.DECISION))]
