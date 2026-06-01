from __future__ import annotations

from pathlib import Path

import typer
from hepflow.api import run_plan_file
from hepflow.build_layout import artifacts_dir, run_summary_path
from hepflow.runtime.config import default_run_outdir_for_plan


def run_plan_command(
    plan_yaml: Path = typer.Argument(..., exists=True, dir_okay=False),
    outdir: Path | None = typer.Option(None, "--outdir", file_okay=False),
    backend: str | None = typer.Option(None, "--backend"),
    strategy: str | None = typer.Option(None, "--strategy"),
    scheduler: str | None = typer.Option(None, "--scheduler"),
    workers: int | None = typer.Option(None, "--workers"),
) -> None:
    result = run_plan_file(
        plan_yaml,
        outdir=outdir,
        backend=backend,
        strategy=strategy,
        scheduler=scheduler,
        workers=workers,
    )
    summary_dir = (
        outdir if outdir is not None else default_run_outdir_for_plan(plan_yaml)
    )
    typer.echo("Run complete")
    typer.echo(f"Backend: {result.backend}.{result.strategy}")
    typer.echo(f"Summary: {run_summary_path(summary_dir)}")
    typer.echo(f"Artifacts: {artifacts_dir(summary_dir)}")
