"""Shared pytest configuration.

- Skips tests marked `live` unless ENGINE_ALLOW_LIVE_LLM=1 (Tom only).
- Records the outcome of every test that carries a `req` marker in var/req_results.json,
  which `python3 scripts/spec_tools.py coverage` reads.
"""

from __future__ import annotations

import json
import os
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "var" / "req_results.json"
_outcomes: dict[str, dict[str, str]] = {}
_ids_by_node: dict[str, set[str]] = {}


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if os.environ.get("ENGINE_ALLOW_LIVE_LLM") == "1":
        return
    skip_live = pytest.mark.skip(reason="live LLM test: runs only with ENGINE_ALLOW_LIVE_LLM=1")
    for item in items:
        if item.get_closest_marker("live") is not None:
            item.add_marker(skip_live)


def _req_ids(item: pytest.Item) -> list[str]:
    return [str(rid) for marker in item.iter_markers("req") for rid in marker.args]


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, Any, None]:
    outcome = yield
    report: pytest.TestReport = outcome.get_result()
    ids = _req_ids(item)
    _ids_by_node[item.nodeid] = set(ids)
    if not ids:
        return
    state: str | None = None
    if hasattr(report, "wasxfail"):
        state = "xfail" if report.skipped else "xpass"
    elif report.when == "call" or (report.when == "setup" and not report.passed):
        state = report.outcome  # passed, failed or skipped
    elif report.when == "teardown" and report.failed:
        state = "error"
    if state is None:
        return
    for rid in ids:
        _outcomes.setdefault(rid, {})[item.nodeid] = state


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if not _ids_by_node:
        return
    existing: dict[str, dict[str, str]] = {}
    if RESULTS.exists():
        try:
            existing = json.loads(RESULTS.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    # Drop stale entries: deleted test files, and tests that ran now without that ID.
    for rid in list(existing):
        kept = {
            node: state
            for node, state in existing[rid].items()
            if (ROOT / node.split("::")[0]).exists()
            and (node not in _ids_by_node or rid in _ids_by_node[node])
        }
        if kept:
            existing[rid] = kept
        else:
            del existing[rid]
    for rid, tests in _outcomes.items():
        existing.setdefault(rid, {}).update(tests)
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    tmp = RESULTS.with_suffix(".tmp")
    tmp.write_text(json.dumps(existing, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(RESULTS)
