"""Command-line entry point (FR-OPS-01). Stage commands are added as the stages are built."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version

import typer

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
