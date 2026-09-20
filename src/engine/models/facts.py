"""Fact types, probes and the values they produce (spec section 4, FR-PRB, FR-JDG)."""

from __future__ import annotations

from pydantic import Field, JsonValue, model_validator

from engine.ids import FactTypeId, ProbeId
from engine.models.base import ExtensibleModel, IRModel
from engine.models.enums import DataType, FactProvenance, Origin, ProbeCost, ProviderKind
from engine.models.epistemic import EpistemicStatus


class ArtefactRef(IRModel):
    """The artefact a probe read, by hash (FR-PRB-02, R-03)."""

    kind: str = Field(min_length=1)
    """The artefact kind, such as `html`. Domain vocabulary, so a plain string (NFR-EXT-01)."""
    path: str | None = None
    sha256: str = Field(min_length=1)


class FactType(ExtensibleModel):
    """A typed input rules depend on, with an ordered list of providers (glossary 1.5).

    `closed_world` defaults to false, so a missing fact is UNKNOWN rather than false: there is
    no negation as failure on an open-world fact (FR-QRY-01).
    """

    fact_type_id: FactTypeId
    name: str = Field(min_length=1)
    data_type: DataType
    allowed_values: tuple[JsonValue, ...] = ()
    closed_world: bool = False
    providers: tuple[ProviderKind, ...] = ()
    """Tried in this order at run time (FR-TOO-04). INV-05 refuses a rule condition on a fact
    type with none."""
    probe_id: ProbeId | None = None
    allow_inference: bool = False
    artefact_kind: str = "none"
    obtained_from: str | None = None
    origin: Origin
    epistemic: EpistemicStatus = Field(default_factory=EpistemicStatus)

    @model_validator(mode="after")
    def _enumerations_list_their_values(self) -> FactType:
        if self.data_type is DataType.ENUM and not self.allowed_values:
            raise ValueError(
                f"fact type {self.fact_type_id} is an enum with no allowed_values. List them, "
                f"or give it another data_type."
            )
        return self

    @model_validator(mode="after")
    def _a_probe_provider_names_its_probe(self) -> FactType:
        if ProviderKind.PROBE in self.providers and self.probe_id is None:
            raise ValueError(
                f"fact type {self.fact_type_id} lists `probe` as a provider but names no "
                f"probe_id. Register the probe in the domain's fact_providers.yaml and name it."
            )
        return self

    @model_validator(mode="after")
    def _inference_is_declared_once(self) -> FactType:
        listed = ProviderKind.INFERRED in self.providers
        if listed != self.allow_inference:
            raise ValueError(
                f"fact type {self.fact_type_id} has allow_inference={self.allow_inference} but "
                f"{'lists' if listed else 'does not list'} `inferred` among its providers. The "
                f"two say the same thing, so make them agree (FR-JDG-02)."
            )
        return self

    @property
    def has_provider(self) -> bool:
        """What INV-05 asks of every fact type a rule condition references."""
        return bool(self.providers)


class Probe(ExtensibleModel):
    """A deterministic function that computes fact types or abstains (glossary 1.5)."""

    probe_id: ProbeId
    implementation: str = Field(min_length=1)
    """A dotted path, such as `engine.probes.html.heading_outline` (FR-PRB-03)."""
    version: int = Field(default=1, ge=1)
    computes: tuple[FactTypeId, ...] = Field(min_length=1)
    artefact_kind: str = Field(min_length=1)
    preconditions: tuple[str, ...] = ()
    cost: ProbeCost
    abstain_reasons: tuple[str, ...] = ()
    """The reasons this probe may give for UNKNOWN. INV-09 refuses any other (FR-PRB-01)."""
    epistemic: EpistemicStatus = Field(default_factory=EpistemicStatus)


class ProbeResult(IRModel):
    """What a probe returned: a value with its artefact, or UNKNOWN with a reason (INV-09).

    The model refuses only the contradiction of being both at once. That a value carries an
    artefact reference, and that an abstention's reason is one the probe declared, are INV-09's
    to check, because the second needs the probe.
    """

    probe_id: ProbeId
    probe_version: int = Field(ge=1)
    fact_type_id: FactTypeId
    value: JsonValue = None
    artefact: ArtefactRef | None = None
    unknown_reason: str | None = None
    duration_ms: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _is_not_both_a_value_and_an_abstention(self) -> ProbeResult:
        if self.unknown_reason is not None and self.value is not None:
            raise ValueError(
                f"probe result for {self.fact_type_id} from {self.probe_id} carries both a "
                f"value and an abstain reason. A probe returns one or the other (FR-PRB-01)."
            )
        return self

    @property
    def is_abstention(self) -> bool:
        return self.unknown_reason is not None


class FactValue(IRModel):
    """A fact as the evaluator sees it, with where it came from (FR-QRY-03)."""

    fact_type_id: FactTypeId
    value: JsonValue = None
    provenance: FactProvenance
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    probe_id: ProbeId | None = None
    artefact_sha256: str | None = None
    unknown_reason: str | None = None

    @property
    def is_unknown(self) -> bool:
        """A missing fact is UNKNOWN; the evaluator never fills it (FR-QRY-01)."""
        return self.value is None
