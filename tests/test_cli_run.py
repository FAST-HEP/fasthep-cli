from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

import fasthep_cli.commands.run as run_command_module
import fasthep_cli.commands.run_plan as run_plan_command_module
from fasthep_cli.app import app
from tests._helpers import fake_run_result, runner, write_empty_plan, write_workflow


def test_run_plan_command_smoke(tmp_path: Path) -> None:
    plan = write_empty_plan(tmp_path)

    result = runner.invoke(app, ["run-plan", str(plan)])

    assert result.exit_code == 0, result.output
    assert (tmp_path / "run_summary.yaml").exists()
    assert f"Summary: {tmp_path / 'run_summary.yaml'}" in result.output
    assert f"Artifacts: {tmp_path / 'artifacts'}" in result.output


@pytest.mark.parametrize(
    ("selector", "expected"),
    [
        ("1", [1]),
        ("1,3,5", [1, 3, 5]),
        ("1, 3, 5", [1, 3, 5]),
    ],
)
def test_run_plan_command_parses_partition_numbers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    selector: str,
    expected: list[int],
) -> None:
    calls: list[list[int] | None] = []

    def fake_run_plan_file(*args: object, **kwargs: object) -> SimpleNamespace:
        del args
        calls.append(kwargs.get("partition_numbers"))  # type: ignore[arg-type]
        return fake_run_result(tmp_path)

    monkeypatch.setattr(run_plan_command_module, "run_plan_file", fake_run_plan_file)
    plan = write_empty_plan(tmp_path)

    result = runner.invoke(app, ["run-plan", str(plan), "--partition", selector])

    assert result.exit_code == 0, result.output
    assert calls == [expected]


@pytest.mark.parametrize("selector", ["a", "1,a", "0", "-1"])
def test_run_plan_command_rejects_bad_partition_selector(
    tmp_path: Path,
    selector: str,
) -> None:
    plan = write_empty_plan(tmp_path)

    result = runner.invoke(app, ["run-plan", str(plan), "--partition", selector])

    assert result.exit_code != 0
    assert "--partition" in result.output


def test_run_plan_command_reports_variation_paths(tmp_path: Path) -> None:
    build_dir = tmp_path / "build"
    plan = write_empty_plan(
        build_dir / "compile" / "trigger_eff_down",
        variation="trigger_eff_down",
    )

    result = runner.invoke(app, ["run-plan", str(plan)])

    assert result.exit_code == 0, result.output
    assert (
        f"Summary: {build_dir / 'reports' / 'trigger_eff_down' / 'run_summary.yaml'}"
        in result.output
    )
    assert f"Artifacts: {build_dir / 'artifacts' / 'trigger_eff_down'}" in result.output
    assert (build_dir / "reports" / "trigger_eff_down" / "run_summary.yaml").exists()
    assert not (build_dir / "trigger_eff_down" / "artifacts").exists()


def test_run_command_smoke(tmp_path: Path) -> None:
    workflow = write_workflow(tmp_path)
    outdir = tmp_path / "build"

    result = runner.invoke(app, ["run", str(workflow), "--outdir", str(outdir)])

    assert result.exit_code == 0, result.output
    assert (outdir / "compile" / "normalized.yaml").exists()
    assert (outdir / "compile" / "plan.yaml").exists()
    assert (outdir / "run_summary.yaml").exists()


@pytest.mark.parametrize(
    ("selector", "expected"),
    [
        ("1", [1]),
        ("1,3,5", [1, 3, 5]),
        ("1, 3, 5", [1, 3, 5]),
    ],
)
def test_run_command_parses_partition_numbers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    selector: str,
    expected: list[int],
) -> None:
    calls: list[list[int] | None] = []

    def fake_run_workflow_file(*args: object, **kwargs: object) -> SimpleNamespace:
        del args
        calls.append(kwargs.get("partition_numbers"))  # type: ignore[arg-type]
        return fake_run_result(tmp_path / "build")

    monkeypatch.setattr(run_command_module, "run_workflow_file", fake_run_workflow_file)
    workflow = write_workflow(tmp_path)

    result = runner.invoke(
        app,
        [
            "run",
            str(workflow),
            "--outdir",
            str(tmp_path / "build"),
            "--partition",
            selector,
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [expected]


@pytest.mark.parametrize("selector", ["a", "1,a", "0", "-1"])
def test_run_command_rejects_bad_partition_selector(
    tmp_path: Path,
    selector: str,
) -> None:
    workflow = write_workflow(tmp_path)

    result = runner.invoke(
        app,
        [
            "run",
            str(workflow),
            "--outdir",
            str(tmp_path / "build"),
            "--partition",
            selector,
        ],
    )

    assert result.exit_code != 0
    assert "--partition" in result.output


def test_backend_override_smoke(tmp_path: Path) -> None:
    plan = write_empty_plan(tmp_path)
    outdir = tmp_path / "run"

    result = runner.invoke(
        app,
        [
            "run-plan",
            str(plan),
            "--outdir",
            str(outdir),
            "--backend",
            "local.default",
        ],
    )

    assert result.exit_code == 0, result.output
    summary = yaml.safe_load((outdir / "run_summary.yaml").read_text())
    assert summary["backend"] == "local"
    assert summary["strategy"] == "default"
