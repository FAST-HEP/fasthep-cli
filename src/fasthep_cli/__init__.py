"""FAST-HEP command line package."""

__all__ = ["__version__"]

try:
    from ._version import version as __version__
except ModuleNotFoundError:
    __version__ = "0+unknown"
