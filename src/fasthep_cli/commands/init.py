from __future__ import annotations

from pathlib import Path

import typer
from hepflow.api import init_project


def init_command(
    target_dir: Path = typer.Option(
        Path(),
        "--target-dir",
        help="Project directory where .fasthep/profiles/hepflow should be created.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing copied profile template files.",
    ),
) -> None:
    result = init_project(target_dir=target_dir, force=force)
    if result.created_profile_dir:
        typer.echo(f"Created {result.profile_dir}")
    else:
        typer.echo(f"Found {result.profile_dir}")

    for path in result.copied:
        typer.echo(f"Wrote {path}")
    for path in result.overwritten:
        typer.echo(f"Wrote {path}")
    for path in result.skipped_existing:
        typer.echo(f"Skipped existing {path}; use --force to overwrite")

    if not result.written and not result.skipped_existing:
        typer.echo("No bundled profiles available")
