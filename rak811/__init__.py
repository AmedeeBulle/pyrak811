"""Main package file.

Import classes, exceptions and enums
"""
import pkg_resources

from .exception import Rak811Error  # noqa: F401

try:
    __version__ = pkg_resources.get_distribution("rak811").version
except Exception:
    __version__ = "unknown"
