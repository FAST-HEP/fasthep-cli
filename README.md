# fasthep-cli

[![Actions Status][actions-badge]][actions-link]
[![Documentation Status][rtd-badge]][rtd-link]

[![PyPI version][pypi-version]][pypi-link]
[![PyPI platforms][pypi-platforms]][pypi-link]

[![GitHub Discussion][github-discussions-badge]][github-discussions-link]
[![Gitter][gitter-badge]][gitter-link]

<!-- prettier-ignore-start -->
[actions-badge]:            https://github.com/FAST-HEP/fasthep-cli/workflows/CI/badge.svg
[actions-link]:             https://github.com/FAST-HEP/fasthep-cli/actions
[github-discussions-badge]: https://img.shields.io/static/v1?label=Discussions&message=Ask&color=blue&logo=github
[github-discussions-link]:  https://github.com/FAST-HEP/fasthep-cli/discussions
[gitter-badge]:             https://badges.gitter.im/FAST-HEP/community.svg
[gitter-link]:              https://gitter.im/FAST-HEP/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge
[pypi-link]:                https://pypi.org/project/fasthep-cli/
[pypi-platforms]:           https://img.shields.io/pypi/pyversions/fasthep-cli
[pypi-version]:             https://badge.fury.io/py/fasthep-cli.svg
[rtd-badge]:                https://readthedocs.org/projects/fasthep-cli/badge/?version=latest
[rtd-link]:                 https://fasthep-cli.readthedocs.io/en/latest/?badge=latest
[sk-badge]:                 https://scikit-hep.org/assets/images/Scikit--HEP-Project-blue.svg
<!-- prettier-ignore-end -->

A Command Line Interface (CLI) for the [FAST-HEP](https://fast-hep.github.io/)
project. Includes simplified commands for the following packages:

- [fasthep-curator](https://github.com/FAST-HEP/fasthep-curator)
- [fasthep-flow](https://github.com/FAST-HEP/fasthep-flow)
- [fasthep-gitlab](https://github.com/FAST-HEP/fasthep-gitlab)
- [fasthep-plot](https://github.com/FAST-HEP/fasthep-plot)
- [fasthep-validate](https://github.com/FAST-HEP/fasthep-validate)

as well as a few other utilities (e.g. `download`, `versions`). All commands are
bundled under the `fasthep` (or `fh`) namespace.

## Installation

You can install the package using `pip`:

```bash
pip install fasthep-cli
```

This package will not install any of the above packages. You need to install
them separately if you want to use them. Alternatively, you can install all of
them at once using the `fasthep` meta-package:

```bash
pip install fasthep[full]
```

for the full set of dependencies.
