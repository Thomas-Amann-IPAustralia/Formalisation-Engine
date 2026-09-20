"""The Appendix D invariants, checked on every IR write.

DP-04 decides the shape of this module: a violation blocks the record, never the run. So
nothing here raises. Every check returns violations and the caller records them, marks the
record `blocked` (FR-TRI-01) and carries on.

Some of what the invariants say is already impossible to express: a conflict needs two
propositions, a decision log entry names what decided it. Those guards live on the models. What
is left here is what a single record cannot know about itself, which is most of it.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from typing import Final, Protocol, assert_never

from engine.models.base import IRModel
from engine.models.conflict import Conflict, Gap
from engine.models.contract import Citation, ToolResponse
from engine.models.decision_log import DecisionLogEntry
from engine.models.enums import (
    UNABLE_TO_DETERMINE,
    ConflictStatus,
    DecidedBy,
    DecisionKind,
    ElementKind,
    LicenceClass,
    NormativeForce,
    ReconstructionMode,
    TriageState,
    compiles_to_rule,
)
from engine.models.facts import FactType, Probe, ProbeResult
from engine.models.ir import IR
from engine.models.judgement import JudgementProcedure
from engine.models.policy import AuthorityProfile
from engine.models.proposition import Proposition
from engine.models.rule import Rule
from engine.models.skeleton import SkeletonElement
from engine.models.source import Document, Passage

#: Forces that compile to an advisory note rather than an obligation (Appendix B, G3).
ADVISORY_FORCES: Final[frozenset[NormativeForce]] = frozenset(
    {NormativeForce.SHOULD, NormativeForce.SHOULD_NOT}
)

#: Licence classes whose text is never stored (glossary 1.5, FR-ING-04).
UNSTORED_LICENCES: Final[frozenset[LicenceClass]] = frozenset(
    {LicenceClass.REFERENCE, LicenceClass.EXCLUDED}
)


class Violation(IRModel):
    """One invariant failing on one record.

    The message names the record and the invariant; the remedy says what to do. Both end up in
    the stage report, which is where a person reads them (NFR-REL-01).
    """

    invariant_id: str
    record_kind: str
    record_id: str
    message: str
    remedy: str


class InvariantSpec(IRModel):
    """What an invariant says and what it applies to, for introspection and reporting."""

    invariant_id: str
    text: str
    record_kinds: tuple[str, ...]


#: Appendix D, verbatim, with the record kinds each check runs over. `ir` means the check needs
#: the whole IR rather than one record.
INVARIANTS: Final[Mapping[str, InvariantSpec]] = {
    spec.invariant_id: spec
    for spec in (
        InvariantSpec(
            invariant_id="INV-01",
            text="Every proposition has a verified verbatim span.",
            record_kinds=("proposition",),
        ),
        InvariantSpec(
            invariant_id="INV-02",
            text=(
                "Every node, rule, judgement procedure and conflict has a source proposition; "
                "every gap has a target and a search record."
            ),
            record_kinds=("element", "rule", "judgement_procedure", "conflict", "gap"),
        ),
        InvariantSpec(
            invariant_id="INV-03",
            text="Every decision has an `unable_to_determine` outcome with an edge.",
            record_kinds=("element", "judgement_procedure"),
        ),
        InvariantSpec(
            invariant_id="INV-04",
            text=("No compiled rule comes from a non-compilable force or a blocked proposition."),
            record_kinds=("rule",),
        ),
        InvariantSpec(
            invariant_id="INV-05",
            text="Every rule condition references a fact type with a provider.",
            record_kinds=("rule",),
        ),
        InvariantSpec(
            invariant_id="INV-06",
            text=(
                "Backbone-led has exactly one backbone; framework-led none. Every document has "
                "an authority level and a licence class."
            ),
            record_kinds=("document", "ir"),
        ),
        InvariantSpec(
            invariant_id="INV-07",
            text=(
                "Defeat relations are acyclic; members of an alternatives set never defeat "
                "each other."
            ),
            record_kinds=("ir",),
        ),
        InvariantSpec(
            invariant_id="INV-08",
            text="Judgement nodes are decided only by their procedure or an override.",
            record_kinds=("element",),
        ),
        InvariantSpec(
            invariant_id="INV-09",
            text=(
                "A probe result is a value with an artefact reference or UNKNOWN with a "
                "declared reason."
            ),
            record_kinds=("probe_result",),
        ),
        InvariantSpec(
            invariant_id="INV-10",
            text="Every tool assertion carries a citation that resolves to a passage.",
            record_kinds=("tool_response",),
        ),
        InvariantSpec(
            invariant_id="INV-11",
            text="No stored text for a `reference` or `excluded` source.",
            record_kinds=("passage",),
        ),
        InvariantSpec(
            invariant_id="INV-12",
            text=(
                "Every policy invocation, judgement and override is in the decision log with "
                "its inputs, and an override beats an automated decision on an unchanged "
                "record."
            ),
            record_kinds=("ir",),
        ),
    )
}


class IRLookup(Protocol):
    """What an invariant needs beyond the record in front of it.

    This is the seam. `engine.stores` implements it in M2 without any check changing, and
    `IRIndex` below is the in-memory implementation the tests and M1's hand-built IR use.
    """

    def document(self, document_id: str) -> Document | None: ...

    def passage(self, passage_id: str) -> Passage | None: ...

    def proposition(self, proposition_id: str) -> Proposition | None: ...

    def element(self, element_id: str) -> SkeletonElement | None: ...

    def fact_type(self, fact_type_id: str) -> FactType | None: ...

    def probe(self, probe_id: str) -> Probe | None: ...

    def judgement_procedure(self, procedure_id: str) -> JudgementProcedure | None: ...

    def authority_profile(self) -> AuthorityProfile | None: ...

    def record_exists(self, record_id: str) -> bool: ...


class IRIndex:
    """An in-memory `IRLookup` over one IR."""

    def __init__(self, ir: IR) -> None:
        self.ir = ir
        self._documents = {one.document_id: one for one in ir.documents}
        self._passages = {one.passage_id: one for one in ir.passages}
        self._propositions = {one.proposition_id: one for one in ir.propositions}
        self._elements = (
            {one.element_id: one for one in ir.skeleton.elements} if ir.skeleton else {}
        )
        self._fact_types = {one.fact_type_id: one for one in ir.fact_types}
        self._probes = {one.probe_id: one for one in ir.probes}
        self._procedures = {one.procedure_id: one for one in ir.judgement_procedures}
        self._rules = {one.rule_id: one for one in ir.rules}
        self._conflicts = {one.conflict_id: one for one in ir.conflicts}
        self._gaps = {one.gap_id: one for one in ir.gaps}

    def document(self, document_id: str) -> Document | None:
        return self._documents.get(document_id)

    def passage(self, passage_id: str) -> Passage | None:
        return self._passages.get(passage_id)

    def proposition(self, proposition_id: str) -> Proposition | None:
        return self._propositions.get(proposition_id)

    def element(self, element_id: str) -> SkeletonElement | None:
        return self._elements.get(element_id)

    def fact_type(self, fact_type_id: str) -> FactType | None:
        return self._fact_types.get(fact_type_id)

    def probe(self, probe_id: str) -> Probe | None:
        return self._probes.get(probe_id)

    def judgement_procedure(self, procedure_id: str) -> JudgementProcedure | None:
        return self._procedures.get(procedure_id)

    def authority_profile(self) -> AuthorityProfile | None:
        return self.ir.authority_profile

    def record_exists(self, record_id: str) -> bool:
        return any(
            record_id in known
            for known in (
                self._documents,
                self._passages,
                self._propositions,
                self._elements,
                self._fact_types,
                self._probes,
                self._procedures,
                self._rules,
                self._conflicts,
                self._gaps,
            )
        )


def _violation(
    invariant_id: str, record_kind: str, record_id: str, message: str, remedy: str
) -> Violation:
    return Violation(
        invariant_id=invariant_id,
        record_kind=record_kind,
        record_id=record_id,
        message=message,
        remedy=remedy,
    )


def check_proposition(proposition: Proposition, lookup: IRLookup) -> Iterator[Violation]:
    """INV-01. Every proposition has a verified verbatim span."""
    span = proposition.span
    if not span.verified:
        yield _violation(
            "INV-01",
            "proposition",
            proposition.proposition_id,
            f"proposition {proposition.proposition_id} carries an unverified span into "
            f"passage {span.passage_id}.",
            "S3 verifies a span by exact match against the passage and rejects it otherwise "
            "(FR-EXT-02). Re-extract the passage or drop the proposition.",
        )
    passage = lookup.passage(span.passage_id)
    if passage is None:
        yield _violation(
            "INV-01",
            "proposition",
            proposition.proposition_id,
            f"proposition {proposition.proposition_id} quotes passage {span.passage_id}, "
            f"which is not in the IR.",
            "Write the passage before the proposition, or correct the span's passage.",
        )
        return
    if passage.text is None:
        return
    quoted = passage.text[span.start : span.end]
    if quoted != span.text:
        yield _violation(
            "INV-01",
            "proposition",
            proposition.proposition_id,
            f"proposition {proposition.proposition_id} quotes {span.text!r} at "
            f"{span.start}:{span.end} of passage {span.passage_id}, which holds {quoted!r}.",
            "The quotation is not verbatim. Reject the proposition and log it (FR-EXT-02, G6).",
        )


def check_passage(passage: Passage, lookup: IRLookup) -> Iterator[Violation]:
    """INV-11. No stored text for a `reference` or `excluded` source."""
    document = lookup.document(passage.document_id)
    if document is None:
        yield _violation(
            "INV-11",
            "passage",
            passage.passage_id,
            f"passage {passage.passage_id} belongs to document {passage.document_id}, which "
            f"is not in the IR, so its licence class cannot be checked.",
            "Write the document before its passages.",
        )
        return
    if document.licence_class in UNSTORED_LICENCES and passage.text:
        yield _violation(
            "INV-11",
            "passage",
            passage.passage_id,
            f"passage {passage.passage_id} stores text from {document.document_id}, which is "
            f"licence class {document.licence_class.value}.",
            "A reference source is fetched at run time and keeps only URI, hash, anchors and "
            "quotations within its licence note; an excluded source is never fetched "
            "(FR-ING-04, G11). Clear the text.",
        )


def check_document(document: Document, lookup: IRLookup) -> Iterator[Violation]:
    """INV-06, second clause. Every document has an authority level and a licence class."""
    profile = lookup.authority_profile()
    if profile is None:
        yield _violation(
            "INV-06",
            "document",
            document.document_id,
            f"document {document.document_id} claims authority level "
            f"{document.authority_level!r} but the IR carries no authority profile.",
            "Load the domain's authority_profile.yaml into the IR (FR-AUT-01).",
        )
        return
    if profile.level(document.authority_level) is None:
        known = ", ".join(level.key for level in profile.levels)
        yield _violation(
            "INV-06",
            "document",
            document.document_id,
            f"document {document.document_id} claims authority level "
            f"{document.authority_level!r}, which the profile does not define.",
            f"Use one of: {known}. An authority level that is not in the profile is as good "
            f"as none (FR-AUT-01).",
        )


def check_element(element: SkeletonElement, lookup: IRLookup) -> Iterator[Violation]:
    """INV-02 (a node has a source proposition), INV-03 (a decision can decline) and INV-08."""
    yield from _sources_resolve(
        "INV-02", "element", element.element_id, element.source_propositions, lookup
    )
    if element.is_decision:
        yield from _decision_can_decline(element, lookup)
    if element.kind is ElementKind.JUDGEMENT:
        yield from _judgement_node_is_decided_by_its_procedure(element, lookup)


def _decision_can_decline(element: SkeletonElement, lookup: IRLookup) -> Iterator[Violation]:
    outcome = element.unable_to_determine
    if outcome is None:
        offered = ", ".join(one.name for one in element.outcomes) or "none"
        yield _violation(
            "INV-03",
            "element",
            element.element_id,
            f"decision {element.element_id} offers {offered} and no "
            f"{UNABLE_TO_DETERMINE!r} outcome.",
            f"Add an {UNABLE_TO_DETERMINE!r} outcome. A decision the facts cannot settle has "
            f"to have somewhere to go (FR-QRY-01).",
        )
        return
    if outcome.target_element_id is None:
        yield _violation(
            "INV-03",
            "element",
            element.element_id,
            f"decision {element.element_id} has an {UNABLE_TO_DETERMINE!r} outcome with no "
            f"edge out of it.",
            "Point the outcome at the element that handles it. INV-03 wants an edge, not only "
            "a label.",
        )
    elif lookup.element(outcome.target_element_id) is None:
        yield _violation(
            "INV-03",
            "element",
            element.element_id,
            f"decision {element.element_id} sends {UNABLE_TO_DETERMINE!r} to "
            f"{outcome.target_element_id}, which is not in the skeleton.",
            "Point it at an element that exists, or add the element.",
        )


def _judgement_node_is_decided_by_its_procedure(
    element: SkeletonElement, lookup: IRLookup
) -> Iterator[Violation]:
    if element.rule_set_id is not None:
        yield _violation(
            "INV-08",
            "element",
            element.element_id,
            f"judgement node {element.element_id} is attached to rule set {element.rule_set_id!r}.",
            "A judgement node is decided by its procedure or by an override, never by rules "
            "(DP-08). Clear rule_set_id.",
        )
    if element.judgement_procedure_id is None:
        yield _violation(
            "INV-08",
            "element",
            element.element_id,
            f"judgement node {element.element_id} names no judgement procedure.",
            "Give it the procedure that decides it (FR-JDG-01).",
        )
    elif lookup.judgement_procedure(element.judgement_procedure_id) is None:
        yield _violation(
            "INV-08",
            "element",
            element.element_id,
            f"judgement node {element.element_id} names procedure "
            f"{element.judgement_procedure_id}, which is not in the IR.",
            "Write the procedure, or point the node at one that exists.",
        )


def check_rule(rule: Rule, lookup: IRLookup) -> Iterator[Violation]:
    """INV-02 (a rule has a source proposition), INV-04 and INV-05."""
    yield from _sources_resolve("INV-02", "rule", rule.rule_id, rule.source_propositions, lookup)
    for proposition_id in rule.source_propositions:
        proposition = lookup.proposition(proposition_id)
        if proposition is None:
            continue
        yield from _source_is_compilable(rule, proposition)
    for fact_type_id in sorted(rule.fact_types_used):
        yield from _condition_has_a_provider(rule, fact_type_id, lookup)


def _source_is_compilable(rule: Rule, proposition: Proposition) -> Iterator[Violation]:
    if proposition.epistemic.triage is TriageState.BLOCKED:
        yield _violation(
            "INV-04",
            "rule",
            rule.rule_id,
            f"rule {rule.rule_id} compiles from proposition "
            f"{proposition.proposition_id}, which is blocked.",
            "A blocked proposition failed an invariant and never compiles (FR-TRI-01). Fix "
            "the proposition or drop the rule.",
        )
    force = proposition.normative_force
    if rule.advisory:
        if force not in ADVISORY_FORCES:
            yield _violation(
                "INV-04",
                "rule",
                rule.rule_id,
                f"advisory note {rule.rule_id} comes from proposition "
                f"{proposition.proposition_id}, whose force is {force.value}.",
                "Only SHOULD and SHOULD_NOT compile to advisory notes (Appendix B, FR-CMP-01).",
            )
        return
    if not compiles_to_rule(force, operative=proposition.operative):
        detail = (
            " and is not marked operative"
            if force in {NormativeForce.CAN, NormativeForce.DESCRIPTIVE}
            else ""
        )
        yield _violation(
            "INV-04",
            "rule",
            rule.rule_id,
            f"rule {rule.rule_id} compiles from proposition "
            f"{proposition.proposition_id}, whose force is {force.value}{detail}.",
            "MUST, MUST_NOT, MAY and DEFINITIONAL compile to rules; SHOULD is advisory, "
            "EVALUATIVE_JUDGEMENT is a judgement procedure, and EXPLANATORY, EXAMPLE and "
            "UNRESOLVED compile to nothing (Appendix B, G3).",
        )


def _condition_has_a_provider(
    rule: Rule, fact_type_id: str, lookup: IRLookup
) -> Iterator[Violation]:
    fact_type = lookup.fact_type(fact_type_id)
    if fact_type is None:
        yield _violation(
            "INV-05",
            "rule",
            rule.rule_id,
            f"rule {rule.rule_id} has a condition on fact type {fact_type_id}, which is not "
            f"in the IR.",
            "Propose the fact type and a provider for it (FR-SKL-03); the rule stays "
            "provisional until one is confirmed (FR-CMP-02).",
        )
    elif not fact_type.has_provider:
        yield _violation(
            "INV-05",
            "rule",
            rule.rule_id,
            f"rule {rule.rule_id} has a condition on fact type {fact_type_id}, which has no "
            f"provider.",
            "Give it an ordered provider list: probe, caller, inferred or derived "
            "(FR-TOO-04). A fact type with no provider can never be settled.",
        )


def check_judgement_procedure(
    procedure: JudgementProcedure, lookup: IRLookup
) -> Iterator[Violation]:
    """INV-02 (a procedure has a source proposition) and INV-03 (it can decline)."""
    yield from _sources_resolve(
        "INV-02",
        "judgement_procedure",
        procedure.procedure_id,
        procedure.source_propositions,
        lookup,
    )
    if not procedure.output_schema.can_decline:
        offered = ", ".join(procedure.output_schema.outcomes)
        yield _violation(
            "INV-03",
            "judgement_procedure",
            procedure.procedure_id,
            f"judgement procedure {procedure.procedure_id} offers {offered} and no "
            f"{UNABLE_TO_DETERMINE!r} outcome.",
            f"Add {UNABLE_TO_DETERMINE!r} to the output schema. A procedure that cannot "
            f"decline will invent an answer (FR-JDG-03).",
        )


def check_conflict(conflict: Conflict, lookup: IRLookup) -> Iterator[Violation]:
    """INV-02. Every conflict has a source proposition."""
    yield from _sources_resolve(
        "INV-02", "conflict", conflict.conflict_id, conflict.proposition_ids, lookup
    )


def check_gap(gap: Gap, lookup: IRLookup) -> Iterator[Violation]:
    """INV-02. Every gap has a target and a search record."""
    if gap.search_record is None:
        yield _violation(
            "INV-02",
            "gap",
            gap.gap_id,
            f"gap {gap.gap_id} records no search.",
            "A gap says what was searched and not found, never that the information does not "
            "exist. Record the queries and candidates (FR-GAP-01).",
        )
    elif not gap.search_record.searched_something:
        yield _violation(
            "INV-02",
            "gap",
            gap.gap_id,
            f"gap {gap.gap_id} has a search record with no queries in it.",
            "Record the queries that were run, so the gap can cite them (FR-RET-01).",
        )
    if gap.target_id is not None and not lookup.record_exists(gap.target_id):
        yield _violation(
            "INV-02",
            "gap",
            gap.gap_id,
            f"gap {gap.gap_id} targets {gap.target_id}, which is not in the IR.",
            "Point the gap at a record that exists, or leave target_id unset and describe the "
            "target in words.",
        )


def check_probe_result(result: ProbeResult, lookup: IRLookup) -> Iterator[Violation]:
    """INV-09. A value with an artefact reference, or UNKNOWN with a declared reason."""
    record_id = f"{result.probe_id}/{result.fact_type_id}"
    probe = lookup.probe(result.probe_id)
    if probe is None:
        yield _violation(
            "INV-09",
            "probe_result",
            record_id,
            f"probe result from {result.probe_id} has no registered probe in the IR.",
            "Register the probe in the domain's fact_providers.yaml (FR-PRB-03).",
        )
    elif result.fact_type_id not in probe.computes:
        computes = ", ".join(probe.computes)
        yield _violation(
            "INV-09",
            "probe_result",
            record_id,
            f"probe {result.probe_id} returned {result.fact_type_id}, which it does not "
            f"declare computing.",
            f"It declares {computes}. Add the fact type to `computes` or fix the probe.",
        )
    if result.is_abstention:
        if probe is not None and result.unknown_reason not in probe.abstain_reasons:
            declared = ", ".join(probe.abstain_reasons) or "none"
            yield _violation(
                "INV-09",
                "probe_result",
                record_id,
                f"probe {result.probe_id} abstained with reason "
                f"{result.unknown_reason!r}, which it does not declare.",
                f"It declares {declared}. A probe abstains for a declared reason, never an "
                f"ad hoc one (FR-PRB-01).",
            )
        return
    if result.value is None:
        yield _violation(
            "INV-09",
            "probe_result",
            record_id,
            f"probe {result.probe_id} returned neither a value nor an abstain reason for "
            f"{result.fact_type_id}.",
            "A probe returns a value or UNKNOWN with a reason, never a default or an estimate "
            "(FR-PRB-01, G10).",
        )
    if result.artefact is None:
        yield _violation(
            "INV-09",
            "probe_result",
            record_id,
            f"probe {result.probe_id} returned a value for {result.fact_type_id} with no "
            f"artefact reference.",
            "Record the artefact and its hash. A wrong probe poisons every rule using it, so "
            "every value names what it was computed from (FR-PRB-02, R-03).",
        )


def check_tool_response(response: ToolResponse, lookup: IRLookup) -> Iterator[Violation]:
    """INV-10. Every tool assertion carries a citation that resolves to a passage."""
    for assertion_id, citations in response.assertions_with_citations:
        if not citations:
            yield _violation(
                "INV-10",
                "tool_response",
                assertion_id,
                f"{assertion_id} is asserted with no citation.",
                "Every assertion cites a passage in the snapshot; the tool adds nothing the "
                "IR does not contain (FR-TOO-03).",
            )
            continue
        for citation in citations:
            yield from _citation_resolves(assertion_id, citation, lookup)


def _citation_resolves(
    assertion_id: str, citation: Citation, lookup: IRLookup
) -> Iterator[Violation]:
    if citation.passage_id is None:
        yield _violation(
            "INV-10",
            "tool_response",
            assertion_id,
            f"{assertion_id} cites {citation.document} at {citation.anchor!r} without a "
            f"passage identifier, so the citation cannot be resolved.",
            "Carry the passage identifier on the citation. Document and anchor are how a "
            "person reads a citation, not how it resolves (ADR-0005).",
        )
        return
    if lookup.passage(citation.passage_id) is None:
        yield _violation(
            "INV-10",
            "tool_response",
            assertion_id,
            f"{assertion_id} cites passage {citation.passage_id}, which is not in the snapshot.",
            "A citation resolves to a passage in the snapshot the package was built from "
            "(FR-PRV-01).",
        )


def _sources_resolve(
    invariant_id: str,
    record_kind: str,
    record_id: str,
    proposition_ids: Iterable[str],
    lookup: IRLookup,
) -> Iterator[Violation]:
    """INV-02's common half: named source propositions exist, and there is at least one."""
    ids = tuple(proposition_ids)
    if not ids:
        yield _violation(
            invariant_id,
            record_kind,
            record_id,
            f"{record_kind} {record_id} has no source proposition.",
            "Nothing exists in the IR without a proposition behind it (NFR-SAF-01). Record "
            "which passage it came from, or remove it.",
        )
        return
    for proposition_id in ids:
        if lookup.proposition(proposition_id) is None:
            yield _violation(
                invariant_id,
                record_kind,
                record_id,
                f"{record_kind} {record_id} names source proposition {proposition_id}, which "
                f"is not in the IR.",
                "Write the proposition first, or correct the reference.",
            )


