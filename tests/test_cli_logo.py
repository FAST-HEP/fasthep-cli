from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

import pytest
import yaml
from fasthep_toolbench.tools import CommandResult
from typer.testing import CliRunner

import fasthep_cli.app as cli_app
import fasthep_cli.commands.tools as tools_module
import fasthep_cli.logo_policy as logo_policy
from fasthep_cli.app import app
from fasthep_cli.logo_policy import logo_allowed, logo_command


@pytest.mark.parametrize(
    ("quiet", "environ", "isatty", "expected"),
    [
        (False, {}, True, True),
        (True, {}, True, False),
        (False, {"FASTHEP_NO_LOGO": "1"}, True, False),
        (False, {}, False, False),
        (True, {"FASTHEP_NO_LOGO": "1"}, False, False),
    ],
)
def test_logo_allowed_matrix(
    quiet: bool, environ: Mapping[str, str], isatty: bool, expected: bool
) -> None:
    assert logo_allowed(quiet=quiet, environ=environ, isatty=isatty) is expected


@pytest.fixture
def printed(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Allow a logo in the environment and record every logo print."""
    calls: list[str] = []
    monkeypatch.setattr(cli_app, "logo_allowed", lambda **_kwargs: True)
    monkeypatch.setattr(logo_policy, "print_logo", lambda: calls.append("logo"))
    return calls


def _plan(tmp_path: Path) -> Path:
    path = tmp_path / "plan.yaml"
    path.write_text(yaml.safe_dump({"context": {}}), encoding="utf-8")
    return path


def test_logo_is_printed_for_a_plain_command(
    printed: list[str], tmp_path: Path
) -> None:
    plan = _plan(tmp_path)

    result = CliRunner().invoke(app, ["diff", str(plan), str(plan)])

    assert result.exit_code == 0, result.output
    assert printed == ["logo"]


def test_logo_is_off_for_diff_json(printed: list[str], tmp_path: Path) -> None:
    plan = _plan(tmp_path)

    result = CliRunner().invoke(app, ["diff", "--json", str(plan), str(plan)])

    assert result.exit_code == 0, result.output
    assert printed == []
    assert json.loads(result.stdout)["command"] == "diff"


def test_logo_is_off_for_versions_display_json(printed: list[str]) -> None:
    result = CliRunner().invoke(app, ["versions", "--display", "json"])

    assert result.exit_code == 0, result.output
    assert printed == []
    json.loads(result.stdout)


def test_logo_is_printed_for_versions_with_another_display(printed: list[str]) -> None:
    result = CliRunner().invoke(app, ["versions"])

    assert result.exit_code == 0, result.output
    assert printed == ["logo"]


def test_logo_is_printed_for_a_sub_app_command(printed: list[str]) -> None:
    result = CliRunner().invoke(app, ["tools", "list"])

    assert result.exit_code == 0, result.output
    assert printed == ["logo"]


def test_no_logo_when_the_environment_disallows_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(logo_policy, "print_logo", lambda: calls.append("logo"))

    result = CliRunner().invoke(app, ["version"])  # CliRunner stdout is not a terminal

    assert result.exit_code == 0, result.output
    assert calls == []


def test_command_predicate_is_stored_as_given() -> None:
    seen: list[object] = []

    def predicate(ctx: object) -> bool:
        seen.append(ctx)
        return True

    command = logo_command(predicate)

    assert command.logo_off_when is predicate
    assert logo_command().logo_off_when is None
    assert predicate("ctx") is True
    assert seen == ["ctx"]


def _fake_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        tools_module,
        "run_registered_tool",
        lambda tool, args: CommandResult(
            command=["example-tool"], exit_code=0, stdout="out\n", stderr=""
        ),
    )
    monkeypatch.setattr(
        tools_module,
        "_ensure_available_for_run",
        lambda tool, *, auto_install, no_install: None,
    )


@pytest.mark.parametrize(
    "args",
    [
        ["tools", "run", "example.tool", "--json"],
        ["tools", "run", "--json", "example.tool"],
        ["tools", "run", "example.tool", "--query", "dataset", "--json"],
    ],
)
def test_logo_is_off_for_tools_run_json(
    printed: list[str], monkeypatch: pytest.MonkeyPatch, args: list[str]
) -> None:
    _fake_tool(monkeypatch)

    result = CliRunner().invoke(app, args)

    assert result.exit_code == 0, result.output
    assert printed == []
    assert json.loads(result.stdout)["tool"] == "example.tool"


def test_logo_is_printed_for_tools_run_without_json(
    printed: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _fake_tool(monkeypatch)

    result = CliRunner().invoke(app, ["tools", "run", "example.tool"])

    assert result.exit_code == 0, result.output
    assert printed == ["logo"]
