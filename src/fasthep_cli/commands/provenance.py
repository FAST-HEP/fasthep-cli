from __future__ import annotations

from enum import StrEnum
from pathlib import Path

import typer
from hepflow.api import (
    provenance_artifact_text,
    provenance_graph_text,
    provenance_summary_text,
)

provenance_app = typer.Typer(no_args_is_help=True)


class ProvenanceGraphFormat(StrEnum):
    mermaid = "mermaid"
    dot = "dot"
    json = "json"


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


@provenance_app.command("graph")
def provenance_graph_command(
    artifact_path: Path = typer.Argument(..., dir_okay=False),
    output_format: ProvenanceGraphFormat = typer.Option(
        ProvenanceGraphFormat.mermaid,
        "--format",
        help="Graph output format.",
    ),
    out: Path | None = typer.Option(
        None,
        "--out",
        dir_okay=False,
        help="Write graph output to a file instead of stdout.",
    ),
) -> None:
    try:
        text = provenance_graph_text(
            artifact_path,
            output_format=output_format.value,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        return
    typer.echo(text, nl=False)
