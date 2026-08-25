from __future__ import annotations

import json
from pathlib import Path

import pytest
from fasthep_toolbench.command import CommandResult
from fasthep_toolbench.install import InstallResult
from fasthep_toolbench.model import ToolAvailability

import fasthep_cli.commands.tools as tools_command_module
from fasthep_cli.app import app
from tests._helpers import runner


def test_tools_list_command_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        tools_command_module,
        "tools_list_text",
        lambda: "Registered tools:\n  example.tool\n",
    )

    result = runner.invoke(app, ["tools", "list"])

    assert result.exit_code == 0, result.output
    assert "example.tool" in result.output


def test_tools_info_command_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_info(tool: str) -> str:
        calls.append(tool)
        return "Tool: example.tool\n"

    monkeypatch.setattr(tools_command_module, "tool_info_text", fake_info)

    result = runner.invoke(app, ["tools", "info", "example.tool"])

    assert result.exit_code == 0, result.output
    assert calls == ["example.tool"]
    assert "Tool: example.tool" in result.output


def test_tools_das_discover_command_delegates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    list_dir = tmp_path / "list"
    list_dir.mkdir()
    output_dir = tmp_path / "out"
    proxy = tmp_path / "proxy"
    proxy.write_text("proxy", encoding="utf-8")
    calls: list[tuple[Path, Path, str, str, Path | None, float]] = []

    def fake_discover(
        *,
        list_dir: Path,
        output_dir: Path,
        era: str,
        version: str,
        x509_proxy: Path | None,
        timeout: float,
    ) -> dict[str, Path]:
        calls.append((list_dir, output_dir, era, version, x509_proxy, timeout))
        return {
            "datasets": output_dir / "discovery" / "datasets.json",
            "files": output_dir / "discovery" / "files.json",
        }

    monkeypatch.setattr(
        tools_command_module,
        "discover_das_datasets",
        fake_discover,
    )

    result = runner.invoke(
        app,
        [
            "tools",
            "das-discover",
            str(list_dir),
            "--out",
            str(output_dir),
            "--era",
            "RunIII2024Summer24",
            "--version",
            "v15",
            "--x509-proxy",
            str(proxy),
            "--timeout",
            "5",
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [
        (
            list_dir,
            output_dir,
            "RunIII2024Summer24",
            "v15",
            proxy,
            5.0,
        )
    ]
    assert "datasets:" in result.output
    assert "files:" in result.output


def test_tools_install_command_uses_project_local_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, Path | None]] = []

    def fake_install(tool: str, *, install_dir: Path | None = None) -> InstallResult:
        calls.append((tool, install_dir))
        return InstallResult(
            tool=tool,
            version="0.7.0",
            binary=tmp_path / ".fasthep" / "bin" / "d2-0.7.0",
            link=tmp_path / ".fasthep" / "bin" / "d2",
            installed=True,
            message="Installed d2 0.7.0",
        )

    monkeypatch.setattr(tools_command_module, "install_tool", fake_install)

    result = runner.invoke(app, ["tools", "install", "d2"])

    assert result.exit_code == 0, result.output
    assert calls == [("d2", None)]
    assert "Installed d2 0.7.0" in result.output


def test_tools_install_command_accepts_global_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[Path | None] = []

    def fake_install(tool: str, *, install_dir: Path | None = None) -> InstallResult:
        assert tool == "d2"
        calls.append(install_dir)
        return InstallResult(
            tool=tool,
            version="0.7.0",
            binary=tmp_path / "global" / "bin" / "d2-0.7.0",
            link=tmp_path / "global" / "bin" / "d2",
            installed=True,
            message="Installed d2 0.7.0",
        )

    monkeypatch.setattr(tools_command_module, "install_tool", fake_install)

    result = runner.invoke(
        app,
        ["tools", "install", "d2", "--global", str(tmp_path / "global")],
    )

    assert result.exit_code == 0, result.output
    assert calls == [tmp_path / "global"]


def test_tools_run_command_formats_python_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, list[str]]] = []

    def fake_run(tool: str, args: list[str]) -> dict[str, bool]:
        calls.append((tool, args))
        return {"ok": True}

    monkeypatch.setattr(tools_command_module, "run_registered_tool", fake_run)
    monkeypatch.setattr(
        tools_command_module,
        "_ensure_available_for_run",
        lambda tool, *, auto_install, no_install: None,
    )

    result = runner.invoke(
        app,
        ["tools", "run", "example.tool", "--query", "dataset"],
    )

    assert result.exit_code == 0, result.output
    assert calls == [("example.tool", ["--query", "dataset"])]
    assert '"ok": true' in result.output


