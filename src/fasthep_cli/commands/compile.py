from __future__ import annotations

from pathlib import Path

import typer
from hepflow.api import compile_author_file
from hepflow.build_layout import compile_dir, graph_dir, normalized_path, plan_path


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
    typer.echo(f"Wrote {normalized_path(outdir)}")
    systematics_path = compile_dir(outdir) / "systematics.yaml"
    if systematics_path.exists():
        typer.echo(f"Wrote {systematics_path}")
    else:
        typer.echo(f"Wrote {plan_path(outdir)}")
        typer.echo(f"Wrote {graph_dir(outdir) / 'graph.mmd'}")
        typer.echo(f"Wrote {graph_dir(outdir) / 'graph.dot'}")
