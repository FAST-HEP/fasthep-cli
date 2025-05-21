"""Functions for finding FAST-HEP software"""

from __future__ import annotations

from typing import Callable, Iterator

from importlib.metadata import distributions
from rich.progress import Progress, SpinnerColumn, TextColumn


def __find_package_versions(
    filter_function: Callable[[str], bool],
) -> Iterator[tuple[str, str]]:
    """
    Find the versions of a list of packages
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Finding packages...", total=0)

        for dist in distributions():
            progress.update(task, advance=1)
            if filter_function(dist.metadata["Name"].lower()):
                yield dist.metadata["Name"].lower(), dist.version
        progress.update(task, completed=0)


def _is_fasthep_package(package_name: str) -> bool:
    """
    Check if a package is a FAST-HEP package
    """
    fast_hep_prefixes = ["fasthep-", "fast-", "scikit-validate"]
    for prefix in fast_hep_prefixes:
        if package_name.startswith(prefix):
            return True
    return False


def _find_fast_hep_packages() -> list[tuple[str, str]]:
    """
    Find all FAST-HEP packages
    """
    return sorted(list(__find_package_versions(_is_fasthep_package)))
