"""The IR envelope (spec section 4).

DP-03: the IR is canonical; rules, procedures, packages and indexes are compiled from it. The
envelope carries the versions and hashes that make a run reproducible (FR-CFG-03, NFR-DET-01).
"""

from __future__ import annotations

from datetime import datetime
from typing import Final

from pydantic import Field

from engine.ids import RunId, SnapshotId
from engine.models.base import ExtensibleModel
from engine.models.conflict import Conflict, Gap
from engine.models.decision_log import DecisionLogEntry
from engine.models.enums import ReconstructionMode
from engine.models.facts import FactType, Probe
from engine.models.judgement import JudgementProcedure
from engine.models.policy import AuthorityProfile, DecisionPolicy
from engine.models.proposition import Proposition
from engine.models.relations import PropositionElementRelation, PropositionPropositionRelation
from engine.models.review import Override, ReviewDecision
from engine.models.rule import Rule
from engine.models.skeleton import Skeleton
from engine.models.source import Document, Passage

#: The version of these models. Removing or renaming a field changes it (`models.md`).
IR_SCHEMA_VERSION: Final = "1.0.0"


class IR(ExtensibleModel):
    """One run's intermediate representation."""

    schema_version: str = IR_SCHEMA_VERSION
    """The version of the models this was written by."""
    ir_version: str = Field(min_length=1)
    """The version of this domain's IR content, as the package reports it (Appendix E)."""
    run_id: RunId
    snapshot_id: SnapshotId
    domain: str = Field(min_length=1)
    reconstruction_mode: ReconstructionMode
    config_hash: str = Field(min_length=1)
    policy_hash: str = Field(min_length=1)
    prompt_set_version: str = Field(min_length=1)
    created_at: datetime

    documents: tuple[Document, ...] = ()
    passages: tuple[Passage, ...] = ()
    propositions: tuple[Proposition, ...] = ()
    skeleton: Skeleton | None = None
    element_relations: tuple[PropositionElementRelation, ...] = ()
    proposition_relations: tuple[PropositionPropositionRelation, ...] = ()
    fact_types: tuple[FactType, ...] = ()
    probes: tuple[Probe, ...] = ()
    rules: tuple[Rule, ...] = ()
    judgement_procedures: tuple[JudgementProcedure, ...] = ()
    conflicts: tuple[Conflict, ...] = ()
    gaps: tuple[Gap, ...] = ()
    policies: tuple[DecisionPolicy, ...] = ()
    authority_profile: AuthorityProfile | None = None
    reviews: tuple[ReviewDecision, ...] = ()
    overrides: tuple[Override, ...] = ()
    decision_log: tuple[DecisionLogEntry, ...] = ()
