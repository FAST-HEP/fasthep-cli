from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import fasthep_cli.commands.compile as compile_command_module
import fasthep_cli.commands.make_plan as make_plan_command_module
import fasthep_cli.commands.run as run_command_module
import fasthep_cli.commands.run_plan as run_plan_command_module
from fasthep_cli.app import app
from fasthep_cli.testing import strip_ansi
from tests._helpers import (
    fake_run_result,
    runner,
    write_empty_plan,
    write_workflow,
)


def _record(calls: list[dict[str, object]], result: object = None):
    def fake(*args: object, **kwargs: object) -> object:
        del args
        calls.append(dict(kwargs))
        return result

    return fake


def test_run_forwards_dataset_and_per_dataset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        run_command_module,
        "run_workflow_file",
        _record(calls, fake_run_result(tmp_path / "build")),
    )
    workflow = write_workflow(tmp_path)

    result = runner.invoke(
        app,
        [
            "run",
            str(workflow),
            "--outdir",
            str(tmp_path / "build"),
            "--per-dataset",
            "--dataset",
            "sample",
            "--partition",
            "2",
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls[0]["dataset"] == "sample"
    assert calls[0]["per_dataset"] is True
    assert calls[0]["partition_numbers"] == [2]


def test_run_leaves_per_dataset_to_the_workflow_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        run_command_module,
        "run_workflow_file",
        _record(calls, fake_run_result(tmp_path / "build")),
    )
    workflow = write_workflow(tmp_path)

    result = runner.invoke(
        app, ["run", str(workflow), "--outdir", str(tmp_path / "build")]
    )

    assert result.exit_code == 0, result.output
    assert calls[0]["dataset"] is None
    assert calls[0]["per_dataset"] is None


def test_run_plan_forwards_dataset_and_chunk_size(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        run_plan_command_module,
        "run_plan_file",
        _record(calls, fake_run_result(tmp_path / "build")),
    )
    plan = write_empty_plan(tmp_path)

    result = runner.invoke(
        app,
        [
            "run-plan",
            str(plan),
            "--dataset",
            "sample",
            "--chunk-size",
            "5",
            "--partition",
            "1,3",
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls[0]["dataset"] == "sample"
    assert calls[0]["chunk_size"] == 5
    assert calls[0]["partition_numbers"] == [1, 3]


def test_compile_forwards_dataset_and_per_dataset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        compile_command_module, "compile_workflow_file", _record(calls)
    )
    workflow = write_workflow(tmp_path)

    result = runner.invoke(
        app,
        [
            "compile",
            str(workflow),
            "--outdir",
            str(tmp_path / "build"),
            "--per-dataset",
            "--dataset",
            "sample",
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls[0]["dataset"] == "sample"
    assert calls[0]["per_dataset"] is True


def test_make_plan_forwards_dataset_and_per_dataset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(make_plan_command_module, "make_plan_file", _record(calls))
    normalized = tmp_path / "normalized.yaml"
    normalized.write_text("{}", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "make-plan",
            str(normalized),
            "--outdir",
            str(tmp_path / "build"),
            "--dataset",
            "sample",
            "--per-dataset",
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls[0]["dataset"] == "sample"
    assert calls[0]["per_dataset"] is True


def test_run_dataset_without_the_mode_is_a_usage_error(tmp_path: Path) -> None:
    workflow = write_workflow(tmp_path)

    result = runner.invoke(
        app,
        [
            "run",
            str(workflow),
            "--outdir",
            str(tmp_path / "build"),
            "--dataset",
            "sample",
        ],
    )

    assert result.exit_code == 2
    assert "not per-dataset" in strip_ansi(result.output)
    assert "Traceback" not in result.output
    assert not (tmp_path / "build").exists()


def test_compile_dataset_without_the_mode_is_a_usage_error(tmp_path: Path) -> None:
    workflow = write_workflow(tmp_path)

    result = runner.invoke(
        app,
        [
            "compile",
            str(workflow),
            "--outdir",
            str(tmp_path / "build"),
            "--dataset",
            "sample",
        ],
    )

    assert result.exit_code == 2
    assert "not per-dataset" in strip_ansi(result.output)
    assert not (tmp_path / "build").exists()


def test_run_plan_reports_api_value_errors_as_usage_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(*args: object, **kwargs: object) -> SimpleNamespace:
        del args, kwargs
        message = "Dataset 'a' was compiled with chunk size 2, not 3"
        raise ValueError(message)

    monkeypatch.setattr(run_plan_command_module, "run_plan_file", fail)
    plan = write_empty_plan(tmp_path)

    result = runner.invoke(
        app, ["run-plan", str(plan), "--dataset", "a", "--chunk-size", "3"]
    )

    assert result.exit_code == 2
    assert "compiled with chunk size 2" in strip_ansi(result.output)
