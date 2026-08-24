from __future__ import annotations

import sys

from hepflow.progress import ProgressUpdate


class TerminalProgressSink:
    def __init__(self) -> None:
        self._last_line = ""

    def handle(self, update: ProgressUpdate) -> None:
        event = update.event
        if event.kind not in {
            "phase_started",
            "partition_state",
            "run_completed",
            "run_failed",
        }:
            return
        line = _line(update)
        if line == self._last_line:
            return
        self._last_line = line
        sys.stderr.write(f"{line}\n")
        sys.stderr.flush()


def _line(update: ProgressUpdate) -> str:
    event = update.event
    snapshot = update.snapshot
    counts = snapshot.counts
    if event.kind == "run_completed":
        return (
            f"Run complete: {counts.completed} complete / "
            f"{counts.failed} failed / {counts.total} total"
        )
    if event.kind == "run_failed":
        return (
            f"Run failed: {counts.completed} complete / "
            f"{counts.failed} failed / {counts.running} running / "
            f"{counts.pending} pending"
        )
    if snapshot.phase == "finalizing":
        return "Finalizing outputs..."
    if counts.failed:
        return (
            f"Executing: {counts.completed} complete / {counts.failed} failed / "
            f"{counts.running} running / {counts.pending} pending"
        )
    return (
        f"Executing: {counts.completed} complete / "
        f"{counts.running} running / {counts.pending} pending"
    )
