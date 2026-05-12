from __future__ import annotations

from pathlib import Path

import typer

from hepflow.api import compile_author_file


def compile_command(
    author_yaml: Path = typer.Argument(..., exists=True, dir_okay=False),
    outdir: Path = typer.Option(..., "--outdir", file_okay=False),
    chunk_size: int | None = typer.Option(None, "--chunk-size"),
) -> None:
    compile_author_file(
        author_yaml,
        outdir=outdir,
        chunk_size=chunk_size,
    )
    typer.echo(f"Wrote {outdir / 'normalized.yaml'}")
    typer.echo(f"Wrote {outdir / 'plan.yaml'}")
    typer.echo(f"Wrote {outdir / 'graph.mmd'}")
    typer.echo(f"Wrote {outdir / 'graph.dot'}")
