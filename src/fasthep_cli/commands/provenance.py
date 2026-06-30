from __future__ import annotations

from pathlib import Path

import typer
from hepflow.api import provenance_artifact_text, provenance_summary_text

provenance_app = typer.Typer(no_args_is_help=True)


@provenance_app.command("summary")
def provenance_summary_command(
    outdir: Path = typer.Argument(..., file_okay=False),
) -> None:
    try:
        typer.echo(provenance_summary_text(outdir))
    except (FileNotFoundError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc


@provenance_app.command("show")
def provenance_show_command(
    artifact_path: Path = typer.Argument(..., dir_okay=False),
) -> None:
    try:
        typer.echo(provenance_artifact_text(artifact_path))
    except (FileNotFoundError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
