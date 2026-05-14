# fasthep-cli

[![CI](https://github.com/FAST-HEP/fasthep-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/FAST-HEP/fasthep-cli/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/fasthep-cli)](https://pypi.org/project/fasthep-cli/)
[![Python Versions](https://img.shields.io/pypi/pyversions/fasthep-cli)](https://pypi.org/project/fasthep-cli/)
[![Documentation Status](https://readthedocs.org/projects/fasthep-cli/badge/?version=latest)](https://fasthep-cli.readthedocs.io/en/latest/)
[![Discussions](https://img.shields.io/static/v1?label=Discussions\&message=Ask\&color=blue\&logo=github)](https://github.com/FAST-HEP/fasthep/discussions)

<p align="center">
  <a href="https://github.com/FAST-HEP/fasthep">
    <picture>
      <source
        media="(prefers-color-scheme: dark)"
        srcset="https://raw.githubusercontent.com/FAST-HEP/logos-etc/master/fast-hep-white.png"
      >
      <source
        media="(prefers-color-scheme: light)"
        srcset="https://raw.githubusercontent.com/FAST-HEP/logos-etc/master/fast-hep-black.png"
      >
      <img
        alt="FAST-HEP"
        src="https://raw.githubusercontent.com/FAST-HEP/logos-etc/master/fast-hep-black.png"
        width="500"
      >
    </picture>
  </a>
</p>

`fasthep-cli` provides the unified command-line interface for the FAST-HEP ecosystem.

It exposes workflow, rendering, inspection, and utility commands through the `fasthep` executable.

## Scope

`fasthep-cli` is responsible for:

* the `fasthep` command
* workflow compilation and execution commands
* environment and package inspection
* dataset/example downloads
* CLI formatting and UX
* command dispatch to FAST-HEP packages

It intentionally contains very little domain logic itself.

## Design philosophy

`fasthep-cli` should remain thin.

The CLI should:

* parse arguments
* call public package APIs
* display results

It should *not*:

* implement workflow internals
* duplicate runtime logic
* bypass public APIs

This keeps:

* notebook APIs
* Python APIs
* CLI behavior

consistent across the ecosystem.

## Relationship to other FAST-HEP packages

`fasthep-cli` primarily dispatches to:

* `fasthep-flow`

  * workflow compilation and execution

* `fasthep-curator`

  * dataset inspection and validation

* `fasthep-render`

  * plotting and reporting

* `fasthep-carpenter`

  * HEP analysis transforms and runtime extensions

* `fasthep-toolbench`

  * shared CLI utilities and helpers

## Installation

Install directly:

```bash
pip install fasthep-cli
```

Or install the meta package:

```bash
pip install fasthep
```

Development environment:

```bash
pixi install
pixi run ci
```

## Example commands

Compile a workflow:

```bash
fasthep compile examples/CMS/Hinv/author.yaml --work-dir build/Hinv
```

Run a compiled plan:

```bash
fasthep run-plan build/Hinv/plan.yaml
```

Compile and run in one step:

```bash
fasthep run examples/CMS/Hinv/author.yaml --work-dir build/Hinv
```

Inspect installed FAST-HEP packages:

```bash
fasthep versions
```

Download workshop/example datasets:

```bash
fasthep download --json examples/downloads.json --destination data
```

## Documentation

Main FAST-HEP documentation:

* [https://fast-hep.github.io](https://fast-hep.github.io)

API documentation for this package:

* [https://fasthep-cli.readthedocs.io/en/latest/](https://fasthep-cli.readthedocs.io/en/latest/)

## Repository

Main FAST-HEP repository and project links:

* [https://github.com/FAST-HEP/fasthep](https://github.com/FAST-HEP/fasthep)

## Contributing

Contribution guidelines, development setup, and project-wide documentation are maintained centrally in the main FAST-HEP repository.

## Legacy branch

The pre-split prototype CLI implementation is preserved in legacy repositories and branches.

The current repository contains the split-package CLI architecture.

## Status

FAST-HEP is currently in active pre-alpha development.

Interfaces and commands may evolve rapidly while the ecosystem stabilizes.
