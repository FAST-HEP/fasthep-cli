from __future__ import annotations

import json
from pathlib import Path

import fasthep_render.api as render_api
import pytest
import yaml
from fasthep_render.model import RenderStatus

import fasthep_cli.commands.render as render_command_module
from fasthep_cli.app import app
from fasthep_cli.testing import strip_ansi
from tests._helpers import runner


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
