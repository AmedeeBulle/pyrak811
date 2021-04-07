"""RAK811 serial communication layer.

Copyright 2019, 2021 Philippe Vanhaesendonck

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

SPDX-License-Identifier: Apache-2.0
"""
from logging import getLogger
from re import match
from threading import Condition, Event, Thread
from time import sleep
from typing import List, Union

from rak811.exception import Rak811Error
from serial import Serial

# Default instance parameters. Can be overridden  at creation
# Serial port configuration
PORT = '/dev/serial0'
BAUDRATE = 115200
# Timeout for the reader thread. Any value will do, the only impact is the time
# needed to stop the thread when the instance is destroyed...
TIMEOUT = 2
# Timeout for response and events
# The RAK811 typically respond in less than 1.5 seconds
READ_BUFFER_TIMEOUT = 5

# Constants
EOL = '\r\n'


logger = getLogger(__name__)


class Rak811TimeoutError(Rak811Error):
    """Read timeout exception."""

    pass


class Rak811Serial(object):
    """Handles serial communication between the RPi and the RAK811 module."""

    def __init__(self,
                 port=PORT,
                 baudrate=BAUDRATE,
                 timeout=TIMEOUT,
                 read_buffer_timeout=READ_BUFFER_TIMEOUT,
                 keep_untagged=False,
                 **kwargs):
        """Initialise class.

        The serial port is immediately opened and flushed.
        All parameters are optional and passed to Serial.
        """
        self._read_buffer_timeout = read_buffer_timeout
        self._serial = Serial(port=port,
                              baudrate=baudrate,
                              timeout=timeout,
                              **kwargs)
        self._serial.reset_input_buffer()

        self._keep_untagged = keep_untagged

        # Mutex
        self._cv_serial = Condition()
        self._read_buffer = []

        # Read thread
        self._read_done = Event()
        self._read_thread = Thread(target=self._read_loop, daemon=True)
        self._read_thread.start()

        self._alive = True
        logger.debug('Serial initialized')

    def close(self):
        """Release resources."""
        if self._alive:
            self._read_done.set()
            self._read_thread.join()
            self._serial.close()
            self._alive = False

    def _read_loop(self):
        """Read thread.

        Continuously read serial. When data is available we want to read all of
        it and notify once:
            - We need to drain the input after a response. If we notify()
            too early the module will miss next command
            - We want to catch all events at the same time
        """
        while not self._read_done.is_set():
            line = self._serial.readline()
            if line != b'':
                # Not a timeout; process data stream
                with self._cv_serial:
                    while True:
                        try:
                            line = line.decode('ascii').rstrip(EOL)
                        except UnicodeDecodeError:
                            # Wrong speed or port not configured properly
                            line = '?'
                        if match(r'^(OK|ERROR|at+)', line):
                            logger.debug(f'Received: >{line}<')
                            self._read_buffer.append(line)
                        elif self._keep_untagged:
                            logger.debug(f'Received untagged: >{line}<')
                            self._read_buffer.append(line)
                        else:
                            logger.debug(f'Ignoring untagged: >{line}<')
                        sleep(0.1)
                        if self._serial.in_waiting > 0:
                            line = self._serial.readline()
                        else:
                            break
                    if len(self._read_buffer) > 0:
                        self._cv_serial.notify()

    def receive(self, single: bool = True, timeout: int = None) -> Union[str, List[str]]:
        """Receive data from module.

        This is a blocking call: it will data or raise Rak811TimeoutError if
        nothing is received in time.

        Args:
            single (optional): Return single line of data when true, otherwise
                all available lines are returned. Defaults to True.
            timeout (optional): Time to wait for. Defaults to None.

        Raises:
            Rak811TimeoutError: No data received in time.

        Returns:
            Single line of data or list of lines.
        """
        if timeout is None:
            timeout = self._read_buffer_timeout

        with self._cv_serial:
            while len(self._read_buffer) == 0:
                success = self._cv_serial.wait(timeout)
                if not success:
                    raise Rak811TimeoutError('Timeout while waiting for data')
            if single:
                response = self._read_buffer.pop(0)
            else:
                response = self._read_buffer
                self._read_buffer = []
        return response

    def send_string(self, string):
        """Send string to the module."""
        logger.debug(f"Sending: >{string.encode('unicode_escape').decode('utf-8')}<")
        self._serial.write((bytes)(string, 'utf-8'))

    def send_command(self, command):
        """Send AT command to the module."""
        self.send_string('at+{0}\r\n'.format(command))
