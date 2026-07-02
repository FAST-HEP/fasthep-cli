from __future__ import annotations

import json
from typing import Annotated

import typer
from fasthep_toolbench import tool_info_text, tools_list_text
from fasthep_toolbench.command import CommandResult
from fasthep_toolbench.tools import run_registered_tool

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
    try:
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
