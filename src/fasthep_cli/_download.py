"""Functions for download command"""

from __future__ import annotations

import json
import os

import requests
import typer


def download_from_url(url: str, destination: str, force: bool = False) -> None:
    """Download a file from a URL"""
    if os.path.exists(path=destination) and not force:
        typer.echo(f"{destination} already exists, skipping...")
        return
    result = requests.get(url, allow_redirects=True, timeout=60)
    with open(destination, "wb") as file_handle:
        file_handle.write(result.content)


def download_from_json(json_input: str, destination: str, force: bool = False) -> None:
    """Download files specified in JSON input file into destination directory.
    JSON input file should be a dictionary with the following structure:
    {   "file1": "url1", "file2": "url2", ... }
    """
    with open(json_input, encoding="utf-8") as json_file:
        data = json.load(json_file)
    if not os.path.exists(destination):
        os.makedirs(destination)
    for name, url in data.items():
        # TODO: this should be a logger
        typer.echo(f"Downloading {name}...")
        output_path = os.path.join(destination, name)
        download_from_url(url, output_path, force)
