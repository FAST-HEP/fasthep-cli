from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
import yaml
from typer.testing import CliRunner

import fasthep_cli.app as cli_app
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


def test_command_predicate_sees_the_parsed_parameters() -> None:
    seen: list[Mapping[str, Any]] = []

    def predicate(params: Mapping[str, Any]) -> bool:
        seen.append(dict(params))
        return True

    command = logo_command(predicate)

    assert command.logo_off_when is predicate
    assert logo_command().logo_off_when is None
    assert predicate({"a": 1}) is True
    assert seen == [{"a": 1}]
