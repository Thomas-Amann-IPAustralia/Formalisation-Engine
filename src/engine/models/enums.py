"""The fixed label sets of the IR.

DP-06 is "classify, don't generate": every classification in the Engine chooses from one of the
sets below. Domain-specific vocabularies that a new domain must be free to extend without a core
change (artefact kinds, abstain reasons, authority level keys) are plain strings, not enums,
because NFR-EXT-01 says onboarding a domain needs no core code change.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final


class NormativeForce(StrEnum):
    """Appendix B. What a proposition does, and therefore what it may compile to."""

    MUST = "MUST"
    MUST_NOT = "MUST_NOT"
    SHOULD = "SHOULD"
    SHOULD_NOT = "SHOULD_NOT"
    MAY = "MAY"
    CAN = "CAN"
    DESCRIPTIVE = "DESCRIPTIVE"
    DEFINITIONAL = "DEFINITIONAL"
    EVALUATIVE_JUDGEMENT = "EVALUATIVE_JUDGEMENT"
    EXPLANATORY = "EXPLANATORY"
    EXAMPLE = "EXAMPLE"
    UNRESOLVED = "UNRESOLVED"


#: Forces that compile to a rule outright (Appendix B, FR-CMP-01). DEFINITIONAL compiles to a
#: fact derivation, which is a rule whose conclusion is a fact.
ALWAYS_COMPILABLE_FORCES: Final[frozenset[NormativeForce]] = frozenset(
    {
        NormativeForce.MUST,
        NormativeForce.MUST_NOT,
        NormativeForce.MAY,
        NormativeForce.DEFINITIONAL,
    }
)

#: Forces that compile to a rule only where the proposition is marked operative (Appendix B).
OPERATIVE_ONLY_FORCES: Final[frozenset[NormativeForce]] = frozenset(
    {NormativeForce.CAN, NormativeForce.DESCRIPTIVE}
)


def compiles_to_rule(force: NormativeForce, *, operative: bool) -> bool:
    """Whether a proposition of this force may become a rule (Appendix B, FR-CMP-01, INV-04).

    SHOULD and SHOULD_NOT become advisory notes, EVALUATIVE_JUDGEMENT a judgement procedure,
    and EXPLANATORY, EXAMPLE and UNRESOLVED nothing at all.
    """
    if force in ALWAYS_COMPILABLE_FORCES:
        return True
    return operative and force in OPERATIVE_ONLY_FORCES


class LicenceClass(StrEnum):
    """Glossary 1.5. `reference` and `excluded` sources never have stored text (INV-11)."""

    STORE = "store"
    REFERENCE = "reference"
    EXCLUDED = "excluded"


class CorpusKind(StrEnum):
    """What kind of corpus a domain is built from."""

    POLICY = "policy"
    STANDARD = "standard"
    METHODOLOGY = "methodology"


class ReconstructionMode(StrEnum):
    """Spec 1.1. Backbone-led has exactly one backbone; framework-led has none (INV-06)."""

    BACKBONE = "backbone"
    FRAMEWORK = "framework"


class SourceKind(StrEnum):
    """Where a document came from (FR-ING-01)."""

    FILE = "file"
    WEB = "web"
    REPOSITORY = "repository"
    SNAPSHOT = "snapshot"


class ParseStatus(StrEnum):
    """The S1 exit gate: every file is parsed, referenced or rejected with a reason."""

    PARSED = "parsed"
    REFERENCED = "referenced"
    REJECTED = "rejected"


class PassageType(StrEnum):
    """Spec section 4. Notes and examples inherit their force from the passage type."""

    BODY = "body"
    LIST_ITEM = "list_item"
    TABLE_CELL = "table_cell"
    NOTE = "note"
    EXAMPLE = "example"
    DEFINITION = "definition"
    TEST_RULE = "test_rule"


class ElementKind(StrEnum):
    """Spec section 4. A skeleton element asserts nothing of its own."""

    OBJECTIVE = "objective"
    STEP = "step"
    DECISION_POINT = "decision_point"
    REQUIREMENT_GROUP = "requirement_group"
    METHOD_FAMILY = "method_family"
    METHOD = "method"
    CHECK = "check"
    JUDGEMENT = "judgement"


class Origin(StrEnum):
    """Spec section 4. A file marked `edited` is only re-proposed as a diff (FR-CFG-02)."""

    DERIVED = "derived"
    PROPOSED = "proposed"
    EDITED = "edited"


class ElementStatus(StrEnum):
    """Whether an element has been confirmed. The pilot skeleton marks every element confirmed."""

    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    RETIRED = "retired"


class RelationMethod(StrEnum):
    """How a relation was arrived at (spec section 4)."""

    DETERMINISTIC = "deterministic"
    LLM = "llm"
    PANEL = "panel"
    HUMAN = "human"


class BackboneRelation(StrEnum):
    """Appendix C.1. Proposition to step, in backbone-led mode."""

    ELABORATES_STEP = "elaborates_step"
    INTRODUCES_STEP = "introduces_step"
    INTRODUCES_DECISION = "introduces_decision"
    INTRODUCES_PREREQUISITE = "introduces_prerequisite"
    INTRODUCES_EXCEPTION = "introduces_exception"
    INTRODUCES_ALTERNATIVE_PATHWAY = "introduces_alternative_pathway"
    DEFINES_TERM = "defines_term"
    SPECIFIES_AUTHORITY = "specifies_authority"
    SPECIFIES_EVIDENCE = "specifies_evidence"
    MODIFIES_RULE = "modifies_rule"
    CONTRADICTS = "contradicts"
    ESTABLISHES_DEPENDENCY = "establishes_dependency"
    CONTEXT_ONLY = "context_only"
    NO_RELATION = "no_relation"


#: Appendix C.1: the `introduces_*` types and `contradicts` are structural, so they go to triage.
STRUCTURAL_BACKBONE_RELATIONS: Final[frozenset[BackboneRelation]] = frozenset(
    {
        BackboneRelation.INTRODUCES_STEP,
        BackboneRelation.INTRODUCES_DECISION,
        BackboneRelation.INTRODUCES_PREREQUISITE,
        BackboneRelation.INTRODUCES_EXCEPTION,
        BackboneRelation.INTRODUCES_ALTERNATIVE_PATHWAY,
        BackboneRelation.CONTRADICTS,
    }
)


class FrameworkRelation(StrEnum):
    """Appendix C.3. Proposition to element, in framework-led mode."""

    STATES_REQUIREMENT = "states_requirement"
    DEFINES_CRITERION = "defines_criterion"
    PROVIDES_METHOD = "provides_method"
    PROVIDES_TEST = "provides_test"
    CONSTRAINS_METHOD = "constrains_method"
    RECOMMENDS_METHOD = "recommends_method"
    SPECIFIES_EVIDENCE = "specifies_evidence"
    DEFINES_TERM = "defines_term"
    VALIDATES_STEP = "validates_step"
    ALTERNATIVE_TO = "alternative_to"
    CONTRADICTS = "contradicts"
    CONTEXT_ONLY = "context_only"
    NO_RELATION = "no_relation"


#: Appendix C.3 names these five structural.
STRUCTURAL_FRAMEWORK_RELATIONS: Final[frozenset[FrameworkRelation]] = frozenset(
    {
        FrameworkRelation.DEFINES_CRITERION,
        FrameworkRelation.CONSTRAINS_METHOD,
        FrameworkRelation.RECOMMENDS_METHOD,
        FrameworkRelation.ALTERNATIVE_TO,
        FrameworkRelation.CONTRADICTS,
    }
)


class PropositionRelation(StrEnum):
    """Appendix C.2. Proposition to proposition."""

    SUPPORTS = "SUPPORTS"
    ELABORATES = "ELABORATES"
    QUALIFIES = "QUALIFIES"
    EXCEPTS = "EXCEPTS"
    SUPERSEDES = "SUPERSEDES"
    ALTERNATIVES = "ALTERNATIVES"
    CONTRADICTS = "CONTRADICTS"
    DUPLICATES = "DUPLICATES"
    REFERENCES = "REFERENCES"
    DEPENDS_ON = "DEPENDS_ON"
    DEFINES = "DEFINES"
    IMPLEMENTED_BY = "IMPLEMENTED_BY"


class ProviderKind(StrEnum):
    """Spec section 4. A fact type's providers, tried in this declared order (FR-TOO-04)."""

    PROBE = "probe"
    CALLER = "caller"
    INFERRED = "inferred"
    DERIVED = "derived"


