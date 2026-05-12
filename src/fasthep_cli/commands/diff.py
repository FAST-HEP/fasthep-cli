from __future__ import annotations

from pathlib import Path

import typer

from hepflow.api import diff_plan_files


def diff_command(
    old_plan: Path = typer.Argument(..., exists=True, dir_okay=False),
    new_plan: Path = typer.Argument(..., exists=True, dir_okay=False),
) -> None:
    output, equal = diff_plan_files(old_plan, new_plan)
    typer.echo(output)
    if not equal:
        raise typer.Exit(code=1)
