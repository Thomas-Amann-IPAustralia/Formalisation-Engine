"""A small IR that satisfies every invariant, and the pieces to break one at a time.

Not a test module: pytest collects `test_*.py` only. The shape follows Appendix A's worked
example, so the fixtures read like the domain rather than like placeholders.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from engine.models.conflict import Conflict, Gap, Resolution, SearchQuery, SearchRecord
from engine.models.decision_log import DecisionLogEntry
from engine.models.enums import (
    UNABLE_TO_DETERMINE,
    ConditionOperator,
    ConflictKind,
    ConflictStatus,
    CorpusKind,
    DataType,
    DecidedBy,
    DecisionKind,
    ElementKind,
    GapKind,
    LicenceClass,
    NormativeForce,
    Origin,
    ParseStatus,
    PassageType,
    ProbeCost,
    ProviderKind,
    ReconstructionMode,
    SourceKind,
)
from engine.models.facts import FactType, Probe
from engine.models.ir import IR
from engine.models.judgement import (
    Consideration,
    JudgementOutputSchema,
    JudgementProcedure,
)
from engine.models.policy import AuthorityLevel, AuthorityProfile
from engine.models.proposition import Proposition, Span
from engine.models.rule import Conclusion, FactCondition, Rule
from engine.models.skeleton import Outcome, Skeleton, SkeletonElement
from engine.models.source import Anchor, Document, Passage

NOW = datetime(2026, 9, 20, tzinfo=UTC)

ORDER_TEXT = "Heading levels must not be skipped."
ORDER_QUOTE = "must not be skipped"
ORDER_START = ORDER_TEXT.index(ORDER_QUOTE)

SHORT_TEXT = "Headings should be short."
SHORT_QUOTE = "should be short"
SHORT_START = SHORT_TEXT.index(SHORT_QUOTE)

DOC = "DOC-STYLE-MANUAL"
PAS_ORDER = "PAS-0a1b2c3d4e5f6071"
PAS_SHORT = "PAS-0a1b2c3d4e5f6072"
PROP_ORDER = "PROP-0a1b2c3d4e5f6071"
PROP_SHORT = "PROP-0a1b2c3d4e5f6072"


def authority_profile() -> AuthorityProfile:
    return AuthorityProfile(
        corpus_kind=CorpusKind.STANDARD,
        levels=(
            AuthorityLevel(key="guidance", label="Australian Government Style Manual", rank=3),
        ),
    )


def document(**changes: Any) -> Document:
    return Document(
        **{
            "document_id": DOC,
            "title": "Australian Government Style Manual",
            "document_type": "guidance",
            "authority_level": "guidance",
            "source_kind": SourceKind.WEB,
            "source_uri": "https://www.stylemanual.gov.au/",
            "licence_class": LicenceClass.STORE,
            "parse_status": ParseStatus.PARSED,
            **changes,
        }
    )


def passage(passage_id: str, text: str, section: str, **changes: Any) -> Passage:
    return Passage(
        **{
            "passage_id": passage_id,
            "document_id": DOC,
            "anchor": Anchor(section=section),
            "passage_type": PassageType.BODY,
            "text": text,
            **changes,
        }
    )


def proposition(
    proposition_id: str,
    passage_id: str,
    text: str,
    quote: str,
    force: NormativeForce,
    **changes: Any,
) -> Proposition:
    start = text.index(quote)
    return Proposition(
        **{
            "proposition_id": proposition_id,
            "passage_id": passage_id,
            "span": Span(
                passage_id=passage_id,
                start=start,
                end=start + len(quote),
                text=quote,
                verified=True,
            ),
            "normative_force": force,
            **changes,
        }
    )


def fact_type(**changes: Any) -> FactType:
    return FactType(
        **{
            "fact_type_id": "FACT-heading_levels_skipped",
            "name": "heading_levels_skipped",
            "data_type": DataType.NUMBER,
            "providers": (ProviderKind.PROBE,),
            "probe_id": "PRB-html-heading-outline",
            "artefact_kind": "html",
            "origin": Origin.EDITED,
            **changes,
        }
    )


def probe(**changes: Any) -> Probe:
    return Probe(
        **{
            "probe_id": "PRB-html-heading-outline",
            "implementation": "engine.probes.html.heading_outline",
            "computes": ("FACT-heading_levels_skipped",),
            "artefact_kind": "html",
            "cost": ProbeCost.CHEAP,
            "abstain_reasons": ("artefact_not_parseable", "no_headings_found"),
            **changes,
        }
    )


def skeleton(**changes: Any) -> Skeleton:
    elements = (
        SkeletonElement(
            element_id="EL-page-structure",
            kind=ElementKind.OBJECTIVE,
            label="Page structure and headings",
            origin=Origin.EDITED,
            source_propositions=(PROP_ORDER,),
        ),
        SkeletonElement(
            element_id="EL-heading-order",
            kind=ElementKind.DECISION_POINT,
            parent_element_id="EL-page-structure",
            label="Are heading levels used in order?",
            origin=Origin.EDITED,
            source_propositions=(PROP_ORDER,),
            outcomes=(
                Outcome(name="yes", target_element_id="EL-heading-check"),
                Outcome(name="no", target_element_id="EL-heading-check"),
                Outcome(name=UNABLE_TO_DETERMINE, target_element_id="EL-heading-check"),
            ),
        ),
        SkeletonElement(
            element_id="EL-heading-describes",
            kind=ElementKind.JUDGEMENT,
            parent_element_id="EL-page-structure",
            label="Do headings describe the content that follows?",
            origin=Origin.EDITED,
            source_propositions=(PROP_SHORT,),
            judgement_procedure_id="JDG-heading-describes",
        ),
        SkeletonElement(
            element_id="EL-heading-check",
            kind=ElementKind.CHECK,
            parent_element_id="EL-page-structure",
            label="How to test heading structure",
            origin=Origin.EDITED,
            source_propositions=(PROP_ORDER,),
        ),
    )
    return Skeleton(
        **{
            "skeleton_id": "SKEL-ux-standards",
            "version": 1,
            "mode": ReconstructionMode.FRAMEWORK,
            "origin": Origin.EDITED,
            "elements": elements,
            **changes,
        }
    )


def order_rule(**changes: Any) -> Rule:
    return Rule(
        **{
            "rule_id": "RULE-heading-order",
            "rule_set_id": "page-structure",
            "statement": ORDER_TEXT,
            "conditions": FactCondition(
                fact_type_id="FACT-heading_levels_skipped",
                operator=ConditionOperator.GT,
                value=0,
            ),
            "conclusion": Conclusion(statement="Heading order is not satisfied."),
            "source_propositions": (PROP_ORDER,),
            **changes,
        }
    )


def short_rule(**changes: Any) -> Rule:
    return Rule(
        **{
            "rule_id": "RULE-heading-short",
            "rule_set_id": "page-structure",
            "statement": SHORT_TEXT,
            "conclusion": Conclusion(statement="Headings should be short."),
            "source_propositions": (PROP_SHORT,),
            "advisory": True,
            **changes,
        }
    )


def procedure(**changes: Any) -> JudgementProcedure:
    return JudgementProcedure(
        **{
            "procedure_id": "JDG-heading-describes",
            "question": "Do the headings describe their sections?",
            "considerations": (
                Consideration(
                    text="A heading names what follows it.", source_proposition_id=PROP_SHORT
                ),
            ),
            "prompt_id": "judgement/heading-describes",
            "prompt_version": 1,
            "output_schema": JudgementOutputSchema(
                outcomes=("yes", "mostly", "no", UNABLE_TO_DETERMINE)
            ),
            "source_propositions": (PROP_SHORT,),
            **changes,
        }
    )


def gap(**changes: Any) -> Gap:
    return Gap(
        **{
            "gap_id": "GAP-heading-length-threshold",
            "kind": GapKind.MISSING_THRESHOLD,
            "target": "a maximum heading length",
            "search_record": SearchRecord(
                queries=(SearchQuery(query="maximum heading length", method="hybrid"),),
                calls_spent=3,
            ),
            **changes,
        }
    )


def resolved_conflict(**changes: Any) -> Conflict:
    return Conflict(
        **{
            "conflict_id": "CFL-heading-length",
            "kind": ConflictKind.NUMERIC,
            "proposition_ids": (PROP_ORDER, PROP_SHORT),
            "resolution": Resolution(
                decided_by=DecidedBy.POLICY,
                policy_id="POL-ux-stricter-wins",
                decision="serve the stricter requirement",
                rationale="equal-ranked sources, impact high",
                inputs={"impact_on_users": "high", "effort_to_fix": "low"},
                hook="policy.invoked",
            ),
            "status": ConflictStatus.RESOLVED,
            **changes,
        }
    )


def policy_log_entry(**changes: Any) -> DecisionLogEntry:
    return DecisionLogEntry(
        **{
            "entry_id": "DEC-0a1b2c3d4e5f6071",
            "recorded_at": NOW,
            "kind": DecisionKind.POLICY_INVOCATION,
            "subject_id": "CFL-heading-length",
            "policy_id": "POL-ux-stricter-wins",
            "inputs": {"impact_on_users": "high", "effort_to_fix": "low"},
            "decision": "serve the stricter requirement",
            "rationale": "equal-ranked sources, impact high",
            "decided_by": "engine",
            "hook": "policy.invoked",
            **changes,
        }
    )


def valid_ir(**changes: Any) -> IR:
    """An IR that every invariant is happy with. Change one thing to break one thing."""
    return IR(
        **{
            "ir_version": "0.1.0",
            "run_id": "RUN-20260920T0000Z",
            "snapshot_id": "SNAP-0a1b2c3d4e5f6071",
            "domain": "style-manual-wcag",
            "reconstruction_mode": ReconstructionMode.FRAMEWORK,
            "config_hash": "c0ffee",
            "policy_hash": "beef",
            "prompt_set_version": "1",
            "created_at": NOW,
            "documents": (document(),),
            "passages": (
                passage(PAS_ORDER, ORDER_TEXT, "headings"),
                passage(PAS_SHORT, SHORT_TEXT, "headings"),
            ),
            "propositions": (
                proposition(
                    PROP_ORDER, PAS_ORDER, ORDER_TEXT, ORDER_QUOTE, NormativeForce.MUST_NOT
                ),
                proposition(PROP_SHORT, PAS_SHORT, SHORT_TEXT, SHORT_QUOTE, NormativeForce.SHOULD),
            ),
            "skeleton": skeleton(),
            "fact_types": (fact_type(),),
            "probes": (probe(),),
            "rules": (order_rule(), short_rule()),
            "judgement_procedures": (procedure(),),
            "conflicts": (resolved_conflict(),),
            "gaps": (gap(),),
            "authority_profile": authority_profile(),
            "decision_log": (policy_log_entry(),),
            **changes,
        }
    )
