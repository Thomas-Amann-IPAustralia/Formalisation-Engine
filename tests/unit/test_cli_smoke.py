import pytest
from typer.testing import CliRunner

from engine.cli import app


@pytest.mark.fast
def test_cli_version_runs() -> None:
    result = CliRunner().invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.output.strip()
