from __future__ import annotations

from importlib import import_module, resources
from pathlib import Path
from typing import NamedTuple

import typer
from hepflow.api import init_project

HEP_PROFILE_PACKAGES = [
    "fasthep_curator",
    "fasthep_carpenter",
    "fasthep_render",
]


class ProfileCopyResult(NamedTuple):
    copied: list[Path]
    overwritten: list[Path]
    skipped_existing: list[Path]
    warnings: list[str]


def init_command(
    target_dir: Path = typer.Option(
        Path(),
        "--target-dir",
        help="Project directory where .fasthep/profiles should be created.",
    ),
    include: list[str] = typer.Option(
        [],
        "--include",
        help=(
            "Profile reference to copy into the scaffold. Repeat for multiple "
            "profiles, for example fasthep_workshop:registry or "
            "./profiles/custom.yaml."
        ),
    ),
    profile: list[str] = typer.Option(
        [],
        "--profile",
        help="Profile bundle to scaffold. Repeat for multiple bundles. Currently: HEP.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing copied profile template files.",
    ),
) -> None:
    result = init_project(target_dir=target_dir, force=force, include=include)
    profile_result = copy_profile_bundles(
        target_dir=target_dir,
        profiles=profile,
        force=force,
    )
    if result.created_profile_dir:
        typer.echo(f"Created {result.profile_dir}")
    else:
        typer.echo(f"Found {result.profile_dir}")

    for warning in profile_result.warnings:
        typer.echo(f"Warning: {warning}")

    for path in [*result.copied, *profile_result.copied]:
        typer.echo(f"Wrote {path}")
    for path in [*result.overwritten, *profile_result.overwritten]:
        typer.echo(f"Wrote {path}")
    for path in [*result.skipped_existing, *profile_result.skipped_existing]:
        typer.echo(f"Skipped existing {path}; use --force to overwrite")

    if (
        not result.written
        and not result.skipped_existing
        and not profile_result.copied
        and not profile_result.overwritten
        and not profile_result.skipped_existing
    ):
        typer.echo("No bundled profiles available")


def copy_profile_bundles(
    *,
    target_dir: Path,
    profiles: list[str],
    force: bool,
) -> ProfileCopyResult:
    copied: list[Path] = []
    overwritten: list[Path] = []
    skipped_existing: list[Path] = []
    warnings: list[str] = []

    for profile in profiles:
        normalized = profile.casefold()
        if normalized != "hep":
            warnings.append(f"unknown profile bundle: {profile}")
            continue
        package_names = HEP_PROFILE_PACKAGES

        for package_name in package_names:
            package_result = copy_package_profiles(
                target_dir=target_dir,
                package_name=package_name,
                force=force,
            )
            copied.extend(package_result.copied)
            overwritten.extend(package_result.overwritten)
            skipped_existing.extend(package_result.skipped_existing)
            warnings.extend(package_result.warnings)

    return ProfileCopyResult(
        copied=copied,
        overwritten=overwritten,
        skipped_existing=skipped_existing,
        warnings=warnings,
    )


def copy_package_profiles(
    *,
    target_dir: Path,
    package_name: str,
    force: bool,
) -> ProfileCopyResult:
    copied: list[Path] = []
    overwritten: list[Path] = []
    skipped_existing: list[Path] = []
    warnings: list[str] = []

    try:
        import_module(package_name)
    except ImportError:
        return ProfileCopyResult(
            copied=[],
            overwritten=[],
            skipped_existing=[],
            warnings=[f"profile package not found: {package_name}"],
        )

    profile_dir = resources.files(package_name).joinpath("profiles")
    if not profile_dir.is_dir():
        yaml_files = []
    else:
        yaml_files = sorted(
            (
                child
                for child in profile_dir.iterdir()
                if child.is_file() and child.name.endswith(".yaml")
            ),
            key=lambda child: child.name,
        )
    if not yaml_files:
        return ProfileCopyResult(
            copied=[],
            overwritten=[],
            skipped_existing=[],
            warnings=[f"profile package has no profiles/*.yaml files: {package_name}"],
        )

    destination_dir = Path(target_dir) / ".fasthep" / "profiles" / package_name
    for source in yaml_files:
        destination = destination_dir / source.name
        exists = destination.exists()
        if exists and not force:
            skipped_existing.append(destination)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
        if exists:
            overwritten.append(destination)
        else:
            copied.append(destination)

    return ProfileCopyResult(
        copied=copied,
        overwritten=overwritten,
        skipped_existing=skipped_existing,
        warnings=warnings,
    )
