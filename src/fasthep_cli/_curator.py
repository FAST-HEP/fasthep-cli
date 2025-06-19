"""CLI commands for managing FAST-HEP curator"""

import rich
import typer


from fasthep_toolbench.logger import default_logger

logger = default_logger()

app = typer.Typer()


@app.command()
def add(
    files: list[str],
    dataset: str = typer.Option(..., "--dataset", "-d", help="Name of the dataset"),
    event_type: str = "data",
    metadata: str = typer.Option(
        None,
        "--metadata",
        "-m",
        help="JSON string with additional metadata for the dataset",
    ),
    output: str = typer.Option(..., "--output", "-o", help="Output file path"),
) -> None:
    """
    files (list[str]): List of file paths to compile.
    dataset (str): Name of the dataset.
    output (str): Output file path. Created if it does not exist.
    """
    try:
        from fasthep_curator import add_dataset
    except ImportError:
        logger.error(
            "[red]FAST-HEP curator is not installed. Please run 'pip install fasthep-curator'[/]",
        )
        return
    config = add_dataset(
        dataset_name=dataset,
        files=files,
        event_type=event_type,
        metadata=metadata,
        output_file=output,
    )
    logger.info(
        f"[green]Dataset '{dataset}' added to {output}.[/green]",
    )
    logger.debug(
        f"[blue]Configuration: {config}[/blue]",
    )


@app.command()
def check(config_files: list[str]) -> None:
    """
    Check the configuration files for errors.

    Args:
        config_files (list[str]): Path to the configuration file.
    """
    try:
        from fasthep_curator import check as check_config
    except ImportError:
        logger.error(
            "[red]FAST-HEP curator is not installed. Please run 'pip install fasthep-curator'[/]",
        )
        raise

    check_config(config_files, prefix="")
    rich.print("[green]Configuration files are valid.[/green]")


@app.command()
def display(
    config_file: str,
) -> None:
    """
    Display the contents of the configuration file.

    Args:
        config_file (str): Path to the configuration file.
    """

    try:
        from fasthep_curator import load_config
    except ImportError:
        logger.error(
            "[red]FAST-HEP curator is not installed. Please run 'pip install fasthep-curator'[/]",
        )
        raise

    config = load_config(config_file)
    datasets = config.datasets
    if not datasets:
        rich.print("[yellow]No datasets found in the configuration file.[/yellow]")
        return
    # print datasets in a table format
    from rich.table import Table

    table = Table(title="Datasets")
    table.add_column("Name", justify="left", style="cyan")
    table.add_column("Event Type", justify="left", style="magenta")
    table.add_column("Files", justify="left", style="green")
    table.add_column("Metadata", justify="left", style="yellow")
    for dataset in datasets:
        name = dataset.name
        event_type = dataset.eventtype
        files = ", ".join(dataset.files)
        metadata = dataset.metadata
        table.add_row(name, event_type, files, str(metadata))
    rich.print(table)

    metadata = config.metadata
    if metadata:
        rich.print("[blue]Metadata:[/blue]")
        for key, value in metadata.items():
            rich.print(f"[yellow]{key}:[/yellow] {value}")
    else:
        rich.print("[yellow]No metadata found.[/yellow]")
    defaults = config.defaults
    if defaults:
        rich.print("[blue]Defaults:[/blue]")
        for key, value in defaults.items():
            rich.print(f"[yellow]{key}:[/yellow] {value}")
    else:
        rich.print("[yellow]No defaults found.[/yellow]")
