"""Main package file.

Import classes, exceptions and enums
"""
import pkg_resources
from rak811.exception import Rak811Error # noqa
from rak811.rak811 import ErrorCode, EventCode, Mode, RecvEx, Reset # noqa
from rak811.rak811 import Rak811 # noqa
from rak811.rak811 import Rak811EventError, Rak811ResponseError # noqa
from rak811.serial import Rak811TimeoutError # noqa

try:
    __version__ = pkg_resources.get_distribution('setuptools').version
except Exception:
    __version__ = 'unknown'
