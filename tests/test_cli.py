from __future__ import annotations

from pathlib import Path

import yaml
from typer.testing import CliRunner

from fasthep_cli.app import app

runner = CliRunner(env={"FASTHEP_NO_LOGO": "1"})


def test_import_package() -> None:
    import fasthep_cli

    assert fasthep_cli.__version__


def test_app_help_smoke() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "normalise" in result.output
    assert "make-plan" in result.output


def test_init_command_smoke(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", "--target-dir", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert (tmp_path / ".hepflow" / "profiles" / "registry.yaml").exists()


def test_normalise_command_smoke(tmp_path: Path) -> None:
    author = _write_author(tmp_path)
    outdir = tmp_path / "build"

    result = runner.invoke(app, ["normalise", str(author), "--outdir", str(outdir)])

    assert result.exit_code == 0, result.output
    assert (outdir / "normalized.yaml").exists()


def test_normalize_alias_smoke(tmp_path: Path) -> None:
    author = _write_author(tmp_path)
    outdir = tmp_path / "build"

    result = runner.invoke(app, ["normalize", str(author), "--outdir", str(outdir)])

    assert result.exit_code == 0, result.output
    assert (outdir / "normalized.yaml").exists()


def test_make_plan_command_smoke(tmp_path: Path) -> None:
    author = _write_author(tmp_path)
    outdir = tmp_path / "build"
    result = runner.invoke(app, ["normalise", str(author), "--outdir", str(outdir)])
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        app,
        ["make-plan", str(outdir / "normalized.yaml"), "--outdir", str(outdir)],
    )

    assert result.exit_code == 0, result.output
    assert (outdir / "plan.yaml").exists()
    assert (outdir / "graph.mmd").exists()
    assert (outdir / "graph.dot").exists()


def test_compile_command_smoke(tmp_path: Path) -> None:
    author = _write_author(tmp_path)
    outdir = tmp_path / "build"

    result = runner.invoke(app, ["compile", str(author), "--outdir", str(outdir)])

    assert result.exit_code == 0, result.output
    assert (outdir / "normalized.yaml").exists()
    assert (outdir / "plan.yaml").exists()


def test_run_plan_command_smoke(tmp_path: Path) -> None:
    plan = _write_empty_plan(tmp_path)

    result = runner.invoke(app, ["run-plan", str(plan)])

    assert result.exit_code == 0, result.output
    assert (tmp_path / "run_summary.yaml").exists()


def test_run_command_smoke(tmp_path: Path) -> None:
    author = _write_author(tmp_path)
    outdir = tmp_path / "build"

    result = runner.invoke(app, ["run", str(author), "--outdir", str(outdir)])

    assert result.exit_code == 0, result.output
    assert (outdir / "normalized.yaml").exists()
    assert (outdir / "plan.yaml").exists()
    assert (outdir / "run_summary.yaml").exists()


def test_backend_override_smoke(tmp_path: Path) -> None:
    plan = _write_empty_plan(tmp_path)
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


def test_no_forbidden_workflow_imports() -> None:
    root = Path(__file__).parents[1] / "src" / "fasthep_cli"
    forbidden = [
        "hepflow.compiler",
        "hepflow.runtime.engine",
        "hepflow.backends.loaders",
    ]
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert not any(item in text for item in forbidden), path


def _write_author(tmp_path: Path) -> Path:
    author = {
        "version": "1.0",
        "data": {
            "datasets": [],
            "defaults": {},
        },
        "sources": {
            "events": {
                "kind": "root_tree",
                "tree": "events",
                "stream_type": "event_stream",
            },
        },
        "registry": {
            "sources": {
                "root_tree": {
                    "spec": "fasthep_cli.testing:ROOT_TREE_SOURCE_SPEC",
                    "impl": "fasthep_cli.testing:run_root_tree_source",
                }
            }
        },
        "analysis": {"stages": []},
    }
    path = tmp_path / "author.yaml"
    path.write_text(yaml.safe_dump(author, sort_keys=False), encoding="utf-8")
    return path


def _write_empty_plan(tmp_path: Path) -> Path:
    plan = {
        "context": {},
        "registry": {
            "backends": {
                "local.default": {
                    "impl": "hepflow.backends.local:LocalBackend",
                }
            }
        },
        "execution": {
            "backend": "local",
            "strategy": "default",
            "config": {},
        },
        "execution_hooks": [],
        "data_flow": {},
        "partitions": [],
        "nodes": [],
    }
    path = tmp_path / "plan.yaml"
    path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
    return path
