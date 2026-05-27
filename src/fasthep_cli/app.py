from __future__ import annotations

import os
import sys
from importlib import import_module
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
from fasthep_cli.commands.make_plan import make_plan_command
from fasthep_cli.commands.normalise import normalise_command
from fasthep_cli.commands.render import render_app
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
def _callback(
    ctx: typer.Context,
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress logo."),
) -> None:
    if ctx.invoked_subcommand is None:
        return
    if quiet or _is_json_versions_request():
        return
    _maybe_print_logo()


@app.command("version")
def version_command() -> None:
    rich.print(f"[blue]fasthep-cli[/] [magenta]{__version__}[/]")


@app.command("versions")
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


@app.command("download")
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


app.command("init")(init_command)
app.command("normalise")(normalise_command)
app.command("normalize")(normalise_command)
app.command("make-plan")(make_plan_command)
app.command("compile")(compile_command)
app.command("run-plan")(run_plan_command)
app.command("run")(run_command)
app.command("diff")(diff_command)
app.command("show-defaults")(show_defaults_command)
app.add_typer(render_app, name="render")


def _maybe_print_logo() -> None:
    if os.environ.get("FASTHEP_NO_LOGO"):
        return
    if not sys.stdout.isatty():
        return
    try:
        logo_module = import_module("fasthep_cli.logo")
        typer.echo(logo_module.get_logo())
    except Exception:
        return


def _is_json_versions_request() -> bool:
    args = sys.argv[1:]
    if "versions" not in args:
        return False

    for index, arg in enumerate(args):
        if arg == "--display" and index + 1 < len(args):
            return args[index + 1] == "json"
        if arg == "-d" and index + 1 < len(args):
            return args[index + 1] == "json"
        if arg.startswith("--display="):
            return arg.partition("=")[2] == "json"
    return False


def main() -> None:
    app()


if __name__ == "__main__":
    main()
