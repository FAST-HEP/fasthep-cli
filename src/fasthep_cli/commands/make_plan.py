from __future__ import annotations

from pathlib import Path

import typer
from hepflow.api import make_plan_file


def make_plan_command(
    normalized_yaml: Path = typer.Argument(..., exists=True, dir_okay=False),
    outdir: Path = typer.Option(..., "--outdir", file_okay=False),
    chunk_size: int | None = typer.Option(None, "--chunk-size"),
) -> None:
    make_plan_file(normalized_yaml, outdir=outdir, chunk_size=chunk_size)
    typer.echo(f"Wrote {outdir / 'plan.yaml'}")
    typer.echo(f"Wrote {outdir / 'graph.mmd'}")
    typer.echo(f"Wrote {outdir / 'graph.dot'}")
