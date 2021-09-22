"""Interface with the RAK811 module (Firmware V3.0).

Copyright 2021 Philippe Vanhaesendonck

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
from binascii import hexlify
from enum import IntEnum
from logging import getLogger
from re import match
from time import sleep
from typing import List, Union

from RPi import GPIO

from .exception import Rak811Error
from .serial import Rak811Serial, Rak811TimeoutError

RESET_BCM_PORT = 17
RESET_DELAY = 0.01
RESET_POST = 2
RESPONSE_OK = 'OK '
RESPONSE_INIT_OK = 'Initialization OK'
RESPONSE_ERROR = 'ERROR:'
RESPONSE_EVENT = 'at+recv='

# Timeout for response and events
# The RAK811 typically respond in less than 1.5 seconds
RESPONSE_TIMEOUT = 5
# Event wait time strongly depends on duty cycle, when sending often at high SF
# the module will wait to respect the duty cycle.
# In normal operation, 5 minutes should be more than enough.
EVENT_TIMEOUT = 5 * 60

logger = getLogger(__name__)


# RAK811 error codes and associated messages
class ErrorCode(IntEnum):
    """AT commands error codes."""

    ERR_001 = 1
    ERR_002 = 2
    ERR_003 = 3
    ERR_004 = 4
    ERR_005 = 5
    ERR_041 = 41
    ERR_080 = 80
    ERR_081 = 81
    ERR_082 = 82
    ERR_083 = 83
    ERR_084 = 84
    ERR_085 = 85
    ERR_086 = 86
    ERR_087 = 87
    ERR_088 = 88
    ERR_089 = 89
    ERR_090 = 90
    ERR_091 = 91
    ERR_092 = 92
    ERR_093 = 93
    ERR_094 = 94
    ERR_095 = 95
    ERR_096 = 96
    ERR_097 = 97
    ERR_098 = 98
    ERR_099 = 99
    ERR_100 = 100
    ERR_101 = 101
    ERR_102 = 102
    ERR_103 = 102
    ERR_104 = 104
    ERR_INVALID_EVENT = 998
    ERR_UNKNOWN = 999


ERROR_MESSAGE = {
    ErrorCode.ERR_001: 'Unsupported AT command',
    ErrorCode.ERR_002: 'Invalid parameter in AT command',
    ErrorCode.ERR_003: 'Error when reading or writing flash',
    ErrorCode.ERR_004: 'Error reading or writing IIC',
    ErrorCode.ERR_005: 'Error sending through UART',
    ErrorCode.ERR_041: 'BLE in invalid state',
    ErrorCode.ERR_080: 'LoRa busy',
    ErrorCode.ERR_081: 'LoRa service unknown',
    ErrorCode.ERR_082: 'Invalid LoRa parameters',
    ErrorCode.ERR_083: 'Invalid LoRa frequency',
    ErrorCode.ERR_084: 'Invalid LoRa datarate (DR)',
    ErrorCode.ERR_085: 'Invalid LoRa frequency and datarate',
    ErrorCode.ERR_086: 'Device has not joined LoRa network',
    ErrorCode.ERR_087: 'Packet length too long',
    ErrorCode.ERR_088: 'Service closed by server',
    ErrorCode.ERR_089: 'Unsupported region.',
    ErrorCode.ERR_090: 'Restricted duty cycle',
    ErrorCode.ERR_091: 'No valid channel can be found.',
    ErrorCode.ERR_092: 'No free channel found',
    ErrorCode.ERR_093: 'Status is error',
    ErrorCode.ERR_094: 'LoRa transmiting timeout',
    ErrorCode.ERR_095: 'LoRa RX1 timeout',
    ErrorCode.ERR_096: 'LoRa RX2 timeout',
    ErrorCode.ERR_097: 'Error receiving RX1',
    ErrorCode.ERR_098: 'Error  receiving RX2',
    ErrorCode.ERR_099: 'LoRa join failed',
    ErrorCode.ERR_100: 'Repeated downlink',
    ErrorCode.ERR_101: 'Payload size error with transmit DR',
    ErrorCode.ERR_102: 'Too many downlink frames lost',
    ErrorCode.ERR_103: 'Address fail',
    ErrorCode.ERR_104: 'Error verifying MIC',
    ErrorCode.ERR_INVALID_EVENT: 'Invalid event received',
    ErrorCode.ERR_UNKNOWN: 'Unknown error',
}


class Rak811ResponseError(Rak811Error):
    """Exception raised by response from the module.

    Attributes:
        errno -- as returned by the module
        strerror -- textual representation

    """

    def __init__(self, code):
        """Just assign return codes."""
        try:
            self.errno = int(code)
        except ValueError:
            self.errno = code

        if self.errno in ERROR_MESSAGE:
            self.strerror = ERROR_MESSAGE[self.errno]
        else:
            self.strerror = ERROR_MESSAGE[ErrorCode.ERR_UNKNOWN]
        super().__init__(('[Errno {}] {}').format(self.errno, self.strerror))


class Rak811(object):
    """Main class."""

    def __init__(self, **kwargs):
        """Initialise class.

        The serial port is immediately opened and flushed.

        Args:
            response_timeout (optional): override default response timeout.
                Defaults to None.
            event_timeout (optional): override default event timeout.
                Defaults to None.
            Remainder parameters are passed to RackSerial.
        """
        self._response_timeout = kwargs.pop('response_timeout', RESPONSE_TIMEOUT)
        self._event_timeout = kwargs.pop('event_timeout', EVENT_TIMEOUT)
        self._serial = Rak811Serial(
            keep_untagged=True,
            read_buffer_timeout=self._response_timeout,
            **kwargs
        )
        self._downlink = []

    def close(self) -> None:
        """Terminates session.

        Terminates read thread and close serial port.
        """
        self._serial.close()

    def hard_reset(self) -> None:
        """Hard reset of the RAK811 module.

        Hard reset should not be required in normal operation. It needs to be
        issued once after host boot, or module restart.
        Note that we do not cleanup() as the reset port should stay high (it is
        configured that way at boot time).

        Note: left for historical reasons, it does not appear to be effective
        with the V3 firmware
        """
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RESET_BCM_PORT, GPIO.OUT)
        GPIO.output(RESET_BCM_PORT, GPIO.LOW)
        sleep(RESET_DELAY)
        GPIO.output(RESET_BCM_PORT, GPIO.HIGH)
        sleep(RESET_POST)

    """ Private methods."""

    def _int(self, i: str) -> Union[int, str]:
        """Attempt int conversion.

        Args:
            i: Integer string.

        Returns:
            Integer conversion if possible, else the original string.
        """
        try:
            i = int(i)
        except ValueError:
            pass
        return i

    def _send_string(self, string: str) -> None:
        """Send string to the RAK811 module.

        Args:
            string: String to send.
        """
        self._serial.send_string(string)

    def _send_command(self, command: str, timeout: float = None) -> str:
        """Send AT command to the RAK811 module and return the response.

        This method will wait until the module answer or timeout is reached.

        Args:
            command: Command to send
            timeout (optional): Time to wait before raising a timeout.
                Defaults to None.

        Raises:
            Rak811ResponseError: Module answered with an error code.
            Rack811TimeoutError: No answer received and timeout is reached.

        Returns:
            Module answer.
        """
        if timeout is None:
            timeout = self._response_timeout

        self._serial.send_command(command)
        response = self._serial.receive(timeout=timeout)

        # Ignore anything but OK/ERROR messages
        while not (response.startswith(RESPONSE_OK)
                   or response.startswith(RESPONSE_INIT_OK)
                   or response.startswith(RESPONSE_ERROR)):
            response = self._serial.receive()

        if response.startswith(RESPONSE_ERROR):
            raise Rak811ResponseError(response[len(RESPONSE_ERROR):])
        elif response.startswith(RESPONSE_INIT_OK):
            return response[len(RESPONSE_INIT_OK):]
        else:
            return response[len(RESPONSE_OK):]

    def _send_command_list(self, command: str) -> List[str]:
        """Send AT command to the RAK811 module and return the responses.

        Similar to _send_command, but returns the complete read buffer. It is
        used for commands returning several lines.

        This method will wait until the module answer or timeout is reached.

        Args:
            command: Command to send

        Raises:
            Rak811ResponseError: Module answered with an error code.
            Rack811TimeoutError: No answer received and timeout is reached.

        Returns:
            List of module answers.
        """
        self._serial.send_command(command)

        prelude = []
        response = []
        while True:
            if not response:
                response = self._serial.receive(single=False)
            if response[0].startswith(RESPONSE_OK):
                response[0] = response[0][len(RESPONSE_OK):]
                break
            elif response[0].startswith(RESPONSE_INIT_OK):
                response[0] = response[0][len(RESPONSE_INIT_OK):]
                break
            elif response[0].startswith(RESPONSE_ERROR):
                raise Rak811ResponseError(response[0][len(RESPONSE_ERROR):])
            else:
                # Ignore anything until we get an OK/ERROR message
                prelude.append(response.pop(0))

        return prelude + response

    def _get_events(self, timeout: float = None) -> List[str]:
        """Get list of events from the RAK811 module.

        Args:
            timeout (optional): Time to wait before raising a timeout.
                Defaults to None.

        Raises:
            Rack811TimeoutError: No answer received and timeout is reached.

        Returns:
            Event list
        """
        if timeout is None:
            timeout = self._event_timeout

        return [i[len(RESPONSE_EVENT):] if i.startswith(RESPONSE_EVENT) else i for i in
                self._serial.receive(single=False, timeout=timeout)]

    def _add_downlink(self, port: str, rssi: str, snr: str, length: str, data: str) -> None:
        """Add message to the downlink list.

        Args:
            port: Message port.
            rssi: Message RSSI.
            snr: Message SNR.
            length: Message length.
            data: Message data
        """
        r_port = 0 if port is None else self._int(port)
        r_rssi = self._int(rssi)
        r_snr = self._int(snr)
        r_len = self._int(length)
        if r_len > 0:
            try:
                r_data = bytes.fromhex(data)
            except ValueError:
                r_data = b''
        else:
            r_data = b''
        self._downlink.append(
            {
                'port': r_port,
                'rssi': r_rssi,
                'snr': r_snr,
                'len': r_len,
                'data': r_data,
            }
        )

    def _process_events(self, timeout=None) -> None:
        """Process module event queue.

        Process event queue looking for incoming (downlink) messages.

        Args:
            timeout (optional): maximum time to wait for event.
                Defaults to None.

        Raises:
            - Rak811TimeoutError: no answer
            - Rak811ResponseError: error returned or unexpected response
                received
        """
        events = self._get_events(timeout)
        # Check for downlink
        for event in events:
            # LoRaWan format: <port>,<rssi>,<snr>,<len>[:<data>]
            # LoRa P2P format: ,<rssi>,<snr>,<len>[:<data>]
            m = match(r'((\d+),)?(-?\d+),(-?\d+),(\d+)(:(.*))?$', event)
            if m:
                _, port, rssi, snr, length, _, data = m.groups()
                self._add_downlink(port, rssi, snr, length, data)
            else:
                raise Rak811ResponseError(ErrorCode.ERR_INVALID_EVENT)

    """Generic get / set commands."""

    def set_config(self, config: str) -> List[str]:
        """Execute set_config command.

        The module will return:
            - "OK" (most cases)
            - "OK" / "<BOOT MODE>" (device:boot)
            - some info / "Initialization OK" (device:restart / lora:work_mode)

        Args:
            config: Config string to send in the format <type>:<topic>[:<param>]...
                Supported types and topics:
                - device: restart, sleep, boot, status, uart, uart_mode, gpio
                - lora: region, channel, dev_eui, app_eui, app_key, dev_addr,
                    apps_key, nwks_key, join_mode, work_mode, ch_mask, class,
                    confirm, dr, tx_power, adr, send_interval
                - lorap2p: transfer_mode, channel configuration

        Raises:
            Rak811ResponseError: Module answered with an error code.
            Rack811TimeoutError: No answer received and timeout is reached.

        Returns:
            List of responses (Informational)
        """
        # We use the "_list" variant to drain the buffer
        return self._send_command_list(f'set_config={config}')

    def get_config(self, config: str) -> List[str]:
        """Get configuration item.

        Args:
            config: Config string to send in the format <type>:<topic>[:<param>]
                Supported types and topics:
                - device: status, gpio, adc
                - lora: channel, status

        Raises:
            Rak811ResponseError: Module answered with an error code.
            Rack811TimeoutError: No answer received and timeout is reached.

        Returns:
            Module answers (list).
        """
        return(self._send_command_list(f'get_config={config}'))

    """General AT commands."""

    @property
    def version(self) -> str:
        """Get module version.

        Raises:
            - Rak811TimeoutError: no answer
            - Rak811ResponseError: error returned

        Returns:
            Module version.
        """
        return(self._send_command('version'))

    @property
    def help(self) -> List[str]:
        """Get module help.

        Raises:
            - Rak811TimeoutError: no answer
            - Rak811ResponseError: error returned

        Returns:
            Module help (list).
        """
        return(self._send_command_list('help'))

    def run(self) -> None:
        """Exit boot mode and enter normal mode.

        Raises:
            - Rak811TimeoutError: no answer
            - Rak811ResponseError: error returned
        """
        self._send_command('run')

    """Interface commands."""

    def send_uart(self, data: Union[bytes, str], index: int = 3) -> None:
        """Send data over UART.

        Args:
            data: data to be sent. If the datatype is bytes it will be send
                as such. Strings will be converted to bytes.
            index (optional): UART index to use (1, 3). Defaults to 3.
                UART1 is the AT Command interface, so you probably want to use
                UART3!

        Raises:
            - Rak811TimeoutError: no answer
            - Rak811ResponseError: error returned
        """
        if type(data) is not bytes:
            data = (bytes)(data, 'utf-8')
        data = hexlify(data).decode('ascii')

        self._send_command(f'send=uart:{index}:{data}')

    """LoRa commands"""

    def join(self) -> None:
        """Join the configured network.

        ABP requires the following parameters to be set prior join:
            - dev_addr
            - nwks_key
            - apps_key

        OTAA requires the following parameters to be set prior join:
            - dev_eui
            - app_eui
            - app_key

        Raises:
            - Rak811TimeoutError: no answer
            - Rak811ResponseError: error returned
        """
        # Extend timeout for the join command
        self._send_command('join', timeout=self._event_timeout)

    def send(self, data: Union[bytes, str], port: int = 1) -> None:
        """Send LoRaWan message.

        Args:
            data: data to be sent. If the datatype is bytes it will be send
                as such. Strings will be converted to bytes.
            port (optional): port number to use (1-223). Defaults to 1.

        Raises:
            - Rak811TimeoutError: no answer
            - Rak811ResponseError: error returned
        """
        if type(data) is not bytes:
            data = (bytes)(data, 'utf-8')
        data = hexlify(data).decode('ascii')

        self._send_command(f'send=lora:{port}:{data}', timeout=self._event_timeout)

        # Process events - Check for downlink / send confirmation
        # It is issued immediately after the "OK" response so don't have to
        # wait long.
        try:
            self._process_events(timeout=0.1)
        except Rak811TimeoutError:
            logger.debug('No downlink')
        else:
            logger.debug('Downlink available')

    @property
    def nb_downlinks(self) -> int:
        """Get the number of downlink messages in the receive buffer.

        Returns:
            Number of messages in the downlink buffer.
        """
        return len(self._downlink)

    def get_downlink(self) -> str:
        """Get a downlink message from the receive buffer.

        Returns:
            Dictionary with the following keys:
                port: port number
                rssi: RSSI
                snr: SNR
                len: data length (0 for empty / confirmation messages)
                data: data itself (None is len is 0)
        """
        if len(self._downlink) == 0:
            return None
        else:
            return self._downlink.pop(0)

    """ LoraP2P commands."""

    def send_p2p(self, data: Union[bytes, str]) -> None:
        """Send P2P message.

        Args:
            data: data to be sent. If the datatype is bytes it will be send
                as such. Strings will be converted to bytes.

        Raises:
            - Rak811TimeoutError: no answer
            - Rak811ResponseError: error returned
        """
        if type(data) is not bytes:
            data = (bytes)(data, 'utf-8')
        data = hexlify(data).decode('ascii')

        self._send_command(f'send=lorap2p:{data}')

    def receive_p2p(self, timeout: float) -> None:
        """Wait for P2P message.

        The method wil return when one or more messages are received or when
        timeout is reached.

        The method does not return messages, use nb_downlinks and
        get_downlink() to fetch downlinks.

        Args:
            timeout: maximum time to wait.
        """
        try:
            self._process_events(timeout=timeout)
        except Rak811TimeoutError:
            logger.debug('Nothing received')
        else:
            logger.debug('Message available')
