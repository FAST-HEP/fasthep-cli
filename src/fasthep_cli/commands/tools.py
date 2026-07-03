from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

import typer
from fasthep_toolbench import tool_info_text, tools_list_text
from fasthep_toolbench.availability import tool_availability
from fasthep_toolbench.command import CommandResult
from fasthep_toolbench.loader import load_tool_binding
from fasthep_toolbench.tools import (
    default_global_bin_dir,
    install_plan_text,
    install_tool,
    normalize_global_bin_dir,
    run_registered_tool,
)

tools_app = typer.Typer(no_args_is_help=True)


@tools_app.command("list")
def tools_list_command() -> None:
    typer.echo(tools_list_text(), nl=False)


@tools_app.command("info")
def tools_info_command(tool: Annotated[str, typer.Argument()]) -> None:
    try:
        typer.echo(tool_info_text(tool), nl=False)
    except (KeyError, TypeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc


@tools_app.command(
    "install",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def tools_install_command(
    ctx: typer.Context,
    tool: Annotated[str, typer.Argument()],
) -> None:
    try:
        install_dir = _install_dir_from_args(list(ctx.args))
        result = install_tool(tool, install_dir=install_dir)
    except (KeyError, TypeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    except NotImplementedError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc
    typer.echo(result.message)


@tools_app.command(
    "run",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def tools_run_command(
    ctx: typer.Context,
    tool: Annotated[str, typer.Argument()],
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit structured command metadata instead of streaming output.",
    ),
) -> None:
    tool_args = list(ctx.args)
    if "--json" in tool_args:
        json_output = True
        tool_args.remove("--json")
    auto_install = _pop_flag(tool_args, "--auto-install")
    no_install = _pop_flag(tool_args, "--no-install")
    if auto_install and no_install:
        msg = "--auto-install and --no-install cannot be combined"
        raise typer.BadParameter(msg)
    try:
        _ensure_available_for_run(
            tool,
            auto_install=auto_install,
            no_install=no_install,
        )
        result = run_registered_tool(tool, tool_args)
    except (KeyError, TypeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    if isinstance(result, CommandResult):
        if json_output:
            typer.echo(json.dumps(result.to_dict(tool=tool), indent=2, sort_keys=True))
        else:
            if result.stdout:
                typer.echo(result.stdout, nl=False)
            if result.stderr:
                typer.echo(result.stderr, nl=False, err=True)
        raise typer.Exit(result.exit_code)
    if isinstance(result, str):
        typer.echo(result if result.endswith("\n") else f"{result}\n", nl=False)
        return
    typer.echo(json.dumps(result, indent=2, sort_keys=True) + "\n", nl=False)


def _install_dir_from_args(args: list[str]) -> Path | None:
    if not args:
        return None
    if args[0] != "--global":
        msg = f"Unknown install option: {args[0]}"
        raise typer.BadParameter(msg)
    if len(args) == 1:
        return default_global_bin_dir()
    if len(args) == 2:
        return normalize_global_bin_dir(Path(args[1]))
    msg = f"Unexpected install arguments: {' '.join(args[2:])}"
    raise typer.BadParameter(msg)


def _ensure_available_for_run(
    tool: str,
    *,
    auto_install: bool,
    no_install: bool,
) -> None:
    binding = load_tool_binding(tool)
    availability = tool_availability(binding.spec)
    if availability.available:
        return
    if no_install:
        _fail_missing_tool(tool)
    if auto_install:
        install_tool(tool)
        return
    if sys.stdin.isatty():
        typer.echo(install_plan_text(tool), nl=False)
        if typer.confirm("Install?", default=False):
            install_tool(tool)
            return
    _fail_missing_tool(tool)


def _fail_missing_tool(tool: str) -> None:
    typer.echo(
        (
            f"Tool '{tool}' is not available. "
            f"Run 'fasthep tools install {tool}' or retry with --auto-install."
        ),
        err=True,
    )
    raise typer.Exit(127)


def _pop_flag(args: list[str], flag: str) -> bool:
    found = False
    while flag in args:
        args.remove(flag)
        found = True
    return found
