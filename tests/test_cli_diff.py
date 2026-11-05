from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml
from hepflow.api import DiffSection, PlanDiffError, diff_plan_files
from typer import BadParameter
from typer.testing import CliRunner

import fasthep_cli.app as cli_app
from fasthep_cli.app import _is_json_diff_request, app
from fasthep_cli.commands.diff import _exit_code, _selected_sections
from fasthep_cli.testing import strip_ansi
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

    assert result.exit_code == 2
    assert "plan input not found" in result.stderr
    assert "does not exist" not in result.stderr


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


# -- JSON envelope, errors and logo ---------------------------------------------


def _json(result: Any) -> dict[str, Any]:
    assert result.stderr == "", result.stderr
    document = json.loads(result.stdout)
    assert isinstance(document, dict)
    return document


def _build(
    tmp_path: Path, names: list[str], plan: dict[str, Any] | None = None
) -> Path:
    root = tmp_path / "build"
    for name in names:
        directory = root / "compile" / name
        directory.mkdir(parents=True)
        (directory / "plan.yaml").write_text(
            yaml.safe_dump(plan or _plan(), sort_keys=False), encoding="utf-8"
        )
    summary = {
        "variations": [
            {"name": n, "is_nominal": n == "nominal", "plan": f"compile/{n}/plan.yaml"}
            for n in names
        ]
    }
    (root / "compile" / "systematics.yaml").write_text(
        yaml.safe_dump(summary), encoding="utf-8"
    )
    return root


def test_json_equal_envelope_is_complete(tmp_path: Path) -> None:
    old, new = _pair(tmp_path, _plan(), _plan())

    document = _json(_invoke("--json", str(old), str(new)))

    assert sorted(document) == [
        "cli_schema_version",
        "command",
        "error",
        "exit_code",
        "inputs",
        "policy",
        "report",
        "resolved",
        "scope",
        "status",
    ]
    assert document["cli_schema_version"] == 1
    assert document["command"] == "diff"
    assert document["inputs"] == {"old": str(old), "new": str(new)}
    assert document["resolved"] == {"old": str(old), "new": str(new)}
    assert document["scope"] == {
        "include": [s.value for s in DiffSection],
        "ignore": [],
    }
    assert document["policy"] == "semantic"
    assert (document["status"], document["exit_code"], document["error"]) == (
        "equal",
        0,
        None,
    )
    assert {"entries", "counts", "warnings", "equal", "semantically_equal"} <= set(
        document["report"]
    )


def test_json_difference_envelope_and_exit_one(tmp_path: Path) -> None:
    old, new = _pair(tmp_path, *_semantic())

    result = _invoke("--json", "--strict", str(old), str(new))
    document = _json(result)

    assert result.exit_code == 1
    assert (document["status"], document["exit_code"], document["policy"]) == (
        "different",
        1,
        "strict",
    )
    assert document["report"]["entries"][0]["section"] == "graph"


def test_json_provenance_only_default_exit_zero_keeps_entries(tmp_path: Path) -> None:
    old, new = _pair(tmp_path, *_provenance_only())

    result = _invoke("--json", str(old), str(new))
    document = _json(result)

    assert result.exit_code == 0
    assert document["status"] == "equal"
    assert document["report"]["equal"] is False
    assert document["report"]["semantically_equal"] is True
    assert len(document["report"]["entries"]) == 2


def test_json_scope_and_scoped_report(tmp_path: Path) -> None:
    old, new = _pair(tmp_path, *_provenance_only())

    document = _json(
        _invoke(
            "--json",
            "--ignore",
            "provenance",
            "--ignore",
            "provenance",
            str(old),
            str(new),
        )
    )

    assert document["scope"]["ignore"] == ["provenance"]
    assert document["report"]["entries"] == []
    assert document["report"]["scope"]["ignore"] == ["provenance"]


def test_json_is_deterministic_and_key_sorted(tmp_path: Path) -> None:
    old, new = _pair(tmp_path, *_semantic())

    first = _invoke("--json", str(old), str(new)).stdout
    second = _invoke("--json", str(old), str(new)).stdout

    assert first == second
    assert first.rstrip("\n") == json.dumps(json.loads(first), indent=2, sort_keys=True)


def test_json_missing_input(tmp_path: Path) -> None:
    result = _invoke("--json", str(tmp_path / "no"), str(tmp_path / "no2"))
    document = _json(result)

    assert result.exit_code == 2
    assert document["status"] == "error"
    assert document["report"] is None
    assert document["error"]["code"] == "input_not_found"
    assert document["resolved"] == {"old": None, "new": None}


def test_json_no_plan_found(tmp_path: Path) -> None:
    (tmp_path / "empty" / "compile").mkdir(parents=True)
    other = _write(tmp_path, "p.yaml", _plan())

    document = _json(_invoke("--json", str(other), str(tmp_path / "empty")))

    assert document["error"]["code"] == "no_plan_found"
    assert document["resolved"] == {"old": str(other), "new": None}


def test_json_ambiguous_plans_lists_candidates(tmp_path: Path) -> None:
    build = _build(tmp_path, ["nominal", "up"])
    other = _write(tmp_path, "p.yaml", _plan())

    result = _invoke("--json", str(build), str(other))
    document = _json(result)

    assert result.exit_code == 2
    assert document["error"]["code"] == "ambiguous_plans"
    assert [c["name"] for c in document["error"]["candidates"]] == ["nominal", "up"]
    assert document["error"]["candidates"][0]["path"].endswith(
        "compile/nominal/plan.yaml"
    )
    assert "explicit plan" in document["error"]["message"]


