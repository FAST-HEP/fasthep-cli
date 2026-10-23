from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from hepflow.progress import ProgressEvent

from fasthep_cli.progress import _distributed_preparation_line


def _line(detail: dict[str, Any]) -> str:
    event = ProgressEvent(
        run_id="run",
        sequence=1,
        kind="phase_completed",
        timestamp=datetime.now(tz=UTC),
        elapsed_seconds=0.0,
        detail=detail,
    )
    update: Any = SimpleNamespace(event=event)
    return _distributed_preparation_line(update)


def test_completed_preparation_reports_sizes() -> None:
    line = _line(
        {
            "status": "completed",
            "elapsed_seconds": 2.5,
            "staging": {"transfer_bytes": 3 * 1024 * 1024},
            "worker_environment": {
                "prefix_archive_bytes": 2 * 1024 * 1024 * 1024,
                "editable_snapshot_bytes": 1536,
            },
        }
    )

    assert line == (
        "Preparing distributed execution complete "
        "(2.5s, prefix=2.0GiB, snapshot=1.5KiB, staging=3.0MiB)"
    )


@pytest.mark.parametrize(
    "detail",
    [
        {"status": "completed", "elapsed_seconds": 1.0},
        {"status": "completed", "elapsed_seconds": 1.0, "staging": None},
        {"status": "completed", "elapsed_seconds": 1.0, "worker_environment": "x"},
    ],
)
def test_completed_preparation_without_usable_details_reports_zero_bytes(
    detail: dict[str, Any],
) -> None:
    assert _line(detail) == (
        "Preparing distributed execution complete "
        "(1.0s, prefix=0B, snapshot=0B, staging=0B)"
    )


def test_failed_preparation_names_the_active_step() -> None:
    line = _line({"status": "failed", "active_step": "pack_environment"})

    assert line == "Preparing distributed execution failed during pack environment"


def test_running_preparation_names_the_step() -> None:
    assert _line({"step": "stage_inputs"}) == (
        "Preparing distributed execution: stage inputs"
    )
