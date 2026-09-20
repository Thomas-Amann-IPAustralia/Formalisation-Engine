"""Command-line entry point (FR-OPS-01). Stage commands are added as the stages are built."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Annotated

import typer

from engine import schema_export

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Policy and Process Formalisation Engine.",
)


@app.callback()
def main() -> None:
    """Formalisation Engine command line."""


@app.command()
def version() -> None:
    """Print the installed version."""
    try:
        typer.echo(package_version("formalisation-engine"))
    except PackageNotFoundError:
        typer.echo("unknown")


schema_app = typer.Typer(
    no_args_is_help=True,
    help="JSON Schema generated from the models (NFR-INT-01).",
)
app.add_typer(schema_app, name="schema")


@schema_app.command("export")
def schema_export_command(
    root: Annotated[
        Path,
        typer.Option("--root", help="Where the schemas are published."),
    ] = Path("schema"),
    check: Annotated[
        bool,
        typer.Option("--check", help="Report drift and exit non-zero instead of writing."),
    ] = False,
) -> None:
    """Write the IR and contract schemas, or check the committed ones are current.

    `schema/` is generated, not written by hand. CI and the unit tests run --check, so a model
    change that is not exported fails before it reaches anyone.
    """
    if check:
        reports = schema_export.drift(root)
        if reports:
            for report in reports:
                typer.echo(report, err=True)
            typer.echo(
                f"{len(reports)} schema file(s) differ from the models. "
                f"Run `uv run engine schema export` and commit the result.",
                err=True,
            )
            raise typer.Exit(code=1)
        typer.echo("Schemas are current.")
        return
    for relative in schema_export.write(root):
        typer.echo(f"wrote {root / relative}")
