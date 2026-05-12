from __future__ import annotations

import os
import sys

import typer

from fasthep_cli.commands.compile import compile_command
from fasthep_cli.commands.diff import diff_command
from fasthep_cli.commands.init import init_command
from fasthep_cli.commands.make_plan import make_plan_command
from fasthep_cli.commands.normalise import normalise_command
from fasthep_cli.commands.run import run_command
from fasthep_cli.commands.run_plan import run_plan_command
from fasthep_cli.commands.show_defaults import show_defaults_command

PROFILE_HELP = (
    "Profile example: use.profiles = [registry, fasthep_carpenter:registry, "
    "fasthep_curator:registry, fasthep_render:registry]"
)

app = typer.Typer(
    help=(
        "FAST-HEP workflow CLI. Core workflow verbs are top-level commands; "
        "specialised inspect/render/validate/dataset namespaces will arrive later."
    ),
    epilog=PROFILE_HELP,
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def _callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        return
    _maybe_print_logo()


app.command("init")(init_command)
app.command("normalise")(normalise_command)
app.command("normalize")(normalise_command)
app.command("make-plan")(make_plan_command)
app.command("compile")(compile_command)
app.command("run-plan")(run_plan_command)
app.command("run")(run_command)
app.command("diff")(diff_command)
app.command("show-defaults")(show_defaults_command)


def _maybe_print_logo() -> None:
    if os.environ.get("FASTHEP_NO_LOGO"):
        return
    if not sys.stdout.isatty():
        return
    try:
        from fasthep_cli.logo import get_logo

        typer.echo(get_logo())
    except Exception:
        return


def main() -> None:
    app()


if __name__ == "__main__":
    main()
