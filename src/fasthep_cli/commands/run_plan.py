from __future__ import annotations

from pathlib import Path

import typer
from hepflow.api import run_plan_file

from fasthep_cli.partition import (
    dataset_option,
    echo_partition_runs,
    parse_partition_numbers,
    usage_errors,
)
from fasthep_cli.progress import TerminalProgressSink


def run_plan_command(
    plan_yaml: Path = typer.Argument(..., exists=True, dir_okay=False),
    outdir: Path | None = typer.Option(None, "--outdir", file_okay=False),
    dataset: str | None = dataset_option(),
    chunk_size: int | None = typer.Option(
        None,
        "--chunk-size",
        help="Must equal the chunk size the plan was compiled with.",
    ),
    backend: str | None = typer.Option(None, "--backend"),
    strategy: str | None = typer.Option(None, "--strategy"),
    scheduler: str | None = typer.Option(None, "--scheduler"),
    workers: int | None = typer.Option(None, "--workers"),
    partition: str | None = typer.Option(
        None,
        "--partition",
        help="Run only selected 1-based partition numbers, e.g. 1 or 1,3,5.",
    ),
) -> None:
    with usage_errors():
        result = run_plan_file(
            plan_yaml,
            outdir=outdir,
            backend=backend,
            strategy=strategy,
            scheduler=scheduler,
            workers=workers,
            partition_numbers=parse_partition_numbers(partition),
            progress_sinks=[TerminalProgressSink()],
            dataset=dataset,
            chunk_size=chunk_size,
        )
    typer.echo("Run complete")
    typer.echo(f"Backend: {result.backend}.{result.strategy}")
    typer.echo(f"Summary: {result.summary['summary_path']}")
    typer.echo(f"Artifacts: {result.summary['artifacts_path']}")
    echo_partition_runs(result.summary)
