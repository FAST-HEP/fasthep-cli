from __future__ import annotations

from typing import Any

ROOT_TREE_SOURCE_SPEC = {
    "name": "root_tree",
    "params": {},
    "outputs": {"stream": "event_stream"},
}


def run_root_tree_source(*, ctx: dict[str, Any] | None = None, **params: Any) -> dict[str, Any]:
    return {
        "ctx": dict(ctx or {}),
        "params": dict(params),
    }
