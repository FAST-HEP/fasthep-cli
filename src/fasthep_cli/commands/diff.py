from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

import typer
from hepflow.api import (
    DiffKind,
    DiffSection,
    PlanDiffEntry,
    PlanDiffReport,
    diff_plan_files,
)


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


def _summary(report: PlanDiffReport, *, strict: bool) -> str:
    if report.equal:
        return "Plans equal."
    counts = report.counts()["sections"]
    if not strict and report.semantically_equal:
        return (
            f"Plans equal except provenance ({counts[DiffSection.PROVENANCE.value]})."
        )
    parts = [f"{s.value}={counts[s.value]}" for s in DiffSection if counts[s.value]]
    return f"Plans differ: {', '.join(parts)}."


def _format_value(value: object) -> list[str]:
    """Lines for one value: JSON for scalars, indented blocks for text and structures."""
    if isinstance(value, str) and "\n" in value:
        return value.split("\n")
    if isinstance(value, dict | list):
        return json.dumps(value, indent=2, sort_keys=True).split("\n")
    return [json.dumps(value)]


def _value_lines(
    label: str, value: object, display: dict[str, Any] | None
) -> list[str]:
    if display is not None:
        suffix = "" if display["label"] in ("relative",) else f" ({display['label']})"
        return [f"    {label}: {json.dumps(display['value'])}{suffix}"]
    lines = _format_value(value)
    if len(lines) == 1:
        return [f"    {label}: {lines[0]}"]
    return [f"    {label}:", *(f"      {line}" for line in lines)]


def _moved_path(display: dict[str, Any] | None, row: object) -> str:
    if display:
        shown = display.get("resolved") or display.get("declared")
        if shown:
            return str(shown["value"])
    return str(row.get("declared")) if isinstance(row, dict) else ""


def _entry_lines(entry: PlanDiffEntry) -> list[str]:
    head = f"  {entry.kind.value}  {entry.rendered_location}"
    if entry.fallback:
        head += " [fallback alignment]"
    lines = [head]
    if entry.kind is DiffKind.MOVED:
        lines.append(f"    from: {_moved_path(entry.old_display, entry.old)}")
        lines.append(f"    to: {_moved_path(entry.new_display, entry.new)}")
        return lines
    if entry.old_present and entry.kind is not DiffKind.ADDED:
        lines += _value_lines("old", entry.old, entry.old_display)
    if entry.new_present and entry.kind is not DiffKind.REMOVED:
        lines += _value_lines("new", entry.new, entry.new_display)
    return lines


def _render_report(report: PlanDiffReport, *, strict: bool) -> str:
    lines = [_summary(report, strict=strict)]
    for section in DiffSection:
        entries = [e for e in report.entries if e.section is section]
        if not entries:
            continue
        lines.append(f"[{section.value}]")
        for entry in entries:
            lines.extend(_entry_lines(entry))
    return "\n".join(lines)


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
    typer.echo(_render_report(report, strict=strict))
    for warning in report.warnings:
        typer.echo(f"warning: {warning.message}", err=True)
    code = _exit_code(report, strict=strict)
    if code:
        raise typer.Exit(code=code)
