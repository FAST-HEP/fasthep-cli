from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from fasthep_curator.api import (
    filter_schema_fields,
    format_schema_alignment,
    format_schema_table,
    format_schema_yaml_list,
    inspect_root_tree_schema,
)

inspect_app = typer.Typer(no_args_is_help=True)


@inspect_app.command("schema")
def inspect_schema_command(
    file: Annotated[Path, typer.Argument(dir_okay=False)],
    tree: str = typer.Option("Events", "--tree", help="ROOT TTree name."),
    output_format: str = typer.Option(
        "table",
        "--format",
        help="Output format: table, yaml-list, or alignment.",
    ),
    include: list[str] = typer.Option(
        [],
        "--include",
        help="Shell-style field glob to include; may be repeated.",
    ),
    exclude: list[str] = typer.Option(
        [],
        "--exclude",
        help="Shell-style field glob to exclude after includes; may be repeated.",
    ),
) -> None:
    formatters = {
        "alignment": format_schema_alignment,
        "table": format_schema_table,
        "yaml-list": format_schema_yaml_list,
    }
    try:
        formatter = formatters[output_format]
    except KeyError as exc:
        msg = "--format must be one of alignment, table, yaml-list"
        raise typer.BadParameter(msg) from exc

    try:
        schema = inspect_root_tree_schema(file, tree=tree)
        fields = filter_schema_fields(
            schema,
            include=list(include),
            exclude=list(exclude),
        )
    except Exception as exc:
        raise typer.BadParameter(str(exc)) from exc

    typer.echo(formatter(schema, fields=fields))


__all__ = ["inspect_app"]
