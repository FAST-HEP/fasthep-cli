# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project uses
calendar versioning (`YYYY.MM.N`) rather than semantic versioning.

Add new entries under `## [Unreleased]`, in the category they belong to. At release time, rename
`## [Unreleased]` to `## [<version>] - <YYYY-MM-DD>` and start a fresh `## [Unreleased]` above it.

## [Unreleased]

### Added

- Progress display for distributed execution updates.

### Changed

- Now depends on `fasthep-toolbench[display,http]` explicitly, since Toolbench is making `rich`,
  `httpx` and `tabulate` optional extras rather than hard dependencies.

## [2026.08.2] - 2026-08-25

### Added

- Partition selection for runtime commands.
- Simple progress reporting during command execution.