def test_json_invalid_plan(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("- 1\n- 2\n", encoding="utf-8")
    good = _write(tmp_path, "good.yaml", _plan())

    document = _json(_invoke("--json", str(good), str(bad)))

    assert document["error"]["code"] == "invalid_plan"


def test_json_comparison_failed_for_plain_flow_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(*_args: object) -> None:
        message = "boom"
        raise PlanDiffError(message)

    monkeypatch.setattr("fasthep_cli.commands.diff.diff_plan_files", boom)
    old, new = _pair(tmp_path, _plan(), _plan())

    result = _invoke("--json", str(old), str(new))
    document = _json(result)

    assert (result.exit_code, document["error"]["code"]) == (2, "comparison_failed")


def test_human_errors_go_to_stderr_with_exit_two(tmp_path: Path) -> None:
    build = _build(tmp_path, ["nominal", "up"])
    other = _write(tmp_path, "p.yaml", _plan())

    for args in (
        (str(tmp_path / "no"), str(other)),
        (str(build), str(other)),
    ):
        result = _invoke(*args)
        assert result.exit_code == 2
        assert result.stdout == ""
        assert result.stderr.startswith("error: ")


def test_json_warnings_are_in_the_envelope_and_stderr_is_empty(tmp_path: Path) -> None:
    old = _plan()
    new = copy.deepcopy(old)
    new["provenance"]["compilation"]["flow_version"] = "2.0"
    paths = _pair(tmp_path, old, new)

    document = _json(_invoke("--json", *map(str, paths)))

    assert [w["code"] for w in document["report"]["warnings"]] == [
        "flow_version_mismatch"
    ]


def test_usage_error_with_json_stays_text_on_stderr(tmp_path: Path) -> None:
    old, new = _pair(tmp_path, _plan(), _plan())

    result = _invoke("--json", "--section", "nope", str(old), str(new))

    assert result.exit_code == 2
    assert result.stdout == ""
    assert "nope" in result.stderr


def test_file_and_build_directory_inputs(tmp_path: Path) -> None:
    build = _build(tmp_path, ["only"])
    plan_file = _write(tmp_path, "p.yaml", _plan())

    for directory in (build, build / "compile"):
        for args in (
            (str(plan_file), str(directory)),
            (str(directory), str(plan_file)),
        ):
            result = _invoke("--json", *args)
            document = _json(result)
            assert result.exit_code == 0
            assert document["resolved"]["old"] is not None
    assert document["resolved"]["new"].endswith("p.yaml")


def test_delegates_to_flow_api_with_resolved_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old, new = _pair(tmp_path, _plan(), _plan())
    resolved_old, resolved_new = tmp_path / "ro.yaml", tmp_path / "rn.yaml"
    seen: dict[str, Any] = {"resolve": [], "diff": []}

    def fake_resolve(path: Path) -> Path:
        seen["resolve"].append(path)
        return resolved_old if path == old else resolved_new

    def fake_diff(a: Path, b: Path) -> Any:
        seen["diff"].append((a, b))
        return diff_plan_files(old, new)

    monkeypatch.setattr("fasthep_cli.commands.diff.resolve_plan_input", fake_resolve)
    monkeypatch.setattr("fasthep_cli.commands.diff.diff_plan_files", fake_diff)

    result = _invoke(str(old), str(new))

    assert result.exit_code == 0
    assert seen["resolve"] == [old, new]
    assert seen["diff"] == [(resolved_old, resolved_new)]


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["diff", "--json", "a", "b"], True),
        (["--quiet", "diff", "a", "b", "--json"], True),
        (["diff", "a", "b"], False),
        (["versions", "--json"], False),
        (["diff", "--", "--json"], False),
    ],
)
def test_is_json_diff_request(argv: list[str], expected: bool) -> None:
    assert _is_json_diff_request(argv) is expected


def test_logo_is_not_printed_for_diff_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_logo() -> None:
        pytest.fail("logo must not be printed before diff --json")

    old, new = _pair(tmp_path, _plan(), _plan())
    monkeypatch.delenv("FASTHEP_NO_LOGO", raising=False)
    monkeypatch.setattr(cli_app, "_stdout_is_tty", lambda: True)
    monkeypatch.setattr(sys, "argv", ["fasthep", "diff", "--json", str(old), str(new)])
    monkeypatch.setattr(cli_app, "_maybe_print_logo", fail_logo)

    result = CliRunner().invoke(app, ["diff", "--json", str(old), str(new)])

    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["command"] == "diff"


def test_logo_is_printed_for_plain_diff_on_a_tty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    old, new = _pair(tmp_path, _plan(), _plan())
    monkeypatch.delenv("FASTHEP_NO_LOGO", raising=False)
    monkeypatch.setattr(sys, "argv", ["fasthep", "diff", str(old), str(new)])
    monkeypatch.setattr(cli_app, "_maybe_print_logo", lambda: calls.append("logo"))

    result = CliRunner().invoke(app, ["diff", str(old), str(new)])

    assert result.exit_code == 0, result.output
    assert calls == ["logo"]


def test_help_describes_options_and_exit_codes() -> None:
    result = _invoke("--help")
    text = strip_ansi(result.output)

    assert result.exit_code == 0
    for needle in ("--strict", "--json", "--section", "--ignore", "OLD", "NEW"):
        assert needle in text
    assert "provenance" in text
    for code in ("0", "1", "2"):
        assert f"{code}  " in text or f"{code}:" in text or f" {code} " in text
    assert "plan-diff" in text


def test_old_two_file_invocation_still_works(tmp_path: Path) -> None:
    old, new = _pair(tmp_path, _plan(), _plan())

    result = _invoke(str(old), str(new))

    assert (result.exit_code, result.stdout) == (0, "Plans equal.\n")
