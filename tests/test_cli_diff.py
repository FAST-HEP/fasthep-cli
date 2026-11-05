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


def _with_params(plan: dict[str, Any], **params: Any) -> dict[str, Any]:
    plan = copy.deepcopy(plan)
    plan["nodes"][0]["params"] = params
    return plan


def _moved_pair() -> tuple[dict[str, Any], dict[str, Any]]:
    old = _plan()
    old["provenance"]["inputs"][0].update(
        declared="skim/legacy/x.yaml", resolved="/a/skim/legacy/x.yaml"
    )
    new = copy.deepcopy(old)
    new["context"].update(project_root="/b", workflow_path="/b/wf.yaml")
    new["provenance"]["root"] = "/b"
    new["provenance"]["inputs"][0].update(
        declared="skim/productions/x.yaml", resolved="/b/skim/productions/x.yaml"
    )
    return old, new


def test_equal_plans_summary(tmp_path: Path) -> None:
    old, new = _pair(tmp_path, _plan(), _plan())

    result = _invoke(str(old), str(new))

    assert result.exit_code == 0
    assert result.stdout == "Plans equal.\n"


def test_provenance_only_summary_default_and_strict(tmp_path: Path) -> None:
    old, new = _pair(tmp_path, *_provenance_only())

    default = _invoke(str(old), str(new))
    strict = _invoke("--strict", str(old), str(new))

    first = default.stdout.splitlines()[0]
    assert first == "Plans equal except provenance (2)."
    assert strict.stdout.splitlines()[0] == "Plans differ: provenance=2."


def test_default_mode_lists_moves_and_exits_zero(tmp_path: Path) -> None:
    old, new = _pair(tmp_path, *_moved_pair())

    result = _invoke(str(old), str(new))

    assert result.exit_code == 0
    assert "  moved  provenance.inputs[role='workflow',sha256='" in result.stdout
    assert "    from: skim/legacy/x.yaml\n" in result.stdout
    assert "    to: skim/productions/x.yaml\n" in result.stdout


def test_sections_listed_in_public_order_with_counts(tmp_path: Path) -> None:
    old = _plan()
    new = copy.deepcopy(old)
    new["nodes"][0]["params"]["x"] = 2
    new["partitions"].append({"source": "s", "dataset": "d", "file": "f", "part": 0})
    new["context"]["workflow_path"] = "/b/wf.yaml"
    new["extra"] = 1
    paths = _pair(tmp_path, old, new)

    result = _invoke(*map(str, paths))

    assert result.stdout.splitlines()[0] == (
        "Plans differ: graph=1, data=1, provenance=1, unknown=1."
    )
    headers = [line for line in result.stdout.splitlines() if line.startswith("[")]
    assert headers == ["[graph]", "[data]", "[provenance]", "[unknown]"]


def test_scalar_types_are_unambiguous(tmp_path: Path) -> None:
    old = _with_params(_plan(), a=1, b=1, c="1")
    new = _with_params(_plan(), a="1", b=True, c=1.0)
    paths = _pair(tmp_path, old, new)

    out = _invoke(*map(str, paths)).stdout

    assert '    old: 1\n    new: "1"\n' in out
    assert "    old: 1\n    new: true\n" in out
    assert '    old: "1"\n    new: 1.0\n' in out


def test_multiline_and_structured_values_are_indented_blocks(tmp_path: Path) -> None:
    old = _with_params(_plan(), text="a\nb")
    new = _with_params(_plan(), text="a\nc", nested={"k": [1, 3]})
    paths = _pair(tmp_path, old, new)

    out = _invoke(*map(str, paths)).stdout

    assert "    old:\n      a\n      b\n    new:\n      a\n      c\n" in out
    assert "  added  nodes[id='n1'].params.nested\n    new:\n      {\n" in out
    assert '        "k": [\n' in out


def test_large_report_is_not_truncated(tmp_path: Path) -> None:
    old = _with_params(_plan(), **{f"p{i}": i for i in range(200)})
    new = _with_params(_plan(), **{f"p{i}": i + 1 for i in range(200)})
    paths = _pair(tmp_path, old, new)

    result = _invoke(*map(str, paths))

    assert result.stdout.splitlines()[0] == "Plans differ: graph=200."
    assert (
        sum(line.startswith("  changed  ") for line in result.stdout.splitlines())
        == 200
    )


def test_added_removed_and_conflict_blocks(tmp_path: Path) -> None:
    old = _plan()
    new = copy.deepcopy(old)
    new["nodes"].append({"id": "n2", "inputs": [], "params": {}, "meta": {}})
    new["provenance"]["inputs"].append(
        dict(new["provenance"]["inputs"][0], resolved="/a/other.yaml")
    )
    new["provenance"]["inputs"].append(
        dict(new["provenance"]["inputs"][0], resolved="/a/third.yaml")
    )
    paths = _pair(tmp_path, old, new)

    out = _invoke(*map(str, paths)).stdout

    assert "  added  nodes[id='n2']\n    new:\n" in out
    assert (
        "  identity_conflict  provenance.inputs[role='workflow',declared='wf.yaml']\n"
        in out
    )
    assert "[fallback alignment]" in out


def test_warning_goes_to_stderr_in_human_mode(tmp_path: Path) -> None:
    old = _plan()
    new = copy.deepcopy(old)
    new["provenance"]["compilation"]["flow_version"] = "2.0"
    paths = _pair(tmp_path, old, new)

    result = _invoke(*map(str, paths))

    assert result.exit_code == 0
    assert "warning:" in result.stderr
    assert "warning:" not in result.stdout


def test_external_path_values_carry_their_label(tmp_path: Path) -> None:
    old = _plan()
    new = copy.deepcopy(old)
    new["provenance"]["inputs"][0]["resolved"] = "/elsewhere/wf.yaml"
    paths = _pair(tmp_path, old, new)

    out = _invoke(*map(str, paths)).stdout

    assert '    old: "wf.yaml"\n' in out
    assert '    new: "/elsewhere/wf.yaml" (external)\n' in out
