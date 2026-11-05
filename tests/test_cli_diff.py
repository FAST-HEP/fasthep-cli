from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest
import yaml
from hepflow.api import DiffSection, InputNotFound, diff_plan_files
from typer import BadParameter

from fasthep_cli.app import app
from fasthep_cli.commands.diff import _exit_code, _selected_sections
from tests._helpers import runner

SHA = "a" * 64


def _plan() -> dict[str, Any]:
    return {
        "context": {"project_root": "/a", "workflow_path": "/a/wf.yaml"},
        "nodes": [
            {
                "id": "n1",
                "inputs": [
                    {"node_id": "src", "output_name": "stream", "input_name": "stream"}
                ],
                "params": {"x": 1},
                "meta": {"stage_id": "n1"},
            }
        ],
        "partitions": [],
        "reports": [],
        "provenance": {
            "root": "/a",
            "inputs": [
                {
                    "role": "workflow",
                    "declared": "wf.yaml",
                    "resolved": "/a/wf.yaml",
                    "origin": "root",
                    "sha256": SHA,
                    "size": 1,
                    "note": None,
                }
            ],
            "compilation": {"flow_version": "1.0"},
        },
    }


def _write(tmp_path: Path, name: str, plan: dict[str, Any]) -> Path:
    path = tmp_path / name
    path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
    return path


def _pair(
    tmp_path: Path, old: dict[str, Any], new: dict[str, Any]
) -> tuple[Path, Path]:
    return _write(tmp_path, "old.yaml", old), _write(tmp_path, "new.yaml", new)


def _invoke(*args: str) -> Any:
    return runner.invoke(app, ["diff", *args])


def _provenance_only() -> tuple[dict[str, Any], dict[str, Any]]:
    old = _plan()
    new = copy.deepcopy(old)
    new["context"]["workflow_path"] = "/b/wf.yaml"
    new["provenance"]["root"] = "/b"
    return old, new


def _semantic() -> tuple[dict[str, Any], dict[str, Any]]:
    old = _plan()
    new = copy.deepcopy(old)
    new["nodes"][0]["params"]["x"] = 2
    return old, new


G, D, P = DiffSection.GRAPH, DiffSection.DATA, DiffSection.PROVENANCE


def test_selected_sections_dedupes_orders_and_subtracts() -> None:
    included, ignored = _selected_sections([P, G, G], [P])

    assert included == (G, P)
    assert ignored == (P,)


def test_default_scope_is_all_sections() -> None:
    included, ignored = _selected_sections([], [])

    assert included == tuple(DiffSection)
    assert ignored == ()


def test_empty_scope_raises_bad_parameter() -> None:
    with pytest.raises(BadParameter):
        _selected_sections([G], [G])


@pytest.mark.parametrize("extra", [[], ["--json"]])
def test_empty_scope_is_a_usage_error(tmp_path: Path, extra: list[str]) -> None:
    old, new = _pair(tmp_path, *_provenance_only())

    result = _invoke(
        "--section", "graph", "--ignore", "graph", *extra, str(old), str(new)
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    assert result.stderr != ""


def test_exit_code_policy(tmp_path: Path) -> None:
    prov = diff_plan_files(*_pair(tmp_path, *_provenance_only()))
    sem = diff_plan_files(*_pair(tmp_path, *_semantic()))
    same = diff_plan_files(*_pair(tmp_path, _plan(), _plan()))

    assert [_exit_code(prov, strict=s) for s in (False, True)] == [0, 1]
    assert [_exit_code(sem, strict=s) for s in (False, True)] == [1, 1]
    assert [_exit_code(same, strict=s) for s in (False, True)] == [0, 0]


def test_default_provenance_only_exits_zero_and_strict_exits_one(
    tmp_path: Path,
) -> None:
    old, new = _pair(tmp_path, *_provenance_only())

    assert _invoke(str(old), str(new)).exit_code == 0
    assert _invoke("--strict", str(old), str(new)).exit_code == 1


def test_semantic_difference_exits_one(tmp_path: Path) -> None:
    old, new = _pair(tmp_path, *_semantic())

    assert _invoke(str(old), str(new)).exit_code == 1


def test_ignore_wins_over_strict(tmp_path: Path) -> None:
    old, new = _pair(tmp_path, *_provenance_only())

    result = _invoke("--strict", "--ignore", "provenance", str(old), str(new))

    assert result.exit_code == 0, result.output


def test_section_provenance_alone_needs_strict(tmp_path: Path) -> None:
    old, new = _pair(tmp_path, *_provenance_only())

    assert _invoke("--section", "provenance", str(old), str(new)).exit_code == 0
    assert (
        _invoke("--strict", "--section", "provenance", str(old), str(new)).exit_code
        == 1
    )


def test_path_arguments_are_not_checked_by_typer(tmp_path: Path) -> None:
    result = _invoke(str(tmp_path / "missing.yaml"), str(tmp_path / "also.yaml"))

    # Typer no longer rejects the path; Flow raises (turned into exit 2 in a later task).
    assert isinstance(result.exception, InputNotFound)
    assert "does not exist" not in result.output
