"""Entry point for fasthep command line interface"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

import rich
import typer
from tabulate import tabulate

# from .logger import console_handler, user_logger
from . import __version__
from ._download import download_from_json
from ._software import _find_fast_hep_packages

app = typer.Typer()

# TODO: Add a logger to the CLI
# 1. implement a callback for the logger setup
# 2. add parameter for --quiet # LOG_LEVEL = logging.ERROR
# 3. add parameter for --verbose # LOG_LEVEL = logging.DEBUG
# 4. add parameter for --log-file # LOG_FILE = "fasthep.log"
# 5. add parameter for --debug <detail> # LOG_LEVEL = logging.<detail>
# where detail is one of [TRACE, TIMING]


@app.command()
def version() -> None:
    """
    Show version
    """
    rich.print(f"[blue]FAST-HEP CLI Version[/]: [magenta]{__version__}[/]")


class DisplayFormats(str, Enum):
    """Display formats for command output"""

    SIMPLE = "simple"
    PIP = "pip"
    TABLE = "table"


@app.command()
def versions(
    display_format: DisplayFormats = typer.Option(
        "simple", "--display", "-d", help="Display format"
    ),
) -> None:
    """Show versions of all found FAST-HEP packages"""
    separator = ": "
    if display_format == DisplayFormats.PIP:
        separator = "=="

    if display_format in (DisplayFormats.SIMPLE, DisplayFormats.PIP):
        for package, _version in _find_fast_hep_packages():
            rich.print(f"[blue]{package}[/]{separator}[magenta]{_version}[/]")
    elif display_format == DisplayFormats.TABLE:
        headers = ["Package", "Version"]
        table = list(_find_fast_hep_packages())
        tablefmt = "github"
        rich.print(
            tabulate(
                table,
                headers=headers,
                tablefmt=tablefmt,
                colalign=("left", "right"),
            )
        )


@app.command()
def download(
    json_input: str = typer.Option(None, "--json", "-j", help="JSON input file"),
    destination: str = typer.Option(
        None, "--destination", "-d", help="Destination directory"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force download; overwriting existing files"
    ),
) -> None:
    """Download files specified in JSON input file into destination directory.
    JSON input file should be a dictionary with the following structure:
    {   "file1": "url1", "file2": "url2", ... }
    """
    download_from_json(json_input, destination, force)


@app.command()
def carpenter(
    dataset_cfg: Path = typer.Argument(None, help="Dataset config to run over"),
    sequence_cfg: Path = typer.Argument(None, help="Config for how to process dataset"),
    output_dir: str = typer.Option(
        "output", "--outdir", "-o", help="Where to save the results"
    ),
    processing_backend: str = typer.Option(
        "multiprocessing", "--backend", "-b", help="Backend to use for processing"
    ),
    store_bookkeeping: bool = typer.Option(
        True, "--store-bookkeeping", "-s", help="Store bookkeeping information"
    ),
) -> None:
    """
    Run the FAST-HEP carpenter
    """
    try:
        from fasthep_carpenter import run_carpenter
    except ImportError:
        rich.print(
            "[red]FAST-HEP carpenter is not installed. Please run 'pip install fasthep-carpenter'[/]",
        )
        return
    run_carpenter(
        dataset_cfg,
        sequence_cfg,
        output_dir,
        processing_backend,
        store_bookkeeping,
    )


@app.command()
def plotter(
    input_files: list[str] = typer.Argument(None, min=1, help="Input files"),
    config_file: str = typer.Option(None, "--config", "-c", help="PlotConfig file"),
    output_dir: str = typer.Option(
        "output", "--outdir", "-o", help="Where to save the results"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing output_dir"
    ),
) -> None:
    """Command to invoke the FAST-HEP plotter"""
    from ._plotter import _make_plots

    _make_plots(input_files, config_file, output_dir, force)


def main() -> typer.Typer:
    """Entry point for fasthep command line interface"""
    from .logo import get_logo

    logo = get_logo()
    typer.echo(logo)
    return app()
