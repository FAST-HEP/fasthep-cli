from __future__ import annotations

import json
from pathlib import Path

import typer
from hepflow.api import list_workflow_partitions, run_workflow_file
from hepflow.build_layout import compile_dir

from fasthep_cli.partition import parse_partition_numbers
from fasthep_cli.progress import TerminalProgressSink


def run_command(
    workflow_yaml: Path = typer.Argument(..., exists=True, dir_okay=False),
    outdir: Path | None = typer.Option(None, "--outdir", file_okay=False),
    chunk_size: int | None = typer.Option(None, "--chunk-size"),
    dataset: str | None = typer.Option(None, "--dataset"),
    list_partitions: bool = typer.Option(False, "--list-partitions"),
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
    if list_partitions:
        listing = list_workflow_partitions(
            workflow_yaml,
            dataset=dataset,
            chunk_size=chunk_size,
        )
        typer.echo(json.dumps(listing))
        return
    if dataset is not None:
        message = "--dataset is only supported with --list-partitions in this release."
        raise typer.BadParameter(
            message,
            param_hint="--dataset",
        )
    if outdir is None:
        message = "--outdir is required unless --list-partitions is used."
        raise typer.BadParameter(
            message,
            param_hint="--outdir",
        )
    result = run_workflow_file(
        workflow_yaml,
        outdir=outdir,
        chunk_size=chunk_size,
        backend=backend,
        strategy=strategy,
        scheduler=scheduler,
        workers=workers,
        partition_numbers=parse_partition_numbers(partition),
        progress_sinks=[TerminalProgressSink()],
    )
    if (compile_dir(outdir) / "systematics.yaml").exists():
        typer.echo(
            "Systematics plans were generated; ran nominal only. "
            "Use `fasthep run-plan` to run a specific variation."
        )
    typer.echo("Run complete")
    typer.echo(f"Backend: {result.backend}.{result.strategy}")
    typer.echo(f"Summary: {result.summary['summary_path']}")
    typer.echo(f"Artifacts: {result.summary['artifacts_path']}")
