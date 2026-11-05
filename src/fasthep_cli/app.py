from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, cast

import rich
import typer
from fasthep_toolbench.display.console import DisplayFormats, display
from fasthep_toolbench.http import download_from_json
from fasthep_toolbench.package import find_fast_hep_packages, find_hep_packages

from fasthep_cli import __version__
from fasthep_cli.commands.compile import compile_command
from fasthep_cli.commands.diff import diff_command
from fasthep_cli.commands.init import init_command
from fasthep_cli.commands.inspect import inspect_app
from fasthep_cli.commands.make_plan import make_plan_command
from fasthep_cli.commands.normalise import normalise_command
from fasthep_cli.commands.provenance import provenance_app
from fasthep_cli.commands.render import render_app
from fasthep_cli.commands.run import run_command
from fasthep_cli.commands.run_plan import run_plan_command
from fasthep_cli.commands.show_defaults import show_defaults_command
from fasthep_cli.commands.tools import tools_app
from fasthep_cli.logo_policy import (
    LOGO_META_KEY,
    FastHepCommand,
    logo_allowed,
    logo_command,
)

PROFILE_HELP = (
    "Profile example: use.profiles = [registry, fasthep_carpenter:registry, "
    "fasthep_curator:registry, fasthep_render:registry]"
)

app = typer.Typer(
    help=(
        "FAST-HEP workflow CLI. Core workflow verbs are top-level commands; "
        "specialised workflows live under grouped namespaces such as render "
        "and provenance."
    ),
    epilog=PROFILE_HELP,
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def _callback(
    ctx: typer.Context,
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress logo."),
) -> None:
    if ctx.invoked_subcommand is None:
        return
    ctx.meta[LOGO_META_KEY] = logo_allowed(
        quiet=quiet, environ=os.environ, isatty=sys.stdout.isatty()
    )


@app.command("version", cls=FastHepCommand)
def version_command() -> None:
    rich.print(f"[blue]fasthep-cli[/] [magenta]{__version__}[/]")


@app.command(
    "versions",
    cls=logo_command(lambda params: params["display_format"] == DisplayFormats.JSON),
)
def versions_command(
    display_format: DisplayFormats = typer.Option(
        DisplayFormats.SIMPLE,
        "--display",
        "-d",
        help="Display format.",
    ),
    hep: bool = typer.Option(
        False,
        "--hep",
        "-H",
        help="Include HEP ecosystem packages.",
    ),
) -> None:
    fasthep_packages = list(find_fast_hep_packages())
    hep_packages = list(find_hep_packages()) if hep else []

    if display_format == DisplayFormats.JSON:
        packages: dict[str, dict[str, str]] = {
            "fasthep_packages": dict(fasthep_packages),
        }
        if hep:
            packages["hep_packages"] = dict(hep_packages)
        display(cast(Any, packages), display_format=display_format)
        return

    headers = ["Package", "Version"]
    display(cast(Any, fasthep_packages), "FAST-HEP Packages", headers, display_format)
    if hep:
        display(cast(Any, hep_packages), "HEP Packages", headers, display_format)


@app.command("download", cls=FastHepCommand)
def download_command(
    json_input: Path = typer.Option(
        ...,
        "--json",
        "-j",
        exists=True,
        dir_okay=False,
        help="JSON manifest mapping output filenames to URLs.",
    ),
    destination: Path = typer.Option(
        Path("downloads"),
        "--destination",
        "-d",
        file_okay=False,
        help="Destination directory.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing files.",
    ),
) -> None:
    download_from_json(str(json_input), str(destination), force)


app.command("init", cls=FastHepCommand)(init_command)
app.command("normalise", cls=FastHepCommand)(normalise_command)
app.command("normalize", cls=FastHepCommand)(normalise_command)
app.command("make-plan", cls=FastHepCommand)(make_plan_command)
app.command("compile", cls=FastHepCommand)(compile_command)
app.command("run-plan", cls=FastHepCommand)(run_plan_command)
app.command("run", cls=FastHepCommand)(run_command)
app.command("diff", cls=logo_command(lambda params: params["json_output"]))(
    diff_command
)
app.command("show-defaults", cls=FastHepCommand)(show_defaults_command)
app.add_typer(provenance_app, name="provenance")
app.add_typer(inspect_app, name="inspect")
app.add_typer(render_app, name="render")
app.add_typer(tools_app, name="tools")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
