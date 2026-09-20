"""JSON Schema generated from the models (NFR-MNT-01, NFR-INT-01).

`schema/` is generated and committed. These tests are what stop it drifting: a model change
that is not exported fails here before it reaches CI.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from engine import schema_export
from engine.cli import app
from engine.models.contract import CONTRACT_VERSION
from engine.models.ir import IR_SCHEMA_VERSION

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = REPO_ROOT / "schema"


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01", "NFR-MNT-01")
def test_the_committed_schemas_match_the_models() -> None:
    """If this fails, run `uv run engine schema export` and commit the result."""
    assert schema_export.drift(SCHEMA_ROOT) == ()


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
def test_the_schemas_are_published_per_version() -> None:
    """NFR-INT-01: IR schema and contract schema published per version."""
    assert set(schema_export.generate()) == {
        f"ir/{IR_SCHEMA_VERSION}/ir.schema.json",
        f"contract/{CONTRACT_VERSION}/request.schema.json",
        f"contract/{CONTRACT_VERSION}/response.schema.json",
    }


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01")
def test_every_schema_carries_a_resolvable_identifier() -> None:
    for relative, content in schema_export.generate().items():
        document = json.loads(content)
        assert document["$id"] == f"{schema_export.BASE_IRI}{relative}"
        assert document["$schema"] == schema_export.JSON_SCHEMA_DIALECT
        assert document["title"]


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_the_ir_schema_carries_the_computed_status() -> None:
    """Serialisation mode, because `overall` is computed and a validation-mode schema would
    leave it out of the published IR."""
    ir_schema = json.loads(schema_export.generate()[f"ir/{IR_SCHEMA_VERSION}/ir.schema.json"])
    assert "overall" in ir_schema["$defs"]["EpistemicStatus"]["properties"]


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_generation_is_byte_deterministic(tmp_path: Path) -> None:
    """A diff on a generated file should mean a model changed and nothing else."""
    schema_export.write(tmp_path)
    first = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in sorted(tmp_path.rglob("*.json"))
    }
    schema_export.write(tmp_path)
    second = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in sorted(tmp_path.rglob("*.json"))
    }
    assert first == second
    assert first, "the exporter wrote nothing"


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_drift_is_reported_as_a_diff(tmp_path: Path) -> None:
    """The failure path: a directory with no schemas in it is entirely out of date."""
    reports = schema_export.drift(tmp_path)
    assert len(reports) == 3
    assert all("(from the models)" in report for report in reports)


@pytest.mark.fast
@pytest.mark.req("NFR-INT-01", "NFR-MNT-01")
def test_the_cli_checks_and_writes(tmp_path: Path) -> None:
    runner = CliRunner()

    missing = runner.invoke(app, ["schema", "export", "--root", str(tmp_path), "--check"])
    assert missing.exit_code == 1

    written = runner.invoke(app, ["schema", "export", "--root", str(tmp_path)])
    assert written.exit_code == 0
    assert "wrote" in written.output

    current = runner.invoke(app, ["schema", "export", "--root", str(tmp_path), "--check"])
    assert current.exit_code == 0
    assert "Schemas are current." in current.output


@pytest.mark.fast
@pytest.mark.req("NFR-MNT-01")
def test_the_cli_reports_a_stale_schema(tmp_path: Path) -> None:
    """A committed schema that no longer matches its model is named, with the diff."""
    schema_export.write(tmp_path)
    stale = tmp_path / f"ir/{IR_SCHEMA_VERSION}/ir.schema.json"
    stale.write_text('{"$id": "wrong"}\n', encoding="utf-8")

    result = CliRunner().invoke(app, ["schema", "export", "--root", str(tmp_path), "--check"])
    assert result.exit_code == 1
    assert "ir.schema.json" in result.output
    assert "engine schema export" in result.output
