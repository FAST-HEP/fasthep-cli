"""Entry point for fasthep command line interface"""

from __future__ import annotations

from pathlib import Path

import rich
import typer

from fasthep_toolbench.display.console import DisplayFormats, display
from fasthep_toolbench.http import download_from_json
from fasthep_toolbench.package import find_fast_hep_packages, find_hep_packages

from . import __version__
from ._curator import app as curator_app

app = typer.Typer()
app.add_typer(
    curator_app, name="curator", help="Commands for FAST-HEP curator operations"
)

# TODO: Add a logger to the CLI
# 1. implement a callback for the logger setup
# 2. add parameter for --quiet # LOG_LEVEL = logging.ERROR
# 3. add parameter for --verbose # LOG_LEVEL = logging.DEBUG
# 4. add parameter for --log-file # LOG_FILE = "fasthep.log"
# 5. add parameter for --debug <detail> # LOG_LEVEL = logging.<detail>
# where detail is one of [TRACE, TIMING]


@app.callback()
def main_callback(
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress logo"),
) -> None:
    """
    Main callback for the FAST-HEP CLI.
    Use --quiet to suppress logo output
    """
    if not quiet:
        # we could also have `fh`` be quiet by default and `fasthep` the normal version
        from .logo import get_logo

        logo = get_logo()
        typer.echo(logo)


@app.command()
def version() -> None:
    """
    Show version
    """
    rich.print(f"[blue]FAST-HEP CLI Version[/]: [magenta]{__version__}[/]")


@app.command()
def versions(
    display_format: DisplayFormats = typer.Option(
        "simple", "--display", "-d", help="Display format"
    ),
    hep: bool = typer.Option(False, "--hep", "-H", help="Display HEP packages"),
) -> None:
    """Show versions of all found FAST-HEP and HEP packages"""
    fasthep_packages = list(find_fast_hep_packages())
    hep_packages = [] if not hep else list(find_hep_packages())

    if display_format == DisplayFormats.JSON:
        packages = {
            "fasthep_packages": dict(fasthep_packages),
        }
        if hep:
            packages["hep_packages"] = dict(hep_packages)
        display(packages, display_format=display_format)
        return
    headers = ["Package", "Version"]
    display(fasthep_packages, "FAST-HEP Packages", headers, display_format)
    if hep:
        display(hep_packages, "HEP Packages", headers, display_format)


@app.command()
def download(
    json_input: str = typer.Option(None, "--json", "-j", help="JSON input file"),
    destination: str = typer.Option(
        "downloads", "--destination", "-d", help="Destination directory"
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
    return app()


def main_fh() -> typer.Typer:
    """Entry point for fasthep command line interface with 'fh' prefix"""
    return app()
