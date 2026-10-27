# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project uses
calendar versioning (`YYYY.MM.N`) rather than semantic versioning.

Add new entries under `## [Unreleased]`, in the category they belong to. At release time, rename
`## [Unreleased]` to `## [<version>] - <YYYY-MM-DD>` and start a fresh `## [Unreleased]` above it.

## [Unreleased]

### Changed

- Depends on `fasthep-flow`, `fasthep-curator`, `fasthep-render`, and `fasthep-toolbench[display,http]`
  at `>=2026.10.1` (previously unpinned, except `fasthep-render` which was not a direct dependency
  at all), and on `typer >=0.27.0` (previously unpinned); older `typer` releases call a
  `click.utils.get_binary_stream` API that now raises a `DeprecationWarning` under strict
  `filterwarnings = ["error"]` test suites.

## [2026.10.1] - 2026-10-26

### Added

- Progress display for distributed execution updates.

### Changed

- Now depends on `fasthep-toolbench[display,http]` explicitly, since Toolbench is making `rich`,
  `httpx` and `tabulate` optional extras rather than hard dependencies.

## [2026.08.2] - 2026-08-25

### Added

- Partition selection for runtime commands.
- Simple progress reporting during command execution.
