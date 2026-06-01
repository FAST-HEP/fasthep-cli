from __future__ import annotations

from pathlib import Path

import typer
from hepflow.api import run_author_file
from hepflow.build_layout import artifacts_dir, compile_dir, run_summary_path


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
    summary_dir = outdir
    if (compile_dir(outdir) / "systematics.yaml").exists():
        typer.echo(
            "Systematics plans were generated; ran nominal only. "
            "Use `fasthep run-plan` to run a specific variation."
        )
    typer.echo("Run complete")
    typer.echo(f"Backend: {result.backend}.{result.strategy}")
    typer.echo(f"Summary: {run_summary_path(summary_dir)}")
    typer.echo(f"Artifacts: {artifacts_dir(summary_dir)}")