def check_backbone_count(ir: IR) -> Iterator[Violation]:
    """INV-06, first clause. Backbone-led has exactly one backbone; framework-led none."""
    backbones = [one.document_id for one in ir.documents if one.is_backbone]
    mode = ir.reconstruction_mode
    if mode is ReconstructionMode.BACKBONE and len(backbones) != 1:
        found = ", ".join(backbones) or "none"
        yield _violation(
            "INV-06",
            "ir",
            ir.run_id,
            f"backbone-led run {ir.run_id} has {len(backbones)} backbone documents ({found}).",
            "Backbone-led mode derives the skeleton from exactly one document. Mark one, or "
            "switch the domain to framework-led (FR-CFG-01).",
        )
    if mode is ReconstructionMode.FRAMEWORK and backbones:
        found = ", ".join(backbones)
        yield _violation(
            "INV-06",
            "ir",
            ir.run_id,
            f"framework-led run {ir.run_id} marks {found} as a backbone.",
            "Framework-led mode has no backbone; the Engine proposes the framework and the "
            "corpus populates it (spec 1.1). Clear is_backbone.",
        )


_WHITE, _GREY, _BLACK = 0, 1, 2


def _canonical_cycle(cycle: tuple[str, ...]) -> tuple[str, ...]:
    """The same cycle written the same way whichever node it was found from."""
    start = min(range(len(cycle)), key=lambda index: cycle[index])
    return cycle[start:] + cycle[:start]