class FactProvenance(StrEnum):
    """FR-QRY-03. Where a fact value actually came from, which adds `override` to the providers."""

    PROBE = "probe"
    CALLER = "caller"
    INFERRED = "inferred"
    DERIVED = "derived"
    OVERRIDE = "override"


class DataType(StrEnum):
    """The type of a fact type's value (spec section 4)."""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ENUM = "enum"
    DATE = "date"
    DURATION = "duration"


class ProbeCost(StrEnum):
    """Spec section 4. Expensive probes are opt-in (FR-PRB-02)."""

    TRIVIAL = "trivial"
    CHEAP = "cheap"
    EXPENSIVE = "expensive"


class TemporalStatus(StrEnum):
    """Spec section 4. Only `current` compiles as executable by default (FR-TMP-01)."""

    CURRENT = "current"
    HISTORICAL = "historical"
    SCHEDULED = "scheduled"
    SUPERSEDED = "superseded"
    UNKNOWN = "unknown"


class ConsistencyState(StrEnum):
    """Spec section 4, one dimension of epistemic status."""

    CONSISTENT = "consistent"
    QUALIFIED = "qualified"
    RESOLVED_BY_POLICY = "resolved_by_policy"
    ALTERNATIVES = "alternatives"
    CONFLICTED = "conflicted"


