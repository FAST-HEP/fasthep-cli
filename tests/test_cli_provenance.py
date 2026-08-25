from __future__ import annotations

from pathlib import Path

import pytest

import fasthep_cli.commands.provenance as provenance_command_module
from fasthep_cli.app import app
from tests._helpers import runner


def test_provenance_summary_command_delegates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[Path] = []

    def fake_summary(outdir: Path) -> str:
        calls.append(outdir)
        return "summary text"

    monkeypatch.setattr(
        provenance_command_module,
        "provenance_summary_text",
        fake_summary,
    )

    result = runner.invoke(app, ["provenance", "summary", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert calls == [tmp_path]
    assert "summary text" in result.output


def test_provenance_show_command_delegates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = tmp_path / "artifacts" / "files" / "selected.root"
    calls: list[Path] = []

    def fake_show(path: Path) -> str:
        calls.append(path)
        return "artifact text"

    monkeypatch.setattr(
        provenance_command_module,
        "provenance_artifact_text",
        fake_show,
    )

    result = runner.invoke(app, ["provenance", "show", str(artifact)])

    assert result.exit_code == 0, result.output
    assert calls == [artifact]
    assert "artifact text" in result.output


def test_provenance_graph_command_delegates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = tmp_path / "artifacts" / "files" / "selected.root"
    calls: list[tuple[Path, str]] = []

    def fake_graph(path: Path, *, output_format: str) -> str:
        calls.append((path, output_format))
        return "flowchart TD\n"

    monkeypatch.setattr(
        provenance_command_module,
        "provenance_graph_text",
        fake_graph,
    )

    result = runner.invoke(
        app,
        ["provenance", "graph", str(artifact), "--format", "mermaid"],
    )

    assert result.exit_code == 0, result.output
    assert calls == [(artifact, "mermaid")]
    assert "flowchart TD" in result.output


def test_provenance_graph_command_writes_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = tmp_path / "artifacts" / "files" / "selected.root"
    output = tmp_path / "graph.dot"

    def fake_graph(path: Path, *, output_format: str) -> str:
        assert path == artifact
        assert output_format == "dot"
        return "digraph provenance {}\n"

    monkeypatch.setattr(
        provenance_command_module,
        "provenance_graph_text",
        fake_graph,
    )

    result = runner.invoke(
        app,
        [
            "provenance",
            "graph",
            str(artifact),
            "--format",
            "dot",
            "--out",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert result.output == ""
    assert output.read_text(encoding="utf-8") == "digraph provenance {}\n"
