"""Documents and passages (spec section 4, FR-ING, FR-SEG)."""

from __future__ import annotations

from datetime import date

from pydantic import Field, model_validator

from engine.ids import ConceptId, DocumentId, PassageId
from engine.models.base import ExtensibleModel, IRModel
from engine.models.enums import LicenceClass, ParseStatus, PassageType, SourceKind
from engine.models.epistemic import EpistemicStatus


class Document(ExtensibleModel):
    """One source document in a snapshot.

    `authority_level` is a key into the domain's authority profile and `licence_class` decides
    whether text may be stored at all; INV-06 checks both, and INV-11 enforces the second.
    """

    document_id: DocumentId
    title: str = Field(min_length=1)
    document_type: str = Field(min_length=1)
    """Domain vocabulary, such as `standard`, `test_rule`, `technique` or `guidance`."""
    authority_level: str = Field(min_length=1)
    """A level key from the domain's authority profile (INV-06, FR-AUT-01)."""
    is_backbone: bool = False
    """Backbone-led mode has exactly one of these; framework-led has none (INV-06)."""
    source_kind: SourceKind
    source_uri: str = Field(min_length=1)
    source_ref: str | None = None
    """The commit a repository is pinned to, or the version of a web source (FR-ING-01)."""
    content_hash: str | None = None
    licence_class: LicenceClass
    licence_note: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    parse_status: ParseStatus
    parse_note: str | None = None
    """Why a document was rejected or only referenced (FR-ING-03)."""
    required: bool = False
    epistemic: EpistemicStatus = Field(default_factory=EpistemicStatus)

    @model_validator(mode="after")
    def _rejected_documents_say_why(self) -> Document:
        if self.parse_status is ParseStatus.REJECTED and not self.parse_note:
            raise ValueError(
                f"document {self.document_id} is rejected without a reason. FR-ING-03 requires "
                f"a rejected file to record why; set parse_note."
            )
        return self

    @model_validator(mode="after")
    def _effective_dates_are_ordered(self) -> Document:
        if (
            self.effective_from is not None
            and self.effective_to is not None
            and self.effective_to < self.effective_from
        ):
            raise ValueError(
                f"document {self.document_id} has effective_to {self.effective_to} before "
                f"effective_from {self.effective_from}. Correct the dates in the manifest."
            )
        return self


class Anchor(IRModel):
    """Where a passage sits in its document. Every anchor resolves to one location
    (FR-SEG-01)."""

    section: str | None = None
    paragraph: int | None = Field(default=None, ge=0)
    list_path: tuple[int, ...] = ()
    table_cell: str | None = None
    page: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _locates_something(self) -> Anchor:
        if not any(
            (
                self.section is not None,
                self.paragraph is not None,
                self.list_path,
                self.table_cell is not None,
                self.page is not None,
            )
        ):
            raise ValueError(
                "an anchor with no section, paragraph, list path, table cell or page locates "
                "nothing. Give it at least one component (FR-SEG-01)."
            )
        return self


class Passage(ExtensibleModel):
    """A unit of segmented source text (FR-SEG-01).

    `text` is None for a `reference` or `excluded` source, which is what INV-11 checks. Source
    text is recoverable from the anchor and offsets either way (FR-ING-02).
    """

    passage_id: PassageId
    document_id: DocumentId
    anchor: Anchor
    heading_path: tuple[str, ...] = ()
    passage_type: PassageType
    text: str | None = None
    start_offset: int | None = Field(default=None, ge=0)
    end_offset: int | None = Field(default=None, ge=0)
    parent_passage_id: PassageId | None = None
    cross_references: tuple[str, ...] = ()
    definitions_in_scope: tuple[ConceptId, ...] = ()
    epistemic: EpistemicStatus = Field(default_factory=EpistemicStatus)

    @model_validator(mode="after")
    def _offsets_are_ordered(self) -> Passage:
        if (
            self.start_offset is not None
            and self.end_offset is not None
            and self.end_offset < self.start_offset
        ):
            raise ValueError(
                f"passage {self.passage_id} has end_offset {self.end_offset} before "
                f"start_offset {self.start_offset}. Re-segment the document (S2)."
            )
        return self

    @model_validator(mode="after")
    def _is_not_its_own_parent(self) -> Passage:
        if self.parent_passage_id == self.passage_id:
            raise ValueError(
                f"passage {self.passage_id} is its own parent. A split passage's parent is the "
                f"passage it was split from (FR-SEG-01)."
            )
        return self