class ProvenanceKind(StrEnum):
    """Spec section 4, one dimension of epistemic status."""

    EXTRACTED = "extracted"
    INFERRED = "inferred"
    JUDGED = "judged"
    DERIVED = "derived"
    OVERRIDDEN = "overridden"


class TriageState(StrEnum):
    """Glossary 1.5 and FR-TRI-01. `blocked` happens only when an invariant fails."""

    AUTO_APPROVED = "auto_approved"
    PROVISIONAL = "provisional"
    QUEUED = "queued"
    BLOCKED = "blocked"


class ConfidenceBand(StrEnum):
    """A banded confidence. Bands, not raw probabilities, because a model's self-reported
    probability is never the sole input to a status (FR-EPI-01)."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class EpistemicOverall(StrEnum):
    """DP-05: the status that travels with every claim. Computed, never set (see `epistemic`)."""

    VERIFIED = "verified"
    PROVISIONAL = "provisional"
    INFERRED = "inferred"
    JUDGED = "judged"
    OVERRIDDEN = "overridden"
    BLOCKED = "blocked"


class PriorityBasis(StrEnum):
    """Spec section 4. Why one rule defeats another."""

    EXCEPTION = "exception"
    SPECIFIC_OVER_GENERAL = "specific_over_general"
    LATER_OVER_EARLIER = "later_over_earlier"
    HIGHER_AUTHORITY = "higher_authority"
    POLICY = "policy"
    REVIEWER = "reviewer"


class Executability(StrEnum):
    """Spec section 4. A frozen rule always carries a reason (FR-CMP-02)."""

    EXECUTABLE = "executable"
    FROZEN = "frozen"


class ConflictKind(StrEnum):
    """FR-CFL-01 detects the first four deterministically; FR-VOC-02 raises terminology."""

    NUMERIC = "numeric"
    DATE = "date"
    RESPONSIBILITY = "responsibility"
    SEQUENCE = "sequence"
    TERMINOLOGY = "terminology"
    OTHER = "other"


class DecidedBy(StrEnum):
    """Spec section 4. How a conflict was resolved, or that it was not."""

    POLICY = "policy"
    PANEL = "panel"
    REVIEWER = "reviewer"
    UNRESOLVED = "unresolved"


class GapKind(StrEnum):
    """Spec section 4 and FR-GAP-01."""

    MISSING_FACT_SOURCE = "missing_fact_source"
    MISSING_THRESHOLD = "missing_threshold"
    MISSING_OUTCOME = "missing_outcome"
    MISSING_DEFINITION = "missing_definition"
    EMPTY_ELEMENT = "empty_element"
    UNREACHABLE_BRANCH = "unreachable_branch"
    DANGLING_REFERENCE = "dangling_reference"


class PolicyScope(StrEnum):
    """Spec section 4. What a decision policy governs."""

    CONFLICTS = "conflicts"
    ALTERNATIVES = "alternatives"
    JUDGEMENT_DEFAULTS = "judgement_defaults"


class PolicyKind(StrEnum):
    """Spec section 4. The shape of a policy's definition depends on this."""

    AUTHORITY_ORDER = "authority_order"
    RISK_MATRIX = "risk_matrix"
    CONSERVATIVE = "conservative"