def _cycles(adjacency: Mapping[str, tuple[str, ...]]) -> list[tuple[str, ...]]:
    """Every distinct cycle a depth-first search reaches, reported once each.

    Written out rather than taken from NetworkX, which is a base dependency but belongs to the
    compile and validate toolchain (`.claude/rules/compile.md`); NFR-PRT-01 keeps the IR free
    of it. Iterative rather than recursive so that a deep graph cannot raise out of a checker
    that DP-04 requires never to stop the run.
    """
    colour: dict[str, int] = dict.fromkeys(adjacency, _WHITE)
    found: list[tuple[str, ...]] = []
    seen: set[tuple[str, ...]] = set()
    for root in sorted(adjacency):
        if colour[root] != _WHITE:
            continue
        colour[root] = _GREY
        path: list[str] = [root]
        stack: list[tuple[str, Iterator[str]]] = [(root, iter(adjacency[root]))]
        while stack:
            node, successors = stack[-1]
            descended = False
            for successor in successors:
                if successor not in colour:
                    continue  # an edge to a rule that is not in the IR: INV-02's business
                if colour[successor] == _WHITE:
                    colour[successor] = _GREY
                    path.append(successor)
                    stack.append((successor, iter(adjacency[successor])))
                    descended = True
                    break
                if colour[successor] == _GREY:
                    cycle = _canonical_cycle(tuple(path[path.index(successor) :]))
                    if cycle not in seen:
                        seen.add(cycle)
                        found.append(cycle)
            if not descended:
                colour[node] = _BLACK
                path.pop()
                stack.pop()
    return found


