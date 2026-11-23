from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import typer
from hepflow.api import PublishConflict

DATASET_HELP = (
    "Select one dataset of a per-dataset workflow; partition numbers then count "
    "inside it."
)
PER_DATASET_HELP = (
    "Enable per-dataset mode (overrides execution.partitioning.per_dataset)."
)


def dataset_option() -> Any:
    return typer.Option(None, "--dataset", help=DATASET_HELP)


def per_dataset_option() -> Any:
    # None keeps the workflow's own setting; only the flag overrides it.
    return typer.Option(None, "--per-dataset", help=PER_DATASET_HELP)


@contextmanager
def usage_errors() -> Iterator[None]:
    """Report the errors Flow raises for bad dataset or partition input, and for a conflict.

    A ValueError is a usage error (exit code 2). A ``PublishConflict`` (a shared plan or a run
    binding that another plan or manifest already owns) is a failed run, not a bad option: its
    message says what differs and what to do, so it is shown without a traceback (exit code 1).
    """
    try:
        yield
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    except PublishConflict as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc


def echo_partition_runs(summary: dict[str, Any]) -> None:
    """Name the run roots of a per-dataset run; there is one summary per partition below them."""
    runs = [str(path) for path in summary.get("partition_runs") or []]
    if not runs:
        return
    roots = list(dict.fromkeys(str(Path(path).parent) for path in runs))
    typer.echo(f"Partition records: {len(runs)} (one summary each) below {', '.join(roots)}")


def parse_partition_numbers(value: str | None) -> list[int] | None:
    if value is None:
        return None

    text = value.strip()
    if not text:
        message = "Partition selector must not be empty."
        raise typer.BadParameter(message, param_hint="--partition")

    numbers: list[int] = []
    for token in text.split(","):
        numbers.append(_parse_partition_token(token))
    return numbers


def _parse_partition_token(token: str) -> int:
    text = token.strip()
    if not text:
        message = "Partition selector contains an empty entry."
        raise typer.BadParameter(message, param_hint="--partition")
    if "-" in text or ":" in text or text == "*":
        message = (
            f"Unsupported partition selector {text!r}; use comma-separated "
            "1-based numbers."
        )
        raise typer.BadParameter(message, param_hint="--partition")
    if not text.isdecimal():
        message = (
            f"Invalid partition number {text!r}; use comma-separated 1-based numbers."
        )
        raise typer.BadParameter(message, param_hint="--partition")

    number = int(text)
    if number <= 0:
        message = f"Partition numbers are 1-based; requested partition {number}."
        raise typer.BadParameter(message, param_hint="--partition")
    return number
