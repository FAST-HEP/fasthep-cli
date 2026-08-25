from __future__ import annotations

from pathlib import Path

import pytest

import fasthep_cli.commands.init as init_command_module
from fasthep_cli.app import app
from fasthep_cli.testing import strip_ansi
from tests._helpers import runner


def test_init_command_smoke(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", "--target-dir", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert (tmp_path / ".fasthep" / "profiles" / "hepflow" / "registry.yaml").exists()
    assert not (tmp_path / ".hepflow").exists()


def test_init_command_accepts_repeatable_includes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[Path, bool, list[str], list[str]]] = []

    class FakeResult:
        def __init__(self) -> None:
            self.profile_dir = tmp_path / ".fasthep" / "profiles" / "hepflow"
            self.created_profile_dir = True
            self.copied: list[Path] = []
            self.overwritten: list[Path] = []
            self.skipped_existing: list[Path] = []
            self.written: list[Path] = []
            self.warnings: list[str] = []

    def fake_init_project(
        *,
        target_dir: Path,
        force: bool,
        include: list[str],
        profiles: list[str],
    ) -> FakeResult:
        calls.append((target_dir, force, include, profiles))
        return FakeResult()

    monkeypatch.setattr(init_command_module, "init_project", fake_init_project)

    result = runner.invoke(
        app,
        [
            "init",
            "--target-dir",
            str(tmp_path),
            "--include",
            "fasthep_workshop:registry",
            "--include",
            "./profiles/custom.yaml",
            "--profile",
            "HEP",
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [
        (
            tmp_path,
            False,
            ["fasthep_workshop:registry", "./profiles/custom.yaml"],
            ["HEP"],
        )
    ]


def test_init_command_displays_api_warnings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResult:
        def __init__(self) -> None:
            self.profile_dir = tmp_path / ".fasthep" / "profiles" / "hepflow"
            self.created_profile_dir = True
            self.copied: list[Path] = []
            self.overwritten: list[Path] = []
            self.skipped_existing: list[Path] = []
            self.written: list[Path] = []
            self.warnings = ["profile package not found: fasthep_render"]

    def fake_init_project(**_: object) -> FakeResult:
        return FakeResult()

    monkeypatch.setattr(init_command_module, "init_project", fake_init_project)

    result = runner.invoke(
        app,
        ["init", "--target-dir", str(tmp_path), "--profile", "HEP"],
    )

    assert result.exit_code == 0, result.output
    assert "Warning: profile package not found: fasthep_render" in result.output


def test_init_command_has_no_profile_expansion_helpers() -> None:
    assert not hasattr(init_command_module, "HEP_PROFILE_PACKAGES")
    assert not hasattr(init_command_module, "copy_profile_bundles")
    assert not hasattr(init_command_module, "copy_package_profiles")


def test_init_help_documents_include_examples() -> None:
    result = runner.invoke(app, ["init", "--help"])

    assert result.exit_code == 0, result.output
    assert "--include" in strip_ansi(result.output)
    assert "--profile" in strip_ansi(result.output)
    assert "fasthep_workshop:registry" in strip_ansi(result.output)
    assert "./profiles/custom.yaml" in strip_ansi(result.output)
