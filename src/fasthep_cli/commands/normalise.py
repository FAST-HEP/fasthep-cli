from __future__ import annotations

from pathlib import Path

import typer

from hepflow.api import normalise_author_file


def normalise_command(
    author_yaml: Path = typer.Argument(..., exists=True, dir_okay=False),
    outdir: Path = typer.Option(..., "--outdir", file_okay=False),
) -> None:
    normalise_author_file(author_yaml, outdir=outdir)
    typer.echo(f"Wrote {outdir / 'normalized.yaml'}")
