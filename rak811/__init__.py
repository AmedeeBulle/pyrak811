"""Main package file.

Import classes, exceptions and enums
"""
import pkg_resources

from .exception import Rak811Error  # noqa: F401
from .rak811 import ErrorCode, EventCode, Mode, RecvEx, Reset  # noqa: F401
from .rak811 import Rak811  # noqa: F401
from .rak811 import Rak811EventError, Rak811ResponseError  # noqa: F401
from .serial import Rak811TimeoutError  # noqa: F401

try:
    __version__ = pkg_resources.get_distribution('setuptools').version
except Exception:
    __version__ = 'unknown'