def test_tools_run_command_streams_command_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(tool: str, args: list[str]) -> CommandResult:
        assert tool == "example.tool"
        assert args == ["--query", "dataset"]
        return CommandResult(
            command=["example-tool", "--query", "dataset"],
            exit_code=3,
            stdout="out text\n",
            stderr="err text\n",
        )

    monkeypatch.setattr(tools_command_module, "run_registered_tool", fake_run)
    monkeypatch.setattr(
        tools_command_module,
        "_ensure_available_for_run",
        lambda tool, *, auto_install, no_install: None,
    )

    result = runner.invoke(
        app,
        ["tools", "run", "example.tool", "--query", "dataset"],
    )

    assert result.exit_code == 3
    assert "out text\n" in result.output
    assert "err text\n" in result.stderr


def test_tools_run_command_json_formats_command_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(tool: str, args: list[str]) -> CommandResult:
        assert tool == "example.tool"
        assert args == ["--query", "dataset"]
        return CommandResult(
            command=["example-tool", "--query", "dataset"],
            exit_code=3,
            stdout="out text\n",
            stderr="err text\n",
        )

    monkeypatch.setattr(tools_command_module, "run_registered_tool", fake_run)
    monkeypatch.setattr(
        tools_command_module,
        "_ensure_available_for_run",
        lambda tool, *, auto_install, no_install: None,
    )

    result = runner.invoke(
        app,
        ["tools", "run", "example.tool", "--query", "dataset", "--json"],
    )

    assert result.exit_code == 3
    assert result.stderr == ""
    parsed = json.loads(result.output)
    assert parsed == {
        "command": ["example-tool", "--query", "dataset"],
        "executable": "example-tool",
        "exit_code": 3,
        "stderr": "err text\n",
        "stdout": "out text\n",
        "timed_out": False,
        "tool": "example.tool",
    }


def test_tools_run_command_d2_positional_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(tool: str, args: list[str]) -> CommandResult:
        assert tool == "d2"
        assert args == ["input.d2", "output.svg"]
        return CommandResult(
            command=["d2", "input.d2", "output.svg", "--format", "svg"],
            exit_code=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(tools_command_module, "run_registered_tool", fake_run)
    monkeypatch.setattr(
        tools_command_module,
        "_ensure_available_for_run",
        lambda tool, *, auto_install, no_install: None,
    )

    result = runner.invoke(app, ["tools", "run", "d2", "input.d2", "output.svg"])

    assert result.exit_code == 0, result.output
    assert result.output == ""


def test_tools_run_command_d2_json_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(tool: str, args: list[str]) -> CommandResult:
        assert tool == "d2"
        assert args == ["input.d2", "output.svg"]
        return CommandResult(
            command=["d2", "input.d2", "output.svg", "--format", "svg"],
            exit_code=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(tools_command_module, "run_registered_tool", fake_run)
    monkeypatch.setattr(
        tools_command_module,
        "_ensure_available_for_run",
        lambda tool, *, auto_install, no_install: None,
    )

    result = runner.invoke(
        app,
        ["tools", "run", "d2", "input.d2", "output.svg", "--json"],
    )

    assert result.exit_code == 0, result.output
    parsed = json.loads(result.output)
    assert parsed["tool"] == "d2"
    assert parsed["command"] == ["d2", "input.d2", "output.svg", "--format", "svg"]


def test_tools_run_command_no_install_fails_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        tools_command_module,
        "tool_availability",
        lambda spec: ToolAvailability(
            available=False,
            method="path",
            executable="d2",
            message="missing",
        ),
    )
    monkeypatch.setattr(tools_command_module, "run_registered_tool", pytest.fail)

    result = runner.invoke(
        app,
        ["tools", "run", "d2", "input.d2", "output.svg", "--no-install"],
    )

    assert result.exit_code == 127
    assert "fasthep tools install d2" in result.stderr


def test_tools_run_command_auto_install_before_running(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        tools_command_module,
        "tool_availability",
        lambda spec: ToolAvailability(
            available=False,
            method="path",
            executable="d2",
            message="missing",
        ),
    )

    def fake_install(tool: str, *, install_dir: Path | None = None) -> InstallResult:
        assert install_dir is None
        calls.append(f"install:{tool}")
        return InstallResult(
            tool=tool,
            version="0.7.0",
            binary=tmp_path / ".fasthep" / "bin" / "d2-0.7.0",
            link=tmp_path / ".fasthep" / "bin" / "d2",
            installed=True,
            message="Installed d2 0.7.0",
        )

    def fake_run(tool: str, args: list[str]) -> CommandResult:
        calls.append(f"run:{tool}:{' '.join(args)}")
        return CommandResult(command=["d2"], exit_code=0, stdout="", stderr="")

    monkeypatch.setattr(tools_command_module, "install_tool", fake_install)
    monkeypatch.setattr(tools_command_module, "run_registered_tool", fake_run)

    result = runner.invoke(
        app,
        [
            "tools",
            "run",
            "d2",
            "input.d2",
            "output.svg",
            "--auto-install",
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == ["install:d2", "run:d2:input.d2 output.svg"]
