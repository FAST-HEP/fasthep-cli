from __future__ import annotations

import json
from pathlib import Path

import fasthep_render.api as render_api
import pytest
import yaml
from fasthep_render.model import RenderStatus
from fasthep_toolbench.command import CommandResult
from fasthep_toolbench.install import InstallResult
from fasthep_toolbench.model import ToolAvailability
from typer.testing import CliRunner

import fasthep_cli
import fasthep_cli.app as cli_app
import fasthep_cli.commands.init as init_command_module
import fasthep_cli.commands.provenance as provenance_command_module
import fasthep_cli.commands.render as render_command_module
import fasthep_cli.commands.tools as tools_command_module
from fasthep_cli.app import app
from fasthep_cli.testing import strip_ansi

runner = CliRunner(env={"FASTHEP_NO_LOGO": "1"})


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


def test_render_spec_command_delegates_to_render_api(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = tmp_path / "render.yaml"
    product = tmp_path / "hist.pkl"
    out = tmp_path / "plot.png"
    spec.write_text("spec: {}\n", encoding="utf-8")
    product.write_bytes(b"pickle")
    calls: list[tuple[Path, Path | None, Path | None, Path | None]] = []

    class FakeOutcome:
        status = RenderStatus.RENDERED
        output_path = out

    def fake_render_spec_file(
        spec_path: Path,
        *,
        product: Path | None,
        out: Path | None,
        plan_path: Path | None,
    ) -> FakeOutcome:
        calls.append((spec_path, product, out, plan_path))
        return FakeOutcome()

    monkeypatch.setattr(render_api, "render_spec_file", fake_render_spec_file)

    result = runner.invoke(
        app,
        [
            "render",
            "spec",
            str(spec),
            "--product",
            str(product),
            "--out",
            str(out),
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [(spec, product, out, None)]
    assert f"Output: {out}" in result.output


def test_render_spec_command_passes_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = tmp_path / "render.yaml"
    product = tmp_path / "hist.pkl"
    plan = tmp_path / "plan.yaml"
    spec.write_text("spec: {}\n", encoding="utf-8")
    product.write_bytes(b"pickle")
    plan.write_text("nodes: []\n", encoding="utf-8")
    calls: list[Path | None] = []

    class FakeOutcome:
        status = RenderStatus.RENDERED
        output_path = tmp_path / "plot.png"

    def fake_render_spec_file(
        spec_path: Path,
        *,
        product: Path | None,
        out: Path | None,
        plan_path: Path | None,
    ) -> FakeOutcome:
        calls.append(plan_path)
        return FakeOutcome()

    monkeypatch.setattr(render_api, "render_spec_file", fake_render_spec_file)

    result = runner.invoke(
        app,
        [
            "render",
            "spec",
            str(spec),
            "--product",
            str(product),
            "--plan",
            str(plan),
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [plan]


def test_render_spec_command_requires_product(tmp_path: Path) -> None:
    spec = tmp_path / "render.yaml"
    spec.write_text("spec: {}\n", encoding="utf-8")

    result = runner.invoke(app, ["render", "spec", str(spec)])

    assert result.exit_code != 0
    assert "--product is required" in strip_ansi(result.output)


def test_render_spec_command_renders_cutflow_csv(
    tmp_path: Path,
) -> None:
    spec = tmp_path / "render.yaml"
    product = tmp_path / "EventSelection.json"
    out = tmp_path / "EventSelection.csv"
    spec.write_text(
        yaml.safe_dump(
            {
                "node_id": "render.EventSelection.0",
                "impl": "hep.render.cutflow_csv",
                "out": "EventSelection.csv",
                "spec": {"op": "hep.render.cutflow_csv"},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    product.write_text(
        json.dumps(
            {
                "version": "1.0",
                "kind": "cutflow",
                "producer": "stage.EventSelection",
                "datasets": ["data"],
                "nodes": [
                    {
                        "id": "All[0]",
                        "selection": "All",
                        "index": 0,
                        "label": "NIsoMuon >= 2",
                        "expr": "NIsoMuon >= 2",
                        "kind": "expression",
                        "parents": [],
                        "stats": {
                            "data": {
                                "n_in": 10.5,
                                "n_out": 7.5,
                                "n_unweighted_in": 10,
                                "n_unweighted_out": 7,
                                "sumw_in": 10.5,
                                "sumw_out": 7.5,
                                "sumw2_in": 10.0,
                                "sumw2_out": 7.0,
                            }
                        },
                    }
                ],
                "edges": [],
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "render",
            "spec",
            str(spec),
            "--product",
            str(product),
            "--out",
            str(out),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Render complete" in result.output
    assert "All,NIsoMuon >= 2,data,10.5,7.5,10,7" in out.read_text(encoding="utf-8")


def test_render_command_has_no_dispatch_helpers() -> None:
    assert not hasattr(render_command_module, "render_resolved")
    assert not hasattr(render_command_module, "resolve_runtime_registry")
    assert not hasattr(render_command_module, "read_pickle")


def test_normalise_command_smoke(tmp_path: Path) -> None:
    workflow = _write_workflow(tmp_path)
    outdir = tmp_path / "build"

    result = runner.invoke(app, ["normalise", str(workflow), "--outdir", str(outdir)])

    assert result.exit_code == 0, result.output
    assert (outdir / "compile" / "normalized.yaml").exists()


def test_normalize_alias_smoke(tmp_path: Path) -> None:
    workflow = _write_workflow(tmp_path)
    outdir = tmp_path / "build"

    result = runner.invoke(app, ["normalize", str(workflow), "--outdir", str(outdir)])

    assert result.exit_code == 0, result.output
    assert (outdir / "compile" / "normalized.yaml").exists()


def test_make_plan_command_smoke(tmp_path: Path) -> None:
    workflow = _write_workflow(tmp_path)
    outdir = tmp_path / "build"
    result = runner.invoke(app, ["normalise", str(workflow), "--outdir", str(outdir)])
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        app,
        [
            "make-plan",
            str(outdir / "compile" / "normalized.yaml"),
            "--outdir",
            str(outdir),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (outdir / "compile" / "plan.yaml").exists()
    assert (outdir / "graph" / "graph.mmd").exists()
    assert (outdir / "graph" / "graph.dot").exists()


def test_compile_command_smoke(tmp_path: Path) -> None:
    workflow = _write_workflow(tmp_path)
    outdir = tmp_path / "build"

    result = runner.invoke(app, ["compile", str(workflow), "--outdir", str(outdir)])

    assert result.exit_code == 0, result.output
    assert (outdir / "compile" / "normalized.yaml").exists()
    assert (outdir / "compile" / "plan.yaml").exists()


def test_run_plan_command_smoke(tmp_path: Path) -> None:
    plan = _write_empty_plan(tmp_path)

    result = runner.invoke(app, ["run-plan", str(plan)])

    assert result.exit_code == 0, result.output
    assert (tmp_path / "run_summary.yaml").exists()
    assert f"Summary: {tmp_path / 'run_summary.yaml'}" in result.output
    assert f"Artifacts: {tmp_path / 'artifacts'}" in result.output


def test_run_plan_command_reports_variation_paths(tmp_path: Path) -> None:
    build_dir = tmp_path / "build"
    plan = _write_empty_plan(
        build_dir / "compile" / "trigger_eff_down",
        variation="trigger_eff_down",
    )

    result = runner.invoke(app, ["run-plan", str(plan)])

    assert result.exit_code == 0, result.output
    assert (
        f"Summary: {build_dir / 'reports' / 'trigger_eff_down' / 'run_summary.yaml'}"
        in result.output
    )
    assert (
        f"Artifacts: {build_dir / 'artifacts' / 'trigger_eff_down'}"
        in result.output
    )
    assert (build_dir / "reports" / "trigger_eff_down" / "run_summary.yaml").exists()
    assert not (build_dir / "trigger_eff_down" / "artifacts").exists()


def test_run_command_smoke(tmp_path: Path) -> None:
    workflow = _write_workflow(tmp_path)
    outdir = tmp_path / "build"

    result = runner.invoke(app, ["run", str(workflow), "--outdir", str(outdir)])

    assert result.exit_code == 0, result.output
    assert (outdir / "compile" / "normalized.yaml").exists()
    assert (outdir / "compile" / "plan.yaml").exists()
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
        "fasthep_cli_legacy",
        "fasthep-cli-legacy",
    ]
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert not any(item in text for item in forbidden), path


def _write_workflow(tmp_path: Path) -> Path:
    workflow = {
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
    path = tmp_path / "workflow.yaml"
    path.write_text(yaml.safe_dump(workflow, sort_keys=False), encoding="utf-8")
    return path


def _write_empty_plan(tmp_path: Path, *, variation: str | None = None) -> Path:
    context = {}
    if variation is not None:
        context["variation"] = {"name": variation, "is_nominal": False}
    plan = {
        "context": context,
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
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "plan.yaml"
    path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
    return path
