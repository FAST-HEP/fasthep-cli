from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

import fasthep_cli
import fasthep_cli.app as cli_app
from fasthep_cli.app import app
from fasthep_cli.testing import strip_ansi
from tests._helpers import runner


def test_import_package() -> None:
    assert fasthep_cli.__version__


def test_app_help_smoke() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "normalise" in result.output
    assert "make-plan" in result.output


def test_quiet_version_suppresses_logo(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_logo() -> None:
        pytest.fail("logo should not be printed for --quiet")

    monkeypatch.setattr(cli_app, "_maybe_print_logo", fail_logo)
    result = CliRunner().invoke(app, ["--quiet", "version"])

    assert result.exit_code == 0, result.output
    assert "fasthep-cli" in result.output
    assert "Welcome to the FAST-HEP command line interface" not in result.output


def test_version_command_prints_cli_version() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0, result.output
    assert "fasthep-cli" in result.output
    assert fasthep_cli.__version__ in strip_ansi(result.output)


def test_versions_json_is_parseable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cli_app,
        "find_fast_hep_packages",
        lambda: [("fasthep-cli", "1.2.3")],
    )
    monkeypatch.setattr(
        cli_app,
        "find_hep_packages",
        lambda: [("hist", "2.8.0")],
    )

    result = runner.invoke(app, ["versions", "--display", "json", "--hep"])

    assert result.exit_code == 0, result.output
    parsed = json.loads(strip_ansi(result.output))
    assert parsed == {
        "fasthep_packages": {"fasthep-cli": "1.2.3"},
        "hep_packages": {"hist": "2.8.0"},
    }


def test_download_command_delegates_to_toolbench(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"example.dat": "https://example.invalid/example.dat"}')
    destination = tmp_path / "downloads"
    calls: list[tuple[str, str, bool]] = []

    def fake_download_from_json(
        json_input: str, destination_input: str, force: bool
    ) -> None:
        calls.append((json_input, destination_input, force))
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "example.dat").write_text("payload", encoding="utf-8")

    monkeypatch.setattr(
        cli_app,
        "download_from_json",
        fake_download_from_json,
    )

    result = runner.invoke(
        app,
        [
            "download",
            "--json",
            str(manifest),
            "--destination",
            str(destination),
            "--force",
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [(str(manifest), str(destination), True)]
    assert (destination / "example.dat").read_text(encoding="utf-8") == "payload"


def test_no_forbidden_workflow_imports() -> None:
    root = Path(__file__).parents[1] / "src" / "fasthep_cli"
    forbidden = [
        "hepflow.compiler",
        "hepflow.runtime.engine",
        "hepflow.backends.loaders",
        "fasthep_cli_legacy",
        "fasthep-cli-legacy",
    ]
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert not any(item in text for item in forbidden), path