def check_defeats(ir: IR) -> Iterator[Violation]:
    """INV-07. Defeats are acyclic, and alternatives never defeat each other."""
    adjacency = {
        rule.rule_id: tuple(defeat.defeated_rule_id for defeat in rule.defeats) for rule in ir.rules
    }
    for cycle in _cycles(adjacency):
        shown = " defeats ".join((*cycle, cycle[0]))
        yield _violation(
            "INV-07",
            "ir",
            cycle[0],
            f"defeat relations form a cycle: {shown}.",
            "Defeat is a priority ordering, so it cannot come back to where it started. "
            "Decide which rule wins and remove the other edge.",
        )

    sets: dict[str, list[str]] = {}
    for rule in ir.rules:
        if rule.alternatives_set_id is not None:
            sets.setdefault(rule.alternatives_set_id, []).append(rule.rule_id)
    for set_id, members in sets.items():
        within = set(members)
        for rule in ir.rules:
            if rule.rule_id not in within:
                continue
            for defeat in rule.defeats:
                if defeat.defeated_rule_id in within:
                    yield _violation(
                        "INV-07",
                        "ir",
                        set_id,
                        f"rule {rule.rule_id} defeats {defeat.defeated_rule_id} and both are "
                        f"alternatives in {set_id}.",
                        "Alternatives compile as mutually exclusive guarded options with no "
                        "defeat between them; at run time the policy chooses, or the options "
                        "are returned with their conditions (FR-CFL-03).",
                    )


