from __future__ import annotations

from pathlib import Path

import typer
from hepflow.api import make_plan_file
from hepflow.build_layout import compile_dir, graph_dir, plan_path


def make_plan_command(
    normalized_yaml: Path = typer.Argument(..., exists=True, dir_okay=False),
    outdir: Path = typer.Option(..., "--outdir", file_okay=False),
    chunk_size: int | None = typer.Option(None, "--chunk-size"),
) -> None:
    make_plan_file(normalized_yaml, outdir=outdir, chunk_size=chunk_size)
    systematics_path = compile_dir(outdir) / "systematics.yaml"
    if systematics_path.exists():
        typer.echo(f"Wrote {systematics_path}")
    else:
        typer.echo(f"Wrote {plan_path(outdir)}")
        typer.echo(f"Wrote {graph_dir(outdir) / 'graph.mmd'}")
        typer.echo(f"Wrote {graph_dir(outdir) / 'graph.dot'}")
