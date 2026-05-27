from __future__ import annotations

from pathlib import Path

import typer

render_app = typer.Typer(no_args_is_help=True)


@render_app.command("spec")
def render_spec_command(
    spec_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    product: Path | None = typer.Option(
        None,
        "--product",
        exists=True,
        dir_okay=False,
        help="Explicit product file to render, usually a histogram pickle.",
    ),
    out: Path | None = typer.Option(None, "--out", help="Output path override."),
    plan: Path | None = typer.Option(
        None,
        "--plan",
        exists=True,
        dir_okay=False,
        help="Compiled plan path for future plan-aware rendering.",
    ),
) -> None:
    if product is None:
        raise typer.BadParameter(
            "--product is required until plan-aware render spec execution is available"
        )

    try:
        from fasthep_render.api import render_spec_file
    except ModuleNotFoundError as exc:
        raise typer.BadParameter(
            "fasthep-render is required for 'fasthep render spec'"
        ) from exc

    outcome = render_spec_file(
        spec_path,
        product=product,
        out=out,
        plan_path=plan,
    )
    typer.echo("Render complete")
    typer.echo(f"Status: {outcome.status.value}")
    typer.echo(f"Output: {outcome.output_path}")
