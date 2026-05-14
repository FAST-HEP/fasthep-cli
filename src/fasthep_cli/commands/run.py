from __future__ import annotations

from pathlib import Path

import typer
from hepflow.api import run_author_file


def run_command(
    author_yaml: Path = typer.Argument(..., exists=True, dir_okay=False),
    outdir: Path = typer.Option(..., "--outdir", file_okay=False),
    chunk_size: int | None = typer.Option(None, "--chunk-size"),
    backend: str | None = typer.Option(None, "--backend"),
    strategy: str | None = typer.Option(None, "--strategy"),
    scheduler: str | None = typer.Option(None, "--scheduler"),
    workers: int | None = typer.Option(None, "--workers"),
) -> None:
    result = run_author_file(
        author_yaml,
        outdir=outdir,
        chunk_size=chunk_size,
        backend=backend,
        strategy=strategy,
        scheduler=scheduler,
        workers=workers,
    )
    typer.echo("Run complete")
    typer.echo(f"Backend: {result.backend}.{result.strategy}")
    typer.echo(f"Summary: {outdir / 'run_summary.yaml'}")
    typer.echo(f"Artifacts: {outdir / 'artifacts'}")
