from __future__ import annotations

import typer


def show_defaults_command() -> None:
    typer.echo(
        "Default flow registry/profile config is available through `fasthep init`."
    )
    typer.echo("Use package-owned profiles such as fasthep_carpenter:registry.")
