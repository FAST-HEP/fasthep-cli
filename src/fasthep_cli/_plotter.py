"""Functions for connecting to fasthep-plotter"""

from __future__ import annotations

import os

import rich


def _run_checks(
    input_files: list[str],
    config_file: str,
    output_dir: str,
    force: bool,
) -> None:
    if not os.path.exists(config_file):
        rich.print(f"[red]Config file {config_file} does not exist[/]")
        raise FileNotFoundError(f"Config file {config_file} does not exist")
    for input_file in input_files:
        if not os.path.exists(input_file):
            rich.print(f"[red]Input file {input_file} does not exist[/]")
            raise FileNotFoundError(f"Input file {input_file} does not exist")
    if os.path.exists(output_dir) and not force:
        rich.print(
            f"[red]Output directory {output_dir} already exists. Use --force to overwrite.[/]",
        )
        raise FileExistsError(
            f"Output directory {output_dir} already exists and --force was not used"
        )


def _make_plots(
    input_files: list[str],
    config_file: str,
    output_dir: str,
    force: bool,
) -> None:
    from fast_plotter.v1 import make_plots

    _run_checks(input_files, config_file, output_dir, force)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    make_plots(config_file, input_files, output_dir)
