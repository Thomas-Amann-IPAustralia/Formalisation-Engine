"""Property-based tests for the invariants (NFR-TST-01).

NFR-TST-01 asks for property tests on defeat ordering. INV-07's cycle detection is the piece
worth generating cases for: a hand-written example only ever covers the shape its author
thought of.
"""

from __future__ import annotations

import itertools
from collections.abc import Mapping

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from engine.models.enums import PriorityBasis
from engine.models.invariants import check_ir
from engine.models.rule import Defeat
from tests.unit.ir_builders import PROP_ORDER, order_rule, valid_ir

RULE_IDS = tuple(f"RULE-r{index}" for index in range(6))

#: A defeat graph as a set of edges between distinct rules. A rule defeating itself is refused
#: by the model, so it never reaches the checker and is not generated here.
edge_sets = st.sets(
    st.tuples(st.sampled_from(RULE_IDS), st.sampled_from(RULE_IDS)).filter(
        lambda pair: pair[0] != pair[1]
    ),
    max_size=12,
)


def adjacency_of(edges: set[tuple[str, str]]) -> dict[str, tuple[str, ...]]:
    return {
        rule_id: tuple(sorted(target for source, target in edges if source == rule_id))
        for rule_id in RULE_IDS
    }


def has_cycle(adjacency: Mapping[str, tuple[str, ...]]) -> bool:
    """Kahn's algorithm: a graph is acyclic exactly when a topological order exists.

    Deliberately a different algorithm from the depth-first search the checker uses, so the
    two agreeing means something.
    """
    indegree = dict.fromkeys(adjacency, 0)
    for successors in adjacency.values():
        for successor in successors:
            indegree[successor] += 1
    queue = [node for node, degree in indegree.items() if degree == 0]
    settled = 0
    while queue:
        node = queue.pop()
        settled += 1
        for successor in adjacency[node]:
            indegree[successor] -= 1
            if indegree[successor] == 0:
                queue.append(successor)
    return settled != len(indegree)


def ir_with(edges: set[tuple[str, str]]) -> object:
    adjacency = adjacency_of(edges)
    rules = tuple(
        order_rule(
            rule_id=rule_id,
            conditions=None,
            source_propositions=(PROP_ORDER,),
            defeats=tuple(
                Defeat(
                    defeated_rule_id=target,
                    priority_basis=PriorityBasis.EXCEPTION,
                    rationale="generated",
                )
                for target in adjacency[rule_id]
            ),
        )
        for rule_id in RULE_IDS
    )
    return valid_ir(rules=rules)


@pytest.mark.req("INV-07")
@settings(max_examples=200, deadline=None)
@given(edges=edge_sets)
def test_inv_07_agrees_with_a_topological_sort(edges: set[tuple[str, str]]) -> None:
    reported = [one for one in check_ir(ir_with(edges)) if one.invariant_id == "INV-07"]
    assert bool(reported) == has_cycle(adjacency_of(edges))


@pytest.mark.req("INV-07")
@settings(max_examples=200, deadline=None)
@given(edges=edge_sets)
def test_inv_07_never_raises(edges: set[tuple[str, str]]) -> None:
    """DP-04: a violation blocks the record, never the run. Nothing here may raise."""
    violations = check_ir(ir_with(edges))
    for violation in violations:
        assert violation.invariant_id.startswith("INV-")
        assert violation.message
        assert violation.remedy


@pytest.mark.req("INV-07")
@settings(max_examples=100, deadline=None)
@given(edges=edge_sets)
def test_every_reported_cycle_is_a_real_cycle(edges: set[tuple[str, str]]) -> None:
    """A checker that over-reports would block records that are fine."""
    adjacency = adjacency_of(edges)
    for violation in check_ir(ir_with(edges)):
        if violation.invariant_id != "INV-07" or "form a cycle" not in violation.message:
            continue
        path = violation.message.split(": ", 1)[1].rstrip(".").split(" defeats ")
        assert path[0] == path[-1], "a reported cycle comes back to where it started"
        for source, target in itertools.pairwise(path):
            assert target in adjacency[source], f"{source} does not defeat {target}"
