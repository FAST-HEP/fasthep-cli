from __future__ import annotations

from pathlib import Path

import numpy as np
import uproot

from fasthep_cli.app import app
from fasthep_cli.testing import strip_ansi
from tests._helpers import runner, schema_fixture


def test_inspect_schema_default_table_output(tmp_path: Path) -> None:
    root_path = schema_fixture(tmp_path)

    result = runner.invoke(app, ["inspect", "schema", str(root_path)])

    assert result.exit_code == 0, result.output
    assert "Field" in result.output
    assert "Type" in result.output
    assert "Shape" in result.output
    assert "GenJetAK8_eta" in result.output
    assert "float32" in result.output
    assert "jagged" in result.output


def test_inspect_schema_explicit_tree(tmp_path: Path) -> None:
    root_path = tmp_path / "schema.root"
    with uproot.recreate(root_path) as root_file:
        root_file["OtherEvents"] = {"GenMET_pt": np.array([1.0], dtype=np.float32)}

    result = runner.invoke(
        app,
        ["inspect", "schema", str(root_path), "--tree", "OtherEvents"],
    )

    assert result.exit_code == 0, result.output
    assert "GenMET_pt" in result.output


def test_inspect_schema_yaml_list_output_with_repeated_filters(
    tmp_path: Path,
) -> None:
    root_path = schema_fixture(tmp_path)

    result = runner.invoke(
        app,
        [
            "inspect",
            "schema",
            str(root_path),
            "--include",
            "GenJet*",
            "--include",
            "GenMET*",
            "--exclude",
            "*hadron*",
            "--exclude",
            "nGen*",
            "--format",
            "yaml-list",
        ],
    )

    assert result.exit_code == 0, result.output
    assert result.output.strip() == "- GenJetAK8_eta\n- GenMET_pt"


def test_inspect_schema_alignment_output(tmp_path: Path) -> None:
    root_path = schema_fixture(tmp_path)

    result = runner.invoke(
        app,
        [
            "inspect",
            "schema",
            str(root_path),
            "--include",
            "GenMET*",
            "--format",
            "alignment",
        ],
    )

    assert result.exit_code == 0, result.output
    assert result.output.strip() == "\n".join(
        ["version: 1", "fields:", "  GenMET_pt:", "    dtype: float32"]
    )


def test_inspect_schema_missing_input_fails(tmp_path: Path) -> None:
    result = runner.invoke(app, ["inspect", "schema", str(tmp_path / "missing.root")])

    assert result.exit_code != 0
    assert "ROOT input file does not exist" in strip_ansi(result.output)


def test_inspect_schema_malformed_input_fails(tmp_path: Path) -> None:
    bad_path = tmp_path / "not-root.root"
    bad_path.write_text("not a ROOT file", encoding="utf-8")

    result = runner.invoke(app, ["inspect", "schema", str(bad_path)])

    assert result.exit_code != 0
    assert "Could not open ROOT file" in strip_ansi(result.output)