def check_decision_log(ir: IR) -> Iterator[Violation]:
    """INV-12. Every policy invocation, judgement and override is logged with its inputs, and
    an override beats an automated decision on an unchanged record."""
    entries = ir.decision_log
    for conflict in ir.conflicts:
        if conflict.resolution.decided_by is not DecidedBy.POLICY:
            continue
        yield from _logged(
            entries,
            kind=DecisionKind.POLICY_INVOCATION,
            subject_id=conflict.conflict_id,
            record_kind="conflict",
            what=f"policy {conflict.resolution.policy_id} resolving conflict "
            f"{conflict.conflict_id}",
        )
    for judgement in ir.judgement_records:
        yield from _logged(
            entries,
            kind=DecisionKind.JUDGEMENT,
            subject_id=judgement.procedure_id,
            record_kind="judgement",
            what=f"the judgement {judgement.outcome!r} from procedure {judgement.procedure_id}",
        )
    for override in ir.overrides:
        yield from _logged(
            entries,
            kind=DecisionKind.OVERRIDE,
            subject_id=override.target_id,
            record_kind="override",
            what=f"override {override.override_id} on {override.target_id}",
        )
        yield from _override_wins(ir, override.target_id, override.override_id)


def _logged(
    entries: Iterable[DecisionLogEntry],
    *,
    kind: DecisionKind,
    subject_id: str,
    record_kind: str,
    what: str,
) -> Iterator[Violation]:
    matching = [entry for entry in entries if entry.kind is kind and entry.subject_id == subject_id]
    if not matching:
        yield _violation(
            "INV-12",
            record_kind,
            subject_id,
            f"{what} is not in the decision log.",
            "Write the policy, inputs, decision and rationale to the log as the decision is "
            "made (FR-CFL-02, FR-TOO-05).",
        )
        return
    for entry in matching:
        if entry.inputs:
            continue
        yield _violation(
            "INV-12",
            record_kind,
            subject_id,
            f"{what} is logged by entry {entry.entry_id} without its inputs.",
            "INV-12 wants the inputs on the entry that records the decision, so it can be "
            "re-made and audited. Another entry for the same subject carrying inputs does "
            "not cover this one.",
        )


