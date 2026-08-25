from __future__ import annotations

from pathlib import Path

from fasthep_cli.app import app
from tests._helpers import runner, write_workflow


def test_normalise_command_smoke(tmp_path: Path) -> None:
    workflow = write_workflow(tmp_path)
    outdir = tmp_path / "build"

    result = runner.invoke(app, ["normalise", str(workflow), "--outdir", str(outdir)])

    assert result.exit_code == 0, result.output
    assert (outdir / "compile" / "normalized.yaml").exists()


def test_normalize_alias_smoke(tmp_path: Path) -> None:
    workflow = write_workflow(tmp_path)
    outdir = tmp_path / "build"

    result = runner.invoke(app, ["normalize", str(workflow), "--outdir", str(outdir)])

    assert result.exit_code == 0, result.output
    assert (outdir / "compile" / "normalized.yaml").exists()


def test_make_plan_command_smoke(tmp_path: Path) -> None:
    workflow = write_workflow(tmp_path)
    outdir = tmp_path / "build"
    result = runner.invoke(app, ["normalise", str(workflow), "--outdir", str(outdir)])
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        app,
        [
            "make-plan",
            str(outdir / "compile" / "normalized.yaml"),
            "--outdir",
            str(outdir),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (outdir / "compile" / "plan.yaml").exists()
    assert (outdir / "graph" / "graph.mmd").exists()
    assert (outdir / "graph" / "graph.dot").exists()


def test_compile_command_smoke(tmp_path: Path) -> None:
    workflow = write_workflow(tmp_path)
    outdir = tmp_path / "build"

    result = runner.invoke(app, ["compile", str(workflow), "--outdir", str(outdir)])

    assert result.exit_code == 0, result.output
    assert (outdir / "compile" / "normalized.yaml").exists()
    assert (outdir / "compile" / "plan.yaml").exists()