class ReviewOutcome(StrEnum):
    """Spec section 4 and FR-REV-01. Reject, modify and override all require a rationale."""

    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"
    OVERRIDE = "override"
    DEFER = "defer"


class DecisionKind(StrEnum):
    """What a decision log entry records (INV-12)."""

    POLICY_INVOCATION = "policy_invocation"
    JUDGEMENT = "judgement"
    OVERRIDE = "override"


class SlotResolution(StrEnum):
    """FR-VOC-01. Whether a slot's raw text resolved to a concept."""

    UNRESOLVED = "unresolved"
    CONFIRMED = "confirmed"
    FLAGGED = "flagged"


class ConditionOperator(StrEnum):
    """The comparisons a rule condition may make against a fact value."""

    EQ = "eq"
    NE = "ne"
    LT = "lt"
    LTE = "lte"
    GT = "gt"
    GTE = "gte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    MATCHES = "matches"
    EXISTS = "exists"


class AssertionStatus(StrEnum):
    """Appendix E `applies[].status`. Three-valued, because a missing fact is UNKNOWN
    (FR-QRY-01)."""

    SATISFIED = "satisfied"
    NOT_SATISFIED = "not_satisfied"
    UNKNOWN = "unknown"


class RequestMode(StrEnum):
    """Appendix E `options.mode` (FR-TOO-04)."""

    ANSWER = "answer"
    PLAN = "plan"


class ToolSurface(StrEnum):
    """FR-TOO-01. One implementation behind three surfaces."""

    PYTHON = "python"
    MCP = "mcp"
    CLI = "cli"


class ConflictStatus(StrEnum):
    """Where a conflict has got to (spec section 4)."""

    OPEN = "open"
    RESOLVED = "resolved"
    ALTERNATIVES = "alternatives"
    OVERRIDDEN = "overridden"


class GapStatus(StrEnum):
    """Where a gap has got to. A spent budget leaves it unresolved (FR-GAP-01)."""

    OPEN = "open"
    RESOLVED = "resolved"
    BUDGET_EXHAUSTED = "budget_exhausted"


class PolicyInputSource(StrEnum):
    """Where a policy gets one of its inputs (`inputs_from` in decision_policy.yaml)."""

    CALLER = "caller"
    JUDGEMENT = "judgement"
    PROBE = "probe"
    INFERRED = "inferred"
    DERIVED = "derived"


#: INV-03: every decision carries this outcome, with an edge.
UNABLE_TO_DETERMINE: Final = "unable_to_determine"
