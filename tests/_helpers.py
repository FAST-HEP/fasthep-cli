from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import awkward as ak
import numpy as np
import uproot
import yaml
from typer.testing import CliRunner

runner = CliRunner(env={"FASTHEP_NO_LOGO": "1"})


def fake_run_result(outdir: Path) -> SimpleNamespace:
    return SimpleNamespace(
        backend="local",
        strategy="default",
        summary={
            "summary_path": str(outdir / "run_summary.yaml"),
            "artifacts_path": str(outdir / "artifacts"),
        },
    )


def write_workflow(tmp_path: Path) -> Path:
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


def write_empty_plan(tmp_path: Path, *, variation: str | None = None) -> Path:
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


def schema_fixture(tmp_path: Path) -> Path:
    root_path = tmp_path / "schema.root"
    with uproot.recreate(root_path) as root_file:
        root_file.mktree(
            "Events",
            {
                "GenJetAK8_eta": ak.values_astype(
                    ak.Array([[1.0, 2.0], [], [3.0]]),
                    np.float32,
                ),
                "GenJetAK8_hadronFlavour": ak.values_astype(
                    ak.Array([[5], [], [4, 0]]),
                    np.int32,
                ),
                "GenMET_pt": np.array([20.0, 30.0, 40.0], dtype=np.float32),
                "HLT_IsoMu24": np.array([True, False, True]),
            },
        )
    return root_path
