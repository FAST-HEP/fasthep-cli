from __future__ import annotations

import re
from typing import Any

ROOT_TREE_SOURCE_SPEC = {
    "name": "root_tree",
    "params": {},
    "outputs": {"stream": "event_stream"},
}


def run_root_tree_source(
    *,
    ctx: dict[str, Any] | None = None,
    **params: Any,
) -> dict[str, Any]:
    return {
        "ctx": dict(ctx or {}),
        "params": dict(params),
    }


def strip_ansi(text: str) -> str:
    ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
    return ANSI_RE.sub("", text)
