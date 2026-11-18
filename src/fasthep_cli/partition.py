from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import typer

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
    """Report the ValueErrors Flow raises for bad dataset or partition input."""
    try:
        yield
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc


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