def _override_wins(ir: IR, target_id: str, override_id: str) -> Iterator[Violation]:
    for conflict in ir.conflicts:
        if conflict.conflict_id != target_id:
            continue
        if (
            conflict.resolution.decided_by is DecidedBy.POLICY
            and conflict.status is not ConflictStatus.OVERRIDDEN
        ):
            yield _violation(
                "INV-12",
                "conflict",
                conflict.conflict_id,
                f"conflict {conflict.conflict_id} is overridden by {override_id} but still "
                f"stands as resolved by policy {conflict.resolution.policy_id}.",
                "An override beats an automated decision on an unchanged record. Set the "
                "conflict's status to overridden (FR-CFL-04, DP-08).",
            )


#: Every record kind an invariant runs over. `engine.stores` checks one of these on each write.
CheckableRecord = (
    Document
    | Passage
    | Proposition
    | SkeletonElement
    | Rule
    | JudgementProcedure
    | Conflict
    | Gap
    | ProbeResult
    | ToolResponse
)


def check_record(record: CheckableRecord, lookup: IRLookup) -> tuple[Violation, ...]:
    """Every invariant that applies to one record (`models.md`: checked on every IR write).

    Returns violations; never raises (DP-04). Whole-IR invariants — the backbone count, the
    defeat graph and decision log coverage — cannot be decided from one record and are in
    `check_ir`.
    """
    if isinstance(record, Document):
        return tuple(check_document(record, lookup))
    if isinstance(record, Passage):
        return tuple(check_passage(record, lookup))
    if isinstance(record, Proposition):
        return tuple(check_proposition(record, lookup))
    if isinstance(record, SkeletonElement):
        return tuple(check_element(record, lookup))
    if isinstance(record, Rule):
        return tuple(check_rule(record, lookup))
    if isinstance(record, JudgementProcedure):
        return tuple(check_judgement_procedure(record, lookup))
    if isinstance(record, Conflict):
        return tuple(check_conflict(record, lookup))
    if isinstance(record, Gap):
        return tuple(check_gap(record, lookup))
    if isinstance(record, ProbeResult):
        return tuple(check_probe_result(record, lookup))
    if isinstance(record, ToolResponse):
        return tuple(check_tool_response(record, lookup))
    assert_never(record)


def check_ir(ir: IR) -> tuple[Violation, ...]:
    """Every invariant, over a whole IR. Returns violations; never raises (DP-04)."""
    lookup = IRIndex(ir)
    found: list[Violation] = []
    for document in ir.documents:
        found.extend(check_document(document, lookup))
    for passage in ir.passages:
        found.extend(check_passage(passage, lookup))
    for proposition in ir.propositions:
        found.extend(check_proposition(proposition, lookup))
    if ir.skeleton is not None:
        for element in ir.skeleton.elements:
            found.extend(check_element(element, lookup))
    for rule in ir.rules:
        found.extend(check_rule(rule, lookup))
    for procedure in ir.judgement_procedures:
        found.extend(check_judgement_procedure(procedure, lookup))
    for conflict in ir.conflicts:
        found.extend(check_conflict(conflict, lookup))
    for gap in ir.gaps:
        found.extend(check_gap(gap, lookup))
    found.extend(check_backbone_count(ir))
    found.extend(check_defeats(ir))
    found.extend(check_decision_log(ir))
    return tuple(found)
