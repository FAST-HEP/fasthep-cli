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
            "phase_completed",
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
    if event.phase == "Preparing distributed execution":
        return _distributed_preparation_line(update)
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


def _distributed_preparation_line(update: ProgressUpdate) -> str:
    event = update.event
    detail = dict(event.detail)
    status = detail.get("status")
    if status == "completed":
        staging = detail.get("staging") if isinstance(detail.get("staging"), dict) else {}
        env = (
            detail.get("worker_environment")
            if isinstance(detail.get("worker_environment"), dict)
            else {}
        )
        total = int(staging.get("transfer_bytes") or 0)
        prefix = int(env.get("prefix_archive_bytes") or 0)
        snapshot = int(env.get("editable_snapshot_bytes") or 0)
        return (
            "Preparing distributed execution complete "
            f"({event.detail.get('elapsed_seconds', 0):.1f}s, "
            f"prefix={_format_bytes(prefix)}, "
            f"snapshot={_format_bytes(snapshot)}, "
            f"staging={_format_bytes(total)})"
        )
    if status == "failed":
        active = _step_label(str(detail.get("active_step") or "unknown"))
        return f"Preparing distributed execution failed during {active}"
    step = _step_label(str(detail.get("step") or "preparing"))
    return f"Preparing distributed execution: {step}"


def _step_label(step: str) -> str:
    return step.replace("_", " ")


def _format_bytes(value: int) -> str:
    if value >= 1024 * 1024 * 1024:
        return f"{value / (1024 * 1024 * 1024):.1f}GiB"
    if value >= 1024 * 1024:
        return f"{value / (1024 * 1024):.1f}MiB"
    if value >= 1024:
        return f"{value / 1024:.1f}KiB"
    return f"{value}B"
