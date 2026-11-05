"""When the FAST-HEP logo is printed.

The group callback decides whether a logo is allowed at all (``--quiet``, the
``FASTHEP_NO_LOGO`` environment variable, a terminal on stdout) and stores the answer in
``ctx.meta``. Each command may additionally turn the logo off from its own parsed options,
for example ``diff --json``; :class:`FastHepCommand` combines the two just before the command
runs, after its options have been parsed.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from importlib import import_module
from typing import Any

import typer
from typer.core import TyperCommand

LOGO_META_KEY = "fasthep.logo"

#: Predicate over a command's parsed parameters: True turns the logo off for that call.
LogoOff = Callable[[Mapping[str, Any]], bool]


def logo_allowed(*, quiet: bool, environ: Mapping[str, str], isatty: bool) -> bool:
    """Whether the environment allows a logo: not quiet, not disabled, stdout is a terminal."""
    return not (quiet or environ.get("FASTHEP_NO_LOGO") or not isatty)


def print_logo() -> None:
    try:
        logo_module = import_module("fasthep_cli.logo")
        typer.echo(logo_module.get_logo())
    except Exception:
        return


class FastHepCommand(TyperCommand):
    """A command that prints the logo once, unless the environment or the command opts out."""

    logo_off_when: LogoOff | None = None

    # Typer vendors Click; its Context is a subclass of the base class's parameter type.
    def invoke(self, ctx: typer.Context) -> Any:  # type: ignore[override]
        off = bool(self.logo_off_when and self.logo_off_when(ctx.params))
        if ctx.meta.get(LOGO_META_KEY, False) and not off:
            print_logo()
        return super().invoke(ctx)


def logo_command(predicate: LogoOff | None = None) -> type[FastHepCommand]:
    """A :class:`FastHepCommand` class whose logo is off when ``predicate(params)`` is true."""
    namespace = {
        "logo_off_when": None if predicate is None else staticmethod(predicate)
    }
    return type("FastHepCommand", (FastHepCommand,), namespace)
