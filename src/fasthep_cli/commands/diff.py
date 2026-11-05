from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from hepflow.api import DiffSection, PlanDiffReport, diff_plan_files


def _selected_sections(
    section: list[DiffSection], ignore: list[DiffSection]
) -> tuple[tuple[DiffSection, ...], tuple[DiffSection, ...]]:
    """Return ``(included, ignored)`` in public order, deduplicated."""
    included = set(section) or set(DiffSection)
    ignored = set(ignore)
    if not included - ignored:
        message = "no sections selected: --ignore removes every --section"
        raise typer.BadParameter(message)
    return (
        tuple(s for s in DiffSection if s in included),
        tuple(s for s in DiffSection if s in ignored),
    )


def _exit_code(report: PlanDiffReport, *, strict: bool) -> int:
    satisfied = report.equal if strict else report.semantically_equal
    return 0 if satisfied else 1


def diff_command(
    old: Annotated[Path, typer.Argument(metavar="OLD")],
    new: Annotated[Path, typer.Argument(metavar="NEW")],
    strict: Annotated[bool, typer.Option("--strict")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,  # noqa: ARG001
    section: Annotated[list[DiffSection] | None, typer.Option("--section")] = None,
    ignore: Annotated[list[DiffSection] | None, typer.Option("--ignore")] = None,
) -> None:
    included, ignored = _selected_sections(section or [], ignore or [])
    report = diff_plan_files(old, new)
    if section or ignore:
        report = report.scoped(include=included, ignore=ignored)
    typer.echo(report.to_dict()["counts"])
    code = _exit_code(report, strict=strict)
    if code:
        raise typer.Exit(code=code)
